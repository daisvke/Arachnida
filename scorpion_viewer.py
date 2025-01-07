#!/usr/bin/env python3

import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image, PngImagePlugin
import os
from datetime import datetime
from exif_labels import exif_labels_dict
from scorpion import image_extensions, get_metadata, check_extension
import piexif
from sys import stderr
from typing import Any, Tuple

not_exif = [
    "Name",
    "Format",
    "Mode",
    "Width",
    "Height",
    "Creation time"
    ]


class MetadataViewerApp:
    def __init__(self, root, width, height):
        self.root = root
        self.root.title("Metadata Viewer")
        self.root.geometry(f"{width}x{height}")  # Set the window size
        # Mapping of Treeview item IDs to filenames
        self.item_to_file = {}

        # Setup GUI layout
        self.create_widgets()

    def create_widgets(self) -> None:
        # Buttons for file and folder selection
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(side=tk.TOP, fill=tk.X, pady=10)

        tk.Button(btn_frame, text="Open Files", command=self.open_files).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Open Folders", command=self.open_dirs).pack(side=tk.LEFT, padx=5)

        # Treeview for displaying metadata
        self.tree = ttk.Treeview(self.root, columns=("Tag", "Value"), show="headings")
        self.tree.heading("Tag", text="Tag")
        self.tree.heading("Value", text="Value")
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Double-click binding for editing the value fields
        self.tree.bind("<Double-1>", self.on_double_click)
        # Del key binding for deleting metadata entries
        self.tree.bind("<Delete>", self.delete_selected_entry)

    def open_files(self) -> None:
        """
        Forge the string of the handled extensions.
        This is needed by 'filedialog.askopenfilename',
        and the format is: "*.jpg *.jpg *.png" 
        """
        extensions = ""
        ext_len = len(image_extensions) - 1
        for i, ext in enumerate(image_extensions):
            extensions += '*' + ext
            if i < ext_len:
                extensions += " "

        # Set the filetypes argument for the askopenfilename() method
        filetypes = (
            ('Image files', extensions),
        )

        # Open the dialog to select the file names
        file_paths = filedialog.askopenfilename(
            title="Select image files",
            filetypes=filetypes,  # Send the handled file types
            multiple=True  # Activate multiple selection
        )

        self.read_metadata_from_files(file_paths)

    def read_metadata_from_files(self, files: str|list[str]) -> None:
        for path in files:
            if not check_extension(path):
                continue
            try:
                if os.path.isfile(path):
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

    def display_metadata(self, file_path: str, metadata: dict[str,str]) -> None:
        try:
            if metadata:
                for tag, value in metadata.items():
                    item_id = self.tree.insert(
                        "", tk.END, values=(tag, value))
                    # Map the item to its file (needed when modifying data)
                    self.item_to_file[item_id] = file_path
            else:
                messagebox.showinfo("Metadata Viewer", f"No metadata found for '{file_path}'.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not read metadata: {e}")
        self.tree.insert("", tk.END, values=("", ""))

    def check_if_data_is_editable(self, item_id: str) -> Tuple[Any,Any]:
        """
        Check if the data is not Exif data, as we will
        not edit them.
        """
        # Get the current tag/value in a tuple 
        values = self.tree.item(item_id, "values")
        if not values:
            return (False, False)

        # Get the tag to check if they are Exif data
        if len(values) == 2:
            tag = values[0]
            value = values[1]
        else:
            return (False, False)

        if tag in not_exif:
            return (False, False)
        return (tag, value)

    def delete_selected_entry(self, event) -> None:
        """
        Deletes the currently selected metadata entry when the
        Delete key is pressed.
        """
        # Get the selected item
        selected_item = self.tree.selection()
        if selected_item:
            # Remove the selected item from the Treeview
            for item_id in selected_item:
                tag, value = self.check_if_data_is_editable(item_id)
                if not tag or not value:
                    continue

                # First, delete the metadata entry from the file
                # Get the file associated with the item
                file_path = self.item_to_file.get(item_id)
                if not file_path:
                    continue
                self.modify_and_save_metadata_to_file(file_path, tag)

                # Then, delete the data from the tree
                self.tree.delete(item_id)

    def on_double_click(self, event) -> None:
        """Handles double-clicking a value in the Treeview to edit it."""
        # Identify the selected item and column
        item_id = self.tree.identify_row(event.y)
        column_id = self.tree.identify_column(event.x)

        if column_id != "#2":  # Only allow editing the "Value" column
            return

        tag, value = self.check_if_data_is_editable(item_id)
        if not tag or not value:
            return

        # Create an entry widget for editing
        entry = tk.Entry(self.tree)
        entry.insert(0, value)
        entry.focus()

        # Place the entry widget over the cell
        bbox = self.tree.bbox(item_id, column_id)
        entry.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])

        # Commit the new value when the entry loses focus or Enter is pressed
        def save_edit(event=None):
            new_value = entry.get()

            # Get the file associated with the item
            file_path = self.item_to_file.get(item_id)
            if not file_path:
                return
            # Update the data on the file
            self.modify_and_save_metadata_to_file(
                file_path, tag, new_value
                )
            # Update the data on the tree
            self.tree.item(item_id, values=(tag, new_value))
            entry.destroy()

        entry.bind("<Return>", save_edit)
        entry.bind("<FocusOut>", save_edit)

    def modify_and_save_metadata_to_file(
        self, file_path: str, tag_to_edit: str, value: str = "") -> bool:
        """
        Deletes a specific metadata tag from the image file.

        Args:
            file_path (str): Path to the image file.
            tag_to_remove (str): The name of the tag to remove (e.g., "Model").

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Load the image and extract EXIF data
            img = Image.open(file_path)
            exif_data = img.getexif()

            # If Exif data is present, we are updating it
            if exif_data:
                # Iterate over all EXIF tags and find the tag to remove
                for tag_id, _ in exif_data.items():
                    # Check if tag_id has an entry in the dict
                    if tag_id in exif_labels_dict: 
                        # Get the value (label name) for the tag_id
                        tag = exif_labels_dict[tag_id]
                        # Get the last part of the label
                        tag_name = tag.split('.')[1]

                        if tag_name == tag_to_edit:
                            # If a value is provided, it is a modification
                            if value:
                                print(f"Editing tag: {tag_name} (ID: {tag_id})")
                                exif_data[tag_id] = value
                            else:  # Otherwise, it is a deletion
                                print(f"Removing tag: {tag_name} (ID: {tag_id})")
                                del exif_data[tag_id]
                            print(exif_data)
                            print(f"tag: {tag_to_edit}, val: {value}")

                            # Save the modified metadata back to the file
                            img.save(file_path, exif=exif_data)

            elif img.format == "PNG" and img.info:
                img.save(file_path, pnginfo=img.info)

        except Exception as e:
            messagebox.showerror(
                "Error", f"Error while modifying the file data: {e}"
            )
            return False

        return True

if __name__ == "__main__":
    root = tk.Tk()
    app = MetadataViewerApp(root, 600, 600)
    root.mainloop()
