import copy
import csv
import logging
import math
import os
import re
import time
from scipy.spatial.transform import Rotation as Rot
import numpy as np

from utils.colors import LED_OFF
from utils.coords import Coord3d

logger = logging.getLogger(__name__)

IMAGE_HEIGHT = 1920
IMAGE_WIDTH = 1080


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
    r = Rot.from_rotvec(angle * np.array([0, 0, 1]), degrees=True)

    # Rotate the coordinates 45 degrees to match the angle the images were taken.
    v = r.apply([coord.x, coord.y, coord.z]).tolist()
    return Coord3d(coord.led_id, int(v[0]), int(v[1]), int(v[2]))


def is_back_of_tree(coord, threshold=-100):
    """Input is a list or tuple of size 3. Returns True if this pixel is primarily on the back of the tree."""
    return coord.y < threshold


class LightStripLogger:
    """
    A class for collecting and logging to CSV the animation.
    """

    def __init__(self, coordinates, output_filename=""):
        self.pixels = {}
        self.frames = []
        self.pixel_count = len(coordinates)

        tmp_file = output_filename if output_filename else f"animation-{time.strftime('%Y%m%d-%H%M%S')}.csv"
        self.output_filename = os.path.join("./s4", tmp_file)

    def setPixelColor(self, led, color):
        self.pixels[led] = color

    def show(self):
        self.frames.append(copy.deepcopy(self.pixels))

    def write_to_file(self):
        """
        Writes the frames to file.
        """
        logging.info(f"Writing {len(self.frames)} frames to {self.output_filename}")

        with open(self.output_filename, 'w') as output_file:
            csvwriter = csv.writer(output_file)
            for frame_index, frame in enumerate(self.frames):
                print(f"Writing {frame_index}", end="\r")  # Update terminal only with the current write status.
                data = [frame_index]
                for led_id in range(self.pixel_count):
                    if led_id in frame:
                        data.extend(frame[led_id].rgb_list())
                    else:
                        data.extend([0, 0, 0])

                csvwriter.writerow(data)


def read_coordinates(file_name) -> dict[int, Coord3d]:
    """
    Reads coordinates from the given file name. Coordinates must be a CSV file where the ith row contains RGB values
    for the ith element.
    """
    rgb_pattern = re.compile("^([-+]?[01].[0-9]+),([-+]?[01].[0-9]+),([+]?[0-9]+.[0-9]+)$")

    logging.info("Reading coordinate file %s", file_name)
    with open(file_name, 'r') as input_file:
        lines = [line.rstrip() for line in input_file.readlines()]

    # Scales the coordinates to be in [-500, 500] for x/y and [0, n * 500] for z.
    def scale(val):
        return int(val * 500)

    logging.info("Processing %s coordinates...", len(lines))
    coordinates = {}
    for led_id, xyz in enumerate(lines):
        if not rgb_pattern.match(xyz):
            logging.exception(f"Invalid coordinate input for line {led_id} |{xyz}|."
                              f" Expected to be comma separated rgb values with x/y in [-1,1] and z > 0. ")
        x, y, z = list(map(float, xyz.split(",")))
        coordinates[led_id] = Coord3d(led_id, scale(x), scale(y), scale(z))

    logging.info(
        "Processing complete. Coordinates in [%s, %s] [%s, %s] [%s, %s]",
        min(map(lambda c: c.x, coordinates.values())), max(map(lambda c: c.x, coordinates.values())),
        min(map(lambda c: c.y, coordinates.values())), max(map(lambda c: c.y, coordinates.values())),
        min(map(lambda c: c.z, coordinates.values())), max(map(lambda c: c.z, coordinates.values())))

    return coordinates


# Define functions which animate LEDs in various ways.
def fill(strip, color=LED_OFF):
    """Sets all the lights to a given color"""
    s = 0
    e = strip.numPixels()
    for i in range(s, e):
        strip.setPixelColor(i, color)
