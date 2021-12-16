import argparse
import os
import sys
from collections import namedtuple
from statistics import mean

Snap = namedtuple("Snap", "id angle x y")
Coord = namedtuple("Coord", "id x y z")

IMAGE_WIDTH = 1080

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
    missing_count = 0
    for k in shot.keys():
        led_id = k

        filtered_list = list(filter(lambda s: s.x != 0 and s.y != 0, shot[k]))

        z = mean(map(lambda s: s.y, shot[k]))

        ys = list(filter(lambda s: s.angle in [90, 270], filtered_list))
        if not ys:
            missing_count += 1
            continue
        else:
            y = ys[0].x if ys[0].angle == 270 else IMAGE_WIDTH - ys[0].x

        xs = list(filter(lambda s: s.angle in [0, 180], filtered_list))
        if not xs:
            missing_count += 1
            continue
        else:
            x = xs[0].x if xs[0].angle == 0 else IMAGE_WIDTH - xs[0].x

        coordinates[led_id] = Coord(led_id, x, y, int(z))

    # Write the output to file
    with open(args.output_file, 'w') as output_file:
        output_file.write("#")
        for k, v in coordinates.items():
            c = f"{v.id},{v.x},{v.y},{v.z}"
            output_file.write(c + "\n")
            print(c)

    print(f"Missing elements: {missing_count}")

# Main program logic follows:
if __name__ == '__main__':
    main()
