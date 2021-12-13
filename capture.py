#!/usr/bin/env python3
# rpi_ws281x library strandtest example
# Author: Tony DiCola (tony@tonydicola.com)
#
# Direct port of the Arduino NeoPixel library strandtest example.  Showcases
# various animations on a strip of NeoPixels.
# Code: https://github.com/jgarff/rpi_ws281x/blob/master/python/neopixel.py

import time
from rpi_ws281x import *
import argparse
import os
import sys
import cv2

# LED strip configuration:
LED_COUNT = 500  # Number of LED pixels.
LED_PIN = 18  # GPIO pin connected to the pixels (18 uses PWM!).
# LED_PIN       = 10      # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10  # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 40  # Set to 0 for darkest and 255 for brightest
LED_INVERT = False  # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL = 0  # set to '1' for GPIOs 13, 19, 41, 45 or 53

LED_OFF = Color(0, 0, 0)
LED_WHITE = Color(255, 255, 255)

# Define functions which animate LEDs in various ways.
def fill(strip, start=None, end=None, color=LED_OFF):
    s = start if start else 0
    e = end if end else strip.numPixels()
    for i in range(s, e):
        strip.setPixelColor(i, color)
    strip.show()

def color_wipe(strip, color, wait_ms=1, reverse=False):
    """Wipe color across display a pixel at a time."""
    for i in range(strip.numPixels()):
        index = strip.numPixels() - i - 1 if reverse else i
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms / 1000.0)

def wheel(pos):
    """Generate rainbow colors across 0-255 positions."""
    if pos < 85:
        return Color(pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return Color(255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return Color(0, pos * 3, 255 - pos * 3)


def one_by_one(strip, cam, folder="captures", angle=0, wait_ms=500, dry_run=False, start=0):
    """Lights up the strand one pixel at a time."""
    fill(strip)

    for i in range(start, strip.numPixels()):
        strip.setPixelColor(i, LED_WHITE)
        strip.show()
        time.sleep(wait_ms / 1000.0)

        filename = os.path.join(folder, f"led{i:03}_angle{angle:03}.jpg")
        _capture_image(cam, filename)

        time.sleep(0.1)
        strip.setPixelColor(i, LED_OFF)
        strip.show()
        time.sleep(.05)

    fill(strip, color=LED_WHITE)
    time.sleep(wait_ms / 1000.0)
    _capture_image(cam, os.path.join(folder, f"leds_angle{angle:03}.jpg"))
    fill(strip)
    time.sleep(0.1)


def _capture_image(cam, filename):
    if cam:
        while True:
            # Calls the 'read' method several times. For some reason,
            # this would occasionally give me the same frame as the previous image.
            # I tried diffing images but it proved to be difficult. Instead,
            # Calling read several times seems to 'flush the buffer' or something
            # so that we get a fresh image from the camera.
            s, img = cam.read()
            s, img = cam.read()
            s, img = cam.read()
            s, img = cam.read()
            s, img = cam.read()
            s, img = cam.read()
            if s:  # frame captured without any errors
                print(f"Writing file {filename}")
                img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
                cv2.imwrite(filename, img)  # save image
                break


def _capture_reference(cam, folder, angle=None):
    file_name = os.path.join(folder, f"reference_{angle:03}.jpg")
    _capture_image(cam, file_name)


def _cam(focus=0):
    cam = cv2.VideoCapture(0, cv2.CAP_V4L2)
    cam.set(cv2.CAP_PROP_AUTOFOCUS, 0) # turn off autofocus
    cam.set(cv2.CAP_PROP_FOCUS, focus)
    cam.set(3, 1920) # Set Width
    cam.set(4, 1080) # Set Height
    return cam


def _focus(strip):
    """Focus test turns on the lights and steps through the focus settings to manually find the right one."""
    cam = _cam()

    color_wipe(strip, color=LED_WHITE)
    folder = "focus_captures"
    if not os.path.exists(folder):
        os.makedirs(folder)

    for f in range(0, 256, 5):
        cam.set(cv2.CAP_PROP_FOCUS, f)
        print(f"Focusing at {f}")

        time.sleep(1)
        file_name = os.path.join(folder, f"f_{f:03}.jpg")
        _capture_image(cam, file_name)


def main():
    # Process arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--persist', action='store_true', help='Keeps the display lit on exit')
    parser.add_argument('-d', '--dry-run', action='store_true', help='Dry run only. No values are captured.')
    parser.add_argument('-f', '--focus-test', action='store_true', help='Captures images at different focus')
    parser.add_argument('-s', '--start-index', type=int, default=0, help='The index of the first LED to use.')
    parser.add_argument('-e', '--end-index', type=int, default=LED_COUNT, help='The index of the last LED to use.')
    parser.add_argument('-l', '--light', action='store_true', help='The light the tree for testing')
    args = parser.parse_args()

    # Create NeoPixel object with appropriate configuration.
    strip = Adafruit_NeoPixel(args.end_index, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    # Initialize the library (must be called once before other functions).
    strip.begin()
    # Turn off all LEDs
    strip.show()

    print('Press Ctrl-C to quit.')
    if args.focus_test:
        print('Focusing...')
        _focus(strip)
        sys.exit(0)

    if args.light:
        print('Lighting the Tree')
        fill(strip, color=Color(0,50,0))
        sys.exit(0)

    if not args.persist:
        print('Use "-p" argument to keep LEDs lit on exit')

    try:
        folder = "tree_captures"
        if not os.path.exists(folder):
            os.makedirs(folder)

        angles = [0, 45, 90, 135, 180, 225, 270, 315]
        cam = _cam()
#         time.sleep(5) # Wait 10 seconds to make sure the camera is ready

        for a in angles:
            # Turn on reference pixels
            strip.setPixelColor(0, LED_WHITE)
            strip.setPixelColor(20, Color(255, 0, 0))
            strip.setPixelColor(40, Color(0, 255, 0))
            strip.setPixelColor(60, Color(0, 0, 255))
            strip.show()
            input(f"Press Enter to capture lights-on image {a} degrees.")
            _capture_reference(cam, folder, angle=a)
            fill(strip)

            input(f"Press Enter to capture tree at {a} degrees.")
            one_by_one(strip, cam, folder=folder, angle=a, dry_run=args.dry_run, start=args.start_index)

    except KeyboardInterrupt:
        # Catch interrupt
        pass

    print()
    if not args.persist:
        fill(strip)


# Main program logic follows:
if __name__ == '__main__':
    main()
