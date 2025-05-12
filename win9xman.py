#!/usr/bin/env python3
"""
Windows 9x Manager - A GUI tool to launch Windows 95/98 in DOSBox-X
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys

# Aggiungi la directory corrente al path per importare i moduli locali
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from win9xman.ui.manager import Win9xManager
from win9xman.utils.system import check_requirements

def main():
    """Main entry point for the application"""
    # Check if required dependencies are installed
    if not check_requirements():
        return
        
    root = tk.Tk()
    root.title("Windows 9x Manager")
    
    # Use system theme
    try:
        ttk.Style().theme_use('clam')  # A decent cross-platform theme
    except tk.TclError:
        pass  # If theme not available, use default
    
    # Create the app
    app = Win9xManager(root)
    
    # Add program icon if available
    icon_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "assets", "icon.png")
    if os.path.exists(icon_path):
        img = tk.PhotoImage(file=icon_path)
        root.tk.call('wm', 'iconphoto', root._w, img)
    
    # Start the main loop
    root.mainloop()

if __name__ == "__main__":
    main()
