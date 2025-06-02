#!/usr/bin/env python3
"""
Video Voice Changer Script
Processes recorded videos to change voice using ElevenLabs AI
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path
import argparse
from typing import Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    print("Warning: python-dotenv not installed. Install with: pip install python-dotenv")

try:
    from elevenlabs import generate, set_api_key, voices
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False
    print("Warning: elevenlabs package not installed. Install with: pip install elevenlabs")

class VideoVoiceChanger:
    def __init__(self, elevenlabs_api_key: Optional[str] = None):
        """Initialize the voice changer with ElevenLabs API key."""
        # Try to get API key from multiple sources
        if elevenlabs_api_key is None:
            # First try ELEVEN_LABS_KEY from .env file
            elevenlabs_api_key = os.getenv("ELEVEN_LABS_KEY")
            # Fallback to ELEVENLABS_API_KEY for backward compatibility
            if elevenlabs_api_key is None:
                elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        
        self.elevenlabs_api_key = elevenlabs_api_key
        if elevenlabs_api_key and ELEVENLABS_AVAILABLE:
            set_api_key(elevenlabs_api_key)
        
        # Check for required tools
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check if required tools are installed."""
        required_tools = ['ffmpeg', 'ffprobe']
        missing_tools = []
        
        for tool in required_tools:
            if not self._command_exists(tool):
                missing_tools.append(tool)
        
        if missing_tools:
            print(f"Error: Missing required tools: {', '.join(missing_tools)}")
            print("Install ffmpeg (includes ffprobe) with: brew install ffmpeg")
            sys.exit(1)
    
    def _command_exists(self, command: str) -> bool:
        """Check if a command exists in the system PATH."""
        try:
            subprocess.run(['which', command], check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def extract_audio(self, video_path: str, audio_path: str) -> bool:
        """Extract audio from video file."""
        try:
            cmd = [
                'ffmpeg', '-i', video_path,
                '-vn',  # No video
                '-acodec', 'pcm_s16le',  # Uncompressed audio
                '-ar', '44100',  # Sample rate
                '-ac', '2',  # Stereo
                '-y',  # Overwrite output file
                audio_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error extracting audio: {result.stderr}")
                return False
            
            print(f"Audio extracted to: {audio_path}")
            return True
            
        except Exception as e:
            print(f"Error extracting audio: {e}")
            return False
    
    def transcribe_audio(self, audio_path: str) -> Optional[dict]:
        """Transcribe audio to text with timing information using whisper."""
        # Try faster-whisper first (more compatible)
        try:
            from faster_whisper import WhisperModel
            
            print("Using faster-whisper for transcription...")
            model = WhisperModel("base", device="cpu", compute_type="int8")
            segments, info = model.transcribe(audio_path, beam_size=5)
            
            transcript_data = {
                'full_text': '',
                'segments': [],
                'total_duration': 0
            }
            
            for segment in segments:
                transcript_data['segments'].append({
                    'text': segment.text.strip(),
                    'start': segment.start,
                    'end': segment.end,
                    'duration': segment.end - segment.start
                })
                transcript_data['full_text'] += segment.text + " "
                transcript_data['total_duration'] = max(transcript_data['total_duration'], segment.end)
            
            transcript_data['full_text'] = transcript_data['full_text'].strip()
            
            if transcript_data['full_text']:
                print(f"Transcription: {transcript_data['full_text']}")
                print(f"Found {len(transcript_data['segments'])} segments over {transcript_data['total_duration']:.2f} seconds")
                return transcript_data
                
        except ImportError:
            print("faster-whisper not available, trying openai-whisper...")
        except Exception as e:
            print(f"Error with faster-whisper: {e}")
        
        # Fallback to openai-whisper with timing
        try:
            import whisper
            print("Using openai-whisper for transcription...")
            
            model = whisper.load_model("base")
            result = model.transcribe(audio_path)
            
            transcript_data = {
                'full_text': result['text'].strip(),
                'segments': [],
                'total_duration': 0
            }
            
            for segment in result['segments']:
                transcript_data['segments'].append({
                    'text': segment['text'].strip(),
                    'start': segment['start'],
                    'end': segment['end'],
                    'duration': segment['end'] - segment['start']
                })
                transcript_data['total_duration'] = max(transcript_data['total_duration'], segment['end'])
            
            if transcript_data['full_text']:
                print(f"Transcription: {transcript_data['full_text']}")
                print(f"Found {len(transcript_data['segments'])} segments over {transcript_data['total_duration']:.2f} seconds")
                return transcript_data
                
        except ImportError:
            print("OpenAI Whisper not found. Install with: pip install openai-whisper")
        except Exception as e:
            print(f"Error with openai-whisper: {e}")
        
        # Fallback: ask user for transcript (without timing)
        print("\nAutomatic transcription failed. Please provide the text you spoke in the video:")
        transcript = input("Enter transcript: ").strip()
        if transcript:
            # Estimate timing based on average speech rate (150 words per minute)
            words = transcript.split()
            estimated_duration = len(words) / 150 * 60  # Convert to seconds
            
            return {
                'full_text': transcript,
                'segments': [{
                    'text': transcript,
                    'start': 0,
                    'end': estimated_duration,
                    'duration': estimated_duration
                }],
                'total_duration': estimated_duration
            }
        return None
    
    def generate_ai_voice_with_timing(self, transcript_data: dict, voice_id: str = "UgBBYS2sOqTuMpoF3BR0", output_path: str = None) -> Optional[str]:
        """Generate AI voice that matches the timing of the original audio."""
        if not ELEVENLABS_AVAILABLE:
            print("ElevenLabs package not available. Please install with: pip install elevenlabs")
            return None
        
        if not self.elevenlabs_api_key:
            print("ElevenLabs API key not provided.")
            print("Add ELEVEN_LABS_KEY to your .env file or get one from: https://elevenlabs.io/")
            return None
        
        try:
            print(f"Generating AI voice with timing for: {transcript_data['full_text'][:50]}...")
            
            # Create enhanced text with strategic pauses based on original timing
            enhanced_text = self._create_timed_text(transcript_data)
            print("Created timed text with pauses matching original speech")
            
            # Generate audio with enhanced text
            audio = generate(
                text=enhanced_text,
                voice=voice_id,
                model="eleven_monolingual_v1"
            )
            
            # Save to file
            if output_path is None:
                output_path = tempfile.mktemp(suffix='.mp3')
            
            with open(output_path, 'wb') as f:
                f.write(audio)
            
            print(f"AI voice generated: {output_path}")
            
            # Now stretch the audio to match original timing
            stretched_path = self._stretch_audio_to_match_timing(output_path, transcript_data)
            if stretched_path:
                return stretched_path
            else:
                return output_path
            
        except Exception as e:
            print(f"Error generating AI voice: {e}")
            return None
    
    def _create_timed_text(self, transcript_data: dict) -> str:
        """Create text with strategic pauses based on original timing."""
        import re
        
        if not transcript_data['segments'] or len(transcript_data['segments']) == 1:
            # Single segment or no timing info - use basic pause insertion
            text = transcript_data['full_text']
            # Add longer pauses for better timing match
            text = re.sub(r'([.!?])\s+', r'\1 <break time="1.2s"/> ', text)
            text = re.sub(r'(,)\s+', r'\1 <break time="0.6s"/> ', text)
            text = re.sub(r'([;:])\s+', r'\1 <break time="0.8s"/> ', text)
            return f'<break time="0.8s"/> {text} <break time="1.0s"/>'
        
        # Multiple segments - add pauses between them based on gaps
        enhanced_text = '<break time="0.5s"/> '
        
        for i, segment in enumerate(transcript_data['segments']):
            # Add the segment text with internal pauses
            segment_text = segment['text']
            segment_text = re.sub(r'([.!?])\s+', r'\1 <break time="0.8s"/> ', segment_text)
            segment_text = re.sub(r'(,)\s+', r'\1 <break time="0.4s"/> ', segment_text)
            
            enhanced_text += segment_text
            
            # Add pause between segments based on gap to next segment
            if i < len(transcript_data['segments']) - 1:
                next_segment = transcript_data['segments'][i + 1]
                gap = next_segment['start'] - segment['end']
                
                if gap > 2.0:
                    enhanced_text += ' <break time="2.0s"/> '
                elif gap > 1.0:
                    enhanced_text += f' <break time="{gap:.1f}s"/> '
                elif gap > 0.3:
                    enhanced_text += ' <break time="0.8s"/> '
                else:
                    enhanced_text += ' <break time="0.4s"/> '
        
        enhanced_text += ' <break time="0.8s"/>'
        return enhanced_text
    
    def _stretch_audio_to_match_timing(self, audio_path: str, transcript_data: dict) -> Optional[str]:
        """Stretch generated audio to match original timing using ffmpeg."""
        try:
            # Get duration of generated audio
            generated_duration = self._get_media_duration(audio_path)
            original_duration = transcript_data['total_duration']
            
            if not generated_duration or not original_duration:
                print("Could not determine durations for timing adjustment")
                return audio_path
            
            print(f"Generated audio: {generated_duration:.2f}s, Original: {original_duration:.2f}s")
            
            # Calculate stretch ratio (we want to slow down the AI voice)
            stretch_ratio = original_duration / generated_duration
            
            # Limit stretch ratio to reasonable bounds (0.5x to 2.0x speed)
            if stretch_ratio < 0.5:
                stretch_ratio = 0.5
                print("⚠️  Limiting stretch ratio to 0.5x (maximum speedup)")
            elif stretch_ratio > 2.0:
                stretch_ratio = 2.0
                print("⚠️  Limiting stretch ratio to 2.0x (maximum slowdown)")
            
            print(f"Applying stretch ratio: {stretch_ratio:.2f}x (slowing down AI voice)")
            
            # Create stretched audio file
            stretched_path = audio_path.replace('.mp3', '_stretched.mp3')
            
            # Use atempo filter to adjust speed (inverse of stretch ratio)
            tempo_ratio = 1.0 / stretch_ratio
            tempo_filter = self._create_tempo_filter(tempo_ratio)
            
            if not tempo_filter:
                print("No tempo adjustment needed")
                return audio_path
            
            cmd = [
                'ffmpeg', '-i', audio_path,
                '-af', tempo_filter,
                '-y', stretched_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error stretching audio: {result.stderr}")
                return audio_path
            
            # Verify the stretched duration
            stretched_duration = self._get_media_duration(stretched_path)
            if stretched_duration:
                print(f"Stretched audio duration: {stretched_duration:.2f}s")
                if abs(stretched_duration - original_duration) < 0.5:
                    print("✅ Audio timing successfully matched!")
                else:
                    print(f"⚠️  Timing difference: {abs(stretched_duration - original_duration):.2f}s")
            
            return stretched_path
            
        except Exception as e:
            print(f"Error stretching audio: {e}")
            return audio_path
    
    def list_available_voices(self):
        """List available ElevenLabs voices."""
        if not ELEVENLABS_AVAILABLE or not self.elevenlabs_api_key:
            print("ElevenLabs not available or API key not set.")
            print("Add ELEVEN_LABS_KEY to your .env file")
            return
        
        try:
            voice_list = voices()
            print("\nAvailable voices:")
            for voice in voice_list:
                print(f"- {voice.name}: {voice.voice_id}")
        except Exception as e:
            print(f"Error listing voices: {e}")
    
    def _get_media_duration(self, media_path: str) -> Optional[float]:
        """Get duration of media file in seconds."""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                '-of', 'csv=p=0', media_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return float(result.stdout.strip())
        except (ValueError, subprocess.CalledProcessError):
            pass
        return None
    
    def _create_tempo_filter(self, speed_ratio: float) -> str:
        """Create an audio tempo filter that can handle any speed ratio."""
        if speed_ratio == 1.0:
            return ""
        
        # atempo filter has limits: 0.5 <= tempo <= 2.0
        # For ratios outside this range, we need to chain multiple filters
        filters = []
        remaining_ratio = speed_ratio
        
        while remaining_ratio > 2.0:
            filters.append("atempo=2.0")
            remaining_ratio /= 2.0
        
        while remaining_ratio < 0.5:
            filters.append("atempo=0.5")
            remaining_ratio /= 0.5
        
        if remaining_ratio != 1.0:
            filters.append(f"atempo={remaining_ratio:.3f}")
        
        return ",".join(filters)
    
    def _add_natural_pauses(self, text: str) -> str:
        """Add natural pause markers to text for more realistic speech timing."""
        import re
        
        # Add pauses after sentences
        text = re.sub(r'([.!?])\s+', r'\1 <break time="0.8s"/> ', text)
        
        # Add shorter pauses after commas
        text = re.sub(r'(,)\s+', r'\1 <break time="0.3s"/> ', text)
        
        # Add pauses after colons and semicolons
        text = re.sub(r'([;:])\s+', r'\1 <break time="0.5s"/> ', text)
        
        # Add pause at the beginning and end
        text = f'<break time="0.5s"/> {text} <break time="0.5s"/>'
        
        return text
    
    def replace_audio_in_video(self, video_path: str, new_audio_path: str, output_path: str, original_duration: float = None) -> bool:
        """Replace audio in video with new audio that's already timed to match."""
        try:
            # Get durations of both video and audio
            video_duration = self._get_media_duration(video_path)
            audio_duration = self._get_media_duration(new_audio_path)
            
            if video_duration:
                print(f"Original video duration: {video_duration:.2f} seconds")
            if audio_duration:
                print(f"Generated audio duration: {audio_duration:.2f} seconds")
            
            # Build ffmpeg command
            cmd = [
                'ffmpeg', '-i', video_path,
                '-i', new_audio_path,
                '-c:v', 'copy',  # Copy video stream
                '-c:a', 'aac',   # Encode audio as AAC
                '-map', '0:v:0', # Use video from first input
                '-map', '1:a:0', # Use audio from second input
            ]
            
            # Since we've already timed the audio properly, we mainly need to handle
            # cases where there are still small discrepancies
            if video_duration and audio_duration:
                duration_diff = abs(video_duration - audio_duration)
                
                if duration_diff > 1.0:
                    print(f"Significant duration difference: {duration_diff:.2f}s - adjusting...")
                    
                    if audio_duration < video_duration:
                        # Audio is shorter - pad it to match video
                        print("Padding audio to match video duration")
                        audio_filter = f"apad=whole_dur={video_duration}"
                        cmd.extend(['-af', audio_filter])
                    else:
                        # Audio is longer - trim it to match video
                        print("Trimming audio to match video duration")
                        audio_filter = f"atrim=duration={video_duration}"
                        cmd.extend(['-af', audio_filter])
                else:
                    print("Audio and video durations are well matched")
                    # Small difference is acceptable, use shortest to avoid issues
                    cmd.append('-shortest')
            else:
                # Fallback: use shortest stream
                print("Using shortest stream duration")
                cmd.append('-shortest')
            
            cmd.extend(['-y', output_path])  # Overwrite output file
            
            print("Processing video with timing-matched audio...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error replacing audio: {result.stderr}")
                return False
            
            print(f"Video with new voice saved to: {output_path}")
            
            # Verify the output duration
            output_duration = self._get_media_duration(output_path)
            if output_duration:
                print(f"Final video duration: {output_duration:.2f} seconds")
                if video_duration and abs(output_duration - video_duration) > 0.1:
                    print(f"⚠️  Duration difference: {abs(output_duration - video_duration):.2f}s")
                else:
                    print("✅ Video duration matches perfectly!")
            
            return True
            
        except Exception as e:
            print(f"Error replacing audio: {e}")
            return False
    
    def process_video(self, video_path: str, output_path: str = None, voice_id: str = "UgBBYS2sOqTuMpoF3BR0") -> bool:
        """Complete workflow to process video and change voice."""
        if not os.path.exists(video_path):
            print(f"Error: Video file not found: {video_path}")
            return False
        
        if output_path is None:
            base_name = Path(video_path).stem
            output_path = f"{base_name}_voice_changed.mp4"
        
        print(f"Processing video: {video_path}")
        
        # Create temporary files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_audio = os.path.join(temp_dir, "extracted_audio.wav")
            temp_ai_audio = os.path.join(temp_dir, "ai_voice.mp3")
            
            # Step 1: Extract audio
            print("Step 1: Extracting audio...")
            if not self.extract_audio(video_path, temp_audio):
                return False
            
            # Step 2: Transcribe audio
            print("Step 2: Transcribing audio...")
            transcript_data = self.transcribe_audio(temp_audio)
            if not transcript_data:
                print("Error: Could not get transcript")
                return False
            
            # Step 3: Generate AI voice
            print("Step 3: Generating AI voice...")
            ai_audio_path = self.generate_ai_voice_with_timing(transcript_data, voice_id, temp_ai_audio)
            if not ai_audio_path:
                return False
            
            # Step 4: Replace audio in video
            print("Step 4: Replacing audio in video...")
            original_duration = transcript_data.get('total_duration')
            if not self.replace_audio_in_video(video_path, ai_audio_path, output_path, original_duration):
                return False
        
        print(f"\n✅ Success! Voice-changed video saved to: {output_path}")
        return True

    def generate_ai_voice(self, text: str, voice_id: str = "UgBBYS2sOqTuMpoF3BR0", output_path: str = None) -> Optional[str]:
        """Generate AI voice using ElevenLabs with natural pauses (backward compatibility)."""
        # Convert text to transcript_data format for timing-aware generation
        transcript_data = {
            'full_text': text,
            'segments': [{
                'text': text,
                'start': 0,
                'end': len(text.split()) / 150 * 60,  # Estimate based on 150 WPM
                'duration': len(text.split()) / 150 * 60
            }],
            'total_duration': len(text.split()) / 150 * 60
        }
        
        return self.generate_ai_voice_with_timing(transcript_data, voice_id, output_path)

def main():
    parser = argparse.ArgumentParser(description="Change voice in recorded videos using AI")
    parser.add_argument("video_path", nargs="?", help="Path to the video file")
    parser.add_argument("-o", "--output", help="Output video path")
    parser.add_argument("-v", "--voice", default="UgBBYS2sOqTuMpoF3BR0", help="ElevenLabs voice ID (default: Mark)")
    parser.add_argument("--list-voices", action="store_true", help="List available voices")
    parser.add_argument("--api-key", help="ElevenLabs API key (or set ELEVEN_LABS_KEY in .env file)")
    
    args = parser.parse_args()
    
    # Get API key from argument, .env file, or environment
    api_key = args.api_key or os.getenv("ELEVEN_LABS_KEY") or os.getenv("ELEVENLABS_API_KEY")
    
    # Initialize voice changer
    voice_changer = VideoVoiceChanger(api_key)
    
    # List voices if requested
    if args.list_voices:
        voice_changer.list_available_voices()
        return
    
    # Process video
    if args.video_path:
        voice_changer.process_video(args.video_path, args.output, args.voice)
    else:
        print("Usage: python3 voice_changer.py <video_path> [-o output_path] [-v voice_id]")
        print("       python3 voice_changer.py --list-voices")
        print("\nExample: python3 voice_changer.py recording.mp4 -o changed_voice.mp4")
        print("\nSet your ElevenLabs API key:")
        print("1. Create a .env file with: ELEVEN_LABS_KEY=your_api_key_here")
        print("2. Or export ELEVENLABS_API_KEY='your_api_key_here'")

if __name__ == "__main__":
    main() 