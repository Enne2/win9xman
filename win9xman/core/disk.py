"""
Disk image management functions
"""

import subprocess
import tkinter as tk
from tkinter import ttk, messagebox

def create_hdd_image(root, hdd_image, hdd_size):
    """Create a new HDD image file
    
    Args:
        root: The Tkinter root window
        hdd_image: Path to the HDD image file to create
        hdd_size: Size of the HDD in MB
    
    Returns:
        bool: True if the image was created successfully, False otherwise
    """
    # Confirm creation
    if not messagebox.askyesno("Confirm HDD Creation", 
                             f"Create new disk image of {hdd_size}MB?"):
        return False
    
    # Show progress while creating the image
    progress_window = tk.Toplevel(root)
    progress_window.title("Creating HDD Image")
    progress_window.geometry("400x100")
    progress_window.transient(root)
    progress_window.grab_set()
    
    ttk.Label(progress_window, text=f"Creating disk image of {hdd_size}MB...").pack(pady=10)
    progress = ttk.Progressbar(progress_window, mode="indeterminate", length=300)
    progress.pack(pady=10, padx=20)
    progress.start()
    
    result = [False]  # Use list for result
    
    # Schedule the actual creation task
    def create_task():
        try:
            # Create disk image using DOSBox-X's imgmake command
            cmd = ["dosbox-x", "-c", f"imgmake \"{hdd_image}\" -size {hdd_size} -fat 32 -t hd", "-c", "exit"]
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            result[0] = True
            progress_window.destroy()
            messagebox.showinfo("Success", f"Disk image of {hdd_size}MB created successfully.")
        except subprocess.CalledProcessError:
            progress_window.destroy()
            messagebox.showerror("Error", "Failed to create HDD image. Please check your permissions.")
    
    root.after(100, create_task)
    root.wait_window(progress_window)
    
    return result[0]
