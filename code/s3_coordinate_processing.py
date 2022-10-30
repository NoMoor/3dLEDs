import argparse
import csv
import os
import sys

from utils.visualize import draw, draw_distance_distribution
from utils.coords import Coord3d, Coord2d
from utils import continuation as cont

from datetime import datetime
from statistics import mean

import numpy as np
from scipy.spatial.transform import Rotation as Rot

# The percentile [0 / 100] to keep 'nearby' leds. (eg. 70 = LEDs with peers farther away than 70% of other leds will be
# assumed invalid).
THRESHOLD = 70
IMAGE_HEIGHT = 1920
IMAGE_WIDTH = 1080

with_z_move = {}
without_z_move = {}


def main():
    """Takes an input csv of <angle,x,y,z>"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input-file', type=str, help='The file to read in.')
    parser.add_argument('-o', '--output-folder', default="./s3", type=str, help='The file to output.')
    args = parser.parse_args()

    input_file = cont.get_twod_coordinates_file(args)

    # Reads in coordinates and processes them such that the top back left pixel is 0,0,0.
    coordinates = {}
    shots = parse_data_file(input_file)
    missing = process_90_degrees(coordinates, shots)
    fixed_45 = process_45_degrees(coordinates, missing, shots)

    invalidate_outliers(coordinates)

    fixed_neighbor = fix_with_neighbors(coordinates, missing)

    # Log if there is some coordinate that we are missing.
    for led_id in range(0, 500):
        if led_id not in coordinates:
            print(f"No Value for {led_id}")

    # Normalize from an all positive coordinate system to one that is centered on the tree stem.
    normalize_coordinates(coordinates)
    normalize_coordinates(fixed_45)
    normalize_coordinates(fixed_neighbor)

    # Write the output to file
    output_file_name = os.path.join(args.output_folder, f'{datetime.now().strftime("%Y%m%d_%H%M")}.csv')
    with open(output_file_name, 'w') as output_file:
        csvwriter = csv.writer(output_file)
        # Writes x/y/z to file as csv
        for k in sorted(coordinates.keys()):
            csvwriter.writerow(coordinates[k][1:])
    print(f"Results written to {os.path.abspath(output_file_name)}")

    cont.write_continue_file(twod_coordinates_file=input_file, threed_coordinates_file=output_file_name)

    try:
        draw(list(coordinates.values()), [fixed_45, fixed_neighbor], limit=[0, 500], with_labels=False)

    except KeyboardInterrupt:
        pass


def avg(a, b, offset=2):
    diff = b - a
    return int(a + diff // offset)


def mean_z(shots):
    """Returns the average z of the given shots. """
    return mean(filter(lambda y: y != 0, map(lambda x: x.y, shots)))


def middle_z(shots):
    """Returns the z coordinate by finding the image where the led is nearest the center of the picture."""
    return min(shots, key=lambda s: abs(s.x - 540)).y


def extract_z(shots):
    """This is an attempt to get the z value and minor lensing / perspective based on where the camera was."""
    s = shots[0]

    # 1 means far from the center vertically
    z_diff = ((500 - s.y) / (IMAGE_HEIGHT // 2))
    # print(f"z_diff {z_diff}")

    # 1 means far from the center horizontally
    midpoint_offset = abs(s.x - (IMAGE_WIDTH // 2))
    x_diff = (midpoint_offset - 250) / 300
    # print(f"x_diff {x_diff}")

    net_offset = z_diff * x_diff
    z_shift = -50

    shift = int(z_shift * net_offset)

    # print(f"Shift [{s.x},{s.y}] by {shift}")

    return s.y + shift


def normalize_coordinates(coordinates, with_log=False):
    """Normalizes the coordinates into GIFT format."""
    centered = [normalize_coord_to_center(x) for x in coordinates.values()]
    min_x = min(map(lambda c: c.x, centered))
    max_x = max(map(lambda c: c.x, centered))
    min_y = min(map(lambda c: c.y, centered))
    max_y = max(map(lambda c: c.y, centered))
    min_z = min(map(lambda c: c.z, centered))
    max_z = max(map(lambda c: c.z, centered))

    if with_log:
        print(f"Normalizing to X in [{min_x}, {max_x}] / Y in [{min_y}, {max_y}] / Z in [{min_z}, {max_z}]")

    # Invert the z axis and normalize so that the lowest pixel is 0.
    inverted = [Coord3d(x.led_id, x.x, x.y, max_z - x.z) for x in centered]

    min_z = min(map(lambda c: c.z, inverted))
    max_z = max(map(lambda c: c.z, inverted))

    if with_log:
        print(f"Normalized to Z in [{min_z}, {max_z}]")

    # Scale so that everything is relative to the largest x/y offset

    scaling_factor = max([min_x, max_x, min_y, max_y], key=abs)
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


def invalidate_outliers(coordinates):
    # Generate two normal distributions
    dists = []
    for i in range(0, 500):
        if reliable_coordinate(i, coordinates):
            a = coordinates[i]

            b_id = get_next_neighbor_id(coordinates, i)
            if b_id < 500:
                b = coordinates[b_id]
                dists.append(a.distance(b))

    percentile = np.percentile(dists, THRESHOLD)

    marked_for_deletion = []
    for i in range(0, 500):
        if not reliable_coordinate(i, coordinates):
            if i in coordinates:
                marked_for_deletion.append(i)
            continue

        curr = coordinates[i]

        pi, ni = get_neighbor_ids(coordinates, i)

        if pi < 0:
            pi = i
        if ni >= 500:
            ni = i

        prev_c = coordinates[pi]
        next_c = coordinates[ni]

        prev_too_far = curr.distance(prev_c) > abs(i - pi) * percentile
        next_too_far = curr.distance(next_c) > abs(ni - i) * percentile

        if prev_too_far and next_too_far:
            marked_for_deletion.append(i)

    print(f"{len(marked_for_deletion)} points will be deleted.")
    print(marked_for_deletion)
    for m in marked_for_deletion:
        del coordinates[m]

    draw_distance_distribution(dists, THRESHOLD)


def fix_with_neighbors(coordinates, missing):
    """
    Fix coordinates for all leds that don't have a good x/y/z using linear interpolation
    from the nearest neighbors on each side.
    """
    fixed_neighbor = {}
    for led_id in range(0, 500):
        # Skip ones that aren't marked as missing and we have good coordinates for them.
        if led_id not in missing and reliable_coordinate(led_id, coordinates):
            continue

        prev_id, next_id = get_neighbor_ids(coordinates, led_id)

        if prev_id in range(0, 500) and next_id in range(0, 500):
            prev_coord = coordinates[prev_id]
            next_coord = coordinates[next_id]
            offset = next_id - prev_id

            # Interpolate between these nearest neighbors
            coord = Coord3d(led_id,
                            avg(prev_coord.x, next_coord.x, offset=offset),
                            avg(prev_coord.y, next_coord.y, offset=offset),
                            avg(prev_coord.z, next_coord.z, offset=offset))
            fixed_neighbor[led_id] = coord
            coordinates[led_id] = coord

    print(f"Fixed neighbors: {len(fixed_neighbor)}")
    return fixed_neighbor


def process_45_degrees(coordinates, missing, shots):
    """
    Go through the list of missing leds. Look at 45/135/225/315 angles and try to fill in the coordinates
    If we cannot get both x and y from this, add it to the map of missing_45 leds.
    """
    missing_45 = {}
    fixed_45 = {}
    for k, v in missing.items():
        led_id = k
        filtered_list = v
        stored_point = coordinates[led_id]

        # Extract the coordinates
        z = middle_z(shots[k])

        ys = list(filter(lambda s: s.angle in [135, 315], filtered_list))
        y = (ys[0].x if ys[0].angle == 315 else IMAGE_WIDTH - ys[0].x) if ys else 0
        xs = list(filter(lambda s: s.angle in [45, 225], filtered_list))
        x = (xs[0].x if xs[0].angle == 45 else IMAGE_WIDTH - xs[0].x) if xs else 0

        coord = rotate(Coord3d(led_id, x, y, z), -40)

        # If we aren't sure on x or y, keep it set to 0.
        if x == 0:
            coord = Coord3d(coord.led_id, 0, coord.y, coord.z)
        elif y == 0:
            coord = Coord3d(coord.led_id, coord.x, 0, coord.z)

        if stored_point.x != 0:
            coord = Coord3d(coord.led_id, stored_point.x, coord.y, coord.z)
        if stored_point.y != 0:
            coord = Coord3d(coord.led_id, coord.x, stored_point.y, coord.z)

        if x == 0 or y == 0:
            missing_45[led_id] = filtered_list
        else:
            fixed_45[led_id] = coord

        coordinates[led_id] = coord

    print(f"Fixed 45 degree: {len(fixed_45)}")
    for led_id, coord in fixed_45.items():
        # print(f"F45 - {x.led_id:03}")
        if led_id in missing:
            del missing[led_id]
    print(f"Missing after 45 degree: {len(missing_45)}")
    return fixed_45


def process_90_degrees(coordinates, shots):
    """
    Go through the normal 0/90/180/270 angles and try to fill in the coordinates
    If we cannot get both x and y from this, add it to the map of missing leds.
    """
    missing = {}
    for k in shots.keys():
        led_id = k

        filtered_list = list(filter(lambda s: s.x != 0 and s.y != 0, shots[led_id]))

        z = middle_z(shots[k])

        ys = list(filter(lambda s: s.angle in [90, 270], filtered_list))
        y = (ys[0].x if ys[0].angle == 270 else IMAGE_WIDTH - ys[0].x) if ys else 0

        xs = list(filter(lambda s: s.angle in [0, 180], filtered_list))
        x = (xs[0].x if xs[0].angle == 0 else IMAGE_WIDTH - xs[0].x) if xs else 0

        if x == 0 or y == 0:
            missing[led_id] = filtered_list

        coordinates[led_id] = Coord3d(led_id, x, y, z)
    print(f"Missing after 0 degree: {len(missing)}")
    return missing


def parse_data_file(file_name):
    """Parses a CSV of format 'id###,angle###-x####-y#### into a list of Coordinate objects."""
    # Check that the input file exists.
    if not os.path.exists(f"{file_name}"):
        print(f"Input csv file `{file_name}` not found. Exiting.")
        sys.exit()

    with open(file_name, 'r') as input_file:
        lines = input_file.readlines()
        lines = [line.rstrip() for line in lines]

    shots = {}
    # Parse the lines and filter ones we don't want to consider.
    for line in lines:
        led = Coord2d.from_json(line)

        # If we weren't able to resolve the light, drop this element.
        if (not led.x and not led.y) or led.b < 50:
            continue

        shots.setdefault(led.led_id, []).append(led)
    return shots


def get_neighbor_ids(coordinates, led_id):
    return get_prev_neighbor_id(coordinates, led_id), get_next_neighbor_id(coordinates, led_id)


def get_prev_neighbor_id(coordinates, led_id):
    prev_offset = 1
    while led_id - prev_offset >= 0:
        if reliable_coordinate(led_id - prev_offset, coordinates):
            break
        prev_offset += 1
    return led_id - prev_offset


def get_next_neighbor_id(coordinates, led_id):
    next_offset = 1
    while led_id + next_offset <= 499:
        if reliable_coordinate(led_id + next_offset, coordinates):
            break
        next_offset += 1
    return led_id + next_offset


def rotate(coord, angle):
    r = Rot.from_rotvec(angle * np.array([0, 0, 1]), degrees=True)

    # Rotate the coordinates 45 degrees to match the angle the images were taken.
    v = normalize_to_center([coord.x, coord.y, coord.z])
    v = r.apply(v).tolist()
    v = denormalize_from_center(v)
    return Coord3d(coord.led_id, int(v[0]), int(v[1]), int(v[2]))


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


def denormalize_from_center(v):
    """
    Shifts the origin from the center to the corner. This is the inverse of 'normalize_to_center'.
    """
    return [v[0] + (IMAGE_WIDTH / 2) - 5, v[1] + (IMAGE_WIDTH / 2) + 5, v[2]]


def reliable_neighbors(led_id, coordinates):
    """
    Returns true if the immediate neighbors of the given led_id have x/y/z coordinates.
    :param led_id int identifier of the led index
    :param coordinates dictionary of led_id to Coord object for that led.
    """
    return reliable_coordinate(led_id - 1, coordinates) and reliable_coordinate(led_id + 1, coordinates)


def reliable_coordinate(led_id, coordinates):
    """
    Returns true if the given led has non-zero x/y/z coordinates.
    :param led_id int identifier of the led index
    :param coordinates dictionary of led_id to Coord object for that led.
    """
    led = coordinates.get(led_id)
    return led and led.x > 0 and led.y > 0 and led.z > 0


# Main program logic follows:
if __name__ == '__main__':
    main()
