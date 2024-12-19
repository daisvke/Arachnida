import sys
from shutil import get_terminal_size
from PIL import Image
import piexif
import os
from datetime import datetime
from argparse import ArgumentParser
from ascii_format import ERROR


def display_metadata(file_path):
    try:
        # Get terminal size
        terminal_size = get_terminal_size()
        # Get terminal width
        terminal_width = terminal_size.columns
        
        """
        Open the image file.

        The Pillow library (often imported as PIL, which stands for Python
        Imaging Library) is used in Python for opening, manipulating, and
        saving various image file formats.
        """
        img = Image.open(file_path)
        # Display basic attributes
        print(f"File: {file_path}")
        print(f"Format: {img.format}")
        print(f"Mode: {img.mode}")
        print(f"Size: width: {img.size[0]}, height: {img.size[1]}")
        
        # Get creation date from the file system
        creation_time = os.path.getctime(file_path)
        print(f"Creation Date: {datetime.fromtimestamp(creation_time)}")

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
                the corresponding tag name. If it does not exist, it returns the
                tag_id itself as a fallback. This is useful for handling cases
                where the tag ID might not be recognized.
                """
                tag = piexif.TAGS['Exif'].get(tag_id, tag_id)
                print(f"  {tag}: {value}")
        else:
            print("No EXIF data found.")
        
        print("\n" + "-" * terminal_width + "\n")
        
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
    for file_path in files:
        if os.path.isfile(file_path):
            display_metadata(file_path)
        else:
            print(f"{file_path} is not a valid file.")    


def main():
    if len(sys.argv) < 2:
        print("Usage: ./scorpion FILE1 [FILE2 ...]")
        sys.exit(1)

    args = parse_args()
    loop_through_files(args.files)

    # Check if directories were provided
    if args.directory:
        # Loop through files in the directories
        for dirname in args.directory:
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


if __name__ == "__main__":
    main()
