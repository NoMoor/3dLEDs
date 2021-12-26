import argparse

from animation_utils import *

# LED strip configuration:
LED_COUNT = 500  # Number of LED pixels.
LED_PIN = 18  # GPIO pin connected to the pixels (18 uses PWM!).
# LED_PIN       = 10      # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10  # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 80  # Set to 0 for darkest and 255 for brightest
LED_INVERT = False  # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL = 0  # set to '1' for GPIOs 13, 19, 41, 45 or 53

LED_OFF = Color(0, 0, 0)
LED_WHITE = Color(255, 255, 255)


# Define functions which animate LEDs in various ways.
def fill(strip, color=LED_OFF):
    s = 0
    e = strip.numPixels()
    for i in range(s, e):
        strip.setPixelColor(i, color)
    strip.show()


def main():
    # Process arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input-file', type=str, help='The file to read in.')
    parser.add_argument('-o', '--output-file', type=str, help='The file to write out.')
    args = parser.parse_args()

    strip = StripLogger(args.output_file)

    coordinates = read_coordinates(args.input_file)

    try:
        print("Starting animation")

        reveal(strip, coordinates)

    except KeyboardInterrupt:
        # Catch interrupt
        pass

    strip.write_to_file()


def reveal(strip, coordinates):
    stage_regular = 0
    stage_blue_pink = 1
    stage_build_up = 2
    stage_reveal = 3
    stage_back_to_regular = 4

    coordinates = transform(coordinates, shift_up=True, rear_off=True)

    max_click = 4

    width = 300
    click = 0

    last_frame = 0
    blend = 0
    reveal_stage = stage_regular

    while True:
        try:
            # Expand the width and recompute the coordinates.
            if reveal_stage == stage_build_up:
                width = int(1.2 * width)

            # println(f"Stage {reveal_stage} width {width}")
            coordinates2 = transform(coordinates, twisted=True, width=width)
            click += 1
            click = click % max_click

            acc = 50
            speed = width // acc

            max_iteration = width * 2
            click_size = int(max_iteration / max_click)
            start = click * click_size
            end = (click + 1) * click_size
            for i in range(start, end, speed):
                try:
                    if width > IMAGE_HEIGHT and blend < 1:
                        blend += .02

                    if reveal_stage == stage_reveal:
                        width = 300
                        coordinates2 = transform(coordinates, twisted=True, width=width)

                    color_1 = RED
                    color_2 = GREEN

                    if reveal_stage == stage_blue_pink:
                        if blend < 1:
                            blend += .02
                        color_1 = to_blended_color(RED_C, PINK_C, blend)
                        color_2 = to_blended_color(GREEN_C, BLUE_C, blend)
                    elif reveal_stage == stage_build_up:
                        color_1 = to_blended_color(PINK_C, LED_OFF_C, blend)
                        color_2 = to_blended_color(BLUE_C, LED_OFF_C, blend)
                    elif reveal_stage == stage_reveal:
                        color_1 = PINK
                        color_2 = PINK
                    elif reveal_stage == stage_back_to_regular:
                        if blend < 1:
                            blend += .02
                        color_1 = to_blended_color(PINK_C, RED_C, blend)
                        color_2 = to_blended_color(PINK_C, GREEN_C, blend)

                    for led_id, coord in coordinates2.items():
                        if is_back_of_tree(coord):
                            strip.setPixelColor(led_id, LED_OFF)
                            continue

                        # Distance from the given coordinate
                        d = coord[2]

                        dist = (d - i) % (width * 2)

                        use_color_1 = 0 < dist < width

                        if use_color_1 or width == 0:
                            strip.setPixelColor(led_id, color_1)
                        else:
                            strip.setPixelColor(led_id, color_2)

                    strip.show()

                    e = time.perf_counter()
                    if last_frame:
                        # print(f"{(e - last_frame) * 1000:0.1f}ms")
                        pass
                    last_frame = e

                except KeyboardInterrupt:
                    if reveal_stage >= stage_back_to_regular:
                        print("Exiting...")
                        return
                    if reveal_stage == stage_regular:
                        print("Press Ctrl-C to reveal")
                    if reveal_stage == stage_build_up:
                        print("Revealing now!")
                    elif reveal_stage == stage_reveal:
                        print("Press Going back to regular")

                    blend = 0
                    reveal_countdown = 0
                    reveal_stage += 1

        except KeyboardInterrupt:
            if reveal_stage >= stage_back_to_regular:
                print("Exiting...")
                return
            if reveal_stage == stage_regular:
                print("Press Ctrl-C to reveal")
            if reveal_stage == stage_build_up:
                print("Revealing now!")
            elif reveal_stage == stage_reveal:
                print("Press Going back to regular")

            blend = 0
            reveal_countdown = 0
            reveal_stage += 1


def transform(coordinates, shift_up=False, rear_off=False, twisted=False, width=300):
    min_z = min(map(lambda x: x[2], coordinates.values())) if shift_up else 0

    coordinates2 = {}
    for led_id, coord in coordinates.items():
        if rear_off and is_back_of_tree(coord):
            continue

        v = normalize_to_center(coord)
        z_adjust = percent_off_true(v[0], v[1]) * 2 * width if twisted else 0

        coordinates2[led_id] = [coord[0], coord[1], coord[2] - z_adjust - min_z]

    return coordinates2


# Main program logic follows:
if __name__ == '__main__':
    main()
