# Quick Action Setup Guide

This guide will help you set up a macOS Quick Action that allows you to right-click on any video file and run the voice changer directly from Finder.

## Prerequisites

1. Make sure you have completed the basic setup from the main README.md
2. Ensure you have your `.env` file configured with your ElevenLabs API key
3. Test that the voice changer works from the command line first

## Method 1: Using Automator (Recommended)

### Step 1: Open Automator
1. Press `Cmd + Space` and search for "Automator"
2. Open Automator
3. When prompted, choose "Quick Action" as the workflow type

### Step 2: Configure the Quick Action
1. In the workflow settings at the top:
   - Set "Workflow receives current" to "**files or folders**"
   - Set "in" to "**Finder**"
   - Check "**Image and Video Files**" (this filters to only show the action for video files)

### Step 3: Add the Shell Script Action
1. In the left sidebar, search for "Run Shell Script"
2. Drag "Run Shell Script" to the workflow area
3. Configure the shell script:
   - Set "Shell" to "**/bin/bash**"
   - Set "Pass input" to "**as arguments**"
   - Replace the default script content with the following:

```bash
#!/bin/bash

# Get the absolute path to the voice changer directory
VOICE_CHANGER_DIR="/Users/jd/code/automations/voice-changer"

# Run the quick action wrapper
"$VOICE_CHANGER_DIR/quick_action_wrapper.sh" "$1"
```

**Important**: Replace `/Users/jd/code/automations/voice-changer` with the actual path to your voice-changer directory.

### Step 4: Save the Quick Action
1. Press `Cmd + S` to save
2. Name it "**Change Voice with AI**" (or any name you prefer)
3. The Quick Action will be automatically saved to `~/Library/Services/`

### Step 5: Test the Quick Action
1. Navigate to any video file in Finder
2. Right-click on the video file
3. Look for "Change Voice with AI" in the context menu (it may be under "Quick Actions" submenu)
4. Click it to start the voice changing process

## Method 2: Direct Service Creation (Advanced)

If you prefer to create the service file directly:

1. Create the service directory:
```bash
mkdir -p ~/Library/Services/
```

2. Create the service file at `~/Library/Services/Change Voice with AI.workflow/Contents/document.wflow` with the appropriate plist content.

## Customizing the Quick Action

### Changing the Voice Selection
The Quick Action will prompt you to select a voice each time. You can modify the `quick_action_wrapper.sh` script to:
- Set a default voice (comment out the voice selection dialog)
- Add more voice options
- Remember the last selected voice

### Adding Keyboard Shortcut
1. Go to System Preferences → Keyboard → Shortcuts
2. Select "Services" in the left sidebar
3. Find "Change Voice with AI" and assign a keyboard shortcut

### Customizing File Types
In the Automator workflow settings, you can modify which file types trigger the Quick Action by changing the file type filters.

## Troubleshooting

### Quick Action Doesn't Appear
1. Make sure the Quick Action is saved in `~/Library/Services/`
2. Try logging out and back in, or restart Finder:
   ```bash
   killall Finder
   ```
3. Check that the file types are set correctly in the workflow

### Permission Issues
If you get permission errors:
1. Make sure the wrapper script is executable:
   ```bash
   chmod +x /path/to/voice-changer/quick_action_wrapper.sh
   ```
2. You may need to give Automator or the script access to files in System Preferences → Security & Privacy → Privacy → Files and Folders

### Script Path Issues
Make sure to update the path in the Automator script to point to your actual voice-changer directory:
- Open the Quick Action in Automator (double-click the `.workflow` file)
- Update the `VOICE_CHANGER_DIR` variable to your correct path
- Save the changes

### Environment Setup Issues
If the voice changer fails to run:
1. The wrapper script will automatically run `setup.sh` if the virtual environment doesn't exist
2. Make sure your `.env` file is properly configured
3. Check the notification messages for specific error details

## Features of the Quick Action

- **Voice Selection Dialog**: Choose from popular ElevenLabs voices
- **Progress Notifications**: Get notified at each step of the process
- **Automatic File Naming**: Output files are saved with `_voice_changed` suffix
- **Error Handling**: Clear error messages and automatic troubleshooting
- **Result Options**: Choose to play the video or open the folder when complete

## Removing the Quick Action

To remove the Quick Action:
1. Delete the file: `~/Library/Services/Change Voice with AI.workflow`
2. Or use Automator to open and delete the workflow

## Alternative: Service Menu Entry

If you prefer a more permanent menu entry, you can also:
1. Create an Automator Application instead of a Quick Action
2. Save it in `/Applications` or `~/Applications`
3. Right-click videos and choose "Open With" → your application 