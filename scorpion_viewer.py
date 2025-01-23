#!/usr/bin/env python3

import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image, ImageTk
import os
from datetime import datetime
import time
from shared.exif_labels import exif_labels_dict
from scorpion import get_metadata, check_extension
from typing import Any
from fractions import Fraction
import struct
from shared.config import (
    IMAGE_EXTENSIONS,
    UNMODIFIABLE_TAGS,
    UNDELETABLE_TAGS,
    EXIF_COMPATIBLE_FORMATS,
    THUMB_SIZE,
    BASIC,
    EXIF,
    TAG_FILEPATH,
    PAYLD_DATATYPE,
    PAYLD_TAG_ID,
)


class Scorpion(ttk.Frame):
    def __init__(self, root, width, height, parent=None):
        ttk.Frame.__init__(self, parent)
        self.width = width
        self.parent = parent
        self.root = root
        self.root.geometry(f"{width}x{height}")  # Set the window size
        self.root.title("Scorpion Metadata Editor")
        self.thumbnails = {}  # Image thumbnail collection

        # Attach this frame to the root window
        self.grid(row=0, column=0, sticky='nsew')

        # Make the frame expandable

        # Allow the Treeview to expand vertically
        self.rowconfigure(1, weight=1)
        # Allow the Treeview to expand horizontally
        self.columnconfigure(0, weight=1)

        # Setup GUI layout
        self.create_widgets()

    def add_thumbnail_to_tree(self, file_path: str) -> None:
        """
        Create a thumbnail for the image and add it to the Treeview.
        """
        try:
            # Convert to a format compatible with Tkinter
            img = Image.open(file_path)
            # Resize to better fit the row height
            img.thumbnail((THUMB_SIZE, THUMB_SIZE))
            self._img = ImageTk.PhotoImage(img)
            if self._img:
                # Store the thumbnail to prevent garbage collection
                self.thumbnails[file_path] = self._img
                # Add the thumbnail to the Treeview in the first column
                self.tree.insert(
                    "",
                    tk.END,
                    values=("", ""),
                    image=self._img,
                    tags=(file_path, "THUMBNAIL")
                    )
        except Exception as e:
            raise Exception(f"Failed to create thumbnail: {e}")

    def open_image(self, file_path: str) -> None:
        """
        Open the image in a custom Tkinter window.
        """
        try:
            img = Image.open(file_path)
            img.show()  # For quick cross-platform viewing
        except Exception as e:
            raise Exception(f"Failed to open image: {e}")

    def on_thumbnail_double_click(self, event: Any) -> None:
        """
        Handle double-click on a thumbnail to open the image.
        """
        # Identify the clicked item
        selected_item = self.tree.selection()
        if not selected_item:
            return  # No item selected

        # Get the file path from the item's values
        item = self.tree.item(selected_item[0])
        file_path = item['tags'][TAG_FILEPATH]

        if file_path and os.path.isfile(file_path):
            # Open the image using the default system viewer
            self.open_image(file_path)
        else:
            raise Exception("File path is invalid or file does not exist.")

    def create_widgets(self) -> None:
        # Buttons for file and folder selection
        btn_frame = tk.Frame(self)
        btn_frame.grid(row=0, column=0, sticky='nsew')

        tk.Button(
            btn_frame,
            text="Open Files",
            command=self.open_files
        ).grid(row=0, column=0, padx=5, pady=5)

        tk.Button(
            btn_frame,
            text="Open Folders",
            command=self.open_dirs
        ).grid(row=0, column=1, padx=5, pady=5)

        # Treeview for displaying metadata
        style = ttk.Style()
        # Adjust row height to fit thumbnails
        style.configure("Treeview", rowheight=20)
        # Adjust row height to fit thumbnails
        style.configure("Treeview.Thumbnail", rowheight=50)

        self.tree = ttk.Treeview(self, columns=("Tag", "Value"))
        self.tree.grid(row=1, column=0, sticky='nsew')
        self.tree.tag_configure("THUMBNAIL", background="lightgray")
        # Setup column heading
        self.tree.heading("#0", text="Preview")
        self.tree.heading("Tag", text="Tag")
        self.tree.heading("Value", text="Value")

        # Setup columns that don't contain thumbnails
        metadata_width = int(self.width * 0.3)
        self.tree.column("#0", width=10)
        self.tree.column("Tag", width=metadata_width)
        self.tree.column("Value", width=metadata_width)

        # Add a scrollbar
        scrollbar = ttk.Scrollbar(
            self,
            orient="vertical",
            command=self.tree.yview
            )
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=1, column=1, sticky='ns')

        # Double-click binding for editing the value fields
        self.tree.bind("<Double-1>", self.on_double_click)
        # Del key binding for deleting metadata entries
        self.tree.bind("<Delete>", self.delete_selected_entry)

    def open_files(self) -> None:
        """
        Open all the selected files to extract metadata from.
        """

        """
        Forge the string of the handled extensions.
        This is needed by 'filedialog.askopenfilename',
        and the format is: "*.jpeg *.jpg *.png"
        """
        extensions = ""
        ext_len = len(IMAGE_EXTENSIONS) - 1
        for i, ext in enumerate(IMAGE_EXTENSIONS):
            extensions += '*' + ext
            if i < ext_len:
                extensions += " "

        # Set the filetypes argument for the askopenfilename() method
        filetypes = (
            ('Image files', extensions),
        )

        # Open the dialog to select the file names
        file_paths = filedialog.askopenfilenames(
            title="Select image files",
            filetypes=filetypes,  # Send the handled file types
        )

        self.read_metadata_from_files(file_paths)

    def read_metadata_from_files(self, files: Any) -> None:
        """
        Read and display all metadata from each provided files.
        """
        for path in files:
            # If file extension isn't handled or path isn't a valid file
            if not check_extension(path) or not os.path.isfile(path):
                continue
            try:
                metadata = get_metadata(path)
                self.display_metadata(path, metadata)
            except Exception as e:
                messagebox.showerror("Error", f"Could not read metadata: {e}")

    def open_dirs(self):
        dir_path = filedialog.askdirectory(title="Select folders")
        if dir_path:
            files = [
                os.path.join(dir_path, filename)
                for filename in os.listdir(dir_path)
            ]
            # Read the metadata of each file in the folder
            if files:
                self.read_metadata_from_files(files)

    def display_metadata(
            self, file_path: str, metadata: dict[int, Any] | None) -> None:
        """
        Display metadata of the image.
        Keep useful data as 'tags' in the tree items.
        """
        deletion = None

        def check_if_image_is_already_displayed():
            nonlocal deletion
            # Check if file is already displayed.
            # If so, delete the previous version.
            for item in self.tree.get_children():
                tags = self.tree.item(item, "tags")
                # Ensure tags are valid and compare file path
                if tags and len(tags) > 0 and tags[0] == file_path:
                    deletion = item
                    self.tree.delete(item)

                # Delete the blank separation line after the deleted item.
                if deletion and deletion != item:
                    values = self.tree.item(item, "values")
                    if values == ("", ""):  # Check if it is a blank line
                        self.tree.delete(item)
                        break

        try:
            if not metadata:
                raise ValueError(f"Could not read metadata from {file_path}")

            check_if_image_is_already_displayed()

            self.add_thumbnail_to_tree(file_path)

            basic, exif = metadata[BASIC], metadata[EXIF]

            if basic:
                for tag, value in basic.items():
                    self.tree.insert(
                        "",
                        tk.END,
                        values=(tag, value),
                        tags=([file_path, "BASIC"])
                    )
            if exif:
                for tag, value in exif.items():
                    human_readable_tag = value[0]

                    self.tree.insert(
                        "",
                        tk.END,
                        values=(human_readable_tag, str(value[1])),
                        tags=[file_path, "EXIF", str(tag)]
                    )

        except Exception as e:
            messagebox.showerror("Error", f"{e}")

        self.tree.insert("", tk.END, values=("", ""))

    def delete_selected_entry(self, event) -> None:
        """
        Deletes the currently selected metadata entry when the
        Delete key is pressed.
        """

        def check_if_tag_deletable(tag: str) -> bool:
            if tag in UNDELETABLE_TAGS:
                return False
            return True

        # Get the selected item
        selected_item = self.tree.selection()
        if selected_item:
            # Remove the selected item from the Treeview
            for item_id in selected_item:
                tag = self.tree.item(item_id, "values")[0]

                if not tag or not check_if_tag_deletable(tag):
                    continue

                tags = self.tree.item(item_id, "tags")
                if not tags[PAYLD_DATATYPE] == "BASIC":
                    continue

                # First, delete the metadata entry from the file
                # Get the file associated with the item
                file_path = tags[TAG_FILEPATH]
                if not file_path:
                    continue

                try:
                    self.modify_and_save_metadata_to_file(file_path, tag, tags)
                except Exception as e:
                    messagebox.showerror(
                        "Error", f"Error while modifying the file data: {e}"
                    )

                # Then, delete the data from the tree
                self.tree.delete(item_id)

    def on_double_click(self, event) -> None:
        """Handles double-clicking a value in the Treeview to edit it."""
        def check_if_tag_modifiable(tag: str) -> bool:
            if tag in UNMODIFIABLE_TAGS:
                return False
            return True

        # Identify the selected item and column
        item_id = self.tree.identify_row(event.y)
        column_id = self.tree.identify_column(event.x)

        values = self.tree.item(item_id, "values")
        tag = values[0]
        tags = self.tree.item(item_id, "tags")

        # Open the image when the row containing the image is clicked
        if tags and "THUMBNAIL" in tags:
            try:
                self.on_thumbnail_double_click(event)
            except Exception as e:
                messagebox.showerror(
                    "Error", f"Error while opening the image: {e}"
                )
            return

        # Only allow editing the "Value" column
        if (column_id != "#2" or not tag or not values
                or not check_if_tag_modifiable(tag)):
            return

        # Create an entry widget for editing
        entry = tk.Entry(self.tree)
        entry.insert(0, values[1])
        entry.focus()

        # Place the entry widget over the cell
        bbox = self.tree.bbox(item_id, column_id)
        entry.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])

        # Commit the new value when the entry loses focus or Enter is pressed
        def save_edit(event=None):
            new_value = entry.get()

            # Get the file associated with the item
            file_path = tags[TAG_FILEPATH]
            if not file_path:
                return
            # Update the data on the file
            try:
                self.modify_and_save_metadata_to_file(
                    file_path, tag, tags, new_value
                    )
            except Exception as e:
                messagebox.showerror(
                    "Error", f"Error while modifying the file data: {e}"
                )            # Update the data on the tree

                # Destroy the temporary entry widget
                entry.destroy()
                return

            # Assign new value to the entry
            self.tree.item(item_id, values=(tag, new_value))
            # Destroy the temporary entry widget
            entry.destroy()

        entry.bind("<Return>", save_edit)
        entry.bind("<FocusOut>", save_edit)

    def convert_value_to_metadata_type(
            self, value: Any, metadata_type: int) -> Any:
        """
        Convert a value to the specified metadata type.

        This function handles various data types commonly used in
        metadata formats, including EXIF, `img.info`, and other image
        metadata formats.

        Parameters:
            value: The value to convert.
            metadata_type: An integer representing the metadata type
                                                    (e.g., EXIF types).

        Returns:
            The value converted to the specified metadata type.

        Raises:
            ValueError: If the metadata type is unsupported.

        Notes on floats:
            Float numbers are stored as rationals in all regular
            metadata entries.

            EXIF metadata is meant to be universally compatible across devices
            and platforms, many of which historically lacked robust support
            for floating-point arithmetic.
            Rational types, which represent values as integers, ensure broader
            compatibility.
            This is why float values are stored as rationals.
            The float type also exists for later compatibility and custom
            metadata.

            Computers store floating-point numbers as approximations using
            a binary format (IEEE 754 standard). For instance, 72.1 cannot
            be represented precisely as a binary floating-point number.
            Instead, it is stored as the closest approximation,
            which is 72.0999984741211.

            This is why we are rounding the float value before sending back
            the converted float value.
        """
        # print(f"{INFO} PAYLD_DATATYPE: {metadata_type}, value: {value}")

        if metadata_type == 1:  # Byte
            return int(value) & 0xFF  # Ensure within 0-255
        elif metadata_type == 2:  # ASCII
            return str(value) + '\0'  # Null-terminated string
        elif metadata_type == 3:  # Short
            return int(value) & 0xFFFF  # Ensure within 0-65535
        elif metadata_type == 4:  # Long
            return int(value) & 0xFFFFFFFF  # Ensure within 0-4294967295
        elif metadata_type == 5:  # Rational
            value = struct.unpack('f', struct.pack('f', float(value)))[0]
            return round(value, 1)
        elif metadata_type == 6:  # SByte
            return int(value) if -128 <= int(value) <= 127 else None
        elif metadata_type == 7:  # Undefined
            if isinstance(value, str):
                return bytes(value, "utf-8")
            else:
                return bytes(value)
        elif metadata_type == 8:  # SShort
            return int(value) if -32768 <= int(value) <= 32767 else None
        elif metadata_type == 9:  # SLong
            if -2147483648 <= int(value) <= 2147483647:
                return int(value)
            else:
                return None
        elif metadata_type == 10:  # SRational
            fraction = Fraction(float(value)).limit_denominator(10000)
            return (fraction.numerator, fraction.denominator)
        elif metadata_type == 11:  # Float
            return struct.unpack('f', struct.pack('f', float(value)))[0]
        elif metadata_type == 12:  # DFloat
            return struct.unpack('d', struct.pack('d', float(value)))[0]
        else:
            # If metadata type isn't found, we return the value itself
            return value

    def set_file_times(self, file_path, new_time: str):
        """
        Modify access and modification times on the file.
        """
        formatted_time = time.mktime(
                time.strptime(new_time, "%Y-%m-%d %H:%M:%S")
            )
        os.utime(file_path, (formatted_time, formatted_time))

    def modify_basic_metadata(
                self,
                file_path: str, tag_name: str, value: Any, img: Image.Image
            ) -> tuple:
        """
        Modify the basic informations of the image file.
        """

        def is_valid_datetime(
                    date_string: str, date_format: str = "%Y-%m-%d %H:%M:%S"
                ) -> bool:
            """
            Check if the given string is in the correct date time format.
            """
            try:
                datetime.strptime(date_string, date_format)
                return True
            except ValueError:
                return False

        file_format = img.format

        if tag_name == "Name":
            if value:
                file_path = os.path.dirname(file_path) + "/" + value
        elif tag_name == "Access time" or tag_name == "Modification time":
            if value:
                if not is_valid_datetime(value):
                    raise ValueError("Uncorrect datetime format.")
                self.set_file_times(file_path, value)
        elif tag_name == "Format" and value:
            file_format = value.upper()
        elif tag_name == "Comment":
            if value:
                img.info["comment"] = value
            else:
                img.info.pop("comment", None)

        exif_data = img.getexif()
        if exif_data and file_format in EXIF_COMPATIBLE_FORMATS:
            img.save(file_path, exif=exif_data, format=file_format)
        else:
            img.save(file_path, format=file_format)

        return img, file_path

    def handle_exif(
                self, img: Image.Image, file_path: str, tag_id: int, value: Any
            ) -> None:
        """tag_id: int tag ID (and not human-readable tag name)"""
        exif_data = img.getexif()

        tag_type = 0
        # If Exif data is present, we are updating it
        if exif_data and tag_id in exif_data:
            # Detect type
            tag_type_value = exif_labels_dict.get(tag_id, {}).get("type")

            # Check if the value is a string or int (= convertible to int)
            if isinstance(tag_type_value, (str, int)):
                tag_type = int(tag_type_value)
        value = self.convert_value_to_metadata_type(value, tag_type)

        # If a value is provided, it is a modification
        if value:
            # print(f"{INFO} Editing tag: {tag_name})")
            exif_data[tag_id] = value
        else:  # Otherwise, it is a deletion
            # print(f"{INFO} Removing tag: {tag_name}")
            del exif_data[tag_id]
        # Save the modified metadata back to the file
        img.save(file_path, exif=exif_data, format=img.format)

    def handle_img(
                self,
                img: Image.Image, file_path: str, value: Any, tag_name: str
            ) -> None:
        # Add all key-value pairs from img.info to the PngInfo object
        for key, val in img.info.items():
            # If a value is provided, it is a modification
            if value and key == tag_name:
                val = value
            if isinstance(val, tuple):  # Handle tuples (e.g., dpi)
                # All values are concatenated as strings joined
                # by a comma + space
                val = ", ".join(map(str, val))

            # If we are not in delete mode (no given value) and the key is the
            # key to delete, then we can add the entry to the updated item
            if not (not value and key == tag_name):
                img.info[key] = val

        # Save the file with the new metadata
        img.save(file_path, format=img.format)

    def modify_and_save_metadata_to_file(
                self, file_path: str, tag_name: str, tags: Any, value: Any = ""
            ) -> None:
        """
        Modify or remove a specific metadata tag from the image file.

        Args:
            file_path   : Path to the image file.
            tag_name    : The name of the tag to edit (e.g., "Model").
            tags        : Contains info about the item to edit
            value       : Needed in case of a modification

        Returns:
            bool: True if successful, False otherwise.
        """

        try:
            meta_datatype = tags[PAYLD_DATATYPE]  # BASIC or EXIF
            img = Image.open(file_path)  # Load the image and extract EXIF data

            if meta_datatype == "BASIC":
                img, file_path = self.modify_basic_metadata(
                        file_path, tag_name, value, img
                    )
            elif meta_datatype == "EXIF":
                self.handle_exif(
                        img,
                        file_path,
                        int(tags[PAYLD_TAG_ID]),
                        value
                    )
            else:
                self.handle_img(img, file_path, value, tag_name)

        except Exception as e:
            raise Exception(e)


if __name__ == "__main__":
    root = tk.Tk()
    app = Scorpion(root, 600, 600)

    root.rowconfigure(0, weight=1)
    root.columnconfigure(0, weight=1)
    root.mainloop()
