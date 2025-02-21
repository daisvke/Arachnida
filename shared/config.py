# Type of the scraper
SCRAPTYPE_STR = 0
SCRAPTYPE_IMG = 1

IMAGE_EXTENSIONS = [
    ".jpeg", ".jpg", ".png", ".gif", ".bmp"
]

UNMODIFIABLE_TAGS = [
    "Path", "Mode", "Width", "Height"
]

UNDELETABLE_TAGS = [
    "Name", "Format", "Mode", "Width", "Height",
    "Creation time", "Access time", "Modification time"
]

EXIF_COMPATIBLE_FORMATS = ["JPEG", "JPG"]

# Size of the thumbnails
THUMB_SIZE = 32

# Metadata type
BASIC = 0
EXIF = 1

# There are 2 types of tags in a Treeview
TAG_FILEPATH = 0
# There are 2 types of tag payload
PAYLD_DATATYPE = 1
PAYLD_TAG_ID = 2  # For EXIF: int ID (and not human-readable tag name)
