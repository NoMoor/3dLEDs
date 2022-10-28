# Making a light-up 3D LED Tree

A project for lighting LEDs, calculating their 3d locations, and then lighting up animations and images.

## Test Setup

Run ```sudo python3 ./step0/test.py``` and verify that the script outputs "OK" and an image is captured in `./step0/out`.

## Capture

This step captures images of each LED lit up individually. It does take some time and requires you to rotate
the tree on the ground.

Images are stored as jpegs as
`captures\{angle}\{led_num}.jpg` where `angle` is the angle of rotation (in degrees) clockwise from the
initial position and `led_num` is the led number on the strand.

1. Ensure the camera is set up in a fixed location and can see the entire tree. If needed, run the test script in 1.
2. Ensure the tree legs are marked so it's easy to turn the tree accurately. I put blue tape on a leg and directly in
   front of one leg so I can see 45 and 90 degree turns easily.
3. Start the script using
    ```
    sudo python3 ./step1/capture.py -s 0 -e 499
    ```
   When the script finishes capturing one angle. It will prompt you to turn the tree and press a button to continue.

The capture script supports starting and ending at any contiguous range. If a LED is present in one rotation, it will
be in all of them. In some cases, the captured image may be completely black. This likely indicates that the LED is
obscured by whatever it is hanging on. Don't worry too much about this. The processing scripts try to fix these issues.

### Captured Images

Images should not be included in the repo since they are quite large. If desired, drop them to a file sharing and
include a link below.

https://drive.google.com/drive/folders/1jmmNhNl4d18Hpue5HqjxG8EZfJDkkLYr

## Converting images to coordinates

The process images consists of determining where the LED is on the image and outputting that to CSV. The x/y coordinates
are then processed by the `coordinate_processing.py` script to output 3D coordinates using 2d to 3d projection and
error correction.

These scripts use PIL, OpenCV, NumPy, and MatPlotLib as dependencies.
### LED detection in images.

Let's convert images to x/y coordinates.

`python3 ./step2/image_processing.py -s 0 -e 500 -i "/home/nomoor/Pictures/tree_captures" -o "/home/nomoor/Pictures/processed_tree_captures"`

### 2D to 3D coordinates

`python3 ./step2/coordinate_processing.py "`

This step converts the x/y coordinates in the previous step to 3D coordinates that can be used for animation.

# Create an animation for playback

Then you can read in the coordinates and generate an animation playback csv.

`python3 test_animations.py -i hat_tree_coords_2021_v2.csv -o valentines_animation.csv`

# Playback animation

``