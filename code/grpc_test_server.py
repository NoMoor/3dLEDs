import os
import time
from concurrent import futures
import logging

import grpc

from network import lights_pb2_grpc, lights_pb2
from utils.animation import read_coordinates
from utils.colors import decode_rgb
import tkinter

from utils.coords import Coord3d

TARGET_FPS = 60
TARGET_REFRESH = 1 / TARGET_FPS
SLEEP_OVERHEAD = .0003
X_PADDING = 50
Y_PADDING = 50
SCALING = .5
DOT_SIZE = 10

latest_frame = []
# The number of frames that have passed without an updated frame.
blank_frame_count = 0

tree_coordinates_file = os.path.join("treehero", "data", "coordinates.tree")

coords: dict[int, Coord3d] = read_coordinates(tree_coordinates_file)

min_x = min(map(lambda x: x.x, coords.values())) * SCALING
max_x = max(map(lambda x: x.x, coords.values())) * SCALING
min_z = min(map(lambda x: x.z, coords.values())) * SCALING
max_z = max(map(lambda x: x.z, coords.values())) * SCALING


class LightsServicer(lights_pb2_grpc.LightsServicer):
    """Implements functionality of lights service."""

    def __init__(self):
        pass

    def SetLights(self, request, context):
        self.print_light_values(request.pix)

        return lights_pb2.SetLightsResponse(is_successful=True)

    def print_light_values(self, pix):
        new_frame = []
        for p in pix:
            r, g, b = decode_rgb(p.rgb)
            new_frame.append((p.pix_id, r, g, b))

        global latest_frame
        latest_frame = new_frame


def draw_frame(canvas):
    global blank_frame_count

    if not latest_frame:
        blank_frame_count = blank_frame_count + 1

        # If it has been a while since we've gotten an updated frame, clear the canvas.
        if blank_frame_count > TARGET_FPS:
            canvas.delete("all")
            canvas.update_idletasks()
            canvas.update()
        return

    blank_frame_count = 0

    # Clear everything from the previous drawing of the canvas
    # If we don't delete everything, rectangles pile up and rendering will grind to a halt.
    canvas.delete("all")

    def get_x(c) -> int:
        # Shift the tree to the right to be visible
        return abs(min_x) + (c.x * SCALING) + X_PADDING

    def get_y(c) -> int:
        # In 3d, z is the vertical axis with 0 starting at the bottom.
        return max_z - (c.z * SCALING) + Y_PADDING

    scaled_dot_size = DOT_SIZE * SCALING

    # Draw the latest frame as a 2-D grid of pixels.
    for p in latest_frame:
        pix_id = p[0]
        coord = coords[pix_id]
        x = get_x(coord)
        y = get_y(coord)

        def _from_rgb(rgb):
            """translates an rgb tuple of int to a tkinter friendly color code."""
            return "#%02x%02x%02x" % rgb

        print(max_z)
        canvas.create_rectangle(
            x - scaled_dot_size, y - scaled_dot_size, x + scaled_dot_size, y + scaled_dot_size,
            fill=_from_rgb((p[1], p[2], p[3])))

    latest_frame.clear()

    # Update the rendering in the window.
    canvas.update_idletasks()
    canvas.update()


def serve():
    """Creates a server to process messages and a render loop to render the pixels to canvas."""
    # Create a server to handle set lights messages.
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
    lights_pb2_grpc.add_LightsServicer_to_server(
        LightsServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Server started...")

    # Create a window and canvas to draw the lights.
    root = tkinter.Tk()
    canvas = tkinter.Canvas(root, width=max_x - min_x + (X_PADDING * 2), height=max_z - min_z + (Y_PADDING * 2))
    canvas.pack()
    canvas.update_idletasks()
    canvas.update()

    # Permanent draw loop
    frame_count = 0
    start = time.perf_counter()
    while True:
        if not frame_count % TARGET_FPS:
            end = time.perf_counter()
            print(f"Average FPS: {frame_count / (end - start)}s")
            start = end
            frame_count = 0

        frame_count = frame_count + 1

        frame_start = time.perf_counter()
        draw_frame(canvas)
        frame_duration = time.perf_counter() - frame_start
        sleep_time = TARGET_REFRESH - frame_duration - SLEEP_OVERHEAD
        if sleep_time > 0:
            time.sleep(sleep_time)


if __name__ == '__main__':
    logging.basicConfig()
    serve()
