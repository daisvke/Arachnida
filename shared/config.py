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

# Metadata type
BASIC	        = 0
EXIF	        = 1

# Treeview insertion tags
FILEPATH        = 0
PAYLOAD         = 1
# Payloads
DATATYPE        = 0
TAG_ID          = 1 # For EXIF: int ID (and not human-readable tag name)