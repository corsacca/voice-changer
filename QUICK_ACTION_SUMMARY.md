# Quick Action Summary

## 🎯 What is this?

A macOS Quick Action that lets you **right-click on any video file** and change the voice using AI - no command line needed!

## 🚀 Setup (One Time)

1. Make sure you have your `.env` file set up with your ElevenLabs API key
2. Run this command in Terminal:
   ```bash
   cd /path/to/voice-changer
   ./setup_quick_action.sh
   ```

## 🎬 How to Use

1. **Find any video file** in Finder (MP4, MOV, etc.)
2. **Right-click** on the video file
3. **Select "Change Voice with AI"** from the context menu
4. **Choose a voice** from the dialog that appears
5. **Wait for notifications** showing progress
6. **Done!** The new video will be saved with `_voice_changed` in the filename

## 🔧 Troubleshooting

- **Can't see the Quick Action?** Try restarting Finder: `killall Finder`
- **Getting errors?** Check that your `.env` file has the correct API key
- **Need help?** See `QUICK_ACTION_SETUP.md` for detailed instructions

## ✨ Features

- Voice selection dialog
- Progress notifications
- Automatic file naming
- Opens result when complete
- Error handling with helpful messages

That's it! Super simple to use once set up. 