import copy
import csv
from dataclasses import dataclass
import math
import os
import re
import time
from scipy.spatial.transform import Rotation as R
import numpy as np

from color_utils import LED_OFF

IMAGE_HEIGHT = 1920
IMAGE_WIDTH = 1080


@dataclass
class Coord:
    """Class for keeping x/y/z coordinates"""
    led_id: int
    x: int
    y: int
    z: int

    def with_x(self, new_x):
        return Coord(self.led_id, new_x, self.y, self.z)

    def with_y(self, new_y):
        return Coord(self.led_id, self.x, new_y, self.z)

    def with_z(self, new_z):
        return Coord(self.led_id, self.x, self.y, new_z)


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
    angle = int(angle)
    r = R.from_rotvec(angle * np.array([0, 0, 1]), degrees=True)

    # Rotate the coordinates 45 degrees to match the angle the images were taken.
    v = r.apply([coord.x, coord.y, coord.z]).tolist()
    return Coord(coord.led_id, int(v[0]), int(v[1]), int(v[2]))


def is_back_of_tree(coord, threshold=-100):
    """Input is a list or tuple of size 3. Returns True if this pixel is primarily on the back of the tree."""
    return coord.y < threshold


class StripLogger:
    """
    A class for collecting and logging to CSV the animation.
    """

    def __init__(self, output_filename="", pixel_count=500):
        self.pixels = {}
        self.frames = []

        tmp_file = output_filename if output_filename else f"animation-{time.strftime('%Y%m%d-%H%M%S')}.csv"
        self.output_filename = os.path.join("../animations", "run", tmp_file)

    def setPixelColor(self, led, color):
        self.pixels[led] = color

    def show(self):
        self.frames.append(copy.deepcopy(self.pixels))

    def write_to_file(self):
        """
        Writes the frames to file.
        """
        print(f"Writing {len(self.frames)} frames to {self.output_filename}")

        with open(self.output_filename, 'w') as output_file:
            csvwriter = csv.writer(output_file)
            for frame_index, frame in enumerate(self.frames):
                print(f"Writing {frame_index}", end="\r")
                data = [frame_index]
                for led_id in range(500):
                    if led_id in frame:
                        data.extend(frame[led_id].rgb_list())
                    else:
                        data.extend([0, 0, 0])

                csvwriter.writerow(data)


def read_coordinates(file_name):
    """
    Reads coordinates from the given file name. Coordinates must be a CSV file where the ith row contains RGB values
    for the ith element.
    """
    rgb_pattern = re.compile("^([-+]?[01].[0-9]+),([-+]?[01].[0-9]+),([+]?[0-9]+.[0-9]+)$")

    print("Reading lines")
    with open(file_name, 'r') as input_file:
        lines = input_file.readlines()
        lines = lines[1:]  # Remove the header from the file
        lines = [line.rstrip() for line in lines]

    # Scales the coordinates to be in [-500, 500] for x/y and [0, n * 500] for z.
    def scale(val): return int(val * 500)

    print("Processing lines")
    coordinates = {}
    for led_id, xyz in enumerate(lines):
        if not rgb_pattern.match(xyz):
            print(f"Invalid coordinate input for line {led_id} |{xyz}|."
                  f" Expected to be comma separated rgb values with x/y in [-1,1] and z > 0. ")
        x, y, z = list(map(float, xyz.split(",")))
        coordinates[led_id] = Coord(led_id, scale(x), scale(y), scale(z))

    return coordinates


# Define functions which animate LEDs in various ways.
def fill(strip, color=LED_OFF):
    s = 0
    e = strip.numPixels()
    for i in range(s, e):
        strip.setPixelColor(i, color)
