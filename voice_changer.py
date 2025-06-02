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
    
    def _get_video_info(self, video_path: str) -> dict:
        """Get detailed video information including frame rate."""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_streams', '-select_streams', 'v:0', video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                if data.get('streams'):
                    stream = data['streams'][0]
                    # Parse frame rate
                    fps_str = stream.get('r_frame_rate', '30/1')
                    if '/' in fps_str:
                        num, den = fps_str.split('/')
                        fps = float(num) / float(den)
                    else:
                        fps = float(fps_str)
                    
                    return {
                        'fps': fps,
                        'width': stream.get('width'),
                        'height': stream.get('height'),
                        'codec': stream.get('codec_name'),
                        'profile': stream.get('profile')
                    }
        except Exception as e:
            print(f"Could not get video info: {e}")
        
        return {'fps': 30.0}  # Default fallback

    def _adjust_video_speed_with_itsscale(self, video_path: str, audio_path: str, transcript_data: dict, output_path: str, max_speed_ratio: float = 2.5) -> bool:
        """Speed up video using itsscale method (filter-free, universally compatible)."""
        try:
            # Get durations and video info
            video_duration = self._get_media_duration(video_path)
            audio_duration = self._get_media_duration(audio_path)
            original_duration = transcript_data['total_duration']
            video_info = self._get_video_info(video_path)
            
            if not video_duration or not audio_duration:
                print("Could not determine durations for timing adjustment")
                return False
            
            print(f"Original video: {video_duration:.2f}s, AI audio: {audio_duration:.2f}s, Original audio: {original_duration:.2f}s")
            print(f"Video info: {video_info['fps']:.2f}fps, {video_info.get('codec', 'unknown')} codec")
            
            # Calculate speed ratio - we want to speed up the video to match the AI audio
            speed_ratio = video_duration / audio_duration
            
            # Limit speed ratio to reasonable bounds (0.5x to max_speed_ratio)
            if speed_ratio < 0.5:
                speed_ratio = 0.5
                print("⚠️  Limiting speed ratio to 0.5x (maximum slowdown)")
            elif speed_ratio > max_speed_ratio:
                speed_ratio = max_speed_ratio
                print(f"⚠️  Limiting speed ratio to {max_speed_ratio:.1f}x (maximum speedup)")
            
            print(f"Applying video speed ratio: {speed_ratio:.2f}x")
            
            # Calculate itsscale value (inverse of speed ratio)
            itsscale_value = 1.0 / speed_ratio
            
            # Build ffmpeg command with itsscale (filter-free approach)
            cmd = [
                'ffmpeg', 
                '-itsscale', str(itsscale_value), '-i', video_path,  # Scale video timing
                '-i', audio_path,  # AI audio
                '-c:v', 'libx264',  # Re-encode video (required when using itsscale)
                '-c:a', 'aac',      # Re-encode audio to AAC
                '-profile:v', 'baseline',  # Compatible profile
                '-pix_fmt', 'yuv420p',     # Compatible pixel format
                '-movflags', '+faststart', # Optimize for streaming
                '-map', '0:v:0',    # Use video from first input
                '-map', '1:a:0',    # Use audio from second input
            ]
            
            # Handle audio duration vs video duration
            final_video_duration = video_duration / speed_ratio
            
            if audio_duration < final_video_duration - 0.5:
                # Audio is shorter - pad it
                print("Padding audio to match adjusted video duration")
                audio_filter = f"apad=whole_dur={final_video_duration:.2f}"
                cmd.extend(['-af', audio_filter])
            elif audio_duration > final_video_duration + 0.5:
                # Audio is longer - trim it
                print("Trimming audio to match adjusted video duration")
                audio_filter = f"atrim=duration={final_video_duration:.2f}"
                cmd.extend(['-af', audio_filter])
            
            # Add output settings
            cmd.extend([
                '-f', 'mp4',              # MP4 container
                '-y', output_path         # Overwrite output file
            ])
            
            print("Processing video with speed adjustment...")
            print(f"🔧 Command: ffmpeg -itsscale {itsscale_value:.3f} [video] + [audio] -> {output_path}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error processing video: {result.stderr}")
                return False
            
            # Verify the output
            output_duration = self._get_media_duration(output_path)
            if output_duration:
                print(f"Final video duration: {output_duration:.2f} seconds")
                print(f"Speed adjustment: {speed_ratio:.2f}x")
                if abs(output_duration - audio_duration) < 0.5:
                    print("✅ Video and audio timing successfully matched!")
                else:
                    print(f"⚠️  Timing difference: {abs(output_duration - audio_duration):.2f}s")
            
            return True
            
        except Exception as e:
            print(f"Error adjusting video speed: {e}")
            return False
    
    def generate_ai_voice_with_timing(self, transcript_data: dict, voice_id: str = "UgBBYS2sOqTuMpoF3BR0", output_path: str = None) -> Optional[str]:
        """Generate AI voice with natural timing (no stretching)."""
        if not ELEVENLABS_AVAILABLE:
            print("ElevenLabs package not available. Please install with: pip install elevenlabs")
            return None
        
        if not self.elevenlabs_api_key:
            print("ElevenLabs API key not provided.")
            print("Add ELEVEN_LABS_KEY to your .env file or get one from: https://elevenlabs.io/")
            return None
        
        try:
            print(f"Generating AI voice for: {transcript_data['full_text'][:50]}...")
            
            # Create enhanced text with moderate pauses (less aggressive than before)
            enhanced_text = self._create_natural_text(transcript_data)
            print("Created natural text with appropriate pauses")
            
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
            
            # Return the natural AI voice without stretching
            return output_path
            
        except Exception as e:
            print(f"Error generating AI voice: {e}")
            return None
    
    def _create_natural_text(self, transcript_data: dict) -> str:
        """Create text with natural pauses (less aggressive than before)."""
        import re
        
        text = transcript_data['full_text']
        
        # Add moderate pauses - much less than before to avoid slow speech
        text = re.sub(r'([.!?])\s+', r'\1 <break time="0.4s"/> ', text)  # Reduced from 1.2s
        text = re.sub(r'(,)\s+', r'\1 <break time="0.2s"/> ', text)      # Reduced from 0.6s
        text = re.sub(r'([;:])\s+', r'\1 <break time="0.3s"/> ', text)   # Reduced from 0.8s
        
        # Add minimal pauses at start/end
        return f'<break time="0.2s"/> {text} <break time="0.3s"/>'
    
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
    
    def process_video(self, video_path: str, output_path: str = None, voice_id: str = "UgBBYS2sOqTuMpoF3BR0", max_speed_ratio: float = 2.5, adjust_video_speed: bool = True) -> bool:
        """Complete workflow to process video and change voice."""
        if not os.path.exists(video_path):
            print(f"Error: Video file not found: {video_path}")
            return False
        
        if output_path is None:
            # Save in the same directory as the original video
            video_path_obj = Path(video_path)
            base_name = video_path_obj.stem
            output_path = video_path_obj.parent / f"{base_name}_voice_changed.mp4"
            output_path = str(output_path)  # Convert back to string
        
        print(f"Processing video: {video_path}")
        print(f"Output will be saved to: {output_path}")
        if adjust_video_speed:
            print(f"Maximum video speed adjustment: {max_speed_ratio:.1f}x")
        else:
            print("Video speed adjustment disabled - keeping original timing")
        
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
            
            # Step 4: Either adjust video speed or replace audio with original timing
            if adjust_video_speed:
                print("Step 4: Adjusting video speed to match AI voice...")
                if not self._adjust_video_speed_with_itsscale(video_path, ai_audio_path, transcript_data, output_path, max_speed_ratio):
                    return False
            else:
                print("Step 4: Replacing audio with original video timing...")
                original_duration = transcript_data.get('total_duration')
                if not self.replace_audio_in_video(video_path, ai_audio_path, output_path, original_duration):
                    return False
        
        print(f"\n✅ Success! Voice-changed video saved to: {output_path}")
        return True

    def generate_ai_voice(self, text: str, voice_id: str = "UgBBYS2sOqTuMpoF3BR0", output_path: str = None) -> Optional[str]:
        """Generate AI voice using ElevenLabs with natural pauses (backward compatibility)."""
        # Convert text to transcript_data format for natural generation
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
    parser.add_argument("--max-speed-ratio", type=float, default=2.5, help="Maximum video speed adjustment (default: 2.5x)")
    parser.add_argument("--no-adjust-video", action="store_true", help="Disable video speed adjustment (use original timing)")
    
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
        voice_changer.process_video(args.video_path, args.output, args.voice, args.max_speed_ratio, not args.no_adjust_video)
    else:
        print("Usage: python3 voice_changer.py <video_path> [-o output_path] [-v voice_id]")
        print("       python3 voice_changer.py --list-voices")
        print("\nExample: python3 voice_changer.py recording.mp4 -o changed_voice.mp4")
        print("\nFeatures:")
        print("- Automatic video speed adjustment to match AI voice timing")
        print("- Natural AI voice generation with ElevenLabs")
        print("- Compatible with all major video players")
        print("\nSet your ElevenLabs API key:")
        print("1. Create a .env file with: ELEVEN_LABS_KEY=your_api_key_here")
        print("2. Or export ELEVENLABS_API_KEY='your_api_key_here'")
        print("\nGet your API key from: https://elevenlabs.io/")

if __name__ == "__main__":
    main() 