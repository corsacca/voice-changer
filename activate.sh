#!/bin/bash
# Activation script for Voice Changer virtual environment
# Usage: source activate.sh

echo "🎬 Activating Voice Changer environment..."
source venv/bin/activate

echo "✅ Virtual environment activated!"
echo ""
echo "📋 Available commands:"
echo "  python3 voice_changer.py --help          # Show help"
echo "  python3 voice_changer.py --list-voices   # List available voices"
echo "  python3 voice_changer.py video.mp4       # Process a video"
echo ""
echo "💡 Don't forget to set up your .env file with ELEVEN_LABS_KEY" 