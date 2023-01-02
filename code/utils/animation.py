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


def write_coordinates(file_name: str, coords: dict[int, Coord3d], normalize=False, center_invert=True) -> None:
    if normalize:
        normalize_coordinates(coords, center_invert=center_invert)

    with open(file_name, 'w') as output_file:
        csvwriter = csv.writer(output_file)
        # Writes x/y/z to file as csv
        for k in sorted(coords.keys()):
            csvwriter.writerow(coords[k][1:])
    print(f"Results written to {os.path.abspath(file_name)}")

def normalize_coordinates(coordinates, center_invert=True, with_log=True):
    """Normalizes the coordinates into GIFT format."""
    centered = [normalize_coord_to_center(x) for x in coordinates.values()] if center_invert else list(coordinates.values())
    min_x = min(map(lambda c: c.x, centered))
    max_x = max(map(lambda c: c.x, centered))
    min_y = min(map(lambda c: c.y, centered))
    max_y = max(map(lambda c: c.y, centered))
    min_z = min(map(lambda c: c.z, centered))
    max_z = max(map(lambda c: c.z, centered))

    if with_log:
        print(f"Normalizing to X in [{min_x}, {max_x}] / Y in [{min_y}, {max_y}] / Z in [{min_z}, {max_z}]")

    # Invert the z axis and normalize so that the lowest pixel is 0.
    inverted = [Coord3d(x.led_id, x.x, x.y, max_z - x.z) for x in centered] if center_invert else [Coord3d(x.led_id, x.x, x.y, x.z) for x in centered]

    min_z = min(map(lambda c: c.z, inverted))
    max_z = max(map(lambda c: c.z, inverted))

    if with_log:
        print(f"Normalized to Z in [{min_z}, {max_z}]")

    # Scale so that everything is relative to the largest x/y offset

    scaling_factor = max(map(abs, [min_x, max_x, min_y, max_y]))
    scaled_coordinate = [Coord3d(c.led_id, c.x / scaling_factor, c.y / scaling_factor, c.z / scaling_factor) for c in
                         inverted]

    min_x = min(map(lambda c: c.x, scaled_coordinate))
    max_x = max(map(lambda c: c.x, scaled_coordinate))
    min_y = min(map(lambda c: c.y, scaled_coordinate))
    max_y = max(map(lambda c: c.y, scaled_coordinate))
    min_z = min(map(lambda c: c.z, scaled_coordinate))
    max_z = max(map(lambda c: c.z, scaled_coordinate))

    if with_log:
        print(
            f"Scaled by {scaling_factor} to X in [{min_x}, {max_x}] / Y in [{min_y}, {max_y}] / Z "
            f"in [{min_z}, {max_z}]")

    # Update all the values in the coordinate map.
    for updated_coordinate in scaled_coordinate:
        coordinates[updated_coordinate.led_id] = updated_coordinate

def normalize_to_center(v):
    """
    Shifts the origin from the corner to the center. This is needed to rotate the coordinate plane about the center.
    """
    return [v[0] - (IMAGE_WIDTH / 2) + 5, v[1] - (IMAGE_WIDTH / 2) - 5, v[2]]


def normalize_coord_to_center(coord):
    """
    Shifts the origin from the corner to the center. This is needed to rotate the coordinate plane about the center.
    """
    centered = normalize_to_center([coord.x, coord.y, coord.z])
    return Coord3d(coord.led_id, centered[0], centered[1], centered[2])


# Define functions which animate LEDs in various ways.
def fill(strip, color=LED_OFF):
    """Sets all the lights to a given color"""
    s = 0
    e = strip.numPixels()
    for i in range(s, e):
        strip.setPixelColor(i, color)
