#!/usr/bin/env python3

import requests
from argparse import ArgumentParser, Namespace
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from shared.ascii_format import (
    RED, INFO, RESET, WARNING, ERROR, FOUND, GREEN
    )
from shared.config import SCRAPTYPE_STR
from shared.humanize_scraping import sleep_for_random_secs
from shared.scrape import Scraper
from typing import Any


class Harvestmen:
    """
    This class implements a web scraper that recursively searches
    for a specified string within the content of a given base URL
    and all reachable links from that URL.
    """
    def __init__(
        self,
        verbose: bool,
        base_url: str,
        search_string: str,
        recursive: bool,
        case_insensitive: bool = False,
        recurse_depth: int = 5,
        ko_limit: int = 20,
        sleep: bool = False,
        max_sleep: int = 3
            ):

        self.verbose: bool = verbose
        self.base_url: str = base_url
        self.search_string: str = search_string
        self.recursive: bool = recursive
        self.recurse_depth: int = 1 if not recursive else recurse_depth
        self.case_insensitive: bool = case_insensitive
        self.visited_urls: list[str] = []
        self.found_count: int = 0
        self.ko_limit: int = ko_limit
        self.sleep: bool = sleep
        self.max_sleep: int = max_sleep
        self.ko_count: int = 0

        # Dict containing:
        # Key: The link
        # Value: Texts surrounding the search strings found inside the link
        self.results: dict[Any] = {}

    def save_found_strings_with_contexts(self, url: str, text: str) -> int:
        """
        Loop through the text looking for the search string.
        Any time the string is found, the context (surrounding text)
        is saved along with the link on the results dictionary.
        """
        count = 0
        start = 0

        while True:
            # Find the index of the search string
            start = text.find(self.search_string, start)
            
            if start == -1:  # No more occurrences found
                break
            
            surrounding = self.get_text_surrounding_search_string(text, start)

            # Move past the current occurrence
            start += len(self.search_string)

            # Create a new entry in the results dictionary
            if url in self.results:
                self.results[url].append(surrounding)
            else:
                self.results[url] = [surrounding]

            self.found_count += 1  # Increment counter
            count += 1

            if self.verbose:  # Print the found string with context
                print("..." + surrounding + "...")

        return count

    def find_string(self, url: str) -> None:
        """Find the search string in the content of the given URL."""
        # Send a GET request to the URL
        response = requests.get(url)
        # Raise an error for bad responses
        response.raise_for_status()

        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Get the text from the soup object
        text = soup.get_text()

        # Check if the search string is in the text
        if ((self.search_string and text and
                ((self.search_string.lower() in text.lower()
                    and self.case_insensitive)
                    or (self.search_string in text)))):
            # If not already done, add the URL in the found list
            if url not in self.results:
                count = self.save_found_strings_with_contexts(url, text)
                if self.verbose:
                    print(
                        f"{FOUND} '{self.search_string}' "
                        f"found on the webpage {count} time(s).\033[0m"
                        )

    def get_text_surrounding_search_string(
            self, text: str, begin: int, interval: int = 30) -> str:
        # If str_pos - interval is < 0, we set start to pos 0
        start = max(0, begin - interval)
        # If str_pos + interval is > str_len, we set start to the last char
        end = min(
            begin + len(self.search_string) + interval,
            len(text) - 1
            )

        # Remove leading and trailing whitespace characters from a string.
        # This includes spaces, tabs, newlines (\n), and other whitespace.
        stripped_text = text[start:end].strip()
        # Replace newlines from within the text by spaces
        stripped_text = stripped_text.replace('\n', ' ')

        # Color in red the seaerch string inside the text
        colored_search_string = RED + self.search_string + RESET
        colored_text = stripped_text.replace(
            self.search_string, colored_search_string)

        return colored_text

    def print_result(self) -> None:
        if self.verbose:
            print("\nResults:")
            print("\n============= Found search word in the following links:")
        for link, texts in self.results.items():
            if self.verbose:
                print("> ", end="")
            print(f"{GREEN}{link}{RESET}")
            if self.verbose:
                for text in texts:
                    print(text)
        if self.verbose:
            print("============= Occurence:")
        print(self.found_count)

    def run(self) -> None:
        try:
            if self.recurse_depth == 1:
                self.find_string(self.base_url)
            # Recursively loop only if the depth is > 1
            elif self.recurse_depth > 1:
                # Depth is already at 2 as the first find_image() has gone
                # through depth 1
                scraper = Scraper(SCRAPTYPE_STR, self, self.base_url, 1)
                scraper.scrape()
        except KeyboardInterrupt:
            print("\nExiting...")
        finally:
            """
            If the string search mode is on, print the URLs of the
            images containing the search string in its 'alt' value
            """
            self.print_result()


def parse_args() -> Namespace:
    """Parse command-line arguments."""
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
        '-s', '--search-string', type=str, required=True,
        help='the string to search'
        )
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
            If not indicated, it will be 5. \
            (-r/--recursive has to be activated).'
            )
    parser.add_argument(
        '-k', '--ko-limit', type=int,
        help="Number of already visited/bad links that are \
            allowed before we terminate the search. This is to ensure \
            that we don't get stuck into a loop."
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


def main():
    # Parse command-line arguments
    args = parse_args()

    if not args.recurse_depth:
        args.recurse_depth = 5
    if not args.ko_limit:
        args.ko_limit = 50
    if not args.verbose:
        args.verbose = False
    if not args.max_sleep:
        args.max_sleep = 3

    # Create an instance of Harvestmen
    scraper = Harvestmen(
        args.verbose,
        args.link, args.search_string,
        args.recursive, args.case_insensitive,
        args.recurse_depth, args.ko_limit,
        args.sleep, args.max_sleep
        )

    # Run the scraper
    try:
        scraper.run()
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
