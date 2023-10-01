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

#   count_rows.py
#   Displays the number of rows in the supplied csv file.

import pandas as pd
import sys

def count_rows(csv_filename, chunksize=10000):
    """
    Count the number of rows in a csv file.

    :param csv_filename: The name of the csv file.
    :param chunksize: The number of rows to read at a time. Default is 10000.
    :return: The total number of rows in the csv file.
    """
    row_count = 0
    # Use the 'chunksize' parameter to read the file in chunks
    for chunk in pd.read_csv(csv_filename, chunksize=chunksize):
        row_count += len(chunk)
    return row_count

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python count_rows.py <csv_filename>")
        sys.exit(1)

    csv_file = sys.argv[1]
    num_rows = count_rows(csv_file)
    print(f"The number of rows in {csv_file} is: {num_rows}")