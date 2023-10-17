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

#    reclock_py.
#
#    Add a trailing edge of 'CLK' to a CSV file where only leading edges 
#    have been extracted.
# 
#    Arguments: <input_csv> <offset> <output_csv>
#    Offset should be 0.000000105 for 4.77Mhz.

import csv
import sys

def insert_falling_edge(input_csv, offset, output_csv):
    with open(input_csv, 'r') as infile, open(output_csv, 'w', newline='') as outfile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames

        # Check if 'CLK' column is present, if not, add it
        add_clk_column = False
        if 'CLK' not in fieldnames:
            add_clk_column = True
            fieldnames.append('CLK')

        if 'Time(s)' not in fieldnames:
            print("Error: The input CSV does not have a 'Time(s)' column.")
            return

        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            # If 'CLK' column was missing, set its value to '1' for existing rows
            if add_clk_column:
                row['CLK'] = '1'

            # Write the original row
            writer.writerow(row)

            # Update 'Time(s)' and set 'CLK' to '0' for the falling edge and write the new row
            row['Time(s)'] = str(float(row['Time(s)']) + offset)
            row['CLK'] = '0'
            writer.writerow(row)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python reclock.py <input_csv> <offset> <output_csv>")
        sys.exit(1)

    input_file = sys.argv[1]
    try:
        offset_val = float(sys.argv[2])
    except ValueError:
        print("Error: Invalid offset value provided.")
        sys.exit(1)
    output_file = sys.argv[3]

    insert_falling_edge(input_file, offset_val, output_file)