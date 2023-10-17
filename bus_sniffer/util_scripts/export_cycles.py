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

#   export_cycles.py
#
#   Export only the rows representing a low to high transition of the 'CLK' 
#   column from a CSV file exported from PulseView/DSView.
#
#   Command Line Arguments:
#   input_csv output_csv

import pandas as pd
import sys

def process_chunk(chunk, prev_clk):
    chunk.columns = chunk.columns.str.strip()
    prev_clk_values = chunk['CLK'].shift(fill_value=prev_clk).astype(int)
    result = chunk[(prev_clk_values == 0) & (chunk['CLK'] == 1)]
    return result, chunk['CLK'].iat[-1] 

def process_csv(input_csv, output_csv):
    prev_clk = 0
    chunk_number = 0
    
    with open(output_csv, 'w', newline='') as outfile:
        for chunk in pd.read_csv(input_csv, chunksize=10000, comment=';'):
            try:
                chunk_number += 1
                result_chunk, prev_clk = process_chunk(chunk, prev_clk)
                
                if chunk_number == 1:
                    result_chunk.to_csv(outfile, index=False)
                else:
                    result_chunk.to_csv(outfile, index=False, header=False, line_terminator='\n', mode='a')
                
                sys.stdout.write(f'\rProcessing chunk number {chunk_number}...')
                sys.stdout.flush()
            except Exception as e:
                print(f"An error occurred while processing chunk number {chunk_number}: {e}")
        
        print()

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python export_cycles.py <input_csv> <output_csv>")
        sys.exit(1)

    input_csv, output_csv = sys.argv[1], sys.argv[2]
    process_csv(input_csv, output_csv)