import copy
import csv
import math
import os
import time
from collections import namedtuple

import numpy as np
from scipy.constants import R

from color_utils import LED_OFF

IMAGE_HEIGHT = 1920
IMAGE_WIDTH = 1080

Coord = namedtuple("Coord", "led_id x y z")

def percent_off_true(x, y):
    """
    Returns a [0,1)
    """
    # Radians in -pi / pi
    r = math.atan2(y, x)
    r += math.pi

    return r / (2 * math.pi)


def rotate(coord, angle):
    """
    Rotates the given coordinate the specified angle amount.
    """
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


class StripLogger:
    """
    A class for collecting and logging to CSV the animation.
    """

    def __init__(self, output_filename="", pixel_count=500):
        self.pixels = {}
        self.frames = []
        self.output_filename = output_filename if output_filename else f"animation-{time.strftime('%Y%m%d-%H%M%S')}.csv"

    def setPixelColor(self, led, color):
        self.pixels[led] = color

    def show(self):
        self.frames.append(copy.deepcopy(self.pixels))

    def write_to_file(self):
        """
        Writes the frames to file.
        """
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
        ledid, x, y, z = map(float, line.split(","))
        coordinates[ledid] = (x, y, z)

    return coordinates

# Define functions which animate LEDs in various ways.
def fill(strip, color=LED_OFF):
    s = 0
    e = strip.numPixels()
    for i in range(s, e):
        strip.setPixelColor(i, color)
