IMAGE_EXTENSIONS = [
    ".jpeg", ".jpg", ".png", ".gif", ".bmp", ".tif"
]

UNMODIFIABLE_TAGS = [
    "Path", "Mode", "Width", "Height"
]

UNDELETABLE_TAGS = [
    "Name", "Format", "Mode", "Width", "Height",
    "Creation time", "Access time", "Modification time"
]

EXIF_COMPATIBLE_FORMATS = ["JPEG", "JPG", "TIFF"]

# Size of the thumbnails
THUMB_SIZE      = 32

# Metadata type
BASIC	        = 0
EXIF	        = 1

# There are 2 types of tags in a Treeview
TAG_FILEPATH    = 0
TAG_PAYLOAD     = 1

# There are 2 types of tag payload
PAYLD_DATATYPE   = 0
PAYLD_TAG_ID     = 1 # For EXIF: int ID (and not human-readable tag name)