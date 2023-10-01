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

#   head.py
#
#   Export the specified number of rows from the front of the file to the 
#   destination file. 
#   If a time offset is provided, rows will be scanned forthe 'Time(s)' column
#   to exceed the provided offset before the specified number of rows are 
#   exported.

#   Command Line Arguments:
#   num_rows time_offset input_csv output_csv

import pandas as pd
import sys
import time

def display_status(chunk_count, current_time, start_time, rows_processed):
    elapsed_time = time.time() - start_time
    rows_per_second = rows_processed / elapsed_time
    sys.stdout.write(f"\rProcessing chunk: {chunk_count}, Time(s): {current_time}, Rows/sec: {rows_per_second:.2f}")
    sys.stdout.flush()

def dump_rows(n, time_offset, source_file, destination_file):
    CHUNK_SIZE = 10000
    chunk_count = 0
    rows_processed = 0
    start_time = time.time()

    reader = pd.read_csv(source_file, sep=',', comment=';', chunksize=CHUNK_SIZE)

    first_chunk = True
    rows_to_write = n
    for chunk in reader:
        chunk_count += 1
        rows_processed += len(chunk)
        
        # Not writing the last row of the chunk, as it might be incomplete
        chunk = chunk.iloc[:-1]

        # Filtering based on the Time(s) condition
        filtered_chunk = chunk[chunk['Time(s)'] > time_offset]
        
        if not filtered_chunk.empty:
            # If we find rows greater than the time_offset
            if first_chunk:
                filtered_chunk.head(rows_to_write).to_csv(destination_file, mode='w', index=False)
                first_chunk = False
                rows_to_write -= len(filtered_chunk.head(rows_to_write))
            else:
                filtered_chunk.head(rows_to_write).to_csv(destination_file, mode='a', header=False, index=False)
                rows_to_write -= len(filtered_chunk.head(rows_to_write))

            if rows_to_write <= 0:
                break

        current_time = chunk['Time(s)'].max()
        display_status(chunk_count, current_time, start_time, rows_processed)
        
    if rows_to_write > 0:
        print(f"\nCould only extract {n - rows_to_write} rows after the time offset.")

if __name__ == '__main__':
    # Example usage: script_name.py 100 12.34 source.csv dest.csv
    n = int(sys.argv[1])
    time_offset = float(sys.argv[2])
    source_file = sys.argv[3]
    destination_file = sys.argv[4]

    dump_rows(n, time_offset, source_file, destination_file)