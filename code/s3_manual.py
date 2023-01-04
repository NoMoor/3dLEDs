import argparse
import glob
import os
from datetime import datetime
from enum import Enum
from tkinter import Menu
from typing import Callable

import grpc
from pygame.joystick import Joystick

from network import lights_pb2
from network import lights_pb2_grpc
import pygame
import pygame_menu
from pygame.font import Font

from utils.animation import read_coordinates, write_coordinates, rotate

# The relative file containing the tree coordinates.
from utils.colors import encode_rgb
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
coordinates_modified = False
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
    global coordinates_modified

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

    draw = True

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
                    draw = True
                if e.key == pygame.K_k or e.key == pygame.K_a:
                    selected_led_id = (selected_led_id - 1) % len(coords)
                    draw = True

        if any_pressed(KEYBOARD_DOWN, CONTROLLER_DOWN):
            to_down_pressed[mode](coords[selected_led_id])
            coordinates_modified = True
            draw = True
        elif any_pressed(KEYBOARD_UP, CONTROLLER_UP):
            to_up_pressed[mode](coords[selected_led_id])
            coordinates_modified = True
            draw = True

        pix = to_color_def[mode](selected_led_id)
        render_tree(selected_led_id, to_coord_def[mode], pix, mode)

        if draw:
            send_to_tree(pix)

            clock.tick(fps)


def sign(i):
    return -1 if (i < 0) else 0 if (i == 0) else 1


stick_threshold = 0.5
neg_stick_threshold = -stick_threshold


class XBone:

    def __init__(self, joystick: Joystick):
        self._jstick = joystick

    class XBoneButton(Enum):
        A = 0
        B = 1
        X = 3
        Y = 4
        R1 = 7
        R3 = 14
        L1 = 6
        L3 = 13
        L_SELECT = 15
        R_SELECT = 11

    class XBoneAxis(Enum):
        L_RIGHT = 0
        L_DOWN = 1
        R_RIGHT = 2
        R_DOWN = 3
        R2 = 4
        L2 = 5

    class XBoneHat(Enum):
        D_PAD = 0

    class XBoneStick(Enum):
        def __init__(self, id, axis, threshold):
            self.id = id
            self.axis = axis
            self.threshold = threshold

        L_LEFT = (1, 0, neg_stick_threshold)
        L_RIGHT = (2, 0, stick_threshold)
        L_UP = (3, 1, neg_stick_threshold)
        L_DOWN = (4, 1, stick_threshold)
        R_LEFT = (5, 2, neg_stick_threshold)
        R_RIGHT = (6, 2, stick_threshold)
        R_UP = (7, 3, neg_stick_threshold)
        R_DOWN = (8, 3, stick_threshold)

    class XBoneDPad(Enum):
        D_DOWN = 0
        D_UP = 1
        D_LEFT = 2
        D_RIGHT = 3

    def is_pressed(self, button) -> bool:
        if isinstance(button, XBone.XBoneButton):
            return self._jstick.get_button(button.value)
        if isinstance(button, XBone.XBoneStick):
            print(f"Check Stick {button}")
            value = self._jstick.get_axis(button.axis)
            if value == 0:
                return False
            if sign(value) != sign(button.threshold):
                return False
            return abs(value) >= abs(button.threshold)


def any_pressed(keyboard_keys: list[int], joystick_buttons: list = None) -> bool:
    if not joystick_buttons:
        joystick_buttons = []

    keys_pressed = pygame.key.get_pressed()
    key_pressed = any(keys_pressed[o] for o in keyboard_keys)

    joysticks = [XBone(pygame.joystick.Joystick(x)) for x in range(pygame.joystick.get_count())]
    button_pressed = any(any([j.is_pressed(b) for b in joystick_buttons]) for j in joysticks)

    return key_pressed or button_pressed


def send_to_tree(pix: dict[int, tuple[int, int, int]]):
    """Sends the pixels to the tree to be lit up."""
    if dry_run:
        return

    with grpc.insecure_channel('192.168.0.160:50051') as channel:
        stub = lights_pb2_grpc.LightsStub(channel)

        request = lights_pb2.SetLightsRequest()
        request.id = 1
        for k, v in pix.items():
            request.pix.append(lights_pb2.Pix(pix_id=k, rgb=encode_rgb(*v)))
        _ = stub.SetLights(request)


def render_tree(selected_led_id: int, coord_to_screen_loc, pix, mode: TranslationMode):
    """Renders the tree locally on the surface."""
    global surface
    surface.fill((30, 30, 30))

    if selected_led_id is not None:
        id_surface = text_font.render(f'Id: {selected_led_id}', False, "grey")
        id_rect = id_surface.get_rect()
        id_rect.x += 20
        id_rect.y += 20
        surface.blit(id_surface, id_rect)

    if mode is not None:
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
            pix[led_id] = (250, 250, 250)
        elif selected_led_value - adjustment_distance <= value <= selected_led_value + adjustment_distance:
            pix[led_id] = (0, 50, 0)
        elif value < selected_led_value < value + nearby:
            pix[led_id] = (50, 0, 0)
        elif value - nearby < selected_led_value < value:
            pix[led_id] = (0, 0, 50)
        else:
            pix[led_id] = (0, 0, 0)
    return pix


def rotate_screen(menu: Menu):
    """Enters a mode where the tree can be rotated around the z axis."""
    menu.full_reset()
    menu.disable()

    global coordinates_modified, coords

    min_z = min(map(lambda c: c.z, coords.values()))
    max_z = max(map(lambda c: c.z, coords.values()))
    z_scaling = (max_z - min_z) / view_height
    z_offset = padding

    draw = True

    mode = TranslationMode.X

    clock = pygame.time.Clock()
    rotate_angle = 1

    while True:
        min_x = min(map(lambda c: c.x, coords.values()))
        max_x = max(map(lambda c: c.x, coords.values()))
        x_scaling = (max_x - min_x) / view_width
        x_offset = frame_width / 2

        def flatpos_xz(c: Coord3d) -> tuple[int, int]:
            view_x = ((-c.x if mode.mirrored else c.x) / x_scaling) + x_offset
            view_z = ((max_z - c.z) / z_scaling) + z_offset

            return view_x, view_z

        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                global do_program
                do_program = False
                return
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    menu.enable()
                    return
                if e.key == pygame.K_j or e.key == pygame.K_d or e.key == pygame.K_RETURN:
                    selected_led_id = (selected_led_id + 1) % len(coords)
                    draw = True
                if e.key == pygame.K_k or e.key == pygame.K_a:
                    selected_led_id = (selected_led_id - 1) % len(coords)
                    draw = True

        if any_pressed(KEYBOARD_DOWN, CONTROLLER_DOWN):
            coords = {k: rotate(v, rotate_angle) for k, v in coords.items()}

            coordinates_modified = True
            draw = True
        elif any_pressed(KEYBOARD_UP, CONTROLLER_UP):
            coords = {k: rotate(v, -rotate_angle) for k, v in coords.items()}

            coordinates_modified = True
            draw = True

        pix = {}

        thin_highlight = (max_x - min_x) / 30
        wide_highlight = (max_x - min_x) / 10
        for led_id, coord in coords.items():
            if coord.y > 0:
                # Front of tree
                if -thin_highlight <= coord.x <= thin_highlight:
                    pix[led_id] = (0, 200, 0)
                elif -wide_highlight <= coord.x <= wide_highlight:
                    pix[led_id] = (0, 0, 200)
                else:
                    pix[led_id] = (10, 10, 10)
            elif -thin_highlight < coord.x < thin_highlight:
                # behind the tree
                pix[led_id] = (20, 0, 0)
            else:
                pix[led_id] = (0, 0, 0)

        render_tree(None, flatpos_xz, pix, None)

        if draw:
            send_to_tree(pix)

            clock.tick(fps)


def quit_menu_selection(menu: Menu):
    global do_program
    do_program = False
    menu.disable()


def initialize_main_menu() -> Menu:
    """Shows the menu for the game."""

    main_menu = pygame_menu.Menu('Welcome', frame_width, frame_height, theme=menu_theme)
    main_menu.add.button('Translate', translate, main_menu)
    main_menu.add.button('Rotate', rotate_screen, main_menu)
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


def fill(color: tuple[int, int, int] = (10, 10, 10)):
    pix = {k: color for k, v in coords.items()}
    send_to_tree(pix)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-i', '--input-file', type=str, help='The file to read in.')
    parser.add_argument('-d', '--dry-run', action='store_true')
    args = parser.parse_args()

    pygame.init()
    pygame.joystick.init()

    global surface, coords, text_font, dry_run
    dry_run = args.dry_run
    surface = pygame.display.set_mode((frame_width, frame_height))
    text_font = pygame.font.SysFont('Helvetica', 20)

    input_file = get_input_file(args.input_file)

    coords = read_coordinates(input_file)
    print(f"Read {len(coords)} coordinates from {input_file}")

    main_menu = initialize_main_menu()

    while do_program:
        main_menu.mainloop(surface)

    if not dry_run:
        fill((0, 10, 0))

    output_file = input_file
    if output_file.find('.') != -1:
        output_file = output_file[:output_file.rfind('.')]
    output_file += "." + datetime.now().strftime("%Y%m%d-%H%M%S")
    output_file += ".csv"

    if coordinates_modified:
        write_coordinates(output_file, coords, normalize=True, center_invert=False)


KEYBOARD_UP = [pygame.K_UP, pygame.K_RIGHT]
CONTROLLER_UP = [XBone.XBoneStick.R_UP, XBone.XBoneStick.R_RIGHT]
KEYBOARD_DOWN = [pygame.K_DOWN, pygame.K_LEFT]
CONTROLLER_DOWN = [XBone.XBoneStick.R_DOWN, XBone.XBoneStick.R_LEFT]

if __name__ == '__main__':
    main()
