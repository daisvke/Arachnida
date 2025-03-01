#!/usr/bin/env python3

import sys
from shutil import get_terminal_size
from PIL import Image
from PIL.ExifTags import GPSTAGS
from PIL import ExifTags
import os
from typing import Any
import time
from argparse import ArgumentParser
from shared.ascii_format import (
    RESET, ERROR, YELLOW, GREEN, INFO, FOUND,
    color_search_string_in_context
    )
from shared.exif_labels import exif_labels_dict
from shared.config import IMAGE_EXTENSIONS, BASIC, EXIF


class Scorpion:
    """
    A class to handle extracting and displaying metadata from image files.
    """
    def __init__(
        self,
        verbose: bool = False,
        files: list = [],
        directory: list = [],
        search_string: str = "",
        case_insensitive: bool = False
            ):

        self.verbose: bool = verbose
        self.files: list[str] = files
        self.directory: list[str] = directory
        self.search_string: str = search_string
        self.case_insensitive: bool = case_insensitive

        self.found_count: int = 0
        self.founds: dict = {}

    def get_human_readable_gps_data(self, gps_info: dict[int, Any]) -> dict:
        """
        Generate human-readable GPS data from EXIF metadata.
        """
        # Convert GPS tag numbers to human-readable names
        gps_data = {
            GPSTAGS.get(tag, tag): value for tag, value in gps_info.items()
        }
        # Parse GPS latitude and longitude
        latitude = gps_data.get("GPSLatitude")
        latitude_ref = gps_data.get("GPSLatitudeRef")  # South or North
        longitude = gps_data.get("GPSLongitude")
        longitude_ref = gps_data.get("GPSLongitudeRef")  # East or West

        if latitude and longitude and latitude_ref and longitude_ref:
            # Convert latitude and longitude to decimal format
            lat = self.convert_to_decimal(latitude, latitude_ref)
            lon = self.convert_to_decimal(longitude, longitude_ref)
            gps_data["Latitude"] = lat
            gps_data["Longitude"] = lon

        return gps_data

    def convert_to_decimal(self, coords: Any, ref: str) -> int:
        """
        Convert GPS coordinates to decimal format.
        """
        degrees, minutes, seconds = coords
        decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)

        if ref in ['S', 'W']:
            decimal = -decimal
        return decimal

    def set_GPS_info(
                self,
                exif_data: Image.Exif, metadata_exif: dict[int, Any]
            ) -> dict[int, Any]:
        """
        Extract and add GPS info

        Latitude and longitude are stored under their corresponding tag IDs
        as keys in the metadata_exif dictionary.
        """
        try:
            gps_ifd = exif_data.get_ifd(ExifTags.IFD.GPSInfo)
            if gps_ifd:
                GPSInfo = self.get_human_readable_gps_data(gps_ifd)
                metadata_exif[2] = ("GPSLatitude", GPSInfo['Latitude'])
                metadata_exif[4] = ("GPSLongitude", GPSInfo['Longitude'])
        except Exception as e:
            print(f"{ERROR} {e}")

        return metadata_exif

    def get_exif_data(self, exif_data: Image.Exif) -> dict[int, Any] | None:
        """
        Extract EXIF data.

        Each entry in the Exif data has a tag ID that corresponds to
        a label name. However, the ID is not a human-readable value.
        This is why we are using a custom dictionary that maps each ID into a
        human-readable label.

        Return:
            A dictionary with the tag ID as a key and a tuple:
                (tag name, value)
            as a value.
        """
        metadata_exif: dict[int, Any] = {}

        if not exif_data:
            # No EXIF data was found.
            return None

        # Extract and add GPS info
        metadata_exif = self.set_GPS_info(exif_data, metadata_exif)

        # Loop through every EXIF entry
        for payld_tag_id, value in exif_data.items():
            # print(f"{payld_tag_id}: {value}")

            # Check if payld_tag_id has an entry in the dict
            if payld_tag_id in exif_labels_dict:
                # Get the value (label name) for the payld_tag_id
                tag = str(exif_labels_dict.get(payld_tag_id, {}).get("tag"))
                # Get the last part of the label
                # (e.g., "Model" from "Exif.Image.Model")
                tag_name = tag.split('.')[-1]

                metadata_exif[payld_tag_id] = (tag_name, value)
            else:  # Handle the case where tag is not found
                metadata_exif[payld_tag_id] = (
                    str(payld_tag_id) + " (no tag name found)",
                    str(value)
                )
        return metadata_exif

    def search_string_in_metadata(self, metadata: dict[int, Any]) -> None:
        """
        Searches for a string in the values of a nested dictionary.

        Parameters:
            metadata: The dictionary to search through.
        """
        # Iterate through the outer dictionary
        for int_key, inner_dict in metadata.items():
            # Ensure the inner value is a dictionary
            if isinstance(inner_dict, dict):

                def contains_search_string(str_value: str) -> bool:
                    if self.case_insensitive:
                        return self.search_string.lower() in str_value.lower()
                    return self.search_string in str_value

                # Iterate through the inner dictionary
                for str_key, str_value in inner_dict.items():
                    if contains_search_string(str_value):
                        filename = inner_dict["Name"]
                        if filename not in self.founds:
                            self.founds[f"{filename}"] = {}
                        self.founds[f"{filename}"][f"{str_key}"] \
                            = f"{str_value}"
                        self.found_count += 1

    def get_metadata(
                self, file_path: str, verbose: bool = False
            ) -> dict[int, Any] | None:
        """
        Display all the metadata from the file.
        """
        metadata_all: dict[int, Any] = {}
        metadata_basic: dict[str, str] = {}
        metadata_exif: dict[int, Any] | None = {}

        try:
            """
            Open the image file.

            The Pillow library (often imported as PIL, which stands for Python
            Imaging Library) is used in Python for opening, manipulating, and
            saving various image file formats.
            """
            if not file_path:
                print(f"{ERROR} Found no file path to open.")
                return None

            img = Image.open(file_path)

            # Get creation date from the file system
            creation_time = os.path.getctime(file_path)

            # Get file statistics
            file_stats = os.stat(file_path)
            # Access time
            access_time = time.strftime(
                "%Y-%m-%d %H:%M:%S",
                time.localtime(file_stats.st_atime)
            )
            # Modification time
            modification_time = time.strftime(
                "%Y-%m-%d %H:%M:%S",
                time.localtime(file_stats.st_mtime)
            )

            # Extract basic attributes
            metadata_basic["Name"] = os.path.basename(file_path)
            metadata_basic["Path"] = file_path
            if img.format:
                metadata_basic["Format"] = str(img.format)
            if img.mode:
                metadata_basic["Mode"] = str(img.mode)
            if img.size and len(img.size) == 2:
                metadata_basic["Width"] = str(img.size[0])
                metadata_basic["Height"] = str(img.size[1])
            if creation_time:
                metadata_basic["Creation time"] = time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime(creation_time))
            if access_time:
                metadata_basic["Access time"] = access_time
            if modification_time:
                metadata_basic["Modification time"] = modification_time
            if "comment" in img.info:
                metadata_basic["Comment"] = str(img.info["comment"])

            # print(f"{INFO} img.info: {img.info}")

            # Extract EXIF metadata
            metadata_exif = self.get_exif_data(img.getexif())

            # Combine all metadata
            metadata_all[BASIC] = metadata_basic
            metadata_all[EXIF] = metadata_exif
            # print(metadata_all)
            if self.search_string:
                self.search_string_in_metadata(metadata_all)
        except Exception as e:
            print(
                    f"{ERROR} Error processing {file_path}: {e}",
                    file=sys.stderr
                )

        return metadata_all

    def display_metadata(
            self, file_path: str, metadata: dict[int, Any]) -> None:
        """
        Display each type of metadata on the terminal.
        """
        if not metadata:
            print(f"{ERROR} Found no metadata.")
            return

        print("\nMetadata:")

        basic, exif = metadata[BASIC], metadata[EXIF]

        # Display basic metadata
        if basic:
            print(f"{INFO} Basic metadata:")
            for tag, value in basic.items():
                print(f"  {tag}: {value}")
        # Display EXIF metadata
        if exif:
            print(f"{INFO} EXIF metadata:")
            for tag, value in exif.items():
                print(f"  {value[0]}: {value[1]}")

    def loop_through_files(self, file_paths: list[str]) -> None:
        """
        Treat all the files given as arguments.
        """
        # Get terminal size
        terminal_size = get_terminal_size()
        # Get terminal width
        terminal_width = terminal_size.columns

        for file_path in file_paths:
            if os.path.isfile(file_path):
                # Check if the file extension is handled
                if not check_extension(file_path, True):
                    print("" + "-" * terminal_width)
                    continue
                if self.verbose or not self.search_string:
                    print(f"{INFO} Opening file: {YELLOW}{file_path}{RESET}")
                metadata = self.get_metadata(file_path, True)
                # Display metadata only if search string mode is off
                if not self.search_string:
                    if metadata:
                        self.display_metadata(file_path, metadata)
                    print("-" * terminal_width)
            else:
                print(f"{ERROR} {file_path} is not a valid file.")

    def print_search_results(self) -> None:
        found_count = 0  # Count of values containing the search string

        if len(self.founds) > 0:
            for filename, values in self.founds.items():
                try:
                    for entry in values.items():
                        tagname, value = entry
                        # Color the search string inside `value`
                        colored_value = color_search_string_in_context(
                                self.search_string, value
                            )
                        if self.verbose:
                            print(f"{FOUND} File: {GREEN}{filename}{RESET} | "
                                f"Tag: {tagname} - Value: {colored_value}"
                                )
                        else:
                            print(f"{filename} - {tagname} - {colored_value}")
                        found_count += 1
                except Exception:
                    continue

            if self.verbose:
                print(f"{INFO} Found string in {found_count} entries.")
            else:
                print(found_count)

    def run(self) -> None:
        """
        Run Scorpion on the given files, and
        loop through all the given directories.
        """
        if self.files:
            self.loop_through_files(self.files)

        # Check if directories were provided
        if self.directory:
            # Loop through files in the directories
            for dir_path in self.directory:
                if not self.search_string:
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
                    self.loop_through_files(file_paths)
                except Exception as e:
                    print(f"{ERROR} {e}")
        self.print_search_results()


def check_extension(file_path: str, verbose: bool = False) -> bool:
    """
    Check if the file type is handled.
    """
    img_name = os.path.basename(file_path)
    _, img_extension = os.path.splitext(img_name)
    if img_extension.lower() not in IMAGE_EXTENSIONS:
        if verbose:
            print(
                f"{ERROR} {file_path}: '{img_extension}' is not a "
                f"handled extension.")
        return False
    return True


def parse_args():
    """Set up argparse and return the given arguments."""
    parser = ArgumentParser(
        description="Extract EXIF data and other data from image files."
    )
    parser.add_argument(
        '-f', '--files', metavar='FILE', type=str, nargs='*',
        help='one or more image files to process'
    )
    parser.add_argument(
        '-d', '--directory', metavar='DIR', type=str, nargs='*',
        help='one or more folders containing image files to process'
    )
    parser.add_argument(
        '-v', '--verbose', action='store_true', help="Enable verbose mode.")
    parser.add_argument(
        '-s', '--search-string', type=str, help='the string to search')
    parser.add_argument(
        '-i', '--case-insensitive', action='store_true',
        help='Enable case-insensitive mode'
        )

    return parser.parse_args()


if __name__ == "__main__":
    # Parse command-line arguments
    args = parse_args()

    if not args.verbose:
        args.verbose = False

    # Create an instance of Harvestmen
    scraper = Scorpion(
        args.verbose,
        args.files,
        args.directory,
        args.search_string,
        args.case_insensitive
        )

    # Run the scraper
    scraper.run()
