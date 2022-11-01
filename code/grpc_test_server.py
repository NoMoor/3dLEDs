import time
from concurrent import futures
import logging

import grpc

from network import lights_pb2_grpc, lights_pb2
from utils.colors import decode_rgb
import tkinter

TARGET_FPS = 60
TARGET_REFRESH = 1 / TARGET_FPS
SLEEP_OVERHEAD = .0003

latest_frame = []
# The number of frames that have passed without an updated frame.
blank_frame_count = 0


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

    # Draw the latest frame as a 2-D grid of pixels.
    for p in latest_frame:
        pix_id = p[0]
        x = pix_id % 20
        y = pix_id // 20
        height = 10
        width = 10
        padding = 10

        def _from_rgb(rgb):
            """translates an rgb tuple of int to a tkinter friendly color code."""
            return "#%02x%02x%02x" % rgb

        canvas.create_rectangle(
            padding + (width + padding) * x, padding + (height + padding) * y, (width + padding) * (x + 1),
            (height + padding) * (y + 1), fill=_from_rgb((p[1], p[2], p[3])))

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
    canvas = tkinter.Canvas(root)
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
