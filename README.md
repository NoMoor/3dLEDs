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

# Captured Images

Instead of including all images in the git repo, images of the tree have been moved to Google Drive.

https://drive.google.com/drive/folders/1jmmNhNl4d18Hpue5HqjxG8EZfJDkkLYr

# Process Images

The process images script currently outputs updated images with an indicator of the selected point. 
This is intended to be used for checking the results.

Script currently uses PIL, OpenCV, NumPy, and MatPlotLib as dependencies.

`python3 image_processing.py -s 0 -e 500 -i "/home/nomoor/Pictures/tree_captures" -o "/home/nomoor/Pictures/processed_tree_captures"`
