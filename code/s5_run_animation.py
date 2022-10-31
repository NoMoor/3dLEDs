import argparse
import time
from _csv import reader

from rpi_ws281x import *

# LED strip configuration:
from utils.colors import Color

LED_COUNT = 500  # Number of LED pixels.
LED_PIN = 18  # GPIO pin connected to the pixels (18 uses PWM!).
# LED_PIN       = 10      # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10  # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 25  # Set to 0 for darkest and 255 for brightest
LED_INVERT = False  # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL = 0  # set to '1' for GPIOs 13, 19, 41, 45 or 53

LED_OFF = Color(0, 0, 0)
LED_WHITE = Color(255, 255, 255)


# Reads the list in a given window skipping forward n each time.
def window(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]


def read_animation(file_name):
    light_frames = []

    with open(file_name, 'r') as read_obj:
        # pass the file object to reader() to get the reader object
        csv_reader = reader(read_obj)

        # Iterate over each row in the csv using reader object
        frame_number = 0
        for row in csv_reader:
            # row variable is a list that represents a row in csv
            # break up the list of rgb values
            # remove the first item
            frame_number = int(row.pop(0))

            parsed_frame = []
            leds = list(window(row, 3))
            for led in leds:
                # Flip the Red and Green channels since the tree is grb
                parsed_frame.append(Color(int(led[1]), int(led[0]), int(led[2])))

            # append that line to lightArray
            light_frames.append(parsed_frame)

    return light_frames


# Define functions which animate LEDs in various ways.
def fill(strip, color=LED_OFF):
    s = 0
    e = strip.numPixels()
    for i in range(s, e):
        strip.setPixelColor(i, color)
    strip.show()


def play_animation(strip, animation):
    print(f"Running Animation with {len(animation)} frames...")
    while True:
        start = time.perf_counter()
        for frame_num, frame in enumerate(animation):
            for idx, color in enumerate(frame):
                strip.setPixelColor(idx, color)
            strip.show()
        total_frames = len(animation)
        # print(f"Running at {total_frames / (time.perf_counter() - start):0.2f} fps")


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

    animation = read_animation(args.input_file)

    try:
        print("Starting animation")
        print('Press Ctrl-C to quit.')

        play_animation(strip, animation)

    except KeyboardInterrupt:
        # Catch interrupt
        print("Exiting")
        pass

    fill(strip)


# Main program logic follows:
if __name__ == '__main__':
    main()
