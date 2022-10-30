import os
import sys

CONTINUE_FILE = "./utils/.continue.txt"
UNSET = "-"


def get_image_processing_folder(args):
    """
    Gets the input folder. If the field was set in the args, that value is used. Otherwise, tries to read from the
    continuation file.
    """
    if args.input_folder:
        return args.input_folder
    elif os.path.isfile(CONTINUE_FILE):
        with open(CONTINUE_FILE, 'r') as file:
            return file.read().rstrip().split(",")[0]
    else:
        print("No input folder specified. Use -i <folder> to set a folder with the images to process.")
        sys.exit(1)


def get_twod_coordinates_file(args):
    """
    Gets the input file. If the field was set in the args, that value is used. Otherwise, tries to read from the
    continuation file.
    """
    if args.input_file:
        return args.input_file
    elif os.path.isfile(CONTINUE_FILE):
        with open(CONTINUE_FILE, 'r') as file:
            return file.read().rstrip().split(",")[1]
    else:
        print("No input file specified. Use -i <file> to specify a file with .")
        sys.exit(1)


def get_tree_coordinates(input_file):
    """
    Gets the input file. If the field was set in the args, that value is used. Otherwise, tries to read from the
    continuation file.
    """
    if input_file:
        return input_file
    elif os.path.isfile(CONTINUE_FILE):
        with open(CONTINUE_FILE, 'r') as file:
            return file.read().rstrip().split(",")[2]
    else:
        print("No input file specified. Use -i <file> to set a file with normalized 3d coordinates.")
        sys.exit(1)

def write_continue_file(images_folder="", twod_coordinates_file="", threed_coordinates_file=""):
    """Writes the input / output to the continuation file."""
    if os.path.isfile(CONTINUE_FILE):
        with open(CONTINUE_FILE, 'r') as file:
            data = file.read().rstrip().split(",")
        if images_folder:
            data[0] = images_folder
        if twod_coordinates_file:
            data[1] = twod_coordinates_file
        if threed_coordinates_file:
            data[2] = threed_coordinates_file
    else:
        one = images_folder if images_folder else UNSET
        two = twod_coordinates_file if twod_coordinates_file else UNSET
        three = threed_coordinates_file if threed_coordinates_file else UNSET
        data = [one, two, three]

    with open(CONTINUE_FILE, 'w') as file:
        file.write(",".join(data))
