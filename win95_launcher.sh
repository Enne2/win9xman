#!/bin/bash

# Win95 DOSBox-X Launcher
# A GUI tool to launch Windows 95 in DOSBox-X with different scenarios

# Check if zenity is installed
if ! command -v zenity &> /dev/null; then
    echo "Zenity is not installed. Please install it using:"
    echo "sudo apt-get install zenity"
    exit 1
fi

# Base directory
BASE_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
DOSBOX_CONF="$BASE_DIR/dosbox.conf"
WIN95_DRIVE="$BASE_DIR/win95_drive"
ISO_DIR="$BASE_DIR/iso"
IMG_DIR="$BASE_DIR/disks"
HDD_IMAGE="$IMG_DIR/win95.img"
SNAPSHOT_DIR="$BASE_DIR/snapshots_win95"
DEFAULT_HDD_SIZE=1000  # Default size in MB for HDD image (smaller for Win95)
MIN_HDD_SIZE=300       # Minimum size in MB (Win95 needs less space)
MAX_HDD_SIZE=2000      # Maximum size in MB

# Make sure directories exist
mkdir -p "$WIN95_DRIVE" "$ISO_DIR" "$IMG_DIR" "$SNAPSHOT_DIR"

# Function to create HDD image if it doesn't exist
create_hdd_image() {
    if [ ! -f "$HDD_IMAGE" ]; then
        # Let user choose the size with slider
        HDD_SIZE=$(zenity --scale --title="Select HDD Size" \
            --text="Choose the size of your Windows 95 hard disk (MB):" \
            --min-value=$MIN_HDD_SIZE --max-value=$MAX_HDD_SIZE --value=$DEFAULT_HDD_SIZE \
            --step=100)
        
        # Check if user cancelled the dialog
        if [ $? -ne 0 ]; then
            return 1
        fi
        
        # If no size was selected, use default
        if [ -z "$HDD_SIZE" ]; then
            HDD_SIZE=$DEFAULT_HDD_SIZE
        fi
        
        zenity --question --text="Create new disk image of ${HDD_SIZE}MB?" --title="Confirm HDD Creation" --ok-label="Yes" --cancel-label="No"
        if [ $? -ne 0 ]; then
            return 1
        fi
        
        # Show progress dialog while creating the image
        (
            echo "# Creating disk image of ${HDD_SIZE}MB..."
            # Create disk image using DOSBox-X's imgmake command
            dosbox-x -c "imgmake \"$HDD_IMAGE\" -size ${HDD_SIZE} -fat 16 -t hd" > /dev/null 2>&1
            if [ $? -ne 0 ]; then
                zenity --error --text="Failed to create HDD image. Please check your permissions."
                return 1
            fi

            echo "100"
            echo "# Disk image created successfully!"
        ) | zenity --progress --title="Creating HDD Image" --text="Creating disk image..." --percentage=0 --auto-close --no-cancel
        
        return 0
    fi
    return 0
}

# Function to create temporary config file based on scenario
create_temp_config() {
    local autoexec_content="$1"
    local temp_conf="$BASE_DIR/temp_dosbox_win95.conf"
    
    # Copy the original config file
    cp "$DOSBOX_CONF" "$temp_conf"
    
    # Replace the [autoexec] section
    sed -i '/\[autoexec\]/,$ d' "$temp_conf"
    echo "[autoexec]" >> "$temp_conf"
    echo "$autoexec_content" >> "$temp_conf"
    
    echo "$temp_conf"
}

# Function to start Windows 95 if installed
start_win95() {
    # Check if HDD image exists
    if [ ! -f "$HDD_IMAGE" ]; then
        zenity --error --text="HDD image not found. Please create one first."
        return
    fi
    
    local autoexec=$(cat << EOF
# Mount the Windows 95 HDD image as drive C
imgmount c "$HDD_IMAGE" -t hdd -fs fat
c:
# Start Windows 95
win
EOF
)
    local temp_conf=$(create_temp_config "$autoexec")
    dosbox-x -conf "$temp_conf"
    rm "$temp_conf"
}

# Function to browse and mount an ISO
mount_iso() {
    # Check if HDD image exists
    if [ ! -f "$HDD_IMAGE" ]; then
        if ! create_hdd_image; then
            return
        fi
    fi
    
    local iso_path=$(zenity --file-selection --title="Select ISO file" --file-filter="ISO files (*.iso) | *.iso" --filename="$ISO_DIR/")
    
    if [ -z "$iso_path" ]; then
        zenity --error --text="No ISO file selected."
        return
    fi
    
    local autoexec=$(cat << EOF
# Mount the Windows 95 HDD image as drive C
imgmount c "$HDD_IMAGE" -t hdd -fs fat

# Mount the ISO as drive D
imgmount d "$iso_path" -t iso

c:
EOF
)
    local temp_conf=$(create_temp_config "$autoexec")
    dosbox-x -conf "$temp_conf"
    rm "$temp_conf"
}

# Function to boot from ISO
boot_iso() {
    # Check if we should create a new HDD image
    if [ ! -f "$HDD_IMAGE" ]; then
        if ! create_hdd_image; then
            return
        fi
    fi
    
    local iso_path=$(zenity --file-selection --title="Select Windows 95 Installation ISO" --file-filter="ISO files (*.iso) | *.iso" --filename="$ISO_DIR/")
    
    if [ -z "$iso_path" ]; then
        zenity --error --text="No ISO file selected."
        return
    fi
    
    local autoexec=$(cat << EOF
# Mount the Windows 95 HDD image as drive C
imgmount c "$HDD_IMAGE" -t hdd -fs fat

# Mount the ISO as drive D
imgmount d "$iso_path" -t iso
# Run the setup program
d:
# Start the Windows 95 setup (might be different paths for different Win95 CDs)
if exist setup.exe setup.exe
if exist win95\setup.exe cd win95 && setup.exe
EOF
)
    local temp_conf=$(create_temp_config "$autoexec")
    dosbox-x -conf "$temp_conf"
    rm "$temp_conf"
}

# Function to format C drive (the disk image)
format_c() {
    # Check if HDD image exists
    if [ ! -f "$HDD_IMAGE" ]; then
        if ! create_hdd_image; then
            return
        fi
        zenity --info --text="New disk image created. It's already blank and ready to use."
        return
    fi
    
    local confirm=$(zenity --question --text="This will delete the existing disk image and create a new blank one.\nAll data will be lost.\nDo you want to continue?" --title="Confirm Format" --ok-label="Yes" --cancel-label="No")
    
    if [ $? -ne 0 ]; then
        return
    fi
    
    # Remove existing image
    rm -f "$HDD_IMAGE"
    
    # Create new image with user-selected size
    create_hdd_image
    
    if [ $? -eq 0 ]; then
        zenity --info --text="Format completed. A new blank disk image has been created."
    fi
}

# Function to create a snapshot of the current disk image
create_snapshot() {
    # Check if HDD image exists
    if [ ! -f "$HDD_IMAGE" ]; then
        zenity --error --text="HDD image not found. Cannot create snapshot."
        return 1
    fi
    
    # Get snapshot name from user
    local snapshot_name=$(zenity --entry --title="Create Snapshot" \
        --text="Enter a name for this snapshot:" \
        --entry-text="Windows95_Snapshot")
    
    # Check if user cancelled
    if [ $? -ne 0 ] || [ -z "$snapshot_name" ]; then
        return 1
    fi
    
    # Create a valid filename (replace spaces and special chars)
    snapshot_name=$(echo "$snapshot_name" | tr ' ' '_' | tr -cd '[:alnum:]_-')
    
    # Add timestamp to snapshot name to make it unique
    local timestamp=$(date "+%Y%m%d_%H%M%S")
    local snapshot_file="$SNAPSHOT_DIR/${timestamp}_${snapshot_name}.img"
    
    # Show progress while copying the image
    (
        echo "# Creating snapshot: $snapshot_name..."
        cp "$HDD_IMAGE" "$snapshot_file"
        if [ $? -ne 0 ]; then
            zenity --error --text="Failed to create snapshot. Check disk space and permissions."
            return 1
        fi
        echo "100"
        echo "# Snapshot created successfully!"
    ) | zenity --progress --title="Creating Snapshot" --text="Creating snapshot..." --percentage=0 --auto-close --no-cancel
    
    zenity --info --title="Snapshot Created" --text="Snapshot '$snapshot_name' created successfully.\nLocation: $snapshot_file"
    return 0
}

# Function to restore a snapshot
restore_snapshot() {
    # Check if snapshots directory exists and has at least one snapshot
    if [ ! -d "$SNAPSHOT_DIR" ] || [ -z "$(ls -A "$SNAPSHOT_DIR")" ]; then
        zenity --error --text="No snapshots found."
        return 1
    fi
    
    # Create a list of available snapshots
    local snapshots=()
    for snap in "$SNAPSHOT_DIR"/*.img; do
        local snap_name=$(basename "$snap")
        snapshots+=("$snap" "$snap_name")
    done
    
    # Let user select a snapshot
    local selected_snapshot=$(zenity --list --title="Restore Snapshot" \
        --text="Select a snapshot to restore:" \
        --column="Path" --column="Snapshot Name" \
        "${snapshots[@]}" \
        --hide-column=1 --width=500 --height=300)
    
    # Check if user cancelled
    if [ $? -ne 0 ] || [ -z "$selected_snapshot" ]; then
        return 1
    fi
    
    # Confirm before restoring
    zenity --question --title="Confirm Restore" \
        --text="This will replace your current disk image with the selected snapshot.\nAll unsaved changes will be lost.\n\nContinue?" \
        --ok-label="Restore" --cancel-label="Cancel"
    
    if [ $? -ne 0 ]; then
        return 1
    fi
    
    # Show progress while restoring the snapshot
    (
        echo "# Restoring snapshot..."
        # Create backup of current image first
        if [ -f "$HDD_IMAGE" ]; then
            mv "$HDD_IMAGE" "${HDD_IMAGE}.bak"
        fi
        
        # Copy the snapshot to the disk image location
        cp "$selected_snapshot" "$HDD_IMAGE"
        if [ $? -ne 0 ]; then
            zenity --error --text="Failed to restore snapshot. Check permissions."
            # Try to restore the backup
            if [ -f "${HDD_IMAGE}.bak" ]; then
                mv "${HDD_IMAGE}.bak" "$HDD_IMAGE"
            fi
            return 1
        fi
        
        # Remove backup if restore was successful
        rm -f "${HDD_IMAGE}.bak"
        
        echo "100"
        echo "# Snapshot restored successfully!"
    ) | zenity --progress --title="Restoring Snapshot" --text="Restoring snapshot..." --percentage=0 --auto-close --no-cancel
    
    zenity --info --title="Snapshot Restored" --text="Snapshot restored successfully."
    return 0
}

# Function to tune DOSBox-X settings for optimal Windows 95 performance
tune_settings() {
    local choice=$(zenity --list --title="Tune Windows 95 Settings" \
        --text="Select a performance profile:" \
        --column="Profile" --column="Description" \
        1 "Standard (Balanced settings)" \
        2 "Fast (Better performance but less accurate)" \
        3 "Accurate (Slower but more accurate emulation)" \
        --width=500 --height=200)
    
    if [ -z "$choice" ]; then
        return
    fi
    
    local temp_conf="$BASE_DIR/temp_config_tune.conf"
    cp "$DOSBOX_CONF" "$temp_conf"
    
    case "$choice" in
        1) # Standard profile
            sed -i 's/^cycles=.*/cycles=max 80% limit 15000/' "$temp_conf"
            sed -i 's/^core=.*/core=normal/' "$temp_conf"
            ;;
        2) # Fast profile
            sed -i 's/^cycles=.*/cycles=max 100% limit 30000/' "$temp_conf"
            sed -i 's/^core=.*/core=dynamic/' "$temp_conf"
            ;;
        3) # Accurate profile
            sed -i 's/^cycles=.*/cycles=max 70% limit 10000/' "$temp_conf"
            sed -i 's/^core=.*/core=normal/' "$temp_conf"
            ;;
    esac
    
    # Ask if user wants to make the changes permanent
    zenity --question --title="Save Changes" \
        --text="Would you like to make these settings permanent?\nIf you select 'No', the changes will only apply to the next session." \
        --ok-label="Yes" --cancel-label="No"
    
    if [ $? -eq 0 ]; then
        cp "$temp_conf" "$DOSBOX_CONF"
        zenity --info --title="Settings Saved" --text="Performance settings have been saved."
    else
        zenity --info --title="Temporary Settings" --text="Settings will be applied for the next session only."
    fi
}

# Main menu function
main_menu() {
    while true; do
        local choice=$(zenity --list --title="Windows 95 DOSBox-X Launcher" \
            --text="Select an option:" \
            --column="Option" --column="Description" \
            1 "Start Windows 95 (if installed)" \
            2 "Mount ISO and start Windows 95" \
            3 "Boot from Windows 95 ISO (for installation)" \
            4 "Format C: drive" \
            5 "Create snapshot of current disk image" \
            6 "Restore snapshot" \
            7 "Tune performance settings" \
            8 "Exit" \
            --width=500 --height=380)
        
        case "$choice" in
            1) start_win95 ;;
            2) mount_iso ;;
            3) boot_iso ;;
            4) format_c ;;
            5) create_snapshot ;;
            6) restore_snapshot ;;
            7) tune_settings ;;
            8|"") exit 0 ;;
        esac
    done
}

# Start the main menu
main_menu
