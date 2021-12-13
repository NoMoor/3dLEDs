import argparse
import os
import sys


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
    shot = []

    # Parse the lines and filter ones we don't want to consider.
    for l in lines:
        # print(l)
        id = int(l[2:5])
        # print(f"id {id}")
        angle = int(l[11:14])
        # print(f"angle {angle}")
        x = int(l[16:20])
        # print(f"x {x}")
        y = int(l[22:26])
        # print(f"y {y}")
        if not x or not y:
            continue
        if angle in [45, 135, 225, 315]:
            continue

        shot.append((int(id), int(angle), int(x), int(y)))

    # Calculate the coordinates
    for s in shot:
        if s[0] in coordinates:
            prev = coordinates[s[0]]
            if abs(540 - s[2]) < abs(540 - prev[2]):
                coordinates[s[0]] = s
        else:
            coordinates[s[0]] = s

    # Write the output to file
    with open(args.output_file, 'w') as output_file:
        output_file.write("#")
        for k, v in coordinates.items():
            c = f"{k},{v[2]},0,{v[3]}"
            output_file.write(c + "\n")
            print(c)


# Main program logic follows:
if __name__ == '__main__':
    main()
