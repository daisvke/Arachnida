# Arachnida
A suite of web scrapers and metadata editors designed for efficient web and image data processing:

- **`Harvestmen`**: A tool for searching and extracting strings from web pages.
- **`Spider`**: A scraper for finding images or specific strings within HTML image tags.
- **`Scorpion`**: A utility for viewing metadata from image files.
- **`Scorpion Viewer`**: A more advanced tool for displaying, deleting, and modifying metadata in image files.

## Harvestmen (strings)

This module implements a web scraper that recursively searches for a specified string within the content of a given base URL and all reachable links from that URL. The script utilizes the `requests` library to fetch web pages and `BeautifulSoup` from the `bs4` library to parse HTML content. 

### Key Features:
- **Recursive Scraping**: The scraper navigates through all links found on the base URL and continues to scrape linked pages unless restricted by the user.
- **Search Functionality**: It checks for the presence of a user-defined search string in the text of each page, with an option for case-insensitive searching.
- **Visited URL Tracking**: The script maintains a list of visited URLs to avoid processing the same page multiple times.
- **Skip Limit**: Users can set a limit on the number of skipped links (either due to already visited pages or bad links) before the scraper terminates.
- **Command-Line Interface**: The script accepts command-line arguments for the base URL, search string, case sensitivity, single-page mode, and skip limit.

### Usage:
```
usage: harvestmen.py [-h] -s SEARCH_STRING [-i] [-r] [-l RECURSE_DEPTH] [-k KO_LIMIT] link

This program will search the given string on the provided link and on every link that can be reached from that link, recursively.

positional arguments:
  link                  the name of the base URL to access

options:
  -h, --help            show this help message and exit
  -s SEARCH_STRING, --search-string SEARCH_STRING
                        the string to search
  -i, --case-insensitive
                        Enable case-insensitive mode
  -r, --recursive       Enable recursive search mode
  -l RECURSE_DEPTH, --recurse-depth RECURSE_DEPTH
                        indicates the maximum depth level of the recursive download. If not indicated, it will be 5.
  -k KO_LIMIT, --ko-limit KO_LIMIT
                        Number of already visited/bad links that are allowed before we terminate the search. This is to ensure that we don't get stuck into a loop.
```

## Spider (images, strings in image tags)

This module implements a web image scraper that recursively searches for images on a specified base URL and downloads them to a designated folder. 

### Key Features:

- **Image downloading**: The scraper identifies and downloads images from the base URL and any linked pages, saving them to a specified local directory. If no directory is specified, it defaults to `./data/`.
- **Search functionality**: Users can specify a search string to filter images based on their alt text. The scraper supports both case-sensitive and case-insensitive modes.
- **Recursive scraping**: The script can perform recursive scraping through all links found on the base URL, with an option to set a maximum depth level for the recursion (default is 5).
- **Visited URL tracking**: It maintains a list of visited URLs to avoid processing the same page multiple times, with a configurable limit on the number of already visited or bad links allowed before termination (KO limit).
- **Open image folder option**: Users have the option to automatically open the image folder at the end of the program for easy access to downloaded images.
- **Memory limit**: Set a memory limit for downloaded images to a specified value in MB, with a default of 1000MB.

### Usage:
```
// Display help
python spider.py -h

usage: spider.py [-h] [-s SEARCH_STRING] [-p IMAGE_PATH] [-i] [-r]
                 [-l RECURSE_DEPTH] [-k KO_LIMIT] [-o]
                 link

This program will search the given string on the provided link and on every link
that can be reached from that link, recursively.

positional arguments:
  link                  the name of the base URL to access

options:
  -h, --help            show this help message and exit
  -s SEARCH_STRING, --search-string SEARCH_STRING
                        If not empty enables the string search mode: only images
                        which 'alt' attribute contains the search string are
                        saved
  -p IMAGE_PATH, --image-path IMAGE_PATH
                        indicates the path where the downloaded files will be
                        saved. If not specified, ./data/ will be used.
  -i, --case-insensitive
                        Enable case-insensitive mode
  -r, --recursive       Enable recursive search mode
  -l RECURSE_DEPTH, --recurse-depth RECURSE_DEPTH
                        indicates the maximum depth level of the recursive
                        download. If not indicated, it will be 5.
  -k KO_LIMIT, --ko-limit KO_LIMIT
                        Number of already visited/bad links that are allowed
                        before we terminate the search. This is to ensure that we
                        don't get stuck into a loop.
  -o, --open            Open the image folder at the end of the program.
  -m MEMORY, --memory MEMORY
                        Set a limit to the memory occupied by the dowloaded
                        images (in MB). Default is set to 1000MB.

// Ex. to scrap with a depth of 1 with a search string "42" with the open folder option on :
python3 spider.py "https://42.fr/le-campus-de-paris/diplome-informatique/expert-en-architecture-informatique" -r -l 1 -s "42" -o
```


## Scorpion (image file metadata)

### Description
This is the CLI for Scorpion. This program receives image files as parameters and parses them for EXIF and other metadata, displaying the information on the terminal.<br />
It displays basic attributes such as the creation date, as well as EXIF, or PNG data.


### Usage

```
usage: scorpion.py [-h] [-d [DIR ...]] [FILE ...]

Extract EXIF data and other data from image files.

positional arguments:
  FILE                  one or more image files to process

options:
  -h, --help            show this help message and exit
  -d [DIR ...], --directory [DIR ...]
                        one or more folders containing image files to process
```


## Scorpion Viewer

### Description
This is the GUI for Scorpion. This program let us delete and modify some of the metadata from the image files.<br />
It uses `Tkinter` for the GUI and `Treeview` widget to present metadata in a structured, tabular format.


## Notes

### Modifying extensions
* Sometimes, certain websites do not recognize your ID photo image file because they expect a 'PNG' extension instead of 'JPEG'. Simply changing the file extension manually may not be sufficient.

* We discovered that modifying the `Image.format` attribute using the `Pillow library (PIL)` effectively allows the file to be recognized with the desired extension and successfully passes the checks.

### Exif labels
* EXIF metadata uses numerical identifiers (integers) to represent specific tags, but these integers are not human-readable. To work effectively with EXIF data, you need a way to map these numerical codes to their corresponding tag names and descriptions. 

* We got the Exif Tags from: <a href="https://exiv2.org/tags.html">exiv2.org</a>.
The original tags are in `standard_exif_tags.txt`.
Only the needed columns are stored in `exif_labels.py`.

```
// Make a dictionary from the data on the website in `exif_labels.py`
./generate_exif_labels_dict.sh
```

### Time related metadata
#### Creation Time 
Here’s a refined version of the README section for clarity and readability:

---

### Challenges Faced

1. **Linux Limitation on `Creation Time`**:
   - Linux does not natively support or store a `Creation Time` attribute in the same way as Windows. This limitation prevents direct modification of the `Creation Time` metadata on Linux systems.

2. **Behavior of `Image.save()` Method**:
   - The `Image.save()` method in Python creates a new image file and deletes the original one during the save process. As a result, all time-related metadata (`Creation Time`, `Access Time`, and `Modification Time`) are updated to reflect the time of the save operation, unintentionally overwriting the original timestamps.

3. **Attempted Workaround**:
   - To address the issue, we attempted a workaround where the `Image.save()` operation was performed on a temporary file. The temporary file was then copied to the destination path. However, even with this approach, the destination file's `Access Time` and `Modification Time` were updated because the file system treats the copy operation as an access and modification event.

```python
def save_image_without_time_update(img, file_path, info):
    with NamedTemporaryFile(delete=False) as temp_file:
        temp_path = temp_file.name + ".png"
        img.save(temp_path, exif=info)

    # Copy the temporary file to the original path
    shutil.copyfile(temp_path, file_path)

    # Remove the temporary file
    os.remove(temp_path)

save_image_without_time_update(img, file_path, exif_data)  
```
4. **Successful Modification of `Modification Time`**:
   - The only case where the result reflected our intent was when modifying the `Modification Time`. After the file was created (and its `Modification Time` was unintentionally updated), we explicitly updated the `Modification Time` value, effectively erasing the unintentional update and applying the desired value.


### Common Image (PIL) Methods
```
    img.show():
        This method displays the image using the default image viewer on your system.

    img.save(fp, format=None, **params):
        This method saves the image to a file. You can specify the file path and format (if different from the original).

    img.resize(size):
        This method resizes the image to the specified size (a tuple of width and height) and returns a new image object.

    img.convert(mode):
        This method converts the image to a different color mode (e.g., from 'RGB' to 'L' for grayscale) and returns a new image object.

    img.thumbnail(size: tuple[float, float]):
        This method modifies the image to contain a thumbnail version of itself, no larger than the given size. This method calculates an appropriate thumbnail size to preserve the aspect of the image, calls the draft() method to configure the file reader (where applicable), and finally resizes the image.
```
More [here](https://pillow.readthedocs.io/en/stable/reference/Image.html) 

### Documentation
* [Pillow Doc on handled Image File Formats](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html)
* [Examples of JPG files with EXIF data](https://github.com/ianare/exif-samples)