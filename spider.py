#!/usr/bin/env python3

import os
import sys
import requests
from argparse import ArgumentParser, Namespace
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from shared.ascii_format import (
        GREEN, INFO, RESET, WARNING, DONE, ERROR, FOUND
    )
from shared.open_files import open_folder_in_explorer
from shared.config import IMAGE_EXTENSIONS, SCRAPTYPE_IMG, HEADER
from shared.humanize_scraping import sleep_for_random_secs
from shared.scrape import Scraper

"""
This module implements a web image scraper that recursively searches
for images on a specified base URL and downloads them to a designated folder.
"""

# Default destination of the found images
image_storage_folder = "./data"


class Spider:
    """
    Usage: spider.run()
    """
    def __init__(
        self,
        verbose: bool,
        base_url: str,
        recursive: bool,
        recurse_depth: int = 5,
        ko_limit: int = 50,  # Accepted consecutive bad links
        image_storage_folder: str = image_storage_folder,
        search_string: str = "",  # Filter img by alt text
        case_insensitive: bool = False,
        open_folder: bool = False,  # Open img folder at the end
        memory_limit: int = 1000,  # In MB
        sleep: bool = False,
        max_sleep: int = 3
            ):

        self.verbose: bool = verbose
        self.image_storage_folder = image_storage_folder
        self.base_url: str = base_url
        self.search_string: str = search_string
        # If recursive mode is off, then the depth is set to 1,
        # otherwise it takes the value of recurse_depth
        self.recurse_depth: int = 1 if not recursive else recurse_depth
        self.case_insensitive: bool = case_insensitive
        self.open: bool = open_folder
        # Convert MB to bytes
        self.memory_limit: int = int(memory_limit * 1000000)
        self.ko_limit: int = ko_limit
        self.sleep: bool = sleep
        self.max_sleep: int = max_sleep

        self.visited_urls: list[str] = []
        self.found_links: list[str] = []
        self.found_count: int = 0
        self.ko_count: int = 0
        self.memory_count: int = 0

        # Dict containing:
        # Key: the link
        # Value: texts surrounding the search strings found inside the link
        self.results: dict[str, list] = {}

        # Check if the folder exists
        if not os.path.exists(image_storage_folder):
            # Create the image folder if it doesn't exist
            os.makedirs(image_storage_folder)
            if self.verbose:
                print(
                    f"{INFO} Created image storage folder: "
                    f"'{image_storage_folder}'"
                    )

    def get_image_size(self, img_url: str) -> int | None:
        """
        Make a HEAD request to retrieve the 'Content-Length'
        value that expresses the file size value.

        Return
        ------
         - file size (int) or None if not found
        """
        try:
            # A HEAD request retrieves the headers of the resource
            # without downloading the body.
            response = requests.head(img_url, headers=HEADER)
            if response.status_code == 200:
                file_size = response.headers.get('Content-Length')
                if file_size:
                    # Convert string to int, divide to convert bytes to MB
                    return int(file_size)
                else:
                    if self.verbose:
                        print(
                            f"{WARNING} Content-Length header not "
                            f"found for {img_url}."
                            )
                    return None
            else:  # If HEAD request fails
                print(
                    f"{ERROR} Failed to retrieve headers "
                    f"for {img_url}: {response.status_code}"
                    )
                return None
        except Exception as e:
            print(
                f"{ERROR} An error occurred while checking "
                f"size for {img_url}: {e}"
                )
            return None

    def download_image(
            self, img_url: str, img_path: str, img_name: str) -> None:
        # Try to get the image size with a HEAD request
        filesize = self.get_image_size(img_url)

        if self.verbose:
            print(f"{INFO} Downloading '{img_name}'...")

        img_response = requests.get(img_url, headers=HEADER)
        # Check for request errors
        img_response.raise_for_status()

        if not filesize:
            """
            Now if file size couldn't be accessed from the earlier
            HEAD request, we want to check the file size from the
            file that has been download.
            """
            # Get the size of the image in byte then convert to MB
            filesize = int(len(img_response.content))

        if self.verbose:
            print(f"{INFO} Image file size: {filesize:,} bytes")

        # Quit the program if the memory limit has been reached
        self.memory_count += filesize  # Update the used memory size.
        if self.memory_count >= self.memory_limit:
            print(f"{ERROR} Memory limit has been reached.")
            print("Exiting...")
            self.print_result()
            sys.exit()

        with open(img_path, 'wb') as f:
            f.write(img_response.content)
        if self.verbose:
            print(f"{DONE} Downloaded '{img_name}'")

    def find_images(self, url: str) -> None:
        """Get the images in the content of the given URL and save
        them all"""

        try:
            # Send a GET request to the URL
            response = requests.get(url, headers=HEADER)
            # Raise an error for bad responses
            response.raise_for_status()

            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find all image tags
            img_tags = soup.find_all('img')

            for img in img_tags:
                img_url = img.get('src')
                if not img_url:
                    continue
                if img.get('alt'):  # Get the <img />'s 'title' tag value
                    img_title = img.get('alt')
                else:
                    img_title = ""

                # Create a full URL if the img_url is relative
                img_url = urljoin(url, img_url)

                # Check if the file extension is handled
                img_name = os.path.basename(img_url)
                _, img_extension = os.path.splitext(img_name)
                if img_extension.lower() not in IMAGE_EXTENSIONS:
                    continue

                # Get the path where to save the image by joining the target
                # folder path and the image name
                img_path = os.path.join(self.image_storage_folder, img_name)

                # Check if the search string is in the text
                if ((  # If search string is given, look for it in 'alt'
                    self.search_string and img_title and
                    ((self.search_string.lower() in img_title.lower()
                        and self.case_insensitive)
                        or (self.search_string in img_title)))

                        or (  # If string is given, look for it in the filename
                        self.search_string and img_name and
                        ((self.search_string.lower() in img_name.lower()
                            and self.case_insensitive)
                            or (self.search_string in img_name)))

                        # ...or search string mode is off
                        or not self.search_string):

                    # If the image hasn't been downloaded yet
                    if img_url not in self.found_links:
                        self.found_links.append(img_url)
                        self.found_count += 1  # Increment counter

                        if self.search_string:
                            if self.verbose:
                                print(
                                    f"{FOUND} Found an image containing "
                                    f"'{self.search_string}'."
                                    )

                        # Download the image
                        self.download_image(img_url, img_path, img_name)
                        # Mimic human-like behavior
                        if self.sleep:
                            sleep_for_random_secs(max_sec=self.max_sleep)
        except Exception as e:
            print(f"{ERROR} {e}")

    def print_result(self) -> None:
        if self.verbose:
            print("\nResults:")
            print("\n============= Found search word in the following links:")
        for link in self.found_links:
            if self.verbose:
                print("> ", end="")
            print(f"{GREEN}{link}{RESET}")
        if self.verbose:
            print("============= Occurence:")
        print(self.found_count)

    def run(self) -> None:
        try:
            if self.recurse_depth == 1:
                self.find_images(self.base_url)
            # Recursively loop only if the depth is > 1
            elif self.recurse_depth > 1:
                scraper = Scraper(SCRAPTYPE_IMG, self, self.base_url)
                scraper.scrape()
        except KeyboardInterrupt:
            print("\nExiting...")
        finally:
            """
            If the string search mode is on, print the URLs of the
            images containing the search string in its 'alt' value
            """
            if self.search_string:
                self.print_result()

            # Open the image folder only if at least one img has been saved
            if self.found_count > 0 and self.open:
                open_folder_in_explorer(image_storage_folder)


def parse_args() -> Namespace:
    """
    Parse command-line arguments.
    """
    # Create the parser
    parser = ArgumentParser(description="""This program will
    search the given string on the provided link and on every link that
    can be reached from that link, recursively.
    """)

    # Add arguments
    parser.add_argument(
        'link', type=str, help='the name of the base URL to access'
        )
    parser.add_argument(
        '-s', '--search-string', type=str,
        help="If not empty enables the string search mode: \
            only images which 'alt' attribute contains the \
            search string are saved")
    parser.add_argument(
        '-p', '--image-path', type=str,
        help='indicates the path where the downloaded files will \
        be saved. If not specified, ./data/ will be used.')
    parser.add_argument(
        '-i', '--case-insensitive', action='store_true',
        help='Enable case-insensitive mode'
        )
    parser.add_argument(
        '-r', '--recursive', action='store_true',
        help='Enable recursive search mode'
        )
    parser.add_argument(
        '-l', '--recurse-depth', type=int,
        help='indicates the maximum depth level of the recursive download. \
            If not indicated, it will be 5.'
            )
    parser.add_argument(
        '-k', '--ko-limit', type=int,
        help="Number of already visited/bad links that are \
            allowed before we terminate the search. This is to ensure \
            that we don't get stuck into a loop."
            )
    parser.add_argument(
        '-o', '--open',  action='store_true',
        help="Open the image folder at the end of the program."
            )
    parser.add_argument(
        '-m', '--memory',  type=int,
        help="Set a limit to the memory occupied by the dowloaded images \
            (in MB). Default is set to 1000MB."
            )
    parser.add_argument(
        '-v', '--verbose', action='store_true', help="Enable verbose mode.")
    parser.add_argument(
        '-S', '--sleep', action='store_true',
        help="Enable sleep between HTTP requests to mimic a human-like \
            behavior"
        )
    parser.add_argument(
        '-t', '--max-sleep', type=int,
        help='Maximum duration of the random sleeps between HTTP requests. \
            If not indicated, it will be 3. \
            (-s/--search-string has to be activated).'
        )

    args = parser.parse_args()

    # Validate that -l is not used without -r
    if args.recurse_depth and not args.recursive:
        parser.error(
            "The -l/--recurse-limit option can only be used "
            "with -r/--recursive."
            )

    # Validate that -t is not used without -S
    if args.max_sleep and not args.sleep:
        parser.error(
            "The -t/--max-sleep option can only be used "
            "with -S/--sleep."
            )

    return args


def main(image_storage_folder: str):
    # Parse command-line arguments
    args = parse_args()

    if not args.recurse_depth:
        args.recurse_depth = 5
    if not args.ko_limit:
        args.ko_limit = 50
    if not args.memory:
        args.memory = 1000
    if args.image_path:
        image_storage_folder = args.image_path
    if not args.verbose:
        args.verbose = False
    if not args.max_sleep:
        args.max_sleep = 3

    # Create an instance of Spider
    scraper = Spider(
        args.verbose,
        args.link, args.recursive, args.recurse_depth,
        args.ko_limit, image_storage_folder,
        args.search_string, args.case_insensitive,
        args.open, args.memory,
        args.max_sleep
        )

    # Run the scraper
    try:
        scraper.run()
    except Exception as e:
        print(f"{ERROR} An error occurred: {e}")


if __name__ == "__main__":
    main(image_storage_folder)
