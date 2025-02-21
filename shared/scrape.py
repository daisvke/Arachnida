from shared.ascii_format import (
    RED, INFO, RESET, WARNING, ERROR
    )
from shared.config import SCRAPTYPE_STR, SCRAPTYPE_IMG
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin, urlparse
from shared.humanize_scraping import sleep_for_random_secs
from typing import Any


class Scraper:
    """
    Recursively access all the links from the webpage
    and look for the search string.
    """
    def __init__(
            self,
        scraper_type: int,
        scraper: Any,
        url: str,
        depth: int
        ):
        self.scraper_type: int = scraper_type
        self.scraper: Any = scraper
        self.verbose: bool = scraper.verbose
        self.base_url: str = scraper.base_url
        self.ko_count: int = scraper.ko_count
        self.ko_limit: int = scraper.ko_limit
        self.sleep: bool = scraper.sleep
        self.max_sleep: int = scraper.max_sleep
        self.recurse_depth: int = scraper.recurse_depth
        self.visited_urls = scraper.visited_urls

        self.url: str = url
        depth: int = depth

    def check_if_link_visited(self, url: str) -> bool:
        """Check if the URL has already been visited."""
        if url in self.visited_urls:
            return True
        # Add the new URL to the visited URL list
        self.visited_urls.append(url)
        return False

    def scrape(self, url: str = "", depth: int = 1) -> None:
        if self.verbose:
            print(
                f"{INFO} {RED}---------- Enter depth: "
                f"{depth} ---------{RESET}"
                )
            
        if not url:
            url = self.base_url

        # Run appropriate method according to scraper type
        if self.scraper_type == SCRAPTYPE_STR:
            self.scraper.find_string(url)
        elif self.scraper_type == SCRAPTYPE_IMG:
            self.scraper.find_images(url)

        # Send a GET request to the website
        response = requests.get(self.url)
        # Raise an error for bad responses
        response.raise_for_status()

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the HTML content of the page
            soup = BeautifulSoup(response.content, 'html.parser')
            # Find all links on the page
            links = soup.find_all('a', href=True)

            # Extract and print file and directory URLs
            for link in links:
                href = link['href']
                full_link = urljoin(self.url, href)

                """
                We need to check the link's domain as we only handle links
                from the same domain.
                We wouldn't want to be redirected to the Instagram profile
                linked to the website, for instance.
                """
                base_domain = urlparse(self.base_url).netloc
                link_domain = urlparse(full_link).netloc

                # We access the current link to search the string and to
                # get the included link set
                main_link = full_link.split('#')[0]
                if (not self.check_if_link_visited(main_link)
                        and link_domain == base_domain):
                    if self.verbose:
                        print(f"{INFO} Accessing {main_link}...")
                    self.ko_count = 0

                    # Run appropriate method according to scraper type
                    if self.scraper_type == SCRAPTYPE_STR:
                        self.scraper.find_string(main_link)
                    elif self.scraper_type == SCRAPTYPE_IMG:
                        self.scraper.find_images(main_link)

                    # We access links inside the current link if
                    # depth limit is not reached
                    if depth + 1 <= self.recurse_depth:
                        # Mimic human-like behavior
                        if self.sleep:
                            sleep_for_random_secs(max_sec=self.max_sleep)
                        self.scrape(main_link, depth + 1)
                else:
                    if self.verbose:
                        print(f"{WARNING} Skipped: {main_link}!")
                    self.ko_count += 1

                    # If single page mode is offlimit:
                    if self.ko_count == self.ko_limit:
                        if self.verbose:
                            print(f"{ERROR} Max bad links limit is reached!")
                        exit()
        else:  # If status_code != 200
            if self.verbose:
                print('Failed to fetch the page:', response.status_code)
