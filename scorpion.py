import sys
from shutil import get_terminal_size
from PIL import Image
import os
from datetime import datetime
from argparse import ArgumentParser
from ascii_format import ERROR, INFO, RESET, YELLOW
from exif_labels import exif_labels_dict
from scorpion_viewer import MetadataViewerApp

image_extensions = {
    ".jpeg", ".jpg", ".png", ".gif", ".bmp", ".tif", ".cr2"
    }


def display_metadata(file_path: str, viewer: MetadataViewerApp = None) -> None:
    """
    Display all the metadata from the file.

    Each entry in the Exif data have a tag ID that corresponds to
    a label name. however, the ID is not a human-readable value.
    This is why we are using a dictionary that maps each ID into a
    human-readable label.
    """
    try: 
        """
        Open the image file.

        The Pillow library (often imported as PIL, which stands for Python
        Imaging Library) is used in Python for opening, manipulating, and
        saving various image file formats.
        """
        img = Image.open(file_path)
        # Display basic attributes
        print(f"{INFO} Opening file: {YELLOW}{file_path}{RESET}")
        print(f"Format: {img.format}")
        print(f"Mode: {img.mode}")
        print(f"Size: width: {img.size[0]}, height: {img.size[1]}")
        
        # Get creation date from the file system
        creation_time = os.path.getctime(file_path)
        print(f"Creation Date: {datetime.fromtimestamp(creation_time)}\n")

        # Extract EXIF data
            
        exif_data = img._getexif()
        if exif_data:
            print("EXIF Data:")
            for tag_id, value in exif_data.items():
                """
                The piexif library provides a dictionary called TAGS that
                contains mappings of EXIF tag IDs to their human-readable
                names. This dictionary is organized by different categories,
                such as 'Exif', 'GPS', etc.

                The get method is used to retrieve the name of the tag
                corresponding to the tag_id.
                If the tag_id exists in the TAGS['Exif'] dictionary, it returns
                the corresponding tag name. Otherwise, we choose to return None.

                tag = piexif.TAGS['Exif'].get(tag_id, None)
                if tag:
                    tag_name = tag.get('name', 'Unknown Tag')
                    tag_type = tag.get('type', 'Unknown Type')
                    print(f"  {tag_name} (ID: {tag_id}, Type: {tag_type}): {value}")
                """
                
                # Check if tag_id has an entry in the dict
                if tag_id in exif_labels_dict: 
                    # Get the value (label name) for the tag_id
                    tag = exif_labels_dict[tag_id]
                    # Get the last part of the label
                    # (eg. "Model" from "Exif.Image.Model")
                    tag_name = tag.split('.')[1]
                    print(f"  {tag_name}: {value}")
                else:  # Handle the case where tag is not found
                    print(f"  {tag_id} (no tag name found): {value}")
        else:
            print("No EXIF data found.") 
    except Exception as e:
        print(f"Error processing {file_path}: {e}")


def parse_args():
    """Set up argparse and return the given arguments"""
    parser = ArgumentParser(
        description="Extract EXIF data and other data from image files."
        )
    parser.add_argument(
        'files', metavar='FILE', type=str, nargs='*',
        help='one or more image files to process'
        )
    parser.add_argument(
        '-d', '--directory', metavar='DIR', type=str, nargs='*',
        help='one or more folders containing image files to process'
        )
    
    return parser.parse_args()


def loop_through_files(files: list[str]) -> None:
    """
    Treat all the files given as argument
    """
    # Get terminal size
    terminal_size = get_terminal_size()
    # Get terminal width
    terminal_width = terminal_size.columns

    for file_path in files:
        if os.path.isfile(file_path):
            # Check if the file extension is handled
            img_name = os.path.basename(file_path)
            _, img_extension = os.path.splitext(img_name)
            if img_extension not in image_extensions:
                print(
                    f"{ERROR} {file_path}: '{img_extension}' is not a "
                    f"handled extension.")
                print("\n" + "-" * terminal_width + "\n")
                continue
            display_metadata(file_path)
            print("\n" + "-" * terminal_width + "\n")
        else:
            print(f"{ERROR} {file_path} is not a valid file.")


def run_scorpion(files: list, directories: list) -> None:
    """
    Run scorpion on the given files, and
    loop through all the given directories.
    """
    loop_through_files(files)

    # Check if directories were provided
    if directories:
        # Loop through files in the directories
        for dirname in directories:
            print(f"{INFO} Entering {dirname}...")
            try:
                # Check if the folder exists
                if not os.path.isdir(dirname):
                    print(f"{ERROR} {dirname} is not a valid directory.")
                    continue

                # Create a list of full file paths
                file_paths = [
                    os.path.join(dirname, filename)
                    for filename in os.listdir(dirname)
                    ]
                loop_through_files(file_paths)
            except Exception as e:
                print(f"{ERROR} {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: ./scorpion FILE1 [FILE2 ...]")
        sys.exit(1)

    args = parse_args()
    run_scorpion(args.files, args.directory)


if __name__ == "__main__":
    main()
