import os
import subprocess
import platform


def open_folder_in_explorer(folder_path):
    """
    A function to open a folder on the explorer of the current OS.
    """
    # Normalize the folder path
    folder_path = os.path.abspath(folder_path)

    # Determine the desktop environment and open the folder accordingly
    if platform.system() == "Linux":
        # Check for common desktop environments
        try:
            # Try to open with Nautilus (GNOME)
            subprocess.run(['nautilus', folder_path])
        except FileNotFoundError:
            try:
                # Try to open with Dolphin (KDE)
                subprocess.run(['dolphin', folder_path])
            except FileNotFoundError:
                try:
                    # Try to open with Thunar (XFCE)
                    subprocess.run(['thunar', folder_path])
                except FileNotFoundError:
                    try:
                        # Try to open with PCManFM (LXDE)
                        subprocess.run(['pcmanfm', folder_path])
                    except FileNotFoundError:
                        print("No supported file explorer found.")
    elif platform.system() == "Darwin":
        # macOS
        subprocess.run(['open', folder_path])
    elif platform.system() == "Windows":
        # Windows
        subprocess.run(['explorer', folder_path])
    else:
        print("Unsupported operating system.")
