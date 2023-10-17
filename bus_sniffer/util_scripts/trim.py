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

#   trim.py
#   This utility will trim analyzer dumps, exporting only rows that 
#   have a 'Time(s)' within the range of the min and max times specified.

#   trim.py <min_time> <max_time> <input_file> <output_path>

import sys
import pandas as pd

import sys
import pandas as pd

def process_chunk(chunk, min_time, max_time):
    if max_time > 0:  # If max_time is given, filter rows based on the range
        filtered_chunk = chunk[(chunk['Time(s)'] >= min_time) & (chunk['Time(s)'] <= max_time)]
    else:  # Otherwise, use only min_time as the filter condition
        filtered_chunk = chunk[chunk['Time(s)'] >= min_time]
    return filtered_chunk

def filter_csv(input_file, output_path, min_time, max_time, chunk_size=10000):
    chunk_iter = pd.read_csv(input_file, chunksize=chunk_size)
    first_chunk = True
    for chunk in chunk_iter:
        filtered_chunk = process_chunk(chunk, min_time, max_time)
        filtered_chunk.to_csv(output_path, mode='a', index=False, header=first_chunk)
        first_chunk = False

def main():
    if len(sys.argv) != 5:
        print("Usage: python trim.py <min_time> <max_time> <input_file> <output_path>")
        sys.exit(1)

    min_time = float(sys.argv[1])
    max_time = float(sys.argv[2])

    if max_time < min_time and max_time != 0:
        print("Error: max_time must be greater than or equal to min_time, or 0")
        sys.exit(1)

    input_file = sys.argv[3]
    output_path = sys.argv[4]

    filter_csv(input_file, output_path, min_time, max_time)

if __name__ == '__main__':
    main()