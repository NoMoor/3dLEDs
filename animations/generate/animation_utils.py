import copy
import csv
import math
import os
import time
from collections import namedtuple

import numpy as np
from scipy.constants import R

IMAGE_HEIGHT = 1920
IMAGE_WIDTH = 1080


def to_color(rgb):
    return Color(rgb[0], rgb[1], rgb[2])


def to_blended_color(rgb1, rgb2, r):
    return Color(
        int(_lerp(rgb1[0], rgb2[0], r)),
        int(_lerp(rgb1[1], rgb2[1], r)),
        int(_lerp(rgb1[2], rgb2[2], r)))


def _lerp(a, b, r):
    diff = b - a
    return a + (diff * r)


def percent_off_true(x, y):
    """
    Returns a [0,1)
    """
    # Radians in -pi / pi
    r = math.atan2(y, x)
    r += math.pi

    return r / (2 * math.pi)


def wheel(pos):
    """Generate rainbow colors across 0-255 positions."""
    if pos < 85:
        return Color(pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return Color(255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return Color(0, pos * 3, 255 - pos * 3)


def rotate(coord, angle):
    r = R.from_rotvec(angle * np.array([0, 0, 1]), degrees=True)

    # Rotate the coordinates 45 degrees to match the angle the images were taken.
    v = normalize_to_center([coord.x, coord.y, coord.z])
    v = r.apply(v).tolist()
    v = denormalize_from_center(v)
    return Coord(coord.led_id, int(v[0]), int(v[1]), int(v[2]))


def normalize_to_center(v):
    """
    Shifts the origin from the corner to the center. This is needed to rotate the coordinate plane about the center.
    """
    return [v[0] - (IMAGE_WIDTH / 2) + 5, v[1] - (IMAGE_WIDTH / 2), v[2]]


def denormalize_from_center(v):
    """
    Shifts the origin from the center to the corner. This is the inverse of 'normalize_to_center'.
    """
    return [v[0] + (IMAGE_WIDTH / 2) - 5, v[1] + (IMAGE_WIDTH / 2), v[2]]


def is_back_of_tree(v):
    """Input is a list or tuple of size 3. Returns True if this pixel is primarily on the back of the tree."""
    return v[1] < 400


############################
######     Colors    #######
############################
class Color:
    def __init__(self, r, g, b):
        self.r = r
        self.g = g
        self.b = b

    def rgb_list(self):
        return [self.r, self.g, self.b]


LED_WHITE = Color(255, 255, 255)
LIGHT_BLUE = Color(173, 150, 250)
DIM_LIGHT_BLUE = Color(35, 44, 46)
LED_OFF_C = [0, 0, 0]
LED_OFF = to_color(LED_OFF_C)
BLUE_C = [20, 20, 80]
BLUE = to_color(BLUE_C)
PINK_C = [110, 20, 20]
PINK = to_color(PINK_C)
RED_C = [110, 0, 0]
RED = to_color(RED_C)
GREEN_C = [0, 80, 0]
GREEN = to_color(GREEN_C)
BLUE_V1 = Color(80, 80, 250)
PINK_V1 = Color(250, 80, 80)
Coord = namedtuple("Coord", "led_id x y z")


class StripLogger:

    def __init__(self, output_filename="", pixel_count=500):
        self.pixels = {}
        self.frames = []
        self.output_filename = output_filename if output_filename else f"animation-{time.strftime('%Y%m%d-%H%M%S')}.csv"

    def setPixelColor(self, led, color):
        self.pixels[led] = color

    def show(self):
        self.frames.append(copy.deepcopy(self.pixels))

    def write_to_file(self):
        output_file_path = os.path.join("..", "run", self.output_filename)

        with open(output_file_path, 'w') as output_file:
            csvwriter = csv.writer(output_file)
            for frame_index, frame in enumerate(self.frames):
                data = [frame_index]
                for led_id in range(500):
                    if led_id in frame:
                        data.extend(frame[led_id].rgb_list())
                    else:
                        data.extend([0, 0, 0])

                csvwriter.writerow(data)


def read_coordinates(file_name):
    print("Reading lines")
    with open(file_name, 'r') as input_file:
        lines = input_file.readlines()
        lines = lines[1:]  # Remove the header from the file
        lines = [line.rstrip() for line in lines]

    print("Processing lines")
    coordinates = {}
    for line in lines:
        ledid, x, y, z = map(int, line.split(","))
        coordinates[ledid] = (x, y, z)

    # TODO: If coordinates are in absolute, normalize them here.

    return coordinates
