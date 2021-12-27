import argparse
import csv
import os
import sys
import matplotlib.pyplot as plt
import numpy as np
from collections import namedtuple
from scipy.spatial.transform import Rotation as R

Coord = namedtuple("Coord", "led_id x y z")
Snap = namedtuple("Snap", "led_id angle x y")

IMAGE_HEIGHT = 1920
IMAGE_WIDTH = 1080


def draw(og_leds, led_maps=None, limit=None, with_labels=False):
    if not led_maps:
        led_maps = []

    if not limit:
        limit = [0, len(og_leds) - 1]

    fig = plt.figure()
    ax = fig.add_subplot(projection='3d')

    fixes = {}
    for led_map in led_maps:
        for led_id, led_coord in led_map.items():
            fixes[led_id] = led_coord
    alt_ids = fixes.keys()

    partially_missing = []

    xs = []
    ys = []
    zs = []
    labels = []

    for led in og_leds:
        if led.led_id in alt_ids:
            continue

        # If something is partially missing, don't plot it in the main line.
        if led.x == 0 or led.y == 0:
            partially_missing.append(led)
            continue

        if limit[0] <= led.led_id <= limit[1]:
            labels.append(led.led_id)
            xs.append(led.x)
            ys.append(led.y)
            zs.append(led.z)

    ax.scatter(xs, ys, zs, 'gray')

    if with_labels:
        for i, txt in enumerate(labels):
            ax.text(xs[i], ys[i], zs[i], txt)

    # Plot different groups where there was additional processing separately.
    markers = ['^', 'o', 's']
    for i, led_map in enumerate(led_maps):
        xs = []
        ys = []
        zs = []
        labels = []
        for led_id, led_coord in led_map.items():
            if limit[0] <= led_id <= limit[1]:
                labels.append(led_id)
                xs.append(led_coord.x)
                ys.append(led_coord.y)
                zs.append(led_coord.z)

        ax.scatter(xs, ys, zs, marker=markers[i])

        if with_labels:
            for i, txt in enumerate(labels):
                ax.text(xs[i], ys[i], zs[i], txt)

    # Plot others
    xs = []
    ys = []
    zs = []
    for led in partially_missing:
        xs.append(led.x)
        ys.append(led.y)
        zs.append(led.z)

    ax.scatter(xs, ys, zs, marker='.')

    ax.set_xlabel('X')
    ax.set_xlim([-1, 1])
    ax.set_ylabel('Y')
    ax.set_ylim([-1, 1])
    ax.set_zlabel('Z')
    max_z = max(map(lambda x: x.z, og_leds))
    ax.set_zlim([0, max_z])
    ax.set_box_aspect((9, 9, 16))

    # plt.gca().invert_zaxis()
    plt.gca().invert_yaxis()

    plt.show()


def avg(a, b, offset=2):
    diff = b - a
    return int(a + diff // offset)


def extract_z(shots):
    # TODO: I'm not totally sure this works or is needed.
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


def normalize_coordinates(coordinates):
    """Normalizes the coordinates into GIFT format."""
    centered = [normalize_coord_to_center(x) for x in coordinates.values()]
    min_x = min(map(lambda c: c.x, centered))
    max_x = max(map(lambda c: c.x, centered))
    min_y = min(map(lambda c: c.y, centered))
    max_y = max(map(lambda c: c.y, centered))
    min_z = min(map(lambda c: c.z, centered))
    max_z = max(map(lambda c: c.z, centered))

    print(f"Normalizing to X in [{min_x}, {max_x}] / Y in [{min_y}, {max_y}] / Z in [{min_z}, {max_z}]")

    # Invert the z axis and normalize so that the lowest pixel is 0.
    inverted = [Coord(c.led_id, c.x, c.y, max_z - c.z) for c in centered]

    min_z = min(map(lambda c: c.z, inverted))
    max_z = max(map(lambda c: c.z, inverted))
    print(f"Normalized to Z in [{min_z}, {max_z}]")

    # Scale so that everything is relative to the largest x/y offset

    scaling_factor = max([min_x, max_x, min_y, max_y], key=abs)
    scaled = [Coord(c.led_id, c.x / scaling_factor, c.y / scaling_factor, c.z / scaling_factor) for c in inverted]

    min_x = min(map(lambda c: c.x, scaled))
    max_x = max(map(lambda c: c.x, scaled))
    min_y = min(map(lambda c: c.y, scaled))
    max_y = max(map(lambda c: c.y, scaled))
    min_z = min(map(lambda c: c.z, scaled))
    max_z = max(map(lambda c: c.z, scaled))

    print(f"Scaled by {scaling_factor} to X in [{min_x}, {max_x}] / Y in [{min_y}, {max_y}] / Z in [{min_z}, {max_z}]")

    # Update all the values in the coordinate map.
    for c in scaled:
        coordinates[c.led_id] = c

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input-file', type=str, help='The file to read in.')
    parser.add_argument('-o', '--output-file', type=str, help='The file to output.')
    args = parser.parse_args()

    if not os.path.exists(f"{args.input_file}"):
        print(f"File `{args.input_file}` doesn't exist. Exiting...")
        sys.exit()

    # Reads in coordinates and processes them such that the top back left pixel is 0,0,0.
    coordinates, shots = parse_data_file(args)
    missing = process_90_degrees(coordinates, shots)
    fixed_45 = process_45_degrees(coordinates, missing, shots)
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
    with open(args.output_file, 'w') as output_file:
        csvwriter = csv.writer(output_file)
        csvwriter.writerow(("id", "x", "y", "z"))
        for k in sorted(coordinates.keys()):
            csvwriter.writerow(coordinates[k])

    try:
        draw(coordinates.values(), [fixed_45, fixed_neighbor], limit=[0, 500], with_labels=False)

    except KeyboardInterrupt:
        pass


def fix_with_neighbors(coordinates, missing):
    # Fix coordinates for all leds that don't have a good x/y/z using linear interpolation
    # from the nearest neighbors on each side.
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
            coord = Coord(led_id,
                          avg(prev_coord.x, next_coord.x, offset=offset),
                          avg(prev_coord.y, next_coord.y, offset=offset),
                          avg(prev_coord.z, next_coord.z, offset=offset))
            fixed_neighbor[led_id] = coord
            coordinates[led_id] = coord
    print(f"Fixed neighbors: {len(fixed_neighbor)}")
    return fixed_neighbor


def process_45_degrees(coordinates, missing, shots):
    # Go through the list of missing leds. Look at 45/135/225/315 angles and try to fill in the coordinates
    # If we cannot get both x and y from this, add it to the map of missing_45 leds.
    missing_45 = {}
    fixed_45 = {}
    for k, v in missing.items():
        led_id = k
        filtered_list = v
        stored_point = coordinates[led_id]

        # Extract the coordinates
        z = extract_z(shots[k])

        ys = list(filter(lambda s: s.angle in [135, 315], filtered_list))
        y = (ys[0].x if ys[0].angle == 315 else IMAGE_WIDTH - ys[0].x) if ys else 0
        xs = list(filter(lambda s: s.angle in [45, 225], filtered_list))
        x = (xs[0].x if xs[0].angle == 45 else IMAGE_WIDTH - xs[0].x) if xs else 0

        coord = rotate(Coord(led_id, x, y, z), -40)

        # If we aren't sure on x or y, keep it set to 0.
        if x == 0:
            coord = Coord(coord.led_id, 0, coord.y, coord.z)
        elif y == 0:
            coord = Coord(coord.led_id, coord.x, 0, coord.z)

        if stored_point.x != 0:
            coord = Coord(coord.led_id, stored_point.x, coord.y, coord.z)
        if stored_point.y != 0:
            coord = Coord(coord.led_id, coord.x, stored_point.y, coord.z)

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
    # Go through the normal 0/90/180/270 angles and try to fill in the coordinates
    # If we cannot get both x and y from this, add it to the map of missing leds.
    missing = {}
    for k in shots.keys():
        led_id = k

        filtered_list = list(filter(lambda s: s.x != 0 and s.y != 0, shots[led_id]))

        z = extract_z(shots[k])

        ys = list(filter(lambda s: s.angle in [90, 270], filtered_list))
        y = (ys[0].x if ys[0].angle == 270 else IMAGE_WIDTH - ys[0].x) if ys else 0

        xs = list(filter(lambda s: s.angle in [0, 180], filtered_list))
        x = (xs[0].x if xs[0].angle == 0 else IMAGE_WIDTH - xs[0].x) if xs else 0

        if x == 0 or y == 0:
            missing[led_id] = filtered_list

        coordinates[led_id] = Coord(led_id, x, y, z)
    print(f"Missing after 0 degree: {len(missing)}")
    return missing


def parse_data_file(args):
    with open(args.input_file, 'r') as input_file:
        lines = input_file.readlines()
        lines = [line.rstrip() for line in lines]
    coordinates = {}
    shot = {}
    # Parse the lines and filter ones we don't want to consider.
    for line in lines:
        led_id = int(line[2:5])
        angle = int(line[11:14])
        x = int(line[16:20])
        y = int(line[22:26])
        if not x or not y:
            continue

        shot.setdefault(led_id, []).append(Snap(led_id, angle, x, y))
    return coordinates, shot


def get_neighbor_ids(coordinates, led_id):
    prev_offset = 1
    while led_id - prev_offset >= 0:
        if reliable_coordinate(led_id - prev_offset, coordinates):
            break
        prev_offset += 1

    next_offset = 1
    while led_id + next_offset <= 499:
        if reliable_coordinate(led_id + next_offset, coordinates):
            break
        next_offset += 1
    return (led_id - prev_offset), (led_id + next_offset)


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
    return [v[0] - (IMAGE_WIDTH / 2) + 5, v[1] - (IMAGE_WIDTH / 2) - 5, v[2]]


def normalize_coord_to_center(coord):
    """
    Shifts the origin from the corner to the center. This is needed to rotate the coordinate plane about the center.
    """
    centered = normalize_to_center([coord.x, coord.y, coord.z])
    return Coord(coord.led_id, centered[0], centered[1], centered[2])


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
