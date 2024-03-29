import argparse

import PIL
from PIL import Image
from utils.animation import *
from utils.colors import *
from utils.visualize import animate_tree
from utils import continuation as cont


# Define functions which animate LEDs in various ways.
def fill(strip, color=LED_OFF):
    s = 0
    e = strip.numPixels()
    for i in range(s, e):
        strip.setPixelColor(i, color)
    strip.show()


# Define functions which animate LEDs in various ways.
def fill_by_height(strip, coordinates, axis="z", width=300):
    acc = 150
    speed = width // acc
    half_band = width / 2
    max_brightness = 255
    green_adjust = .5

    for i in range(width * 2, 0, -speed):
        for led_id, coord in coordinates.items():
            # Distance from the given coordinate
            if axis == "x":
                d = coord.x
            elif axis == "y":
                d = coord.y
            else:
                d = coord.z

            dist = (d - i) % (width * 2)

            color_1 = 0 < dist < width

            brightness_modifier = 1 - abs(((dist % width) - half_band) / half_band)

            # c1 = PINK_V1.adjust_brightness(brightness_modifier)
            # c2 = Color(brightness, 0, 0)
            c1 = LIGHT_GREEN.adjust_brightness(brightness_modifier)
            c2 = GREEN.adjust_brightness(brightness_modifier)
            strip.setPixelColor(led_id, c1 if color_1 else c2)

        strip.show()


def test_bars(strip, coordinates, axis="z", size = 100):
    r = range(0, IMAGE_HEIGHT // size)

    if axis == 'x' or axis == 'y':
        r = range(0, IMAGE_WIDTH // size)

    for i in r:
        for led_id, coord in coordinates.items():
            # Distance from the given coordinate
            if axis == "x":
                d = coord[0]
            elif axis == "y":
                d = coord[1]
            else:
                d = coord[2]

            left = i * size
            center = (i + 1) * size
            right = (i + 2) * size

            if left <= d <= center:
                strip.setPixelColor(led_id, Color(0, 255, 0))
            elif center <= d <= right:
                strip.setPixelColor(led_id, Color(0, 0, 255))
            else:
                strip.setPixelColor(led_id, LED_OFF)
        strip.show()

        input(f"Wait for {i}")


def test_image(strip, coordinates):
    # img = Image.open("img/test.png").convert('RGB')

    img = Image.open("s4/snowflake.png").convert('RGB')
    img = PIL.ImageOps.invert(img)

    # img = Image.open("img/WE.png").convert('RGB')

    for led_id, coord in coordinates.items():
        # Get color for that LED
        h = img.getpixel((coord[0], coord[2]))
        strip.setPixelColor(led_id, Color(h[1], h[0], h[2]))

        # if _is_on(coord[0], coord[2] + 100, img, size=10):
        #     strip.setPixelColor(led_id, PINK)
        # else:
        #     strip.setPixelColor(led_id, LED_OFF)

    strip.show()


def _is_on(x, y, img, size=20):

    total = 0
    on_count = 0
    for i in range(x - size, x + size):
        if 0 > i or i > IMAGE_WIDTH:
            print(f"OOR x: {i}")
            continue

        for j in range(y - size, y + size):
            if 0 > j or j > IMAGE_HEIGHT:
                print(f"OOR y: {j}")
                continue

            total += 1
            h = img.getpixel((i, j))
            # print(f"{x} {y} {i} {j} {h}")
            if h[0] > 1:
                on_count += 1

    return on_count > (total // 2)


def main():
    # Process arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input-file', type=str, help='The file to read in.')
    parser.add_argument('-o', '--output-file', type=str, help='The file to write out.')
    parser.add_argument('-s', '--test-image', action='store_true', help='Whether to show the test image')
    parser.add_argument('-t', '--test-bars', action='store_true', help='Whether to show test bars')
    parser.add_argument('-x', '--axis', type=str, help='The axis to run the animation around')
    args = parser.parse_args()

    input_file = cont.get_tree_coordinates(args.input_file)
    coordinates = read_coordinates(input_file)
    print(f"Coor len {len(coordinates)}")

    # Create NeoPixel object with appropriate configuration.
    light_strip = LightStripLogger(coordinates, args.output_file)

    try:
        print("Creating animation")
        if args.test_image:
            test_image(light_strip, coordinates)
        elif args.test_bars:
            test_bars(light_strip, coordinates, axis=args.axis, size=args.test_bars)
        else:
            fill_by_height(light_strip, coordinates, axis=args.axis)

        light_strip.write_to_file()

        animate_tree(input_file, light_strip.output_filename)

    except KeyboardInterrupt:
        # Catch interrupt
        pass

    print("All done here")


# Main program logic follows:
if __name__ == '__main__':
    main()
