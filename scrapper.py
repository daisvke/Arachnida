import sys
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def find_string(url, search_string):
	try:
		# Send a GET request to the URL
		response = requests.get(url)
		response.raise_for_status()  # Raise an error for bad responses

		# Parse the HTML content
		soup = BeautifulSoup(response.text, 'html.parser')

		# Get the text from the soup object
		text = soup.get_text()

		# Check if the search string is in the text
		if search_string in text:
			print(f"\033[32m'{search_string}' found in the webpage.\033[0m")
		else:
			print(f"\033[31m'{search_string}' not found in the webpage.\033[0m")

	except requests.exceptions.RequestException as e:
		print(f"An error occurred: {e}")
		sys.exit(1)

def scrape_website(url, search_string):
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
			print(f"Accessing {link}...")
			find_string(link, search_string)
#			scrape_website(link, search_string)
	else:
		print('Failed to fetch the page:', response.status_code)
				
if __name__ == "__main__":
	# Check if an IP address is provided as a command-line argument
	if len(sys.argv) != 3:
		print("Usage: ", sys.argv[0], " <URL> <SEARCH_STRING>")
		sys.exit(1)

# Get the IP address from the command-line argument
url = sys.argv[1]
search_string = sys.argv[2]

scrape_website(url, search_string)
