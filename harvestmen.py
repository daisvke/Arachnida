#!/usr/bin/env python3

import requests
from argparse import ArgumentParser, Namespace
from bs4 import BeautifulSoup
from shared.ascii_format import (
    RED, RESET, ERROR, FOUND, GREEN, INFO,
    color_search_string_in_context
    )
from shared.config import SCRAPTYPE_STR, HEADER
from shared.scrape import Scraper
from shared.open_files import open_file_and_get_entries


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
        word_list: str,
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
        self.ko_limit: int = ko_limit
        self.sleep: bool = sleep
        self.max_sleep: int = max_sleep
        self.loop_index: int = 0

        if word_list:
            try:  # Get the word list if it is given
                self.word_list: list[str] = \
                    open_file_and_get_entries(word_list)
            except Exception as e:
                raise ValueError(e)
        else:
            self.word_list = []

        self.visited_urls: list[str] = []
        self.found_count: list[int] = [0]
        self.ko_count: int = 0

        # A list containing results (dict) of each iteration
        #
        # Each dict contains:
        # Key: the link
        # Value: texts surrounding the search strings found inside the link
        self.results: list[dict[str, list]] = []

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
            if url in self.results[self.loop_index]:
                self.results[self.loop_index][url].append(surrounding)
            else:
                self.results[self.loop_index][url] = [surrounding]

            self.found_count[self.loop_index] += 1  # Increment counter
            count += 1

            if self.verbose:  # Print the found string with context
                print("..." + surrounding + "...")

        return count

    def find_string(self, url: str) -> None:
        """Find the search string in the content of the given URL."""
        try:
            # Send a GET request to the URL
            response = requests.get(url, headers=HEADER)
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
                if (url not in self.results[self.loop_index]):
                    count = self.save_found_strings_with_contexts(url, text)
                    if self.verbose:
                        print(
                            f"{FOUND} '{self.search_string}' "
                            f"found on the webpage {count} time(s).\033[0m"
                            )
        except Exception as e:
            print(f"{ERROR} {e}")

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

        colored_text = color_search_string_in_context(
            self.search_string,
            stripped_text,
            self.case_insensitive
            )
        return colored_text

    def print_single_result(self, loop_index: int) -> None:
        if self.verbose:
            if self.word_list:
                print(
                    f"\n{INFO} Results for "
                    f"'{RED}{self.word_list[loop_index]}{RESET}':"
                    )
            else:
                print("\nResults:")
            print("\n============= Found search word in the following links:")
            # Check if self.results and self.loop_index are valid
        for link, texts in self.results[loop_index].items():
            if self.verbose:
                print("> ", end="")
            print(f"{GREEN}{link}{RESET}")
            if self.verbose:
                for text in texts:
                    print(text)
        if self.verbose:
            print("============= Occurence:")

        print(self.found_count[loop_index])

    def run(self) -> None:
        end = 1
        words = []
        ko_limit = self.ko_limit
        count = 0

        if self.word_list:
            end = len(self.word_list)
            words = self.word_list

        # Init found count for each iteration
        self.found_count = [0 for _ in words] if words else [0]
        # Init dict for each iteration
        self.results = [{} for _ in words] if words else [{}]

        while self.loop_index < end:
            self.ko_limit = ko_limit
            self.visited_urls = []

            try:
                if words:
                    self.search_string = words[self.loop_index]
                    if self.verbose:
                        print(
                            "\n============= Searching "
                            f"'{RED}{self.search_string}{RESET}'...\n"
                            )
                if self.recurse_depth == 1:
                    self.find_string(self.base_url)
                # Recursively loop only if the depth is > 1
                elif self.recurse_depth > 1:
                    scraper = Scraper(SCRAPTYPE_STR, self, self.base_url)
                    scraper.scrape()
            except KeyboardInterrupt:
                print("\nExiting...")
            finally:
                """
                If the string search mode is on, print the URLs of the
                images containing the search string in its 'alt' value
                """
                if not words:
                    self.print_single_result(self.loop_index)
                count += self.found_count[self.loop_index]
                self.loop_index += 1
        if words:
            for i in range(len(self.results)):
                self.print_single_result(i)
            if self.verbose:
                print(f"\n{INFO} Total occurences:")
            print(count)


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
        '-s', '--search-string', type=str, help='the string to search'
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
    parser.add_argument(
        '-w', '--word-list', type=str,
        help='Give the program a word list that will be used as search \
            strings.'
        )

    args = parser.parse_args()

    if not args.search_string and not args.word_list:
        parser.error(
            "Either s/--search-string or -w/--word-list has to be specified."
            )

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
    if args.search_string and args.word_list:
        parser.error(
            "The -s/--search-string option cannot be used "
            "with -w/--word-list."
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
        args.link,
        args.search_string, args.word_list,
        args.recursive, args.case_insensitive,
        args.recurse_depth, args.ko_limit,
        args.sleep, args.max_sleep
        )

    # Run the scraper
    try:
        scraper.run()
    except Exception as e:
        print(f"{ERROR} An error occurred: {e}")


if __name__ == "__main__":
    main()
