import os
import requests
from argparse import ArgumentParser, Namespace
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from ascii_format import RED, YELLOW, GREEN, INFO, RESET, WARNING, DONE, ERROR

"""
This module implements a web image scraper that recursively searches
for images on a specified base URL and downloads them to a designated folder.
"""

# Default destination of the found images
image_storage_folder = "./data"
image_extensions = {".jpeg", ".jpg", ".png", ".gif", ".bmp"}


class Spider:
    """
    Usage: spider.run()
    """
    def __init__(
        self,
        base_url: str,
        recursive: bool,
        recurse_depth: int = 5,
        ko_limit: int = 50,
        image_storage_folder: str = image_storage_folder,
        search_string: str = "",
        case_insensitive: bool = False
            ):

        self.image_storage_folder = image_storage_folder
        self.base_url: str = base_url
        self.search_string: str = search_string
        # If recursive mode is off, then the depth is set to 1,
        # otherwise it takes the value of recurse_depth
        self.recurse_depth: int = 1 if not recursive else recurse_depth
        self.case_insensitive: bool = case_insensitive

        self.visited_urls: list[str] = []
        self.found_links: list[str] = []
        self.found_count: int = 0
        self.ko_limit: int = ko_limit
        self.ko_count: int = 0

        # Check if the folder exists
        if not os.path.exists(image_storage_folder):
            # Create the image folder if it doesn't exist
            os.makedirs(image_storage_folder)
            print(
                f"{INFO} Created image storage folder: "
                f"'{image_storage_folder}'"
                )

    def check_if_link_visited(self, url: str) -> bool:
        """Check if the URL has already been visited."""
        if url in self.visited_urls:
            return True
        # Add the new URL to the visited URL list
        self.visited_urls.append(url)
        return False

    def download_image(
            self, img_url: str, img_path: str, img_name: str) -> None:
        try:
            print(f"{INFO} Downloading '{img_name}'...")
            img_response = requests.get(img_url)
            # Check for request errors
            img_response.raise_for_status()

            # Save the image
            with open(img_path, 'wb') as f:
                f.write(img_response.content)
            print(f"{DONE} Downloaded '{img_name}'")
        except requests.RequestException as e:
            print(f"{ERROR}Failed to download {img_url}: {e}")

    def find_images(self, url: str) -> None:
        """Get the images in the content of the given URL and save
        them all"""
        try:
            # Send a GET request to the URL
            response = requests.get(url)
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
                if img_extension not in image_extensions:
                    continue

                # Get the path where to save the image by joining the target
                # folder path and the image name
                img_path = os.path.join(self.image_storage_folder, img_name)

                # Check if the search string is in the text
                if ((  # If search string is given
                    self.search_string and img_title and
                    ((self.search_string.lower() in img_title.lower()
                        and self.case_insensitive)
                        or (self.search_string in img_title)))
                        # ...or search string mode is off
                        or not self.search_string):

                    # If the image hasn't been downloaded yet
                    if img_url not in self.found_links:
                        self.found_links.append(img_url)
                        self.found_count += 1  # Increment counter

                        if self.search_string:
                            print(
                                f"{DONE} Found an image containing "
                                f"'{self.search_string}'."
                                )

                        # Download the image
                        self.download_image(img_url, img_path, img_name)

        except requests.exceptions.RequestException as e:
            print(f"{INFO} An error occurred: {e}")

    def scrape_website(self, url: str, depth: int) -> None:
        """
        Recursively access all the links from the webpage and
        look for the search string.

        Parameters
        ----------
         - Target URL to scrap
         - Current depth in the URL structure
        """
        print(
            f"{INFO} {RED}---------- Enter depth: "
            f"{depth} ---------{RESET}"
            )
        # Send a GET request to the website
        response = requests.get(url)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the HTML content of the page
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find all links on the page
            links = soup.find_all('a', href=True)

            # Extract and print file and directory URLs
            for link in links:
                href = link['href']
                full_link = urljoin(url, href)

                # We need to check the link's domain as we only handle links
                # from the same domain
                base_domain = urlparse(self.base_url).netloc
                link_domain = urlparse(full_link).netloc

                # We access the link to search the string and to
                # get the included link set
                if (not self.check_if_link_visited(full_link)
                        and link_domain == base_domain):
                    print(f"{INFO} Accessing {full_link}...")
                    self.ko_count = 0
                    self.find_images(full_link)

                    # We access links from the current link if
                    # depth limit is not reached
                    if depth + 1 <= self.recurse_depth:
                        self.scrape_website(full_link, depth + 1)
                        print(
                            f"{INFO} {RED}---------- back in depth: "
                            f"{depth} ---------{RESET}"
                            )
                else:
                    print(f"{WARNING} Skipped: {full_link}!")
                    self.ko_count += 1
                    # If skipped links limit is reached:
                    if self.ko_count == self.ko_limit:
                        print(f"{ERROR} Max bad links limit is reached!")
                        return
        else:
            print(f"{ERROR} Failed to fetch the page: {response.status_code}")

    def print_result(self) -> None:
        print("\nResults:")
        print("\n==================== Found links containing the search word:")
        for link in self.found_links:
            print(f"{GREEN} {link}{RESET}")
        print("\n==================== Count:")
        print(
            f"{YELLOW}Found '{self.search_string}' "
            f"{self.found_count} times!{RESET}"
            )

    def run(self) -> None:
        try:
            self.find_images(self.base_url)
            if self.recurse_depth:
                self.scrape_website(self.base_url, 1)
        except KeyboardInterrupt:
            print("\nExiting...")
        finally:
            """
            If the string search mode is on, print the URLs of the
            images containing the search string in its 'alt' value
            """
            if self.search_string:
                self.print_result()


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
        help='If not empty enables the string search mode')
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

    args = parser.parse_args()

    # Validate that -l is not used without -r
    if args.recurse_depth and not args.recursive:
        parser.error(
            "The -l/--recurse-limit option can only be used "
            "with -r/--recursive."
            )

    return args


if __name__ == "__main__":
    # Parse command-line arguments
    args = parse_args()
    if not args.recurse_depth:
        args.recurse_depth = 5
    if not args.ko_limit:
        args.ko_limit = 50
    if not args.search_string:
        args.search_string = None
    if args.image_path:
        image_storage_folder = args.image_path

    # Create an instance of Spider
    scraper = Spider(
        args.link, args.recursive, args.recurse_depth,
        args.ko_limit, image_storage_folder,
        args.search_string, args.case_insensitive
        )
    # Run the scraper
    scraper.run()
