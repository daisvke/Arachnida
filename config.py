IMAGE_EXTENSIONS = {
    ".jpeg", ".jpg", ".png", ".gif", ".bmp", ".tif"
}

UNMODIFIABLE_TAGS = {
    "Name", "Format", "Mode", "Width", "Height"
}

UNDELETABLE_TAGS = {
    "Name", "Format", "Mode", "Width", "Height",
    "Creation time", "Access time", "Modification time"
}

BASIC	        = 0
PNG		        = 1
EXIF	        = 2

# Treeview insertion tags
FILEPATH        = 0
PAYLOAD         = 1
# Payloads
DATATYPE        = 0
TAG_ID          = 1 # For EXIF: int ID (and not human-readable tag name)