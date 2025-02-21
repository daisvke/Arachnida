from time import sleep
from random import randint

"""
This module is designed for humanizing scrapers.

It simulates human-like behavior when reading and scraping web pages,
ensuring that the scraping process is more natural and less detectable.
"""


def sleep_for_random_secs(min_sec: int = 1, max_sec: int = 3) -> None:
    """
    Sleep for a random duration to mimic a human visiting a webpage.
    """

    # Generate a random sleeping duration in seconds,
    # from a range = [min, max]
    sleeping_secs = randint(min_sec, max_sec)
    sleep(sleeping_secs)
