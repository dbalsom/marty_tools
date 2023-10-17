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


import sys
import os
import pandas as pd
from enum import Enum

from PIL import Image, ImageDraw, ImageFont

class Colors(Enum):
    BLACK = 0
    WHITE = 1
    RED = 2
    MAGENTA = 3
    CYAN = 4
    YELLOW = 5
    GREEN = 6
    BLUE = 7
    GRAY = 8

# Define the color palette
PALETTE = [
    (0, 0, 0),       # Black
    (255, 255, 255), # White
    (255, 0, 0),     # Red
    (255, 0, 255),   # Magenta
    (0, 255, 255),   # Cyan
    (255, 255, 0),   # Yellow
    (0, 170, 0),     # Green
    (0, 0, 170),     # Blue
    (50, 50, 50),
]

def count_scanlines(csv_file):
    df = pd.read_csv(csv_file)
    if 'HS' not in df.columns:
        print("'HS' column not found in the CSV file.")
        return None
    hs_column = df['HS']
    transitions = sum((hs_column.shift(1) == 1) & (hs_column == 0))
    return transitions

def create_image_from_csv(csv_file, font, N):

    # Create a new indexed image with the palette
    t_img = Image.new('P', (304, N))
    t_img.putpalette([val for sublist in PALETTE for val in sublist])
    
    b_img = Image.new('P', (304, N))
    b_img.putpalette([val for sublist in PALETTE for val in sublist])

    f_img = Image.new('P', (304, N))
    f_img.putpalette([val for sublist in PALETTE for val in sublist])

    # Load the CSV file into a DataFrame
    df = pd.read_csv(csv_file)
    if 'HS' not in df.columns or 'VS' not in df.columns:
        print("'HS' or 'VS' column not found in the CSV file.")
        return None
    
    x, y = 0, 0
    emitting = False
    scanline_len = 0
    ignore_second_inta = False
    in_inta = False
    reset_sync = False
    isr_addr = "00"
    draw_isr_addr = False

    color_inta = False

    for _, row in df.iterrows():

        if not emitting:

            if row['HS'] == 1:
                continue

            if row['HS'] == 0 and (df['HS'].shift(1).iloc[_] == 1):
                emitting = True
            else:
                continue

        if row['HS'] == 0:
            scanline_len += 1

            if scanline_len > (304 * 2):
                reset_sync = True
                print("resetting sync")
                x = 0
                y += 1
                emitting = False
                scanline_len = 0
                continue

        elif row['HS'] == 1:
            scanline_len = 0

        if row["BUSL"] == "INTA":
            in_inta = True

        if in_inta and color_inta:
            if row["BUSL"] == "CODE":
                # Interrupt is fetching first byte of ISR. Record the address.
                isr_addr = row["AL"][-2:]
            b_color_index = Colors.YELLOW.value
            if row['QOP'] == 'F':
                in_inta = False
                draw_isr_addr = True
        elif row['INTR'] == 1 and (df['INTR'].shift(1).iloc[_] == 0):
            b_color_index = Colors.RED.value
        elif row['BUSL'] == "IOW" and pd.notnull(row['D']):
            d_val = int(row['D'].replace("'", ""), 16)  # Remove "'" and interpret as hexadecimal
            al_val = int(row['AL'].replace("'", ""), 16)
            if al_val == 0x3D4:
                # CRTC register select writes
                if d_val == 7:
                    b_color_index = Colors.CYAN.value
                else: 
                    b_color_index = Colors.MAGENTA.value
            elif al_val == 0x40:
                # Timer channel 0 writes
                b_color_index = Colors.BLUE.value
        elif row['BUSL'] == "IOR" and pd.notnull(row['D']):
            al_val = int(row['AL'].replace("'", ""), 16)
            if al_val == 0x3DA:
                # CGA status register read
                b_color_index = Colors.WHITE.value
        else:
            b_color_index = Colors.BLACK.value
        
        if row["DEN"] == 1:
            t_color_index = Colors.GRAY.value
        elif row['HS'] == 1 and row['VS'] == 1:
            t_color_index = Colors.WHITE.value
        elif row['HS'] == 1:
            t_color_index = Colors.YELLOW.value
        elif row['VS'] == 1:
            t_color_index = Colors.BLACK.value
        else:
            t_color_index = Colors.GREEN.value

        if draw_isr_addr and font is not None:
            draw_text(f_img, font, x, y - 16, isr_addr)
            draw_isr_addr = False

        t_img.putpixel((x, y), t_color_index)
        b_img.putpixel((x, y), b_color_index)

        x += 1
        if x >= 304:
            x = 0
            y += 1
            if y >= N:
                break

    return (t_img, b_img, f_img)

def append_path(filepath, append_str):
    # Extract directory, base filename, and extension
    dir_name, file_name = os.path.split(filepath)
    base_name, ext = os.path.splitext(file_name)

    # Append the string to the base filename
    new_name = base_name + append_str + ext

    # Join back the directory and the new filename
    new_path = os.path.join(dir_name, new_name)

    return new_path

def draw_text(img, font, x, y, text):
    draw = ImageDraw.Draw(img)
    draw.text((x, y), text, font=font, fill="white")

def main():
    if len(sys.argv) < 3:
        print("Usage: python csv_to_img.py input_csv_pat output_png_path input_font_path")
        sys.exit(1)

    csv_file_path = sys.argv[1]
    png_file_path = sys.argv[2]

    if sys.argv == 4:
        font_file_path = sys.argv[3]
        font = ImageFont.load(font_file_path)
    else:
        font = None

    N = count_scanlines(csv_file_path)
    if N:
        print(f"Detected {N} scanlines. Converting...")

        t_img, b_img, f_img = create_image_from_csv(csv_file_path, font, N)

        t_fn = append_path(png_file_path, "a")
        b_fn = append_path(png_file_path, "b")
        f_fn = append_path(png_file_path, "c")

        t_img.save(t_fn)
        b_img.save(b_fn)
        f_img.save(f_fn)

        print(f"Images saved to {t_fn}, {b_fn}, {f_fn}")

if __name__ == '__main__':
    main()