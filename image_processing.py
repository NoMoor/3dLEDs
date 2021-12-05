import numpy as np
import PIL
import matplotlib.pyplot as plt
import os

test_image = PIL.Image.open("captures/led030_angle000.jpg")

# code to show an image
# img = plt.imread("captures/led030_angle000.jpg")
# fig, ax = plt.subplots(1, 1)
# ax.imshow(img)
# plt.show()

THRESHOLD_VALUE = 200
ARROW_LENGTH = 50

def detect_light_location(image):
    image = image.convert("L")
    im_arr = np.array(image)
    # testing to see how the grayscale looks
    save_image(im_arr, "processed", "grayscale_test1")

    height = len(im_arr)
    width = len(im_arr[0])

    im_arr = threshold(im_arr, height, width)
    # testing darkening
    save_image(im_arr, "processed", "grayscale_darkened_test1")

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

    im_arr = draw_arrow(im_arr, led_row, led_col, diameter, width, height)

    save_image(im_arr, "processed", "grayscale_led_located_test1")


    result = PIL.Image.fromarray(np.uint8(im_arr))


def draw_arrow(im_arr, led_row, led_col, diameter, width, height):
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
            if(im_arr[row][col] < THRESHOLD_VALUE):
                im_arr[row][col] = 0
    return im_arr

def save_image(im_arr, folder, filename):
    directory = os.getcwd()
    directory = os.path.join(directory, folder)
    img = PIL.Image.fromarray(np.uint8(im_arr))
    full_filename = os.path.join(directory, filename + '.png')
    img.save(full_filename)



detect_light_location(test_image)
