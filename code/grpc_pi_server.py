from concurrent import futures
import logging

import grpc

from network import lights_pb2_grpc, lights_pb2

import board
import neopixel
import time

# LED strip configuration:
from utils.colors import Color, decode_rgb

logger = logging.getLogger(__name__)

LED_COUNT = 500  # Number of LED pixels.
LED_PIN = board.D18  # GPIO pin connected to the pixels (18 uses PWM!).
# LED_PIN       = 10      # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10  # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = .2  # Set to 0 for darkest and 1 for brightest
LED_INVERT = False  # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL = 0  # set to '1' for GPIOs 13, 19, 41, 45 or 53

LED_OFF = (0, 0, 0)
LED_WHITE = (255, 255, 255)

class LightsServicer(lights_pb2_grpc.LightsServicer):
    """Implements functionality of lights service."""

    def __init__(self):
        # TODO: Create a stub for testing?
        self._strip = neopixel.NeoPixel(LED_PIN, LED_COUNT, brightness=LED_BRIGHTNESS, auto_write=False)
        self._strip.show()  # Turn off all the pixels

    def SetLights(self, request, context):
        start = time.perf_counter()
        self.displayLights(request.pix)
        end = time.perf_counter()
        print(f"Frame: {1 / (end - start)}")

        return lights_pb2.SetLightsResponse(is_successful=True)

    def displayLights(self, pix):
        print(len(pix))

        for i in range(LED_COUNT):
            self._strip[i] = LED_OFF

        for idx, p in enumerate(pix):
            self._strip[idx] = decode_rgb(p.rgb)
        self._strip.show()



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
