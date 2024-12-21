import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image
import os
from datetime import datetime
from exif_labels import exif_labels_dict
from scorpion import image_extensions, display_metadata

class MetadataViewerApp:
    def __init__(self, root, width, height):
        self.root = root
        self.root.title("Metadata Viewer")
        self.root.geometry(f"{width}x{height}")  # Set the window size

        # Setup GUI layout
        self.create_widgets()

    def create_widgets(self):
        # Buttons for file and folder selection
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(side=tk.TOP, fill=tk.X, pady=10)

        tk.Button(btn_frame, text="Open File", command=self.open_file).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Open Folder", command=self.open_folder).pack(side=tk.LEFT, padx=5)

        # Treeview for displaying metadata
        self.tree = ttk.Treeview(self.root, columns=("Tag", "Value"), show="headings")
        self.tree.heading("Tag", text="Tag")
        self.tree.heading("Value", text="Value")
        self.tree.pack(fill=tk.BOTH, expand=True)

    def open_file(self):
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

        filetypes = (
            ('Image files', extensions),
        )

        file_path = filedialog.askopenfilename(
            title="Select an Image File",
            filetypes=filetypes
        )
        if file_path:
            display_metadata(file_path)

    def open_folder(self):
        folder_path = filedialog.askdirectory(title="Select a Folder")
        if folder_path:
            files = [
                os.path.join(folder_path, f)
                for f in os.listdir(folder_path)
                if os.path.isfile(os.path.join(folder_path, f))
            ]
            for file in files:
                self.display_metadata(file)

    def display_metadata(self, file_path):
        try:
            img = Image.open(file_path)

            # Clear previous content
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Basic Attributes
            self.tree.insert("", tk.END, values=("File Path", file_path))
            self.tree.insert("", tk.END, values=("Format", img.format))
            self.tree.insert("", tk.END, values=("Mode", img.mode))
            self.tree.insert("", tk.END, values=("Size", f"{img.size[0]}x{img.size[1]}"))

            # Creation Date
            creation_time = os.path.getctime(file_path)
            self.tree.insert("", tk.END, values=("Creation Date", datetime.fromtimestamp(creation_time)))

            # EXIF Data
            exif_data = img._getexif()
            if exif_data:
                for tag_id, value in exif_data.items():
                    tag_name = exif_labels_dict.get(tag_id, f"Unknown Tag (ID: {tag_id})")
                    self.tree.insert("", tk.END, values=(tag_name, value))
            else:
                messagebox.showinfo("Metadata Viewer", "No EXIF data found.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not read metadata: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = MetadataViewerApp(root, 600, 600)
    root.mainloop()
