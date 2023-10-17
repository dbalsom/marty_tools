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

#    normalize_clock.py
#    Resets clock base to 0 + timestep.


import pandas as pd
import sys

def modify_time(input_path, output_path, timestep):
    # Read the CSV file
    df = pd.read_csv(input_path)
    
    # Check if 'Time(s)' column exists in the dataframe
    if 'Time(s)' not in df.columns:
        print("'Time(s)' column not found in the input file!")
        return
    
    # Update the 'Time(s)' column values
    df['Time(s)'] = [i * timestep for i in range(len(df))]
    
    # Write the modified dataframe to the output path
    df.to_csv(output_path, index=False)
    print(f"Modified CSV saved to {output_path}")

def main():
    # Validate command-line arguments
    if len(sys.argv) != 4:
        print("Usage: normalize_clock.py <timestep> <input_path> <output_path> ")
        return

    try:
        timestep = float(sys.argv[1])
    except ValueError:
        print("Error: Timestep should be a decimal number.")
        return

    input_path = sys.argv[2]
    output_path = sys.argv[3]

    modify_time(input_path, output_path, timestep)

if __name__ == "__main__":
    main()