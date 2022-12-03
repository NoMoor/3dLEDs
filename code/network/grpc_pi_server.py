from concurrent import futures
import logging

import grpc

import lights_pb2_grpc, lights_pb2

import board
import neopixel

# LED strip configuration:
from utils.colors import Color, decode_rgb

2
LED_COUNT = 500  # Number of LED pixels.
LED_PIN = board.D18  # GPIO pin connected to the pixels (18 uses PWM!).
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10  # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = .2  # Set to 0 for darkest and 255 for brightest
LED_INVERT = False  # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL = 0  # set to '1' for GPIOs 13, 19, 41, 45 or 53

LED_OFF = Color(0, 0, 0)
LED_WHITE = Color(255, 255, 255)


class LightsServicer(lights_pb2_grpc.LightsServicer):
    """Implements functionality of lights service."""

    def __init__(self):
        # TODO: Create a stub for testing?
        self.strip = neopixel.NeoPixel(LED_PIN, LED_COUNT, brightness=LED_BRIGHTNESS, auto_write=False)
        self.strip.show()  # Turn off all the pixels

    def SetLights(self, request, context):
        print(request)
        self.displayLights(request.pix)

        return lights_pb2.SetLightsResponse(is_successful=True)

    def displayLights(self, pix):
        for idx, p in enumerate(pix):
            r, g, b = decode_rgb(p.rgb)
            self.strip.setPixelColor(idx, (int(g), int(r), int(b)))
        self.strip.show()


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    lights_pb2_grpc.add_LightsServicer_to_server(
        LightsServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Server started...")
    server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig()
    serve()
