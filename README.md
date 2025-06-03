# Video Voice Changer

A Python script that processes recorded videos to change your voice using ElevenLabs AI. This tool extracts audio from video files, transcribes the speech, generates AI voice synthesis, and combines it back with the original video.

## Features

- Extract audio from video files
- Automatic speech transcription using Faster Whisper
- AI voice generation using ElevenLabs
- Automatic video speed adjustment - speeds up video to match AI voice timing
- Automatic duration matching - ensures output audio is synced with the video
- Replace original audio with AI-generated voice
- Support for multiple voice options
- Universal compatibility - works with all major video players (QuickTime, VLC, etc.)
- Command-line interface
- **macOS Quick Action** - Right-click on any video file to change voice!

## Prerequisites

### 1. Install System Dependencies

**macOS (using Homebrew):**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

### 2. Install Python Dependencies

```bash
pip3 install -r requirements.txt
```

### 3. Set Up ElevenLabs API Key

1. Sign up at [ElevenLabs](https://elevenlabs.io/)
2. Get your API key from the dashboard
3. **Create a `.env` file** (recommended method):

```bash
# Copy the example file and edit it
cp env_example.txt .env
# Then edit .env and replace 'your_api_key_here' with your actual API key
```

Your `.env` file should look like:
```
ELEVEN_LABS_KEY=your_actual_api_key_here
```

**Alternative: Environment Variable Method**
```bash
export ELEVENLABS_API_KEY="your_api_key_here"
```

Or add it to your shell profile (`.zshrc`, `.bashrc`, etc.):
```bash
echo 'export ELEVENLABS_API_KEY="your_api_key_here"' >> ~/.zshrc
source ~/.zshrc
```

## Quick Setup for macOS Users 🚀

For the easiest experience, set up the **Quick Action** that lets you right-click on any video file:

```bash
./setup_quick_action.sh
```

This will create a macOS Quick Action that allows you to:
- Right-click on any video file in Finder
- Select "Change Voice with AI" from the context menu
- Choose your preferred voice from a dialog
- Get progress notifications during processing
- Automatically open the result when complete

**That's it!** No need to use the command line anymore.

For detailed setup instructions, see [QUICK_ACTION_SETUP.md](QUICK_ACTION_SETUP.md).

## Usage

### Basic Usage

```bash
python3 voice_changer.py your_recording.mp4
```

This will:
1. Extract audio from `your_recording.mp4`
2. Transcribe the speech automatically using Faster Whisper
3. Generate AI voice using the default voice
4. Create `your_recording_voice_changed.mp4`

### Advanced Usage

**Specify output file:**
```bash
python3 voice_changer.py input.mp4 -o output_with_ai_voice.mp4
```

**Use a specific voice:**
```bash
python3 voice_changer.py input.mp4 -v "UgBBYS2sOqTuMpoF3BR0"
```

**List available voices:**
```bash
python3 voice_changer.py --list-voices
```

**Provide API key directly:**
```bash
python3 voice_changer.py input.mp4 --api-key "your_api_key"
```

## Complete Workflow Example

1. **Record your video** using any screen recorder (Maxscreen, OBS, QuickTime, etc.)
2. **Save the video** (e.g., `my_presentation.mp4`)
3. **Run the voice changer:**
   ```bash
   python3 voice_changer.py my_presentation.mp4 -o presentation_with_ai_voice.mp4
   ```
4. **The script will:**
   - Extract audio from your video
   - Automatically transcribe what you said using AI
   - Generate AI voice saying the same text
   - Create a new video with the AI voice

## Troubleshooting

### Common Issues

**1. FFmpeg not found:**
```
Error: Missing required tools: ffmpeg
```
Solution: Install ffmpeg using the instructions above.

**2. ElevenLabs API key not set:**
```
ElevenLabs API key not provided
```
Solution: Create a `.env` file with `ELEVEN_LABS_KEY=your_api_key` or set the `ELEVENLABS_API_KEY` environment variable.

**3. Whisper transcription fails:**
The script will fall back to asking you to manually type the transcript.

**4. Audio extraction fails:**
Make sure your video file is not corrupted and is in a supported format (mp4, mov, avi, etc.).

**5. Video length mismatch:**
The script automatically handles duration differences between original and AI-generated audio by:
- Padding short audio with silence
- Trimming long audio to match video length
- Verifying final output duration matches original

### Supported Video Formats

- MP4 (recommended)
- MOV
- AVI
- MKV
- WebM

### Voice Quality Tips

- Speak clearly during recording
- Minimize background noise
- Use a good microphone if possible
- Choose appropriate ElevenLabs voice for your content

## API Costs

ElevenLabs charges based on character count. Check their pricing at [elevenlabs.io/pricing](https://elevenlabs.io/pricing).

## License

This project is for educational and personal use. Please respect ElevenLabs' terms of service and usage policies. 