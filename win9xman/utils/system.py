"""
System-related utility functions for Win9xManager
"""

import subprocess
from tkinter import messagebox

def check_requirements():
    """Check if required programs are installed"""
    # Check for DOSBox-X
    try:
        subprocess.run(['dosbox-x', '-version'], 
                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        return True
    except FileNotFoundError:
        # Try with flatpak
        try:
            subprocess.run(['flatpak', 'run', 'com.dosbox_x.DOSBox-X', '-version'], 
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            return True
        except FileNotFoundError:
            messagebox.showerror("Error", "DOSBox-X is not installed or not in PATH.\n"
                               "Please install DOSBox-X from https://dosbox-x.com/")
            return False
