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


import csv
import sys

COLUMNS = [
    {'name': 'Time(s)', 'type': 't'},
    {'name': 'AD0',     'type': 'l'},
    {'name': 'AD1',     'type': 'l'},
    {'name': 'AD2',     'type': 'l'},
    {'name': 'AD3',     'type': 'l'},
    {'name': 'AD4',     'type': 'l'},
    {'name': 'AD5',     'type': 'l'},
    {'name': 'AD6',     'type': 'l'},
    {'name': 'AD7',     'type': 'l'},
    {'name': 'A8',      'type': 'l'},
    {'name': 'A9',      'type': 'l'},
    {'name': 'A10',     'type': 'l'},
    {'name': 'A11',     'type': 'l'},
    {'name': 'A12',     'type': 'l'},
    {'name': 'A13',     'type': 'l'},
    {'name': 'A14',     'type': 'l'},
    {'name': 'A15',     'type': 'l'},
    {'name': 'A16',     'type': 'l'},
    {'name': 'A17',     'type': 'l'},
    {'name': 'A18',     'type': 'l'},
    {'name': 'A19',     'type': 'l'},
    {'name': 'ALE',     'type': 'l'},
    {'name': 'S0',      'type': 'l'},
    {'name': 'S1',      'type': 'l'},
    {'name': 'S2',      'type': 'l'},
    {'name': 'QS0',      'type': 'l'},
    {'name': 'QS1',      'type': 'l'},
    {'name': 'READY',   'type': 'l'}
]

def convert_value(value, datatype):
    """
    Convert the value based on the specified type.
    """
    if datatype == 'l':
        return value
    elif datatype.startswith('x'):
        return value.replace("'", "")  # Strip "'" character for hex columns
    else:
        return value

def preprocess_ale_column(rows):
    """
    Convert 'A' values in the 'ALE' column to 1, and any other value to 0.
    """
    for row in rows:
        if 'ALE' in row:
            if row['ALE'] == 'A':
                row['ALE'] = '1'
            else:
                row['ALE'] = '0'
    return rows

def filter_csv_for_pulseview(input_csv, output_csv):
    # Load the input CSV file into memory
    with open(input_csv, 'r') as infile:

        reader = csv.DictReader(infile)
        rows = list(reader)
        
        # Preprocess the 'ALE' column if it exists
        rows = preprocess_ale_column(rows)
        
        # Determine which columns to keep
        valid_columns = [col['name'] for col in COLUMNS]

        # Convert values in rows based on column types
        for row in rows:
            for col in COLUMNS:
                if col['name'] in row:
                    row[col['name']] = convert_value(row[col['name']], col['type'])
                    

        # Write the filtered data to the output CSV file
        with open(output_csv, 'w', newline='') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=valid_columns, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(rows)

    # Generate the Pulseview import string
    import_string = ','.join([col['type'] for col in COLUMNS])
    print(f"Import string for Pulseview: {import_string}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python convert_csv.py <input_csv_path> <output_csv_path>")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]
    
    filter_csv_for_pulseview(input_path, output_path)