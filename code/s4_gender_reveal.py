import argparse
from enum import IntEnum

from code.utils.animation import *
from code.utils.animator import Animator
from code.utils.visualize import animate_tree
from code.utils.colors import *


def main():
    # Process arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input-file', type=str, help='The file to read in.')
    parser.add_argument('-o', '--output-file', type=str, help='The file to write out.')
    args = parser.parse_args()

    strip = LightStripLogger(args.output_file)

    coordinates = read_coordinates(args.input_file)
    max_z = max(coordinates.values(), key=lambda c: c.z).z

    band_width = 300
    animation_frames = 150

    def shift_up(fn, coord):
        shift_per_frame = band_width * 2 / animation_frames
        shift = fn * shift_per_frame
        return coord.with_z((coord.z - shift) % (band_width * 2))

    def raise_by_rotation(fn, coord):
        # Make 2 rotates up the tree
        percent = percent_off_true(coord.x, coord.y)
        offset = percent * band_width * 2
        return coord.with_z(coord.z + offset)

    def rotate_by_height(fn, coord):
        # Make 2 rotates up the tree
        ratio = 1.5 * 360 * coord.z / max_z  # % through the turn
        return rotate(coord, ratio)

    def h_bands(fn, coord, color):
        # TODO: Generalize this to num bands and colors
        z = coord.z % (band_width * 2)

        if 0 <= z < band_width:
            return RED
        else:
            return GREEN

    def v_bands(fn, coord, color):
        # TODO: Generalize this to num bands and colors
        percent = percent_off_true(coord.x, coord.y)
        if 0 <= percent <= .25 or .5 <= percent <= .75:
            return RED
        else:
            return GREEN

    try:
        print("Starting animation")
        a = Animator(strip)\
            .until(frames=animation_frames) \
            .transform_location(shift_up) \
            .transform_location(raise_by_rotation) \
            .transform_color(h_bands) \

        a.animate(coordinates)

        # reveal(strip, coordinates)

    except KeyboardInterrupt:
        # Catch interrupt
        pass

    strip.write_to_file()

    animate_tree(args.input_file, strip.output_filename)


class RevealStage(IntEnum):
    stage_regular = 0
    stage_blue_pink = 1
    stage_build_up = 2
    stage_reveal = 3
    stage_back_to_regular = 4


def reveal(strip, coordinates):
    max_click = 4

    width = 300
    click = 0

    blend = 0
    reveal_stage = RevealStage.stage_regular
    stage_counter = 0

    while True:
        # Expand the width and recompute the coordinates.
        if reveal_stage == RevealStage.stage_build_up:
            width = int(1.5 * width)

        # println(f"Stage {reveal_stage} width {width}")
        coordinates2 = transform(coordinates, twisted=True, width=width)
        click += 1
        click = click % max_click

        acceleration = 150
        speed = width // acceleration

        max_iteration = width * 2
        click_size = int(max_iteration / max_click)
        start = click * click_size
        end = (click + 1) * click_size
        for i in range(start, end, speed):
            if reveal_stage == RevealStage.stage_reveal:
                width = 300
                coordinates2 = transform(coordinates, twisted=True, width=width)
                stage_counter = 0

            color_1 = RED
            color_2 = GREEN

            if reveal_stage == RevealStage.stage_blue_pink:
                if blend < 1:
                    blend += .02
                color_1 = Color.to_blended_color(RED_C, PINK_C, blend)
                color_2 = Color.to_blended_color(GREEN_C, BLUE_C, blend)
            elif reveal_stage == RevealStage.stage_build_up:
                if width > IMAGE_HEIGHT and blend < 1:
                    blend += .02
                elif blend >= 1:
                    reveal_stage += 1
                    blend = 0
                    stage_counter = 0

                color_1 = Color.to_blended_color(PINK_C, LED_OFF_C, blend)
                color_2 = Color.to_blended_color(BLUE_C, LED_OFF_C, blend)
            elif reveal_stage == RevealStage.stage_reveal:
                color_1 = PINK
                color_2 = PINK
            elif reveal_stage == RevealStage.stage_back_to_regular:
                if blend < 1:
                    blend += .02
                color_1 = Color.to_blended_color(PINK_C, RED_C, blend)
                color_2 = Color.to_blended_color(PINK_C, GREEN_C, blend)

            for led_id, coord in coordinates2.items():

                # Distance from the given coordinate
                d = coord[2]

                dist = (d - i) % (width * 2)

                use_color_1 = 0 < dist < width

                if use_color_1 or width == 0:
                    strip.setPixelColor(led_id, color_1)
                else:
                    strip.setPixelColor(led_id, color_2)

            strip.show()

        stage_counter += 1
        if stage_complete(reveal_stage, stage_counter):
            if reveal_stage == RevealStage.stage_back_to_regular:
                print("Exiting...")
                return
            if reveal_stage == RevealStage.stage_regular:
                print("Press Ctrl-C to reveal")
            if reveal_stage == RevealStage.stage_build_up:
                print("Revealing now!")
            elif reveal_stage == RevealStage.stage_reveal:
                print("Press Going back to regular")

            blend = 0
            stage_counter = 0
            reveal_stage += 1


def stage_complete(stage, counter):
    if stage == RevealStage.stage_regular or stage == RevealStage.stage_back_to_regular:
        return counter % 8 == 0
    if stage == RevealStage.stage_blue_pink:
        return counter % 2 == 0
    if stage == RevealStage.stage_reveal:
        return counter % 2 == 0
    else:
        return counter % 4 == 0


def transform(coordinates, twisted=False, width=300):
    coordinates2 = {}
    for led_id, coord in coordinates.items():
        z_adjust = percent_off_true(coord.x, coord.y) * 2 * width if twisted else 0

        coordinates2[led_id] = Coord(coord.led_id, coord.x, coord.y, coord.z - z_adjust)

    return coordinates2


# Main program logic follows:
if __name__ == '__main__':
    main()
