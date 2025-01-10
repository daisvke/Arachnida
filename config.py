IMAGE_EXTENSIONS = {
    ".jpeg", ".jpg", ".png", ".gif", ".bmp", ".tif"
    }

BASIC	= 0
PNG		= 1
EXIF	= 2

# Treeview insertion tags
FILEPATH    = 0
PAYLOAD     = 1
# Payloads
DATATYPE    = 0
TAG_ID      = 1 # For EXIF: int ID (and not human-readable tag name)

# Piexif data types
class TYPES:
    Byte = 1
    Ascii = 2
    Short = 3
    Long = 4
    Rational = 5
    SByte = 6
    Undefined = 7
    SShort = 8
    SLong = 9
    SRational = 10
    Float = 11
    DFloat = 12
    Unknown = 13