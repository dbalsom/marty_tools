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

#    fix_addr.py
#    Replaces any address lines that may be missing in a capture
#    This may be due to stealing them for other signals!

import pandas as pd
import sys

REQUIRED_COLUMNS = [
    'AD0',
    'AD1',
    'AD2',
    'AD3',
    'AD4',
    'AD5',
    'AD6',
    'AD7',
    'A8', 
    'A9', 
    'A10',
    'A11',
    'A12',
    'A13',
    'A14',
    'A15',
    'A16',
    'A17',
    'A18',
    'A19',
]

def restore_columns(df, required_columns):
    """
    Ensures that all required columns are present in the dataframe.
    If any are missing, they are added with values filled with 0.
    
    Parameters:
        df (pd.DataFrame): The input dataframe.
        required_columns (list of str): List of required column names.
        
    Returns:
        pd.DataFrame: The updated dataframe.
    """
    for column in required_columns:
        if column not in df.columns:
            print(f"Adding column: {column}")
            df[column] = 0

    return df

def main():
    if len(sys.argv) < 3:
        print("Usage: python fix_addr.py <input_file> <output_file>")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]

    df = pd.read_csv(input_path)
    df = restore_columns(df, REQUIRED_COLUMNS)
    df.to_csv(output_path, index=False)

if __name__ == '__main__':
    main()