#!/usr/bin/env sh

echo "exif_labels_dict = {" > exif_labels.py && \
cat standard_exif_tags.txt | \
awk '{
    split($4, a, ".");
    type = $5;
    if (type == "Byte") { type_num = 1; }
    else if (type == "Ascii") { type_num = 2; }
    else if (type == "Short") { type_num = 3; }
    else if (type == "Long") { type_num = 4; }
    else if (type == "Rational") { type_num = 5; }
    else if (type == "SByte") { type_num = 6; }
    else if (type == "Undefined") { type_num = 7; }
    else if (type == "SShort") { type_num = 8; }
    else if (type == "SLong") { type_num = 9; }
    else if (type == "SRational") { type_num = 10; }
    else if (type == "Float") { type_num = 11; }
    else if (type == "DFloat") { type_num = 12; }
    else { type_num = 13; }  # Handle unknown types if necessary

    print "\t" $2 ": {\"tag\": \"" a[2] "." a[3] "\", \"type\": " type_num "},"
}' >> exif_labels.py && echo "}" >> exif_labels.py