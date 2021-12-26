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


def draw(og_leds, fixed_leds=None, limit=None, with_labels=False):
    if not fixed_leds:
        fixed_leds = []

    if not limit:
        limit = [0, len(og_leds) - 1]

    fig = plt.figure()
    ax = fig.add_subplot(projection='3d')

    fixes = []
    for x in fixed_leds:
        fixes.extend(x)
    alt_ids = set(map(lambda l: l.led_id, fixes))

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
    for i, fix in enumerate(fixed_leds):
        xs = []
        ys = []
        zs = []
        labels = []
        for led in fix:
            if limit[0] <= led.led_id <= limit[1]:
                labels.append(led.led_id)
                xs.append(led.x)
                ys.append(led.y)
                zs.append(led.z)

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
    ax.set_xlim([0, IMAGE_HEIGHT])
    ax.set_ylabel('Y')
    ax.set_ylim([0, IMAGE_WIDTH])
    ax.set_zlabel('Z')
    ax.set_zlim([0, IMAGE_HEIGHT])
    ax.set_box_aspect((9, 9, 16))

    plt.gca().invert_zaxis()
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

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input-file', type=str, help='The file to read in.')
    parser.add_argument('-o', '--output-file', type=str, help='The file to output.')
    args = parser.parse_args()

    if not os.path.exists(f"{args.input_file}"):
        print(f"File `{args.input_file}` doesn't exist. Exiting...")
        sys.exit()

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

    # Go through the normal 0/90/180/270 angles and try to fill in the coordinates
    # If we cannot get both x and y from this, add it to the map of missing leds.
    missing = {}
    for k in shot.keys():
        led_id = k

        filtered_list = list(filter(lambda s: s.x != 0 and s.y != 0, shot[led_id]))

        z = extract_z(shot[k])

        ys = list(filter(lambda s: s.angle in [90, 270], filtered_list))
        y = (ys[0].x if ys[0].angle == 270 else IMAGE_WIDTH - ys[0].x) if ys else 0

        xs = list(filter(lambda s: s.angle in [0, 180], filtered_list))
        x = (xs[0].x if xs[0].angle == 0 else IMAGE_WIDTH - xs[0].x) if xs else 0

        if x == 0 or y == 0:
            missing[led_id] = filtered_list

        coordinates[led_id] = Coord(led_id, x, y, z)

    print(f"Missing after 0 degree: {len(missing)}")

    # Go through the list of missing leds. Look at 45/135/225/315 angles and try to fill in the coordinates
    # If we cannot get both x and y from this, add it to the map of missing_45 leds.
    missing_45 = {}
    fixed_45 = []
    for k, v in missing.items():
        led_id = k
        filtered_list = v
        stored_point = coordinates[led_id]

        # Extract the coordinates
        z = extract_z(shot[k])

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
            fixed_45.append(coord)

        coordinates[led_id] = coord

    print(f"Fixed 45 degree: {len(fixed_45)}")
    for x in fixed_45:
        # print(f"F45 - {x.led_id:03}")
        if x.led_id in missing:
            del missing[x.led_id]

    print(f"Missing after 45 degree: {len(missing_45)}")

    # Fix coordinates where possible with by finding the closest neighbors and interpolating
    fixed_neighbor = []
    for k, v in missing.items():
        pn = None
        p_offset = 1
        while not pn and k - p_offset >= 0:
            if reliable_coordinate(k - p_offset, coordinates):
                pn = coordinates[k - p_offset]
                break
            p_offset += 1

        nn = None
        n_offset = 1
        while not nn and k + n_offset <= 499:
            if reliable_coordinate(k + n_offset, coordinates):
                nn = coordinates[k + n_offset]
                break
            n_offset += 1

        if not pn or not nn:
            continue

        # Interpolate between these
        coord = Coord(k,
                      avg(pn.x, nn.x, offset=(p_offset + n_offset)),
                      avg(pn.y, nn.y, offset=(p_offset + n_offset)),
                      avg(pn.z, nn.z, offset=(p_offset + n_offset)))
        fixed_neighbor.append(coord)
        coordinates[k] = coord

    print(f"Fixed neighbors: {len(fixed_neighbor)}")

    # Write the output to file
    with open(args.output_file, 'w') as output_file:
        csvwriter = csv.writer(output_file)
        csvwriter.writerow(("id", "x", "y", "z"))
        for k, v in coordinates.items():
            csvwriter.writerow(v)

    try:
        draw(coordinates.values(), [fixed_45, fixed_neighbor], limit=[0, 500], with_labels=False)

    except KeyboardInterrupt:
        pass


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
    return led and led.x > 0 and led.y > 0


# Main program logic follows:
if __name__ == '__main__':
    main()
