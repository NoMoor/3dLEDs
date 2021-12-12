import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import os
import argparse


# code to show an image
# img = plt.imread("captures/led030_angle000.jpg")
# fig, ax = plt.subplots(1, 1)
# ax.imshow(img)
# plt.show()

THRESHOLD_VALUE = 200
ARROW_LENGTH = 50

def detect_light_location(image):
    gray = image.convert("L")
    im_arr = np.array(gray)
    # testing to see how the grayscale looks
    # save_image(im_arr, "processed", "grayscale_test1")

    height = len(im_arr)
    width = len(im_arr[0])

    im_arr = threshold(im_arr, height, width)
    # testing darkening
    # save_image(im_arr, "processed", "grayscale_darkened_test1")

    # find the the center of the led
    diameter = 0
    led_row = 0
    led_col = 0
    for row in range(height):
        for col in range(width):
            if im_arr[row][col] > 0:
                diameter = diag_span(im_arr, row, col, height, width)
                led_row = row + diameter // 2
                led_col = col + diameter // 2
                break
        else:
            continue
        break

#     im_arr = draw_arrow(im_arr, led_row, led_col, diameter)

    # save_image(im_arr, "processed", "grayscale_led_located_test1")
    return led_row, led_col, diameter

    # result = PIL.Image.fromarray(np.uint8(im_arr))


def draw_arrow(im_arr, led_row, led_col, diameter):
    height = len(im_arr)
    width = len(im_arr[0])

    r = led_row - diameter // 2
    c = led_col
    length = ARROW_LENGTH

    while r >= 0 and length > 0:
        im_arr[r][c] = 255
        r -= 1
        length -= 1

    r = led_row - diameter // 2
    length = ARROW_LENGTH // 2

    while r >= 0 and c >= 0 and length > 0:
        im_arr[r][c] = 255
        r -= 1
        c -= 1
        length -= 1

    r = led_row - diameter // 2
    c = led_col
    length = ARROW_LENGTH // 2

    while r >= 0 and c < width and length > 0:
        im_arr[r][c] = 255
        r -= 1
        c += 1
        length -= 1

    return im_arr


def draw_cross(image, row, col):
    img_draw = ImageDraw.Draw(image)

    horizontal = [(0, row), (image.size[0], row)]
    vertical = [(col, 0), (col, image.size[1])]

    img_draw.line(horizontal, fill="rgb(0, 255, 0)", width=2)
    img_draw.line(vertical, fill="rgb(0, 255, 0)", width=2)

    img_draw.text((col + 10, row + 10), f"{row}, {col}", fill="rgb(0, 255, 0)")

    return image


def diag_span(im_arr, row, col, height, width):
    pixel = im_arr[row][col]
    if row + 1 == height or col + 1 == width:
        return 1
    diameter = 1
    while pixel > 0 and row < height and col < width:
        row += 1
        col += 1
        pixel = im_arr[row][col]
        if pixel > 0:
            diameter += 1
    return diameter


def threshold(im_arr, height, width):
    for row in range(height):
        for col in range(width):
            if im_arr[row][col] < THRESHOLD_VALUE:
                im_arr[row][col] = 0
    return im_arr


def save_image(im_arr, folder, filename):
    img = Image.fromarray(np.uint8(im_arr))

    if not os.path.exists(folder):
        os.makedirs(folder)

    full_filename = os.path.join(folder, filename)
    img.save(full_filename)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--start-index', type=int, default=0, help='The index of the first LED to use.')
    parser.add_argument('-e', '--end-index', type=int, default=500, help='The index of the last LED to use.')
    parser.add_argument('-i', '--input-folder', type=str, help='The relative folder for input files')
    parser.add_argument('-o', '--output-folder', type=str, help='The relative folder for output files')
    args = parser.parse_args()

    if not os.path.exists(args.output_folder):
        print(f"Folder `{args.output_folder}` doesn't exist. Exiting...")
        sys.exit()

    with open(os.path.join(args.output_folder, "processed_data.txt"), 'a') as f:
        for i in range(args.start_index, args.end_index + 1):
            for angle in [0, 45, 90, 135, 180, 225, 270, 315]:
                input_file_name = os.path.join(args.input_folder, f"led{i:03}_angle{angle:03}.jpg")

                if not os.path.exists(input_file_name):
                    print(f"Skipping {input_file_name}. File not found.")
                    continue

                print(f"Processing {input_file_name}")

                test_image = Image.open(input_file_name)

                row, col, _ = detect_light_location(test_image)

                f.write(f"id{i:03},angle{angle:03}-x{col:04},y{row:04}\n")

                processed_image = draw_cross(test_image, row, col)
                save_image(processed_image, args.output_folder, f"processed_led{i:03}_angle{angle:03}.jpg")


# Main program logic follows:
if __name__ == '__main__':
    main()
