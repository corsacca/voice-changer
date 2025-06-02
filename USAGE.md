# Quick Usage Guide

## Simple Voice Changing Workflow

### 1. Record Your Video
Use any screen recorder you prefer:
- **Maxscreen** (your preferred choice)
- **OBS Studio**
- **QuickTime Player** (macOS)
- **Built-in screen recording** (macOS: Cmd+Shift+5)

### 2. Activate Environment
```bash
source activate.sh
```

### 3. Process Your Video
```bash
# Basic usage (uses Mark voice by default)
python3 voice_changer.py your_video.mp4

# With custom output name
python3 voice_changer.py input.mp4 -o my_ai_voice_video.mp4

# With specific voice (Mark's voice ID shown as example)
python3 voice_changer.py input.mp4 -v "UgBBYS2sOqTuMpoF3BR0"
```

### 4. Check Available Voices
```bash
python3 voice_changer.py --list-voices
```

## What Happens During Processing

1. **Audio Extraction** - Extracts audio from your video
2. **Transcription** - Automatically transcribes your speech using AI
3. **Natural Pause Enhancement** - Adds natural pauses after sentences and commas
4. **Voice Generation** - Creates AI voice with enhanced timing (default: Mark voice)
5. **Smart Duration Matching** - Uses natural spacing instead of stretching
6. **Final Assembly** - Combines naturally-timed AI voice with original video

## Natural Timing Features

The script uses intelligent timing instead of simple stretching:

### **For Long Videos (3x+ longer than speech):**
- Adds strategic silence at the beginning
- Preserves natural AI speech speed
- Fills remaining time with natural pauses

### **For Medium Videos (1.5-3x longer):**
- Adds small initial delay
- Maintains normal speech pace
- Pads with silence at the end

### **For Short Videos (AI speech longer):**
- Gentle speed increase (max 1.4x to preserve quality)
- Avoids garbled/distorted audio
- Maintains natural rhythm

### **For Matched Videos:**
- Minimal adjustment
- Preserves original AI speech timing

## Enhanced Speech Quality

- ✅ **Natural Pauses**: Automatic pauses after sentences (0.8s) and commas (0.3s)
- ✅ **No Stretching**: Avoids slow, garbled speech from over-stretching
- ✅ **Quality Preservation**: Limits speed changes to maintain audio quality
- ✅ **Strategic Silence**: Uses silence instead of distortion to fill time
- ✅ **Default Voice**: Uses Mark voice for natural-sounding speech

## Output

Your processed video will be saved as `[original_name]_voice_changed.mp4`

The output will have:
- ✅ Same duration as original video
- ✅ Natural-sounding AI speech at proper speed (Mark voice by default)
- ✅ Appropriate pauses and timing
- ✅ No garbled or distorted audio

## Tips

- Speak clearly in your recordings
- Use a good microphone if possible
- Keep background noise minimal
- The script preserves natural speech rhythm
- Longer videos will have more natural silence/pauses
- AI voice maintains quality without distortion
- Default Mark voice provides natural-sounding speech 