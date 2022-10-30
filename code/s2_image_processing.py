from datetime import datetime
import time

from utils.coords import Coord2d
from utils import continuation as c

import cv2
import os
import argparse

__doc__ = """
This script takes raw images and identifies the brightest x/y coordinate in the image.
The results are output to a csv where each line is formatted "id{led_id},angle{angle_deg}-x{x_coord},y{y_coord}" with
components:

  * led_id = 3 digit id of the led. Ex: 072
  * angle_deg = 3 digit angle in degrees. Ex: 270
  * x_coord = 4 digit x coordinate of the brightest pixel on the image where the left of the image is 0.
  * y_coord = 4 digit y coordinate of the brightest pixel on the image where the top of the image is 0.  
"""

THRESHOLD_VALUE = 40
# Radius must be odd for GaussianBlur
RADIUS = 11


def detect_light_location(file_name):
    """
    Reach an image from file, converts it to gray-scale and then finds the brightest area.
    Returns a tuple of [x, y], value, image.
    """

    image = cv2.imread(file_name)

    processed_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    processed_image = cv2.GaussianBlur(processed_image, (RADIUS, RADIUS), 0)
    # ret, processed_image = cv2.threshold(processed_image, THRESHOLD_VALUE, 255, cv2.THRESH_TOZERO)
    (minVal, maxVal, minLoc, maxLoc) = cv2.minMaxLoc(processed_image)

    return maxLoc, maxVal, processed_image


def save_image(image, folder, filename):
    """
    Saves the image array as a jpeg at the given folder / file name. If the folder doesn't exist, it is created.
    """
    if not os.path.exists(folder):
        os.makedirs(folder)

    full_filename = os.path.join(folder, filename)
    cv2.imwrite(full_filename, image)


def main():
    """
    Executes the processing of jpeg images to coordinates in each image. The result is a CSV with id,angle,x,y columns.
    Flags:
      -s (optional) the start index of the first LED. Ex: 10
      -e (optional)the end index of the last LED to use (exclusive). Ex: 249
      -i the relative folder of the input files. Images are expected to be named like `led###_angle###.jpg`
      -i the relative folder of the output file(s). Images are output as `led###_angle###_processed.jpg
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--start-index', type=int, default=0, help='The index of the first LED to use.')
    parser.add_argument('-e', '--end-index', type=int, default=500, help='The index of the last LED to use.')
    parser.add_argument('-i', '--input-folder', type=str,
                        help='The relative folder for input files')
    parser.add_argument('-o', '--output-folder', type=str, default="./s2",
                        help='The relative folder for output files')
    args = parser.parse_args()

    input_folder = c.get_image_processing_folder(args)

    # Create the output folder
    out_folder = os.path.join(args.output_folder, datetime.now().strftime("%Y%m%d_%H%M"))
    if not os.path.exists(out_folder):
        print(f"Make output directory: {out_folder}")
        os.makedirs(out_folder)

    out_file = os.path.join(out_folder, "processed_images.csv")

    batch_starttime = time.perf_counter()
    image_count = 0
    try:
        with open(out_file, 'w') as f:
            for i in range(args.start_index, args.end_index):
                for angle in [0, 45, 90, 135, 180, 225, 270, 315]:
                    # Initialize some trackers
                    img_starttime = time.perf_counter()

                    # Check the input file
                    base_file_name = f"led{i:03}_angle{angle:03}"
                    input_file_name = os.path.join(input_folder, f"{base_file_name}.jpg")
                    if not os.path.exists(input_file_name):
                        print(f"Skipping {input_file_name}. File not found.")
                        continue
                    print(f"Processing {input_file_name}")
                    image_count = image_count + 1

                    # Find and mark the brightest spot
                    loc, maxVal, processed_image = detect_light_location(input_file_name)
                    cv2.circle(processed_image, loc, RADIUS, (255, 0, 0), 2)

                    # Update the csv and save the image.
                    coord2d = Coord2d(i, angle, loc[0], loc[1], maxVal)
                    f.write(coord2d.to_json() + "\n")
                    save_image(processed_image, out_folder, f"{base_file_name}_processed.jpg")

                    # Print the timing information.
                    img_endtime = time.perf_counter()
                    print(f"Image {image_count} processed in {img_endtime - img_starttime:.2f}s")
        print("Image processing complete\n\n")
    except KeyboardInterrupt:
        print("\nTidying up...\n\n")

    batch_endtime = time.perf_counter()
    c.write_continue_file(images_folder=input_folder, twod_coordinates_file=out_file)
    print(f"Results written to {os.path.abspath(out_folder)}")
    print(f"Took {batch_endtime - batch_starttime:.2f}s to process {image_count} images.")


# Main program logic follows:
if __name__ == '__main__':
    main()
