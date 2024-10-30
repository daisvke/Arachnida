import os
import sys
import requests
import argparse
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

image_storage_folder = "./img"

class WebImageScraper:
	def __init__(self, image_storage_folder, base_url, skip_limit, single_page, search_string="", case_insensitive=False):
		self.image_storage_folder = image_storage_folder
		self.base_url = base_url
		self.search_string = search_string
		self.single_page = single_page
		self.case_insensitive = case_insensitive
		self.visited_urls = []
		self.found_links = []
		self.found_count = 0
		self.skip_limit = skip_limit
		self.skip_count = 0
		
		# Check if the folder exists
		if not os.path.exists(image_storage_folder):
			# Create the image folder if it doesn't exist
			os.makedirs(image_storage_folder)
		else:
			print(f"> Created image storage folder: '{image_storage_folder}")

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
				img_title = img.get('alt') if img.get('alt') is not None else ""
				if not img_url: continue

				# Create a full URL if the img_url is relative
				img_url = urljoin(url, img_url)

				# Get the path where to save the image by joining the target 
				# folder path and the image name
				img_name = os.path.basename(img_url)
				img_path = os.path.join(self.image_storage_folder, img_name)

				# Check if the search string is in the text
				if ((self.search_string and img_title
					and ((self.search_string.lower() in img_title.lower()
					and self.case_insensitive)
					or (self.search_string in img_title)))
					or not self.search_string):
					self.found_count += 1 # Increment counter
					self.found_links.append(url)
					if self.search_string: 
						print(f"\033[32mFound an image containing '{self.search_string}'.\033[0m")

					# Download the image
					try:
						print(f"Downloading '{img_name}'...")
						img_response = requests.get(img_url)
						img_response.raise_for_status()  # Check for request errors

						# Save the image
						with open(img_path, 'wb') as f:
							f.write(img_response.content)
						print(f"\033[32mDownloaded '{img_name}'\033[0m")
					except requests.RequestException as e:
						print(f"\031[32mFailed to download {img_url}: {e}\033[0m")

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
					self.find_images(full_link)
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
	parser.add_argument('-r', '--research_string', type=str, help='If not empty enables the string search mode')
	parser.add_argument('-i', '--case-insensitive', action='store_true', help='Enable case-insensitive mode')
	parser.add_argument('-s', '--single-page', action='store_true', help='Enable single page search mode')
	parser.add_argument('-l', '--limit', type=int, help='Number of already visiited/bad links that are allowed before we terminate the search')
	# Parse the arguments
	return parser.parse_args()

if __name__ == "__main__":
	# Parse command-line arguments
	args = parse_args()
	if not args.limit: args.limit = 20
	if not args.research_string: args.research_string = None

	# Create an instance of WebScraper
	scraper = WebImageScraper(image_storage_folder, args.link, args.limit, args.single_page, args.research_string, args.case_insensitive)

	# Find images from the base url
	scraper.find_images(args.link)
	
	# We access links from the current link if single page mode is off
	if not args.single_page:
		scraper.scrape_website(args.link)
	# If the string search mode is on, print the URLs of the images containing
	# the search string in its 'alt' value  
	if args.research_string: scraper.print_result()
