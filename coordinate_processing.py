import argparse
import csv
import os
import sys
from collections import namedtuple
from statistics import mean
import matplotlib.pyplot as plt

Snap = namedtuple("Snap", "led_id angle x y")
Coord = namedtuple("Coord", "led_id x y z")

IMAGE_WIDTH = 1080


def draw(og_leds, alt_leds):
    fig = plt.figure()
    ax = fig.add_subplot(projection='3d')

    alt_ids = set(filter(lambda x: x.led_id, alt_leds))

    left_out = []

    xs = []
    ys = []
    zs = []
    for led in og_leds:
        if led.led_id in alt_ids:
            continue

        if led.x == 0 or led.y == 0:
            left_out.append(led)
            continue

        xs.append(led.x)
        ys.append(led.y)
        zs.append(led.z)

    ax.plot3D(xs, ys, zs, 'gray')

    xs = []
    ys = []
    zs = []
    for led in alt_leds:
        xs.append(led.x)
        ys.append(led.y)
        zs.append(led.z)

    ax.scatter(xs, ys, zs, marker='^')

    xs = []
    ys = []
    zs = []
    for led in left_out:
        xs.append(led.x)
        ys.append(led.y)
        zs.append(led.z)

    ax.scatter(xs, ys, zs, marker='o')

    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_box_aspect((9, 9, 16))

    plt.gca().invert_zaxis()

    plt.show()


def avg(a, b):
    return int((a+b)/2)


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
    for l in lines:
        # print(l)
        led_id = int(l[2:5])
        # print(f"id {id}")
        angle = int(l[11:14])
        # print(f"angle {angle}")
        x = int(l[16:20])
        # print(f"x {x}")
        y = int(l[22:26])
        # print(f"y {y}")
        if not x or not y:
            continue

        shot.setdefault(led_id, []).append(Snap(led_id, angle, x, y))

    # Calculate the coordinates
    missingx = []
    missingy = []
    for k in shot.keys():
        led_id = k

        filtered_list = list(filter(lambda s: s.x != 0 and s.y != 0, shot[k]))

        z = mean(map(lambda s: s.y, shot[k]))

        ys = list(filter(lambda s: s.angle in [90, 270], filtered_list))
        if not ys:
            missingy.append(led_id)
            y = 0
        else:
            y = ys[0].x if ys[0].angle == 270 else IMAGE_WIDTH - ys[0].x

        xs = list(filter(lambda s: s.angle in [0, 180], filtered_list))
        if not xs:
            missingx.append(led_id)
            x = 0
        else:
            x = xs[0].x if xs[0].angle == 0 else IMAGE_WIDTH - xs[0].x

        coordinates[led_id] = Coord(led_id, x, y, int(z))

    print(f"Missing x: {len(missingx)}")
    print()
    print(f"Missing y: {len(missingy)}")

    fixed = []
    for k, v in coordinates.items():
        if v.x == 0 or v.y == 0:
            if not reliable_neighbors(k, coordinates):
                continue

            pn = coordinates.get(k - 1)
            nn = coordinates.get(k + 1)
            # Interpolate between these
            # TODO: Maybe keep the x/y if it exists?
            fixed_point = Coord(k, avg(pn.x, nn.x), avg(pn.y, nn.y), avg(pn.z, nn.z))

            fixed.append(fixed_point)

            coordinates[k] = fixed_point


    for k, v in coordinates.items():
        if v.x == 0 and v.y == 0:
            if not reliable_neighbors(k, coordinates):
                print(f"{k} is unfixable")

    print()
    # print(f"Fixed Neighbors: {list(map(lambda x: x.led_id, fixed))}")
    print(f"Fixed with Neighbors: {len(fixed)}")

    # Write the output to file
    with open(args.output_file, 'w') as output_file:
        csvwriter = csv.writer(output_file)
        csvwriter.writerow(("id", "x", "y", "z"))
        for k, v in coordinates.items():
            csvwriter.writerow(v)

    try:
        draw(coordinates.values(), fixed)

    except KeyboardInterrupt:
        pass


def reliable_neighbors(led_id, coordinates):
    pn = coordinates.get(led_id - 1)
    nn = coordinates.get(led_id + 1)
    return pn and nn and pn.x > 0 and pn.y > 0 and nn.x > 0 and nn.y > 0


# Main program logic follows:
if __name__ == '__main__':
    main()
