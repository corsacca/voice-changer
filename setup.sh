#!/bin/bash
# Setup script for Video Voice Changer
# This script installs all required dependencies

echo "🚀 Setting up Video Voice Changer"
echo "=================================="

# Check if we're on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "📱 Detected macOS"
    
    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        echo "🍺 Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    else
        echo "✅ Homebrew already installed"
    fi
    
    # Install ffmpeg
    echo "🎬 Installing ffmpeg..."
    brew install ffmpeg
    
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "🐧 Detected Linux"
    
    # Update package list
    echo "📦 Updating package list..."
    sudo apt update
    
    # Install ffmpeg
    echo "🎬 Installing ffmpeg..."
    sudo apt install -y ffmpeg
    
else
    echo "❌ Unsupported operating system: $OSTYPE"
    echo "Please install ffmpeg manually"
    exit 1
fi

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8 or later"
    exit 1
else
    echo "✅ Python 3 found: $(python3 --version)"
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 not found. Please install pip"
    exit 1
else
    echo "✅ pip3 found"
fi

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip3 install -r requirements.txt

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Get your ElevenLabs API key from: https://elevenlabs.io/"
echo "2. Set your API key:"
echo "   cp env_example.txt .env"
echo "   # Edit .env and add your actual API key"
echo ""
echo "🎬 Usage examples:"
echo "   # Process a video file:"
echo "   python3 voice_changer.py your_video.mp4"
echo ""
echo "   # List available voices:"
echo "   python3 voice_changer.py --list-voices"
echo ""
echo "✨ Happy creating!" 