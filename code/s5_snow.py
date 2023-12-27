# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

# Simple test for NeoPixels on Raspberry Pi
import time
import board
import neopixel
import random

# Choose an open pin connected to the Data In of the NeoPixel strip, i.e. board.D18
# NeoPixels must be connected to D10, D12, D18 or D21 to work.
pixel_pin = board.D18

# The number of NeoPixels
num_pixels = 500

# The order of the pixel colors - RGB or GRB. Some NeoPixels have red and green reversed!
# For RGBW NeoPixels, simply change the ORDER to RGBW or GRBW.
ORDER = neopixel.GRB

pixels = neopixel.NeoPixel(
    pixel_pin, num_pixels, brightness=0.05, auto_write=False, pixel_order=ORDER
)

pixel_state = []

# TODO: See the state
fade_time = 60
half_fade = fade_time / 2;

for i in range(num_pixels):
    pixel_state.append(0);

def snow(wait):
    for i in range(num_pixels):
        current_val = pixel_state[i];
        if current_val == 0:
            if random.random() < (1 / (fade_time * 2)):
                current_val = 1
        elif current_val >= fade_time:
            current_val = 0
        else:
            current_val += 1

        pixel_state[i] = current_val
        pct = 1 - (abs(current_val - half_fade) / half_fade)
        pixels[i] = (int(255 * pct), int(255 * pct), int(255 * pct))
    pixels.show()
    time.sleep(wait)


print("Do animation")
while True:
#    pixels.fill((255, 0, 0))
#    pixels.show()
#    time.sleep(1)

    snow(0.050)  # rainbow cycle with 1ms delay per step

print("Exiting")
