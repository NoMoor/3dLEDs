import argparse
import glob
import os
from datetime import datetime
from enum import Enum
from tkinter import Menu
from typing import Callable

import pygame
import pygame_menu
from pygame.font import Font
from pygame_menu import Theme

from utils.animation import read_coordinates, write_coordinates

# The relative file containing the tree coordinates.
from utils.coords import Coord3d

frame_width = 800
frame_height = 800
padding = 50
view_width = frame_width - (2 * padding)
view_height = frame_height - (2 * padding)
nearby = 150
adjustment_distance = 5
fps = 20

menu_theme = pygame_menu.themes.THEME_DARK

surface: pygame.Surface
coords: dict[int, Coord3d]
text_font: Font
modified = False
do_program = True


class TranslationMode(Enum):
    X = (1, False)
    Y = (2, False)
    Z_X = (3, False)
    X_NEG = (4, True)
    Y_NEG = (5, True)
    Z_Y = (6, False)

    def __init__(self, num: int, mirrored: bool):
        self.num = num
        self.mirrored = mirrored


def minus_x(coord: Coord3d) -> Coord3d:
    coord.x -= adjustment_distance
    return coord


def plus_x(coord: Coord3d) -> Coord3d:
    coord.x += adjustment_distance
    return coord


def minus_y(coord: Coord3d) -> Coord3d:
    coord.y -= adjustment_distance
    return coord


def plus_y(coord: Coord3d) -> Coord3d:
    coord.y += adjustment_distance
    return coord


def minus_z(coord: Coord3d) -> Coord3d:
    coord.z -= adjustment_distance
    return coord


def plus_z(coord: Coord3d) -> Coord3d:
    coord.z += adjustment_distance
    return coord


def translate(menu: Menu) -> None:
    global modified

    menu.full_reset()
    menu.disable()
    print("Adjust Z")

    min_x = min(map(lambda c: c.x, coords.values()))
    max_x = max(map(lambda c: c.x, coords.values()))
    min_y = min(map(lambda c: c.y, coords.values()))
    max_y = max(map(lambda c: c.y, coords.values()))
    min_z = min(map(lambda c: c.z, coords.values()))
    max_z = max(map(lambda c: c.z, coords.values()))

    x_scaling = (max_x - min_x) / view_width
    x_offset = abs(int(min_x / x_scaling)) + padding
    y_scaling = (max_y - min_y) / view_width
    y_offset = abs(int(min_y / y_scaling)) + padding
    z_scaling = (max_z - min_z) / view_height
    z_offset = padding

    selected_led_id = 0
    mode = TranslationMode.X

    def flatpos_xz(c: Coord3d) -> tuple[int, int]:
        view_x = ((-c.x if mode.mirrored else c.x) / x_scaling) + x_offset
        view_z = ((max_z - c.z) / z_scaling) + z_offset

        return view_x, view_z

    def flatpos_yz(c: Coord3d) -> tuple[int, int]:
        view_x = ((-c.y if mode.mirrored else c.y) / y_scaling) + y_offset
        view_z = ((max_z - c.z) / z_scaling) + z_offset

        return view_x, view_z

    # Mapping from mode to coordinate function
    to_coord_def: dict[TranslationMode, Callable[[Coord3d], tuple[int, int]]] = {
        TranslationMode.X: flatpos_xz,
        TranslationMode.X_NEG: flatpos_xz,
        TranslationMode.Y: flatpos_yz,
        TranslationMode.Y_NEG: flatpos_yz,
        TranslationMode.Z_X: flatpos_xz,
        TranslationMode.Z_Y: flatpos_yz,
    }

    # Mapping from mode to lambda which returns colored tree nodes
    to_color_def: dict[TranslationMode, Callable[[int], dict[int, tuple[int, int, int]]]] = {
        TranslationMode.X: lambda sid: color_tree(sid, lambda c: c.x),
        TranslationMode.X_NEG: lambda sid: color_tree(sid, lambda c: c.x),
        TranslationMode.Y: lambda sid: color_tree(sid, lambda c: c.y),
        TranslationMode.Y_NEG: lambda sid: color_tree(sid, lambda c: c.y),
        TranslationMode.Z_X: lambda sid: color_tree(sid, lambda c: c.z),
        TranslationMode.Z_Y: lambda sid: color_tree(sid, lambda c: c.z),
    }

    to_up_pressed: dict[TranslationMode, Callable[[Coord3d], Coord3d]] = {
        TranslationMode.X: plus_x,
        TranslationMode.X_NEG: minus_x,
        TranslationMode.Y: plus_y,
        TranslationMode.Y_NEG: minus_y,
        TranslationMode.Z_X: plus_z,
        TranslationMode.Z_Y: plus_z,
    }

    to_down_pressed: dict[TranslationMode, Callable[[Coord3d], Coord3d]] = {
        TranslationMode.X: minus_x,
        TranslationMode.X_NEG: plus_x,
        TranslationMode.Y: minus_y,
        TranslationMode.Y_NEG: plus_y,
        TranslationMode.Z_X: minus_z,
        TranslationMode.Z_Y: minus_z,
    }

    clock = pygame.time.Clock()

    while True:
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                global do_program
                do_program = False
                return
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_x:
                    mode = TranslationMode.X if (mode != TranslationMode.X) else TranslationMode.X_NEG
                if e.key == pygame.K_y:
                    mode = TranslationMode.Y if (mode != TranslationMode.Y) else TranslationMode.Y_NEG
                if e.key == pygame.K_z:
                    mode = TranslationMode.Z_X if (mode != TranslationMode.Z_X) else TranslationMode.Z_Y
                if e.key == pygame.K_ESCAPE:
                    menu.enable()
                    return

                if e.key == pygame.K_j or e.key == pygame.K_d or e.key == pygame.K_RETURN:
                    selected_led_id = (selected_led_id + 1) % len(coords)
                if e.key == pygame.K_k or e.key == pygame.K_a:
                    selected_led_id = (selected_led_id - 1) % len(coords)

        if pygame.key.get_pressed()[pygame.K_DOWN]:
            to_down_pressed[mode](coords[selected_led_id])
            modified = True
        elif pygame.key.get_pressed()[pygame.K_UP]:
            to_up_pressed[mode](coords[selected_led_id])
            modified = True

        pix = to_color_def[mode](selected_led_id)
        render_tree(selected_led_id, to_coord_def[mode], pix, mode)
        clock.tick(fps)


def render_tree(selected_led_id, coord_to_screen_loc, pix, mode: TranslationMode):
    global surface
    surface.fill((30, 30, 30))

    id_surface = text_font.render(f'Id: {selected_led_id}', False, "grey")
    id_rect = id_surface.get_rect()
    id_rect.x += 20
    id_rect.y += 20
    surface.blit(id_surface, id_rect)

    mode_surface = text_font.render(f'Mode: {mode.name}', False, "grey")
    mode_rect = mode_surface.get_rect()
    mode_rect.x = frame_width - 20 - mode_rect.width
    mode_rect.y += 20
    surface.blit(mode_surface, mode_rect)

    for led_id, coord in coords.items():
        color = pix[led_id]
        pygame.draw.circle(surface, color, coord_to_screen_loc(coord), 2)
    pygame.display.update()


def color_tree(selected_led_id: int, extractor: Callable[[Coord3d], int]) -> dict[int, tuple[int, int, int]]:
    selected_led = coords[selected_led_id]
    selected_led_value = extractor(selected_led)

    pix = {}
    for led_id, coord in coords.items():
        value = extractor(coord)
        if led_id == selected_led_id:
            pix[led_id] = (200, 200, 200)
        elif selected_led_value - adjustment_distance <= value <= selected_led_value + adjustment_distance:
            pix[led_id] = (0, 200, 0)
        elif value < selected_led_value < value + nearby:
            pix[led_id] = (200, 0, 0)
        elif value - nearby < selected_led_value < value:
            pix[led_id] = (0, 0, 200)
        else:
            pix[led_id] = (100, 100, 100)
    return pix


def rotate(menu: Menu):
    menu.disable()
    print("Rotate")


def quit_menu_selection(menu: Menu):
    global do_program
    do_program = False
    menu.disable()


def initialize_main_menu() -> Menu:
    """Shows the menu for the game."""

    main_menu = pygame_menu.Menu('Welcome', frame_width, frame_height, theme=menu_theme)
    main_menu.add.button('Translate', translate, main_menu)
    main_menu.add.button('Rotate', rotate, main_menu)
    main_menu.add.button('Quit', quit_menu_selection, main_menu)

    return main_menu


def get_input_file(args_input_file) -> str:
    if args_input_file:
        return args_input_file

    root_folder = os.path.join('s3', '')
    print(f"looking in {root_folder}")
    coord_files = list(glob.glob(f"{root_folder}*"))
    sorted(coord_files, key=lambda file: os.path.getmtime(file))
    print("Candidate files")
    print("----")
    [print(c) for c in coord_files]
    print("----")
    return coord_files[0]


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-i', '--input-file', type=str, help='The file to read in.')
    args = parser.parse_args()

    pygame.init()

    global surface, coords, text_font
    surface = pygame.display.set_mode((frame_width, frame_height))
    text_font = pygame.font.SysFont('Helvetica', 20)

    input_file = get_input_file(args.input_file)

    coords = read_coordinates(input_file)
    print(f"Read {len(coords)} coordinates from {input_file}")

    main_menu = initialize_main_menu()

    while do_program:
        main_menu.mainloop(surface)

    output_file = input_file
    if output_file.rfind('.') != -1:
        output_file = output_file[:output_file.rfind('.')]
    output_file += "_" + datetime.now().strftime("%Y%m%d-%H%M%S")
    output_file += ".csv"

    if modified:
        write_coordinates(output_file, coords, normalize=True, center_invert=False)


if __name__ == '__main__':
    main()
