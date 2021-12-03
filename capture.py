#!/usr/bin/env python3
# rpi_ws281x library strandtest example
# Author: Tony DiCola (tony@tonydicola.com)
#
# Direct port of the Arduino NeoPixel library strandtest example.  Showcases
# various animations on a strip of NeoPixels.

import time
from rpi_ws281x import *
import argparse
import os
import cv2

# LED strip configuration:
LED_COUNT = 150  # Number of LED pixels.
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
def color_wipe(strip, color, wait_ms=50):
    """Wipe color across display a pixel at a time."""
    for i in range(strip.numPixels()):
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


def one_by_one(strip, base_path="captures", angle=0, wait_ms=1500, dry_run=False, start=0):
    """Lights up the strand one pixel at a time."""
    color_wipe(strip, LED_OFF, 1)
    folder = os.path.join(base_path, f"{angle:03}")
    if not os.path.exists(folder):
        os.makedirs(folder)

    # initialize the camera
    cam = cv2.VideoCapture(0) if not dry_run else None # 0 -> index of camera

    for i in range(start, strip.numPixels()):
        strip.setPixelColor(i, LED_WHITE)
        strip.show()
        time.sleep(wait_ms / 1000.0)

        filename = os.path.join(folder, f"{i:03}.jpg")
        print(f"Writing file {filename}", end="\r")

        if cam:
            s, img = cam.read()
            if s:  # frame captured without any errors
                cv2.imwrite(filename, img)  # save image

        time.sleep(wait_ms / 1000.0)
        strip.setPixelColor(i, LED_OFF)
        strip.show()
        time.sleep(.05)

    print()


def main():
    # Process arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--persist', action='store_true', help='Keeps the display lit on exit')
    parser.add_argument('-d', '--dry-run', action='store_true', help='Dry run only. No values are captured.')
    parser.add_argument('-f', '--folder', type=str, default="captures", help='sets the folder to store the images')
    parser.add_argument('-s', '--start-index', type=int, default=0, help='The index of the first LED to use.')
    parser.add_argument('-e', '--end-index', type=int, default=LED_COUNT, help='The index of the last LED to use.')
    args = parser.parse_args()

    # Create NeoPixel object with appropriate configuration.
    strip = Adafruit_NeoPixel(args.end_index, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    # Initialize the library (must be called once before other functions).
    strip.begin()
    # Turn off all LEDs
    color_wipe(strip, LED_OFF, 1)

    print('Press Ctrl-C to quit.')
    if not args.persist:
        print('Use "-p" argument to keep LEDs lit on exit')

    try:

        # angles = [0, 45, 90, 135, 180, 225, 270, 315]
        angles = [0, 45, 135, 180]

        for a in angles:
            input(f"Press Enter to capture tree at {a} degrees.")
            one_by_one(strip, base_path=args.folder, angle=a, dry_run=args.dry_run, start=args.start_index)

    except KeyboardInterrupt:
        # Catch interrupt
        pass

    print()
    if not args.persist:
        color_wipe(strip, LED_OFF, 1)


# Main program logic follows:
if __name__ == '__main__':
    main()
