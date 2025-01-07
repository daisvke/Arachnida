#!/usr/bin/env python3

import sys
from shutil import get_terminal_size
from PIL import Image
import os
from datetime import datetime
from argparse import ArgumentParser
from ascii_format import ERROR, INFO, RESET, YELLOW, WARNING
from exif_labels import exif_labels_dict

image_extensions = {
    ".jpeg", ".jpg", ".png", ".gif", ".bmp", ".tif"
    }

def get_metadata(file_path: str, verbose: bool = False) -> dict[str, str]:
    """
    Display all the metadata from the file.

    Each entry in the Exif data have a tag ID that corresponds to
    a label name. however, the ID is not a human-readable value.
    This is why we are using a dictionary that maps each ID into a
    human-readable label.
    """

    metadata = {}  # Initialize the dict
    try: 
        """
        Open the image file.

        The Pillow library (often imported as PIL, which stands for Python
        Imaging Library) is used in Python for opening, manipulating, and
        saving various image file formats.
        """
        img = Image.open(file_path)
        # Display basic attributes
        metadata["Name"]	= str(file_path)
        metadata["Format"]	= str(img.format)
        metadata["Mode"]	= str(img.mode)
        metadata["Width"]	= str(img.size[0])
        metadata["Height"]	= str(img.size[1])
        
        # Get creation date from the file system
        creation_time = os.path.getctime(file_path)
        metadata["Creation time"] = str(datetime.fromtimestamp(creation_time))

        # Extract PNG metadata
        if img.format == "PNG" and img.info:
            for tag, value in img.info.items():
                metadata[tag] = value

        """
        Extract EXIF data: we get the tag ID from the exif data but
        since we want the corresponding tag name, we get it from the
        exif_labels_dict, a custom dictionary having tag IDs as keys
        and their corresponding tag names as values.
        """
        exif_data = img.getexif()
        if exif_data:
            for tag_id, value in exif_data.items():
                # Check if tag_id has an entry in the dict
                if tag_id in exif_labels_dict: 
                    # Get the value (label name) for the tag_id
                    tag = exif_labels_dict[tag_id]
                    # Get the last part of the label
                    # (eg. "Model" from "Exif.Image.Model")
                    tag_name = tag.split('.')[1]
                    metadata[tag_name] = value
                else:  # Handle the case where tag is not found
                    metadata[str(tag_id) + " (no tag name found)"] = str(value)
    except Exception as e:
        print(f"{ERROR} Error processing {file_path}: {e}", file=sys.stderr)

    return metadata

def display_metadata(file_path: str, metadata: dict[str, str]) -> None:
    if metadata:
        print("\nMetadata:")
        for tag, value in metadata.items():
                print(f"  {tag}: {value}")


def parse_args():
    """Set up argparse and return the given arguments"""
    parser = ArgumentParser(
        description="Extract EXIF data and other data from image files."
        )
    parser.add_argument(
        'files', metavar='FILE', type=str, nargs='*',
        help='one or more image files to process'
        )
    parser.add_argument(
        '-d', '--directory', metavar='DIR', type=str, nargs='*',
        help='one or more folders containing image files to process'
        )
    
    return parser.parse_args()


def check_extension(file_path: str, verbose: bool = False) -> bool:
    """Check if the file type is handled"""
    img_name = os.path.basename(file_path)
    _, img_extension = os.path.splitext(img_name)
    if img_extension.lower() not in image_extensions:
        if verbose:
            print(
                f"{ERROR} {file_path}: '{img_extension}' is not a "
                f"handled extension.")
        return False
    return True


def loop_through_files(files: list[str]) -> None:
    """
    Treat all the files given as argument
    """
    # Get terminal size
    terminal_size = get_terminal_size()
    # Get terminal width
    terminal_width = terminal_size.columns

    for file_path in files:
        if os.path.isfile(file_path):
            # Check if the file extension is handled
            if not check_extension(file_path, True):
                print("" + "-" * terminal_width)
                continue
            print(f"{INFO} Opening file: {YELLOW}{file_path}{RESET}")
            metadata = get_metadata(file_path, True)
            display_metadata(file_path, metadata)
            print("-" * terminal_width)
        else:
            print(f"{ERROR} {file_path} is not a valid file.")


def run_scorpion(files: list, directories: list) -> None:
    """
    Run scorpion on the given files, and
    loop through all the given directories.
    """
    loop_through_files(files)

    # Check if directories were provided
    if directories:
        # Loop through files in the directories
        for dir_path in directories:
            print(f"{INFO} Entering '{dir_path}' folder...")
            try:
                # Check if the folder exists
                if not os.path.isdir(dir_path):
                    print(f"{ERROR} {dir_path} is not a valid directory.")
                    continue

                # Create a list of full file paths
                file_paths = [
                    os.path.join(dir_path, filename)
                    for filename in os.listdir(dir_path)
                    ]
                loop_through_files(file_paths)
            except Exception as e:
                print(f"{ERROR} {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: ./scorpion FILE1 [FILE2 ...] [-d] [DIR1 ...")
        sys.exit(1)

    args = parse_args()
    run_scorpion(args.files, args.directory)


if __name__ == "__main__":
    main()
