#!/usr/bin/env python3
"""
Windows 9x Manager - A GUI tool to launch Windows 95/98 in DOSBox-X
"""

import os
import sys
import subprocess
import shutil
import time
import configparser
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.simpledialog import askstring
from datetime import datetime
from pathlib import Path
import string

class Win9xManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Windows 9x Manager")
        self.root.geometry("600x450")
        self.root.minsize(600, 450)
        
        # Set up base paths
        self.base_dir = Path(os.path.dirname(os.path.realpath(__file__)))
        self.templates_dir = self.base_dir / "templates"
        self.dosbox_conf = self.base_dir / "config" / "dosbox.conf"
        self.win98_drive = self.base_dir / "win98_drive"
        self.win95_drive = self.base_dir / "win95_drive"
        self.iso_dir = self.base_dir / "iso"
        self.img_dir = self.base_dir / "disks"
        self.win98_hdd = self.img_dir / "win98.img"
        self.win95_hdd = self.img_dir / "win95.img"
        self.snapshot_dir = self.base_dir / "snapshots"
        self.snapshot_win95_dir = self.base_dir / "snapshots_win95"
        
        # Default settings
        self.default_hdd_size = 2000  # Default size in MB for HDD image
        self.min_hdd_size = 500       # Minimum size in MB
        self.max_hdd_size = 4000      # Maximum size in MB
        
        # Current OS selection
        self.current_os = tk.StringVar(value="win98")
        
        # Create necessary directories
        self._create_directories()
        
        # Create UI
        self._create_ui()
    
    def _create_directories(self):
        """Create necessary directories if they don't exist"""
        directories = [
            self.win98_drive,
            self.win95_drive,
            self.iso_dir,
            self.img_dir,
            self.snapshot_dir,
            self.snapshot_win95_dir,
            self.base_dir / "config",
            self.templates_dir
        ]
        
        for directory in directories:
            directory.mkdir(exist_ok=True, parents=True)
            
        # Create default DOSBox-X config if it doesn't exist
        if not self.dosbox_conf.exists():
            self._create_default_config()
    
    def _create_default_config(self):
        """Create a default DOSBox-X configuration file from template"""
        config_dir = self.base_dir / "config"
        config_dir.mkdir(exist_ok=True)
        
        # Check if template exists
        template_path = self.templates_dir / "dosbox_template.conf"
        if not template_path.exists():
            self._create_default_template()
        
        # Create config from template
        template_vars = {
            'memsize': '64',
            'cycles': 'max 80% limit 33000',
            'machine': 'svga_s3',
            'windowresolution': '1024x768',
            'output': 'opengl'
        }
        self._generate_config_from_template('dosbox_template.conf', self.dosbox_conf, template_vars)
    
    def _create_default_template(self):
        """Create the default DOSBox-X template file"""
        template_path = self.templates_dir / "dosbox_template.conf"
        
        # Make sure templates directory exists
        self.templates_dir.mkdir(exist_ok=True, parents=True)
        
        # Write template content
        with open(template_path, 'w') as f:
            f.write("""# DOSBox-X configuration file for Windows 9x Manager

[sdl]
fullscreen=false
fulldouble=true
fullresolution=desktop
windowresolution=${windowresolution}
output=${output}
autolock=true

[dosbox]
language=
machine=${machine}
captures=capture
memsize=${memsize}

[render]
frameskip=0
aspect=true
scaler=normal3x

[cpu]
core=dynamic
cputype=pentium_mmx
cycles=${cycles}
cycleup=500
cycledown=500

[mixer]
nosound=false
rate=44100
blocksize=1024
prebuffer=40

[midi]
mpu401=intelligent
mididevice=default

[sblaster]
sbtype=sb16
sbbase=220
irq=7
dma=1
hdma=5
sbmixer=true
oplmode=auto
oplemu=default
oplrate=44100

[gus]
gus=false
gusrate=44100
gusbase=240
irq1=5
dma1=1

[speaker]
pcspeaker=true
pcrate=44100
tandy=auto
tandyrate=44100
disney=true

[dos]
xms=true
ems=true
umb=true
keyboardlayout=auto

[ipx]
ipx=false
""")
    
    def _generate_config_from_template(self, template_name, output_path, variables):
        """Generate a configuration file from a template with variable substitution
        
        Args:
            template_name: Name of the template file in templates directory
            output_path: Path where to save the generated config
            variables: Dictionary of variables to substitute in the template
        """
        template_path = self.templates_dir / template_name
        
        # Read template content
        if not template_path.exists():
            raise FileNotFoundError(f"Template file {template_path} not found")
        
        with open(template_path, 'r') as f:
            template_content = f.read()
        
        # Use string.Template for variable substitution
        template = string.Template(template_content)
        output_content = template.safe_substitute(variables)
        
        # Write the output file
        with open(output_path, 'w') as f:
            f.write(output_content)
    
    def _create_ui(self):
        """Create the UI elements"""
        # OS Selection frame
        os_frame = ttk.LabelFrame(self.root, text="Select Windows Version")
        os_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Radiobutton(os_frame, text="Windows 98", variable=self.current_os, 
                       value="win98").pack(side=tk.LEFT, padx=20, pady=5)
        ttk.Radiobutton(os_frame, text="Windows 95", variable=self.current_os, 
                       value="win95").pack(side=tk.LEFT, padx=20, pady=5)
        
        # Main actions frame
        actions_frame = ttk.Frame(self.root)
        actions_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create buttons with descriptions
        button_data = [
            ("Start Windows", "Launch Windows if already installed", self.start_windows),
            ("Mount ISO & Start Windows", "Mount ISO as CD-ROM drive and start Windows", self.mount_iso),
            ("Install Windows from ISO", "Boot from ISO to install Windows", self.boot_iso),
            ("Format Hard Disk", "Create or reset disk image", self.format_disk),
            ("Create Snapshot", "Save current system state", self.create_snapshot),
            ("Restore Snapshot", "Restore previous system state", self.restore_snapshot),
            ("Settings", "Configure DOSBox-X settings", self.open_settings),
            ("Exit", "Close the application", self.root.quit)
        ]
        
        for i, (text, desc, command) in enumerate(button_data):
            frame = ttk.Frame(actions_frame)
            frame.pack(fill=tk.X, pady=5)
            
            btn = ttk.Button(frame, text=text, command=command, width=20)
            btn.pack(side=tk.LEFT, padx=5)
            
            ttk.Label(frame, text=desc).pack(side=tk.LEFT, padx=5)
    
    def get_current_hdd(self):
        """Get current HDD path based on selected OS"""
        return self.win98_hdd if self.current_os.get() == "win98" else self.win95_hdd
    
    def get_current_drive_dir(self):
        """Get current drive directory based on selected OS"""
        return self.win98_drive if self.current_os.get() == "win98" else self.win95_drive
    
    def get_snapshot_dir(self):
        """Get snapshot directory based on selected OS"""
        return self.snapshot_dir if self.current_os.get() == "win98" else self.snapshot_win95_dir
    
    def create_hdd_image(self):
        """Create HDD image if it doesn't exist"""
        hdd_image = self.get_current_hdd()
        
        if hdd_image.exists():
            return True
        
        # Create slider dialog for HDD size
        size_dialog = tk.Toplevel(self.root)
        size_dialog.title("Select HDD Size")
        size_dialog.geometry("400x150")
        size_dialog.resizable(False, False)
        size_dialog.transient(self.root)
        size_dialog.grab_set()
        
        ttk.Label(size_dialog, text="Choose the size of your Windows hard disk (MB):").pack(pady=10)
        
        size_var = tk.IntVar(value=self.default_hdd_size)
        slider = ttk.Scale(size_dialog, from_=self.min_hdd_size, to=self.max_hdd_size, 
                          variable=size_var, orient=tk.HORIZONTAL, length=300)
        slider.pack(pady=10, padx=20)
        
        size_label = ttk.Label(size_dialog, text=f"{self.default_hdd_size} MB")
        size_label.pack()
        
        def update_label(*args):
            size_label.config(text=f"{size_var.get()} MB")
        
        slider.bind("<Motion>", update_label)
        
        result = [False]  # Use list to store result (Python 3.x closure behavior)
        
        def on_ok():
            result[0] = True
            size_dialog.destroy()
            
        def on_cancel():
            size_dialog.destroy()
            
        button_frame = ttk.Frame(size_dialog)
        button_frame.pack(fill=tk.X, pady=10)
        ttk.Button(button_frame, text="Create", command=on_ok).pack(side=tk.LEFT, padx=20)
        ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side=tk.RIGHT, padx=20)
        
        self.root.wait_window(size_dialog)
        
        if not result[0]:
            return False
        
        hdd_size = size_var.get()
        
        # Confirm creation
        if not messagebox.askyesno("Confirm HDD Creation", 
                                 f"Create new disk image of {hdd_size}MB?"):
            return False
        
        # Show progress while creating the image
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Creating HDD Image")
        progress_window.geometry("400x100")
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        ttk.Label(progress_window, text=f"Creating disk image of {hdd_size}MB...").pack(pady=10)
        progress = ttk.Progressbar(progress_window, mode="indeterminate", length=300)
        progress.pack(pady=10, padx=20)
        progress.start()
        
        # Schedule the actual creation task
        def create_task():
            try:
                # Create disk image using DOSBox-X's imgmake command
                cmd = ["dosbox-x", "-c", f"imgmake \"{hdd_image}\" -size {hdd_size} -fat 32 -t hd", "-c", "exit"]
                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                progress_window.destroy()
                messagebox.showinfo("Success", f"Disk image of {hdd_size}MB created successfully.")
                return True
            except subprocess.CalledProcessError:
                progress_window.destroy()
                messagebox.showerror("Error", "Failed to create HDD image. Please check your permissions.")
                return False
        
        self.root.after(100, create_task)
        self.root.wait_window(progress_window)
        
        return hdd_image.exists()
    
    def create_temp_config(self, autoexec_content):
        """Create a temporary DOSBox-X configuration file with custom autoexec section"""
        # Make sure the base config exists
        if not self.dosbox_conf.exists():
            self._create_default_config()
        
        # Create a temp config based on current settings
        temp_conf = self.base_dir / "temp_dosbox.conf"
        
        # Read current config to preserve settings
        current_config = {}
        config = configparser.ConfigParser()
        config.read(self.dosbox_conf)
        
        for section in config.sections():
            if section != 'autoexec':
                current_config[section] = dict(config[section])
        
        # Generate the temporary config file from template
        template_vars = {
            'memsize': current_config.get('dosbox', {}).get('memsize', '64'),
            'cycles': current_config.get('cpu', {}).get('cycles', 'max 80% limit 33000'),
            'machine': current_config.get('dosbox', {}).get('machine', 'svga_s3'),
            'windowresolution': current_config.get('sdl', {}).get('windowresolution', '1024x768'),
            'output': current_config.get('sdl', {}).get('output', 'opengl')
        }
        
        # Create temp config
        self._generate_config_from_template('dosbox_template.conf', temp_conf, template_vars)
        
        # Add autoexec section to the generated config
        with open(temp_conf, 'a') as f:
            f.write("\n[autoexec]\n")
            for line in autoexec_content.split('\n'):
                if line.strip():
                    f.write(f"{line}\n")
        
        return temp_conf
    
    def start_windows(self):
        """Start Windows if installed"""
        hdd_image = self.get_current_hdd()
        drive_dir = self.get_current_drive_dir()
        
        # Check if HDD image exists
        if not hdd_image.exists():
            if not messagebox.askyesno("HDD Missing", 
                                     "HDD image not found. Do you want to create one?"):
                return
            
            if not self.create_hdd_image():
                return
        
        # Create autoexec content
        autoexec = f"""
# Mount the Windows HDD image as drive C
imgmount c "{hdd_image}" -t hdd -fs fat
# Mount the local directory as drive E
mount e "{drive_dir}"
boot c:
"""
        
        # Create temporary config
        temp_conf = self.create_temp_config(autoexec)
        
        # Launch DOSBox-X with the config
        try:
            subprocess.run(["dosbox-x", "-conf", temp_conf], check=True)
        finally:
            # Clean up temp config
            if temp_conf.exists():
                temp_conf.unlink()
    
    def mount_iso(self):
        """Mount ISO and start Windows"""
        hdd_image = self.get_current_hdd()
        drive_dir = self.get_current_drive_dir()
        
        # Check if HDD image exists
        if not hdd_image.exists():
            if messagebox.askyesno("HDD Missing", 
                                 "HDD image not found. Do you want to create one?"):
                if not self.create_hdd_image():
                    return
            else:
                return
        
        # Open file dialog to select ISO
        iso_path = filedialog.askopenfilename(
            title="Select ISO file",
            filetypes=[("ISO files", "*.iso")],
            initialdir=self.iso_dir
        )
        
        if not iso_path:
            messagebox.showinfo("Cancelled", "No ISO file selected.")
            return
        
        # Create autoexec content
        autoexec = f"""
# Mount the Windows HDD image as drive C
imgmount c "{hdd_image}" -t hdd -fs fat
# Mount the ISO as drive D
imgmount d "{iso_path}" -t iso
# Mount the local directory as drive E
mount e "{drive_dir}"
boot c:
"""
        
        # Create temporary config
        temp_conf = self.create_temp_config(autoexec)
        
        # Launch DOSBox-X with the config
        try:
            subprocess.run(["dosbox-x", "-conf", temp_conf], check=True)
        finally:
            # Clean up temp config
            if temp_conf.exists():
                temp_conf.unlink()
    
    def boot_iso(self):
        """Boot from ISO to install Windows"""
        hdd_image = self.get_current_hdd()
        
        # Create or confirm HDD image exists
        if not hdd_image.exists():
            if messagebox.askyesno("HDD Missing", 
                                 "HDD image not found. Do you want to create one?"):
                if not self.create_hdd_image():
                    return
            else:
                return
        
        # Open file dialog to select ISO
        iso_path = filedialog.askopenfilename(
            title="Select Windows Installation ISO",
            filetypes=[("ISO files", "*.iso")],
            initialdir=self.iso_dir
        )
        
        if not iso_path:
            messagebox.showinfo("Cancelled", "No ISO file selected.")
            return
        
        # Create autoexec content for booting from ISO
        autoexec = f"""
# Mount the Windows HDD image as drive C
imgmount c "{hdd_image}" -t hdd -fs fat
# Mount the ISO as drive D
imgmount d "{iso_path}" -t iso
# Start the setup program
d:
setup.exe
"""
        
        # Create temporary config
        temp_conf = self.create_temp_config(autoexec)
        
        # Launch DOSBox-X with the config
        try:
            subprocess.run(["dosbox-x", "-conf", temp_conf], check=True)
        finally:
            # Clean up temp config
            if temp_conf.exists():
                temp_conf.unlink()
    
    def format_disk(self):
        """Format hard disk image (creates a new one)"""
        hdd_image = self.get_current_hdd()
        
        if hdd_image.exists():
            if not messagebox.askyesno("Confirm Format", 
                                     "This will delete the existing disk image and create a new blank one.\n"
                                     "All data will be lost.\nDo you want to continue?"):
                return
            
            # Remove existing image
            hdd_image.unlink()
        
        # Create new disk image
        if self.create_hdd_image():
            messagebox.showinfo("Format Complete", 
                              "Format completed. A new blank disk image has been created.")
    
    def create_snapshot(self):
        """Create a snapshot of the current disk image"""
        hdd_image = self.get_current_hdd()
        snapshot_dir = self.get_snapshot_dir()
        
        # Check if HDD image exists
        if not hdd_image.exists():
            messagebox.showerror("Error", "HDD image not found. Cannot create snapshot.")
            return
        
        # Get snapshot name
        snapshot_name = askstring("Create Snapshot", "Enter a name for this snapshot:")
        
        if not snapshot_name:
            return  # User cancelled
        
        # Create valid filename
        snapshot_name = ''.join(c if c.isalnum() or c in '_-' else '_' for c in snapshot_name)
        
        # Add timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_file = snapshot_dir / f"{timestamp}_{snapshot_name}.img"
        
        # Show progress dialog
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Creating Snapshot")
        progress_window.geometry("400x100")
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        ttk.Label(progress_window, text=f"Creating snapshot: {snapshot_name}...").pack(pady=10)
        progress = ttk.Progressbar(progress_window, mode="indeterminate", length=300)
        progress.pack(pady=10, padx=20)
        progress.start()
        
        def copy_task():
            try:
                shutil.copy2(hdd_image, snapshot_file)
                progress_window.destroy()
                messagebox.showinfo("Snapshot Created", 
                                  f"Snapshot '{snapshot_name}' created successfully.\n"
                                  f"Location: {snapshot_file}")
            except Exception as e:
                progress_window.destroy()
                messagebox.showerror("Error", f"Failed to create snapshot: {str(e)}")
        
        self.root.after(100, copy_task)
    
    def restore_snapshot(self):
        """Restore a snapshot"""
        hdd_image = self.get_current_hdd()
        snapshot_dir = self.get_snapshot_dir()
        
        # Check if snapshots exist
        snapshots = list(snapshot_dir.glob("*.img"))
        if not snapshots:
            messagebox.showerror("Error", "No snapshots found.")
            return
        
        # Create snapshot selection dialog
        select_dialog = tk.Toplevel(self.root)
        select_dialog.title("Select Snapshot")
        select_dialog.geometry("500x300")
        select_dialog.transient(self.root)
        select_dialog.grab_set()
        
        ttk.Label(select_dialog, text="Select a snapshot to restore:").pack(pady=10)
        
        # Create a listbox for snapshots
        listbox_frame = ttk.Frame(select_dialog)
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        scrollbar = ttk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        snapshot_listbox = tk.Listbox(listbox_frame)
        snapshot_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        snapshot_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=snapshot_listbox.yview)
        
        # Add snapshots to listbox
        snapshot_paths = []
        for snap in snapshots:
            snapshot_paths.append(snap)
            snapshot_listbox.insert(tk.END, snap.name)
        
        selected_index = [-1]  # Use list for closure
        
        def on_select():
            selected_index[0] = snapshot_listbox.curselection()
            if selected_index[0]:
                select_dialog.destroy()
            
        def on_cancel():
            selected_index[0] = -1
            select_dialog.destroy()
        
        button_frame = ttk.Frame(select_dialog)
        button_frame.pack(fill=tk.X, pady=10)
        ttk.Button(button_frame, text="Restore", command=on_select).pack(side=tk.LEFT, padx=20)
        ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side=tk.RIGHT, padx=20)
        
        self.root.wait_window(select_dialog)
        
        # Check if user selected something
        if selected_index[0] == -1 or not selected_index[0]:
            return
        
        selected_snapshot = snapshot_paths[selected_index[0][0]]
        
        # Confirm restore
        if not messagebox.askyesno("Confirm Restore", 
                                 "This will replace your current disk image with the selected snapshot.\n"
                                 "All unsaved changes will be lost.\n\nContinue?"):
            return
        
        # Show progress dialog
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Restoring Snapshot")
        progress_window.geometry("400x100")
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        ttk.Label(progress_window, text="Restoring snapshot...").pack(pady=10)
        progress = ttk.Progressbar(progress_window, mode="indeterminate", length=300)
        progress.pack(pady=10, padx=20)
        progress.start()
        
        def restore_task():
            try:
                # Create backup of current image
                backup_file = None
                if hdd_image.exists():
                    backup_file = hdd_image.with_suffix('.img.bak')
                    shutil.copy2(hdd_image, backup_file)
                
                # Copy snapshot to disk image location
                shutil.copy2(selected_snapshot, hdd_image)
                
                # Remove backup if restoration was successful
                if backup_file and backup_file.exists():
                    backup_file.unlink()
                
                progress_window.destroy()
                messagebox.showinfo("Snapshot Restored", "Snapshot restored successfully.")
            
            except Exception as e:
                progress_window.destroy()
                messagebox.showerror("Error", f"Failed to restore snapshot: {str(e)}")
                
                # Try to restore backup
                if backup_file and backup_file.exists() and not hdd_image.exists():
                    shutil.copy2(backup_file, hdd_image)
                    backup_file.unlink()
        
        self.root.after(100, restore_task)
    
    def open_settings(self):
        """Open DOSBox-X settings editor"""
        if not self.dosbox_conf.exists():
            self._create_default_config()
            
        # Create settings dialog
        settings_dialog = tk.Toplevel(self.root)
        settings_dialog.title("DOSBox-X Settings")
        settings_dialog.geometry("600x400")
        settings_dialog.transient(self.root)
        settings_dialog.grab_set()
        
        # Read current configuration
        config = configparser.ConfigParser()
        config.read(self.dosbox_conf)
        
        # Create a notebook for different configuration sections
        notebook = ttk.Notebook(settings_dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create frames for important config sections
        sections = {
            'System': ['dosbox', 'cpu', 'dos'],
            'Graphics': ['sdl', 'render'],
            'Sound': ['mixer', 'sblaster', 'midi'],
        }
        
        # Track all setting variables
        setting_vars = {}
        
        for section_name, config_sections in sections.items():
            frame = ttk.Frame(notebook)
            notebook.add(frame, text=section_name)
            
            # Add settings for each configuration section
            row = 0
            for config_section in config_sections:
                if config_section in config:
                    ttk.Label(frame, text=f"[{config_section}]", font=("", 11, "bold")).grid(
                        row=row, column=0, columnspan=2, sticky="w", padx=5, pady=(10, 5))
                    row += 1
                    
                    # Add each option in the section
                    for option in config[config_section]:
                        ttk.Label(frame, text=f"{option}:").grid(
                            row=row, column=0, sticky="w", padx=5, pady=2)
                        
                        # Create variable for this setting
                        var = tk.StringVar(value=config[config_section][option])
                        setting_vars[(config_section, option)] = var
                        
                        entry = ttk.Entry(frame, textvariable=var, width=30)
                        entry.grid(row=row, column=1, sticky="w", padx=5, pady=2)
                        
                        row += 1
        
        # Create buttons frame
        button_frame = ttk.Frame(settings_dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def save_settings():
            # Update config with values from variables
            for (section, option), var in setting_vars.items():
                config[section][option] = var.get()
            
            # Save configuration
            with open(self.dosbox_conf, 'w') as f:
                config.write(f)
            
            settings_dialog.destroy()
            messagebox.showinfo("Success", "Settings saved successfully")
        
        def cancel():
            settings_dialog.destroy()
        
        ttk.Button(button_frame, text="Save", command=save_settings).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=cancel).pack(side=tk.RIGHT, padx=5)
        
        # Alternative: open in text editor
        def open_in_editor():
            settings_dialog.destroy()
            
            # Check if system has a GUI text editor
            editors = [
                ('xdg-open', [str(self.dosbox_conf)]),  # Linux
                ('notepad.exe', [str(self.dosbox_conf)]),  # Windows
                ('open', ['-t', str(self.dosbox_conf)])  # macOS
            ]
            
            for editor, args in editors:
                try:
                    subprocess.run([editor] + args)
                    break
                except (subprocess.SubprocessError, FileNotFoundError):
                    continue
            else:
                messagebox.showerror("Error", f"Could not open editor. The config file is at:\n{self.dosbox_conf}")
        
        ttk.Button(button_frame, text="Open in Text Editor", command=open_in_editor).pack(side=tk.LEFT, padx=5)

def check_requirements():
    """Check if required programs are installed"""
    # Check for DOSBox-X
    try:
        subprocess.run(['flatpak run com.dosbox_x.DOSBox-X', '-version'], 
                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    except FileNotFoundError:
        tk.messagebox.showerror("Error", "DOSBox-X is not installed or not in PATH.\n"
                             "Please install DOSBox-X from https://dosbox-x.com/")
        return False
    
    return True

def main():
        
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
