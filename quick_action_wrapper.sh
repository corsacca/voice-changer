#!/bin/bash

# Quick Action Wrapper for Voice Changer
# This script is designed to be called from macOS Quick Actions

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to show notifications
show_notification() {
    local title="$1"
    local message="$2"
    local sound="${3:-Blow}"
    
    osascript -e "display notification \"$message\" with title \"$title\" sound name \"$sound\""
}

# Function to show progress dialog
show_progress() {
    local message="$1"
    osascript -e "display dialog \"$message\" with title \"Voice Changer\" buttons {\"OK\"} default button \"OK\" with icon note giving up after 3"
}

# Function to get user input for voice selection
get_voice_selection() {
    local voices="Mark (Default), Rachel, Domi, Bella, Antoni, Elli, Josh, Arnold, Adam, Sam"
    local selected_voice
    
    selected_voice=$(osascript -e "choose from list {\"Mark (Default)\", \"Rachel\", \"Domi\", \"Bella\", \"Antoni\", \"Elli\", \"Josh\", \"Arnold\", \"Adam\", \"Sam\"} with title \"Voice Changer\" with prompt \"Select a voice for the AI:\" default items {\"Mark (Default)\"}")
    
    if [ "$selected_voice" = "false" ]; then
        return 1
    fi
    
    # Map voice names to voice IDs
    case "$selected_voice" in
        "Mark (Default)") echo "UgBBYS2sOqTuMpoF3BR0" ;;
        "Rachel") echo "21m00Tcm4TlvDq8ikWAM" ;;
        "Domi") echo "AZnzlk1XvdvUeBnXmlld" ;;
        "Bella") echo "EXAVITQu4vr4xnSDxMaL" ;;
        "Antoni") echo "ErXwobaYiN019PkySvjV" ;;
        "Elli") echo "MF3mGyEYCl7XYWbV9V6O" ;;
        "Josh") echo "TxGEqnHWrfWFTfGW9XjX" ;;
        "Arnold") echo "VR6AewLTigWG4xSOukaG" ;;
        "Adam") echo "pNInz6obpgDQGcFmaJgB" ;;
        "Sam") echo "yoZ06aMxZJJ28mfd3POQ" ;;
        *) echo "UgBBYS2sOqTuMpoF3BR0" ;;
    esac
}

# Main execution
main() {
    # Set up PATH to include Homebrew and common binary locations
    export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
    
    # Check if a file was provided
    if [ $# -eq 0 ]; then
        show_notification "Voice Changer" "No video file provided"
        exit 1
    fi
    
    local input_file="$1"
    
    # Validate input file
    if [ ! -f "$input_file" ]; then
        show_notification "Voice Changer" "File not found: $input_file"
        exit 1
    fi
    
    # Check if it's a video file
    local file_ext="${input_file##*.}"
    file_ext=$(echo "$file_ext" | tr '[:upper:]' '[:lower:]')
    case "$file_ext" in
        mp4|mov|avi|mkv|webm|m4v)
            ;;
        *)
            show_notification "Voice Changer" "Unsupported file type: $file_ext"
            exit 1
            ;;
    esac
    
    # Get voice selection from user
    local voice_id
    voice_id=$(get_voice_selection)
    if [ $? -ne 0 ]; then
        show_notification "Voice Changer" "Voice selection cancelled"
        exit 1
    fi
    
    # Show starting notification
    show_notification "Voice Changer" "Starting voice change for: $(basename "$input_file")"
    
    # Change to script directory
    cd "$SCRIPT_DIR" || {
        show_notification "Voice Changer" "Failed to change to script directory"
        exit 1
    }
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        show_notification "Voice Changer" "Setting up environment... This may take a moment."
        
        # Run setup script
        if [ -f "setup.sh" ]; then
            bash setup.sh || {
                show_notification "Voice Changer" "Failed to set up environment"
                exit 1
            }
        else
            show_notification "Voice Changer" "Setup script not found"
            exit 1
        fi
    fi
    
    # Activate virtual environment
    source venv/bin/activate || {
        show_notification "Voice Changer" "Failed to activate virtual environment"
        exit 1
    }
    
    # Check for .env file
    if [ ! -f ".env" ]; then
        show_notification "Voice Changer" "Please set up your .env file with ELEVEN_LABS_KEY"
        open "$SCRIPT_DIR"
        exit 1
    fi
    
    # Generate output filename
    local input_basename=$(basename "$input_file")
    local input_name="${input_basename%.*}"
    local input_dir=$(dirname "$input_file")
    local output_file="$input_dir/${input_name}_voice_changed.mp4"
    
    # Show progress
    show_progress "Processing video... This may take several minutes."
    
    # Create a temporary file for output
    local temp_output=$(mktemp)
    
    # Run the voice changer and capture both output and exit code
    python3 voice_changer.py "$input_file" -o "$output_file" -v "$voice_id" 2>&1 | tee "$temp_output"
    local exit_code=${PIPESTATUS[0]}  # Get exit code of python3, not tee
    
    # Process the output for notifications
    while IFS= read -r line; do
        case "$line" in
            *"Step 1:"*) show_notification "Voice Changer" "Extracting audio..." ;;
            *"Step 2:"*) show_notification "Voice Changer" "Transcribing audio..." ;;
            *"Step 3:"*) show_notification "Voice Changer" "Generating AI voice..." ;;
            *"Step 4:"*) show_notification "Voice Changer" "Processing video..." ;;
        esac
    done < "$temp_output"
    
    # Clean up temp file
    rm -f "$temp_output"
    
    if [ $exit_code -eq 0 ] && [ -f "$output_file" ]; then
        show_notification "Voice Changer" "✅ Success! Video saved as: $(basename "$output_file")" "Glass"
        
        # Ask if user wants to open the result
        local open_result
        open_result=$(osascript -e "display dialog \"Voice change complete! Would you like to open the result?\" with title \"Voice Changer\" buttons {\"No\", \"Open Folder\", \"Play Video\"} default button \"Play Video\" with icon note")
        
        case "$open_result" in
            *"Play Video"*) open "$output_file" ;;
            *"Open Folder"*) open "$input_dir" ;;
        esac
    else
        show_notification "Voice Changer" "❌ Voice change failed. Check your .env file and try again." "Basso"
        
        # Show error info in a dialog
        osascript -e "display dialog \"Voice change failed. Please check:\n\n• Your .env file has the correct ELEVEN_LABS_KEY\n• The video file is not corrupted\n• You have a stable internet connection\n\nInput: $(basename "$input_file")\" with title \"Voice Changer Error\" buttons {\"OK\"} default button \"OK\" with icon stop"
    fi
}

# Run main function with all arguments
main "$@" 