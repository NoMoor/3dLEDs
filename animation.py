import argparse
import time

from rpi_ws281x import *

# LED strip configuration:
LED_COUNT = 500  # Number of LED pixels.
LED_PIN = 18  # GPIO pin connected to the pixels (18 uses PWM!).
# LED_PIN       = 10      # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10  # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 100  # Set to 0 for darkest and 255 for brightest
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


# Define functions which animate LEDs in various ways.
def fillByHeight(strip, coordinates):
    min_height = min(coordinates.values(), key=lambda c: c[2])[2]
    max_height = max(coordinates.values(), key=lambda c: c[2])[2]
    speed = 2
    width = 300
    half_band = width / 2
    max_brightness = 60
    green_adjust = .5

    for i in range(min_height, max_height, speed):
        for ledid, coord in coordinates.items():
            # Distance from the given coordinate
            dist = abs(i - coord[2]) % width

            brightness = max_brightness - int(max_brightness * dist/half_band)
            if brightness > 0:
                strip.setPixelColor(ledid, Color(0, min(brightness, max_brightness), 0))
            else:
                strip.setPixelColor(ledid, Color(int(max(abs(brightness), max_brightness) * green_adjust), 0, 0))
        strip.show()


def main():
    # Process arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input-file', type=str, help='The file to read in.')
    args = parser.parse_args()

    # Create NeoPixel object with appropriate configuration.
    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    # Initialize the library (must be called once before other functions).
    strip.begin()
    # Turn off all LEDs
    strip.show()

    print("Reading lines")
    with open(args.input_file, 'r') as input_file:
        lines = input_file.readlines()
        lines = [line.rstrip() for line in lines]

    print("Processing lines")
    coordinates = {}
    for line in lines:
        ledid, x, y, z = map(int, line.split(","))
        print(f"{ledid} {x} {y} {z}")
        coordinates[ledid] = (x, y, z)

    try:
        print("Starting animation")
        print('Press Ctrl-C to quit.')
        while True:
            # fill(strip, LED_WHITE)
            fillByHeight(strip, coordinates)

    except KeyboardInterrupt:
        # Catch interrupt
        pass

    fill(strip)


# Main program logic follows:
if __name__ == '__main__':
    main()
