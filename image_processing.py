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



def detect_light_location(image):
    image = image.convert("L")
    im_arr = np.array(image)
    save_image(im_arr, "processed", "grayscale_test1")

    im_arr = dark_pixels_to_black(im_arr)
    save_image(im_arr, "processed", "grayscale_darkened_test1")
    result = PIL.Image.fromarray(np.uint8(im_arr))

def dark_pixels_to_black(im_arr):
    height = len(im_arr)
    width = len(im_arr[0])
    for row in range(height):
        for col in range(width):
            if(im_arr[row][col] < 150):
                im_arr[row][col] = 0
    return im_arr

def save_image(im_arr, folder, filename):
    directory = os.getcwd()
    directory = os.path.join(directory, folder)
    img = PIL.Image.fromarray(np.uint8(im_arr))
    full_filename = os.path.join(directory, filename + '.png')
    img.save(full_filename)



detect_light_location(test_image)
