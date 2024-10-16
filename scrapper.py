import sys
import requests
import argparse
from bs4 import BeautifulSoup
from urllib.parse import urljoin

visited_url = []

def check_if_link_visited(url):
	if url in visited_url:
		return 1
	# Add the new URL to the visited URL list
	visited_url.append(url)
	return 0

def find_string(url, search_string, case_insensitive):
	try:
		# Send a GET request to the URL
		response = requests.get(url)
		response.raise_for_status()  # Raise an error for bad responses

		# Parse the HTML content
		soup = BeautifulSoup(response.text, 'html.parser')

		# Get the text from the soup object
		text = soup.get_text()

		# Check if the search string is in the text
        if (search_string in text.lower() and case_insensitive) or search_string in text:
			print(f"\033[32m'{search_string}' found in the webpage.\033[0m")
		else:
			print(f"\033[31m'{search_string}' not found in the webpage.\033[0m")

	except requests.exceptions.RequestException as e:
		print(f"An error occurred: {e}")
		sys.exit(1)

def scrape_website(url, search_string, case_insensitive):
	"""
	This function recursively accesses all the links from the webpage
	and looks for the search_string in it
	"""
	# Send a GET request to the website
	response = requests.get(url)

	# Check if the request was successful (status code 200)
	if response.status_code == 200:
		# Parse the HTML content of the page
		soup = BeautifulSoup(response.content, 'html.parser')

		# Find all links on the page
		links = soup.find_all('a', href=True)
		#print(f"linkkks: '{links}")

		# Extract and print file and directory URLs
		for link in links:
			href = link['href']
			link = urljoin(url, href)
			# We access the link
			# to get the included link set
			if not check_if_link_visited(link):
				print(f"> Accessing {link}...")
				find_string(link, search_string, case_insensitive)
				scrape_website(link, search_string, case_insensitive)
			else:
				print(f"> \033[33m[Skipped]\033[0m {link}!")
	else:
		print('Failed to fetch the page:', response.status_code)
				
def parse_args():
	# Create the parser
	parser = argparse.ArgumentParser(description="""This program will
	search the given string on the provided link and on every link that
	can be reached from that link, recursively.
	""")

    # Add arguments. There must be two arguments for filenames
	parser.add_argument('link', type=str, help='the name of the base URL to access')
	parser.add_argument('search_string', type=str, help='the string to search')
	parser.add_argument('-i', '--case-insensitive', action='store_true', help='Enable case-insensitive mode')

	# Parse the arguments
	args = parser.parse_args()

    # Return the two filenames
	return args

if __name__ == "__main__":
	# Check if an IP address is provided as a command-line argument
	args = parse_args()

	# Get the IP address from the command-line argument
	url = args.link
	search_string = args.search_string
	case_insensitive = args.case_insensitive
	scrape_website(url, search_string, case_insensitive)
