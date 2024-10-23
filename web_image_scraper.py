import os
import sys
import requests
import argparse
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

class WebScraper:
	def __init__(self, base_url, search_string, skip_limit, single_page, case_insensitive=False):
		self.base_url = base_url
		self.search_string = search_string
		self.single_page = single_page
		self.case_insensitive = case_insensitive
		self.visited_urls = []
		self.found_links = []
		self.found_count = 0
		self.skip_limit = skip_limit
		self.skip_count = 0

	def get_save_folder_from_file(filename):
		# Load the dataset
		try:
			# Open the file and read the first line
			with open(filename, 'r') as file:
				buffer = file.readline().strip()  # Read the first line and remove any trailing whitespace

			if not buffer:
				raise ValueError("Found no path for the save folder")
			# Display the first few rows of the dataset
		except Exception as e:
			print(f"An unexpected error occurred: {e}")
			sys.exit()
		return float(theta0), float(theta1) if theta0 and theta1 else None
		def check_if_link_visited(self, url):
			"""Check if the URL has already been visited."""
			if url in self.visited_urls:
				return True
			# Add the new URL to the visited URL list
			self.visited_urls.append(url)
			return False

	def find_images(self, url):
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
				if not img_url: continue

				# Create a full URL if the img_url is relative
				img_url = urljoin(url, img_url)

				# Get the path where to save the image
				img_path = os.path.join(folder, os.path.basename(img_url))

				
				# Download the image
				try:
					img_response = requests.get(img_url)
					img_response.raise_for_status()  # Check for request errors

					# Save the image
					with open(img_name, 'wb') as f:
						f.write(img_response.content)
					print(f"Downloaded: {img_name}")
				except requests.RequestException as e:
					print(f"Failed to download {img_url}: {e}")


			# Check if the search string is in the text
			if ((self.search_string.lower() in text.lower() and self.case_insensitive)
				or (self.search_string in text)):
				self.found_count += 1 # Increment counter
				self.found_links.append(url)
				print(f"\033[32m'{self.search_string}' found in the webpage.\033[0m")
			else:
				print(f"\033[31m'{self.search_string}' not found in the webpage.\033[0m")

		except requests.exceptions.RequestException as e:
			print(f"An error occurred: {e}")

	def scrape_website(self, url):
		"""Recursively access all the links from the webpage and 
		look for the search string."""
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
					print(f"> Accessing {full_link}...")
					self.skip_count = 0
					self.find_string(full_link)
					# We access links from the current link if single page mode is off
					if not self.single_page:
						self.scrape_website(full_link)
				else:
					print(f"> \033[33m[Skipped]\033[0m {full_link}!")
					self.skip_count += 1
					if self.skip_count == self.skip_limit: # If single page mode is offlimit:
						print("\n\033[31mMaximum skipped links' limit is reached!\033[0m")
						self.print_result()
						sys.exit()
		else:
			print('Failed to fetch the page:', response.status_code)

	def print_result(self):
		print(f"\nResults:")
		print(f"\n===================== Found links containing the search word:")
		for link in self.found_links:
			print(f"\033[32m> {link}\033[0m")
		print(f"\n===================== Count:")
		print(f"\033[33mFound '{self.search_string}' {self.found_count} times!\033[0m")

def parse_args():
	"""Parse command-line arguments."""
	# Create the parser
	parser = argparse.ArgumentParser(description="""This program will
	search the given string on the provided link and on every link that
	can be reached from that link, recursively.
	""")

	# Add arguments
	parser.add_argument('link', type=str, help='the name of the base URL to access')
	parser.add_argument('-s', '--single-page', action='store_true', help='Enable single page search mode')
	parser.add_argument('-l', '--limit', type=int, help='Number of already visiited/bad links that are allowed before we terminate the search')

	# Parse the arguments
	return parser.parse_args()

if __name__ == "__main__":
	# Parse command-line arguments
	args = parse_args()
	if not args.limit: args.limit = 20

	# Create an instance of WebScraper
	scraper = WebScraper(args.link, args.search_string, args.limit, args.case_insensitive, args.single_page)

	# Start scraping
	scraper.scrape_website(args.link)
	scraper.print_result()
