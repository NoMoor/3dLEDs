A project for lighting LEDs, calculating their 3d locations, and then lighting up animations and images.

# Capture

Script captures images of each LED lit up individually. Images are stored as jpegs as
`captures\{angle}\{led_num}.jpg` where `angle` is the angle of rotation (in degrees) clockwise from the
initial position and `led_num` is the led number on the strand.

```
sudo python3 ./capture.py -s 58 -e 150
```


NOTE: The capture script supports starting and ending at any contiguous range. If a LED is present in
one rotation, it will be in all of them.

NOTE: In some cases, the captured image may be completely black. This likely indicates that the LED is
obscured by whatever it is hanging on.
