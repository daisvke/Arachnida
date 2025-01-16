#!/usr/bin/env python3

import sys
from shutil import get_terminal_size
from PIL import Image
import os
from datetime import datetime
import time
from argparse import ArgumentParser
from shared.ascii_format import ERROR, INFO, RESET, YELLOW
from shared.exif_labels import exif_labels_dict
from shared.config import IMAGE_EXTENSIONS, BASIC, PNG, EXIF


def get_exif_data(exif_data: dict[str,str]) -> dict[int,(str,str)]:
    """
    Extract EXIF data

    Each entry in the Exif data have a tag ID that corresponds to
    a label name. however, the ID is not a human-readable value.
    This is why we are using a custom dictionary that maps each ID into a
    human-readable label.

    Return:
        A dictionary with the tag ID as a key and a tuple:
            (tag name, value)
        as a value.
    """
    metadata_exif = {}

    if not exif_data:
        # print(f"{WARNING} Found no EXIF data.")
        return
    
    # Loop through every EXIF entry
    for tag_id, value in exif_data.items():
        # Check if tag_id has an entry in the dict
        if tag_id in exif_labels_dict:
            # Get the value (label name) for the tag_id
            tag = exif_labels_dict.get(tag_id, {}).get("tag")
            # Get the last part of the label
            # (eg. "Model" from "Exif.Image.Model")
            tag_name = tag.split('.')[1]
            metadata_exif[tag_id] = (tag_name, value)
        else:  # Handle the case where tag is not found
            metadata_exif[tag_id] = (str(tag_id) + " (no tag name found)", str(value))

    return metadata_exif

def get_metadata(file_path: str, verbose: bool = False) -> dict[str,any]:
    """
    Display all the metadata from the file.
    """

    metadata_all    = {}
    metadata_basic  = {}
    metadata_png    = {}
    metadata_exif   = {}
    
    try: 
        """
        Open the image file.

        The Pillow library (often imported as PIL, which stands for Python
        Imaging Library) is used in Python for opening, manipulating, and
        saving various image file formats.
        """
        if not file_path:
            print(f"{ERROR} Found no file path to open.")
            return
        
        img = Image.open(file_path)

        # Get creation date from the file system
        creation_time = os.path.getctime(file_path)

        # Get file statistics
        file_stats = os.stat(file_path)
        # Access time
        access_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(file_stats.st_atime))
        # Modification time
        modification_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(file_stats.st_mtime))

        # Extract basic attributes
        metadata_basic["Name"]              = str(file_path)
        if img.format:
            metadata_basic["Format"]        = str(img.format)
        if img.mode:
            metadata_basic["Mode"]          = str(img.mode)
        if img.size and len(img.size) == 2:
            metadata_basic["Width"]         = str(img.size[0])
            metadata_basic["Height"]        = str(img.size[1])
        if creation_time:
            metadata_basic["Creation time"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(creation_time))
        if access_time:
            metadata_basic["Access time"] = access_time
        if modification_time:
            metadata_basic["Modification time"] = modification_time
        if "comment" in img.info:
            metadata_basic["Comment"]        = str(img.info["comment"])

        print(f"{INFO} img.info: {img.info}")

        # Extract PNG metadata
        if img.format == "PNG" and img.info:
            for tag, value in img.info.items():
                metadata_png[tag] = value

        # Extract EXIF metadata
        metadata_exif = get_exif_data(img.getexif())

        # Fusion all metadata
        metadata_all[BASIC]   = metadata_basic
        metadata_all[PNG]     = metadata_png
        metadata_all[EXIF]    = metadata_exif
    except Exception as e:
        print(f"{ERROR} Error processing {file_path}: {e}", file=sys.stderr)

    return metadata_all

def display_metadata(file_path: str, metadata: dict[str,str]) -> None:
    """
    Display each type of metadata on the terminal.
    """
    
    if not metadata:
        print(f"{ERROR} Found no metadata.")
        return

    print("\nMetadata:")

    basic, png, exif = metadata[BASIC], metadata[PNG], metadata[EXIF]

    # Display basic metadata
    if basic:
        print(f"{INFO} Basic metadata:")
        for tag, value in basic.items():
            print(f"  {tag}: {value}")
    # Display PNG metadata
    if png:
        print(f"{INFO} PNG metadata:")
        for tag, value in png.items():
            print(f"  {tag}: {value}")
    # Display EXIF metadata
    if exif:
        print(f"{INFO} EXIF metadata:")
        for tag, value in exif.items():
            print(f"  {value[0]}: {value[1]}")    

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
    if img_extension.lower() not in IMAGE_EXTENSIONS:
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
