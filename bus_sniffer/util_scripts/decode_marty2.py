#    Copyright 2022-2023 Daniel Balsom
#    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#    Permission is hereby granted, free of charge, to any person obtaining a
#    copy of this software and associated documentation files (the “Software”),
#    to deal in the Software without restriction, including without limitation
#    the rights to use, copy, modify, merge, publish, distribute, sublicense,
#    and/or sell copies of the Software, and to permit persons to whom the
#    Software is furnished to do so, subject to the following conditions:
#
#    The above copyright notice and this permission notice shall be included in
#    all copies or substantial portions of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER   
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#   Decode.py 
#
#   Decode a CSV file produced by PulseView/DSView into a cycle trace log.
#   Before decoding, the cycles should be extracted via 'export_cycles.py'
#   
#   The input file should have the following columns:
#   Time(s),
#   AD0,AD1,AD2,AD3,AD4,AD5,AD6,AD7,
#   A8,A9,A10,A11,A12,A13,A14,A15,A16,A17,A18,A19,
#   CLK,READY,QS0,QS1,S0,S1,S2
#   
#   Command Line Arguments:
#   input_csv output_csv

import pandas as pd
import sys

from enum import Enum, auto
from iced_x86 import Decoder, Formatter, FormatterSyntax

CLOCK_DIVISOR = 3

BUS_MAPPING = {
    0: 'INTA',
    1: 'IOR',
    2: 'IOW',
    3: 'HALT',
    4: 'CODE',
    5: 'MEMR',
    6: 'MEMW',
    7: 'PASV'
}

Q_MAPPING = {
    '00': '.',
    '01': 'F',
    '10': 'E',
    '11': 'S'
}

SEG_MAPPING = {
    '00': 'ES',
    '01': 'SS',
    '10': 'CS',
    '11': 'DS'
}

ADDRESS_COLS = ['AD0', 'AD1', 'AD2', 'AD3', 'AD4', 'AD5', 'AD6', 'AD7', 'A8', 'A9', 'A10', 'A11', 'A12', 'A13', 'A14', 'A15', 'A16', 'A17', 'A18', 'A19']
DATA_COLS = ['AD0', 'AD1', 'AD2', 'AD3', 'AD4', 'AD5', 'AD6', 'AD7']

INSTR_PREFIXES = {0x26, 0x2E, 0x36, 0x3E, 0xF0, 0xF1, 0xF2, 0xF3}

class State(Enum):
    TI = auto()
    T1 = auto()
    T2 = auto()
    T3 = auto()
    Tw = auto()
    T4 = auto()

def decode_address(row):
    # Construct binary representation by joining values of AD columns
    binary_str = ''.join(map(str, [int(row[col]) for col in reversed(ADDRESS_COLS)]))

    # Convert the binary string to an integer
    address_value = int(binary_str, 2)

    # Convert the integer to hexadecimal and pad to 5 digits
    return "'" + format(address_value, '05X')

def decode_data(row):
    # Construct binary representation by joining values of AD columns
    binary_str = ''.join(map(str, [int(row[col]) for col in reversed(DATA_COLS)]))
    # Convert the binary string to an integer
    data_value = int(binary_str, 2)

    # Convert the integer to hexadecimal and pad to 5 digits
    return "'" + format(data_value, '02X')

def decode_status(row):
    # Convert 3-bit value to decimal
    return row['S2']*4 + row['S1']*2 + row['S0']

def add_ale_column(df):
    condition = (df['B'].shift(1) == 7) & (df['B'] != 7)
    df['ALE'] = '.'
    df.loc[condition, 'ALE'] = 'A'
    return df

def add_ale_and_al_columns(df):
    # Condition for ALE
    condition = (df['B'].shift(1) == 7) & (df['B'] != 7)
    
    # Default columns
    df['ALE'] = '.'
    df['AL'] = None
    
    # Set ALE where condition is true
    df.loc[condition, 'ALE'] = 'A'
    
    # Now, for AL column
    last_latched_address = None
    for index, row in df.iterrows():
        if row['ALE'] == 'A':
            last_latched_address = row['ADDR']
        
        df.at[index, 'AL'] = last_latched_address

    return df
    
def add_t_and_d_column(df):
    state = State.TI
    next_state = None 
    do_wait_state = False
    
    df['PREV_R'] = df['READY'].shift(1)
    
    for index, row in df.iterrows():
        
        data_bus_valid = False
    
        if next_state is not None:
            state = next_state
            next_state = None
        elif row['ALE'] == 'A':
            state = State.T1
        elif state == State.T1:
            state = State.T2
        elif state == State.T2:
            if row['READY'] == 1:
                data_bus_valid = True
            state = State.T3
        elif state == State.T3:
            if row['PREV_R'] == 0 or row['READY'] == 0:
                state = State.Tw
            else:
                state = State.T4
        elif state == State.Tw:
            if row['PREV_R'] == 1:
                data_bus_valid = True
                state = State.T4
            else:
                state = State.Tw
        elif state == State.T4:
            state = State.TI

        if data_bus_valid:
            df.at[index, 'D'] = decode_data(row)

        # Set the T column for the current row
        df.at[index, 'T'] = state.name

    # Drop the temporary next_QOP column after use 
    df = df.drop(columns=['PREV_R'])
        
    return df
    
def add_qop_column(df):
    # Apply the mapping for the QOP column
    df['QOP'] = df.apply(lambda row: Q_MAPPING[f"{int(row['QS1'])}{int(row['QS0'])}"], axis=1)
    
    return df    
    
def add_seg_column(df):
    
    for index, row in df.iterrows():
        # If 'ALE' signal is low, we can decode the segment status from S3-S4 (A16-A17)
        if row['ALE'] != 'A' and row['T'] != 'TI':
            # Apply the mapping for the SEG column.
            df.at[index, 'SEG'] = SEG_MAPPING[f"{int(row['A17'])}{int(row['A16'])}"]

    return df            

def add_busl_column(df):
    # Initialize a variable to hold the latched value of 'BUS'
    latched_value = ""
    # Loop through each row in the DataFrame
    for index, row in df.iterrows():
        # If 'ALE' is 'A', update the latched value
        if row['ALE'] == 'A':
            latched_value = row['BUS']
        elif row['T'] == 'TI':
            latched_value = 'PASV'
            
        # Assign the latched value to the 'BUSL' column
        df.at[index, 'BUSL'] = latched_value

    return df    
    
def add_time_delta(df):
    """Add time delta in nanoseconds to the DataFrame."""

    df['ns_d'] = df['Time(s)'].diff().fillna(0) * 1e9
    df.at[0, 'ns_d'] = 0
    df['ns_d'] = df['ns_d'].astype(int)

    return df

def calculate_d_accum(df):
    # Create a column that indicates a change in the 'CLK' value
    df['CLK_change'] = df['CLK'].diff() != 0

    # Shift the CLK_change by one row so that accumulation continues until the row where the change occurs
    df['group'] = df['CLK_change'].shift(fill_value=False).cumsum()

    # Create an accumulator which resets based on the shifted 'group' values
    df['d_accum'] = df.groupby(df['group'])['ns_d'].cumsum()

    # Drop the 'group' column as it was just an intermediate step
    df.drop('group', axis=1, inplace=True)

    return df

def filter_clock_signal(df):
    # Define the expected half-cycle time and its half value for noise detection
    expected_time = 105  # in ns
    noise_threshold = expected_time / 2

    # Identify rows where CLK_change is TRUE
    transitions = df[df['CLK'].diff() != 0]

    # Determine rows that are considered noise
    mask = transitions['d_accum'] < noise_threshold

    # Mark these transitions as noise
    noisy_transitions = transitions[mask]
    
    df['noise'] = False
    df.loc[noisy_transitions.index, 'noise'] = True

    return df

def remove_noisy_rows_and_recalculate(df):
    # 1. Remove rows with noise
    df_cleaned = df[df['noise'] == False].copy()

    # 2. Recalculate 'ns_d' column
    df_cleaned['ns_d'] = (df_cleaned['Time(s)'] - df_cleaned['Time(s)'].shift(fill_value=0)) * 1e9  # converting to nanoseconds

    # 3. Recalculate 'd_accum' column using the previous `calculate_d_accum` function
    df_cleaned = calculate_d_accum(df_cleaned)
    
    return df_cleaned

def insert_column_after(df, col_after, new_col, new_col_data):
    # Get the index of the column after which the new column will be inserted
    col_after_index = df.columns.get_loc(col_after)
    
    # Insert the new column after the specified existing column
    df.insert(col_after_index + 1, new_col, new_col_data)

    return df

def partial_reorder_columns(df, order_list):
    # Filter out the columns from the DataFrame that are not in the order_list
    other_columns = [col for col in df.columns if col not in order_list]
    
    # Combine the ordered columns with the other columns
    new_order = order_list + other_columns
    
    # Reorder the DataFrame
    df = df[new_order]
    
    return df

def update_queue(df):
    df['Q0'] = None
    df['Q1'] = None
    df['Q2'] = None
    df['Q3'] = None
    df['QL'] = 0  # Queue Length, initialize to 0

    # Shift the QOP column up by one row for the next row value
    df['next_QOP'] = df['QOP'].shift(-1)

    for index, row in df.iterrows():
        if index > 0:  # Copy the Q and QL values from the previous row
            for col in ['Q0', 'Q1', 'Q2', 'Q3', 'QL']:
                df.at[index, col] = df.at[index - 1, col]

        if pd.notna(row['D']) and row['BUSL'] == 'CODE':
            ql = df.at[index, 'QL']
            if ql < 4:  # If queue is not full
                df.at[index, f'Q{ql}'] = row['D']  # Add the value to the first empty Q column
                df.at[index, 'QL'] += 1  # Increase the queue length
            else:
                print(f"Queue overflow at index {index}")

        # Use next_QOP for the queue operation
        if row['next_QOP'] in ['F', 'S']:
            if df.at[index, 'Q0'] is None:
                print(f"Queue underflow at index {index}")
            else:        
                # Store the value from Q0 and shift the values from Q1, Q2, Q3
                df.at[index, 'QB'] = df.at[index, 'Q0']
                
                df.at[index, 'Q0'] = df.at[index, 'Q1']
                df.at[index, 'Q1'] = df.at[index, 'Q2']
                df.at[index, 'Q2'] = df.at[index, 'Q3']
                df.at[index, 'Q3'] = None
            # Decrease the queue length if it is not already 0
            if df.at[index, 'QL'] > 0:
                df.at[index, 'QL'] -= 1 
        elif row['next_QOP'] == 'E':
            # Empty all Q columns and set QL to 0
            df.at[index, 'Q0'] = None
            df.at[index, 'Q1'] = None
            df.at[index, 'Q2'] = None
            df.at[index, 'Q3'] = None
            df.at[index, 'QL'] = 0

    # Drop the temporary next_QOP column after use 
    df = df.drop(columns=['next_QOP'])

    return df

def update_video(df):

    df['FRAME'] = 0
    df['R_X'] = 0
    df['R_Y'] = 0

    cur_frame = 0
    cur_r_y = 0 
    cur_r_x = 0

    # Iterate over the DataFrame rows
    for index, row in df.iterrows():
        if index > 0:  # Skip the first row to avoid index error

            prev_hs = df.at[index - 1, 'HS']
            prev_vs = df.at[index - 1, 'VS']

            current_hs = row['HS']                            
            current_vs = row['VS']

            if prev_vs == 1 and current_vs == 0:                
                # VSYNC is transitioning from high to low, so we have a new frame.
                # Increment the frame counter, and reset the current scanline counter.
                cur_r_y = 0
                cur_frame += 1  # Increment the current frame value

            if prev_hs == 1 and current_hs == 0:
                # HSYNC is transitioning from high to low, so we have a new scanline.
                # Increment the scanline counter and reset the x counter.
                cur_r_x = 0
                cur_r_y += 1

        df.at[index, 'FRAME'] = cur_frame
        df.at[index, 'R_Y'] = cur_r_y
        df.at[index, 'R_X'] = cur_r_x

        # Scan to next pixel.
        cur_r_x += CLOCK_DIVISOR

    return df

def fetch(df):
    """ fetch instruction bytes from the queue and assemble instruction bytes
    
    This function creates the following columns:
    IS    - Instruction status. This is used to track whether we have read in a prefix or 
            a non-prefix 'first' instruction byte. 
    INST  - Instruction; this is a hexadecimal representation of all the instruction bytes
            read from the queue thus far.
    INSTF - Instruction, final. This is the complete hexadecimal representation of the 
            instruction; this is processed the disassembly phase.
    IDX   - Instruction index. The assembly of the instruction is delayed until the end
            of the instruction where the complete instruction representation is guaranteed,
            therefore the index of the beginning of the instruction is cached here, so that
            the disassembly of the instruction can be placed at the index. 
    """

    # Ensure the 'IS', 'INST', and 'IDX' columns exist
    if 'IS' not in df.columns:
        df['IS'] = ''
    if 'INST' not in df.columns:
        df['INST'] = ''
    if 'INSTF' not in df.columns:
        df['INSTF'] = ''        
    if 'IDX' not in df.columns:
        df['IDX'] = 0
        
    # Set some null, default values.
    current_IS = ''
    current_INST = ''
    current_IDX = 0        

    for index, row in df.iterrows():
        
        # Replicate the IS, INST and IDX columns, ongoing.
        df.at[index, 'IS'] = current_IS
        df.at[index, 'INST'] = current_INST
        df.at[index, 'IDX'] = current_IDX
    
        # Was a byte read from the queue?
        value = str(row['QB']).strip("'")
        
        # If so, process it...
        if value: 
            if pd.isna(row['QB']):
                #df.at[index, 'C'] = "NA??"
                continue        
            try:
                int_value = int(value, 16)
            except ValueError:
                print(f"Error converting '{value}' to an integer at index {index}")
                continue

            new_inst = False
            
            if df.at[index + 1, 'QOP'] == 'F':
                # We've read a 'F' "First Instruction Byte" from the queue.
                
                # Is this byte an instruction prefix?
                if int_value in INSTR_PREFIXES:
                    # If so, enter the 'P' instruction state.
                    df.at[index, 'IS'] = 'P'
                    # If we've read a prefix, we're starting a new instruction.
                    new_inst = True                    
                else:                    
                    # Not a prefix, and 'F' first instruction byte.                  
                    if df.at[index, 'IS'] == 'P':
                        # We were in 'read prefix' state, so we don't need to start a 
                        # new instruction - we did so when the prefix was read. Just 
                        # move to 'I' state.
                        df.at[index, 'IS'] = 'I'
                    else:
                        # We weren't in a prefix state, so this represents the start
                        # of a new, non-prefixed instruction.
                        df.at[index, 'IS'] = 'I'
                        new_inst = True            
                
            if new_inst:
                df.at[index, 'INSTF'] = "'" + df.at[index, 'INST'].strip("'")
                df.at[index, 'INST'] = ''
                df.at[index, 'IDX'] = index
            
            old_inst = df.at[index, 'INST'].strip("'")
            df.at[index, 'INST'] = f"'{old_inst}{value}"
                
        current_IS = df.at[index, 'IS']
        current_IDX = df.at[index, 'IDX']
        current_INST = df.at[index, 'INST']

    return df    

def disassemble(df):

    bitness = 16  # 16-bit for 8088

    for index, row in df.iterrows():
        inst_hex = row['INSTF'].strip("'")
        if inst_hex and not pd.isna(inst_hex):
            try:
                inst_bytes = bytes.fromhex(inst_hex)

                decoder = Decoder(bitness, inst_bytes)
                for instr in decoder:
                    # Create a formatter and get the disassembled instruction
                    formatter = Formatter(FormatterSyntax.NASM)
                    disassembled = formatter.format(instr)
                    
                    # Get the instruction start index
                    instr_idx = int(df.at[index - 1, 'IDX'])
                    
                    # Assign the disassembled instruction to a new column in the DataFrame
                    df.at[instr_idx + 1, 'DISASM'] = disassembled
            except Exception as e:
                print(f"Error disassembling instruction at index {index}: {e}")
                continue

    return df
    
def add_index(df):

    for index, row in df.iterrows():
        df.at[index, 'N'] = index
        
    return df

def decode_marty_addr(row):
    # Convert hex to binary and pad to 20 bits
    bin_str = format(int(row['ADDR'], 16), '020b')
    
    # Split the binary string into AD and A columns
    for i in range(8):
        row[f'AD{i}'] = int(bin_str[i])
    for i in range(8, 20):
        row[f'A{i}'] = int(bin_str[i])
    
    return row

def decode_marty_s(row):
    ## Convert hex to binary and pad to 3 bits
    #bin_str = format(int(row['S'], 16), '03b')
    #
    ## Split the binary string into S columns
    #for i in range(3):
    #    row[f'S{i}'] = int(bin_str[i])

    value = row['S']
    row['S0'] = value & 0b01
    row['S1'] = (value >> 1) & 0b01
    row['S2'] = (value >> 2) & 0b01
    
    return row

def decode_marty_q(row):
    ## Convert hex to binary and pad to 2 bits
    #bin_str = format(int(row['QS'], 16), '02b')
    #
    ## Split the binary string into Q columns
    #for i in range(2):
    #    row[f'Q{i}'] = int(bin_str[i])
    
    value = row['QS']
    
    row['QS0'] = value & 0b01
    row['QS1'] = (value >> 1) & 0b01
    return row

def decode_marty(df):

    #df = df.apply(decode_marty_addr, axis=1)
    #df = df.apply(decode_marty_s, axis=1)
    #df = df.apply(decode_marty_q, axis=1)

    # Convert the ADDR column values from hex to binary, ensuring it's 20 bits long
    df['BIN_ADDR'] = df['ADDR'].apply(lambda x: format(int(x, 16), '020b'))

    # Extract individual bits and store them in new columns
    for i in range(8):
        df[f'AD{i}'] = df['BIN_ADDR'].str[12+i].astype(int) # Extract bits 12-19 (8 bits)
    for i in range(8, 20):
        df[f'A{i}'] = df['BIN_ADDR'].str[i].astype(int)     # Extract bits 0-11 (12 bits)


    df['S0'] = df['S'] & 1  # Extracts the 0th bit
    df['S1'] = (df['S'] & 2) // 2  # Extracts the 1st bit
    df['S2'] = (df['S'] & 4) // 4  # Extracts the 2nd bit

    df['QS0'] = df['QS'] & 1
    df['QS1'] = (df['QS'] & 2) // 2
    

    # Drop the ADDR column
    df = df.drop(columns=['ADDR'])

    # Drop the S column
    df = df.drop(columns=['S'])

    # Drop the QS column
    df = df.drop(columns=['QS'])

    return df

def main(input_csv, output_csv):
    # Read the input CSV file
    df = pd.read_csv(input_csv, comment=';')

    # Trim whitespace from column names
    df.columns = df.columns.str.strip()

    print("Converting columns...")
    
    # Convert column names to uppercase, excluding 'Time(s)'
    df.columns = [col.upper() if col != 'Time(s)' else col for col in df.columns]

    print("Dropping clock edges...")
    df = df[df['CLK'] != 0]

    #print("Reindexing...")
    #new_index = range(0, len(df))
    #df = df.reindex(new_index, fill_value=0)
    df = df.reset_index(drop=True)

    print(f"Have {len(df)} cycles.")    

    print("Converting from martypc format...")
    df = decode_marty(df)

    print("Decoding address lines...")
    df['ADDR'] = df.apply(decode_address, axis=1)
    
    # Add time delta to DataFrame
    #df = add_time_delta(df)

    # fix up clock signal
    #df = calculate_d_accum(df)

    # Filter clock signal
    #df = filter_clock_signal(df)
    
    # Remove noise and recalculate deltas
    #df = remove_noisy_rows_and_recalculate(df)
    
    # Filter clock signal again
    #df = filter_clock_signal(df)    

    # Add a new column 'B' that contains the decimal value calculated from columns 'S2', 'S1', and 'S0'
    print("Decoding bus status...")
    df['B'] = df.apply(decode_status, axis=1)

    # Add ALE signal using value of B (ALE is active when changing from PASV to any other bus state)
    # When ALE is detected, update the value of AL.

    #df = add_ale_column(df)
    print("Calculating ALE and latching addresses...")
    df = add_ale_and_al_columns(df)

    # Generate the 'BUS' column using the bus value to string mapping defined above.
    df['BUS'] = df['B'].map(BUS_MAPPING)

    print("Adding T-states and decoding data bus...")
    df = add_t_and_d_column(df)

    print("Decoding segment status...")
    df = add_seg_column(df)

    print("Decoding queue operations...")
    df = add_qop_column(df)

    print("Latching bus status...")
    df = add_busl_column(df)

    print("Calculating queue contents...")
    df = update_queue(df)

    print("Fetching instructions...")
    df = fetch(df)
    
    print("Disassembling instructions...")
    df = disassemble(df)
    
    if 'VS' in df.columns and 'HS' in df.columns:
        # If both columns are present, call the add_frame function
        print("Calculating frames and scanlines...")        
        df = update_video(df)

    # Reorder our new columns.
    print("Adding index...")
    df = add_index(df)
    
    df = partial_reorder_columns(df, ['N', 'ALE', 'AL', 'SEG', 'BUSL', 'READY', 'T', 'D', 'QOP', 'QB','IS', 'INST', 'INSTF', 'DISASM', 'QL', 'Q0', 'Q1', 'Q2', 'Q3'])

    # Write the updated DataFrame to the output CSV file
    df.to_csv(output_csv, index=False)

if __name__ == '__main__':
    # Ensure correct number of command line arguments
    if len(sys.argv) != 3:
        print("Usage: python decode01.py input_csv output_csv")
        sys.exit(1)

    input_csv = sys.argv[1]
    output_csv = sys.argv[2]

    main(input_csv, output_csv)