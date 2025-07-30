import os
import requests
from elevenlabs import ElevenLabs, Voice
from elevenlabs.client import ElevenLabs
import tempfile
import json

class VoiceCloningService:
    def __init__(self):
        # Initialize ElevenLabs client
        # You'll need to set ELEVENLABS_API_KEY environment variable
        self.elevenlabs_api_key = os.getenv('ELEVENLABS_API_KEY')
        if self.elevenlabs_api_key:
            self.client = ElevenLabs(api_key=self.elevenlabs_api_key)
        else:
            self.client = None
            print("Warning: ELEVENLABS_API_KEY not set. Voice cloning will use fallback method.")
    
    def clone_voice_from_sample(self, audio_file_path, voice_name=None):
        """
        Clone a voice from an audio sample
        Returns voice_id that can be used for TTS
        """
        if not voice_name:
            voice_name = f"cloned_voice_{os.path.basename(audio_file_path)}"
        
        if self.client:
            return self._clone_with_elevenlabs(audio_file_path, voice_name)
        else:
            return self._fallback_voice_processing(audio_file_path, voice_name)
    
    def _clone_with_elevenlabs(self, audio_file_path, voice_name):
        """Clone voice using ElevenLabs API"""
        try:
            # Read the audio file
            with open(audio_file_path, 'rb') as audio_file:
                # Create voice clone
                voice = self.client.clone(
                    name=voice_name,
                    description="Cloned voice from user sample",
                    files=[audio_file_path]
                )
                
                return voice.voice_id
                
        except Exception as e:
            print(f"ElevenLabs voice cloning failed: {e}")
            return self._fallback_voice_processing(audio_file_path, voice_name)
    
    def _fallback_voice_processing(self, audio_file_path, voice_name):
        """Fallback method when ElevenLabs is not available"""
        # For demo purposes, we'll just return a placeholder voice ID
        # In a real implementation, you could integrate with other services like:
        # - Resemble.ai
        # - Play.ht
        # - Local voice cloning models (OpenVoice, etc.)
        
        voice_id = f"fallback_{voice_name}_{hash(audio_file_path) % 10000}"
        
        # Store voice metadata for later use
        voice_metadata = {
            'voice_id': voice_id,
            'original_file': audio_file_path,
            'voice_name': voice_name,
            'service': 'fallback'
        }
        
        # Save metadata (in production, use a proper database)
        metadata_path = f"/tmp/voice_metadata_{voice_id}.json"
        with open(metadata_path, 'w') as f:
            json.dump(voice_metadata, f)
        
        return voice_id
    
    def generate_speech(self, text, voice_id, output_path):
        """Generate speech using cloned voice"""
        if self.client and not voice_id.startswith('fallback_'):
            return self._generate_with_elevenlabs(text, voice_id, output_path)
        else:
            return self._generate_with_fallback(text, voice_id, output_path)
    
    def _generate_with_elevenlabs(self, text, voice_id, output_path):
        """Generate speech using ElevenLabs"""
        try:
            # Generate audio
            audio = self.client.generate(
                text=text,
                voice=Voice(voice_id=voice_id),
                model="eleven_multilingual_v2"
            )
            
            # Save audio to file
            with open(output_path, 'wb') as f:
                for chunk in audio:
                    f.write(chunk)
            
            return output_path
            
        except Exception as e:
            print(f"ElevenLabs TTS failed: {e}")
            return self._generate_with_fallback(text, voice_id, output_path)
    
    def _generate_with_fallback(self, text, voice_id, output_path):
        """Fallback TTS method"""
        # Use OpenAI TTS as fallback
        try:
            from openai import OpenAI
            
            openai_client = OpenAI()
            
            response = openai_client.audio.speech.create(
                model="tts-1",
                voice="alloy",  # Default voice
                input=text
            )
            
            response.stream_to_file(output_path)
            return output_path
            
        except Exception as e:
            print(f"OpenAI TTS fallback failed: {e}")
            # Last resort: create silent audio
            import subprocess
            duration = len(text) * 0.1  # Rough estimate
            subprocess.run([
                'ffmpeg', '-f', 'lavfi', '-i', f'anullsrc=duration={duration}',
                '-y', output_path
            ], check=True, capture_output=True)
            
            return output_path
    
    def list_available_voices(self):
        """List all available voices"""
        voices = []
        
        if self.client:
            try:
                elevenlabs_voices = self.client.voices.get_all()
                for voice in elevenlabs_voices.voices:
                    voices.append({
                        'voice_id': voice.voice_id,
                        'name': voice.name,
                        'service': 'elevenlabs'
                    })
            except Exception as e:
                print(f"Failed to fetch ElevenLabs voices: {e}")
        
        # Add fallback voices
        fallback_voices = [
            {'voice_id': 'openai_alloy', 'name': 'Alloy (OpenAI)', 'service': 'openai'},
            {'voice_id': 'openai_echo', 'name': 'Echo (OpenAI)', 'service': 'openai'},
            {'voice_id': 'openai_fable', 'name': 'Fable (OpenAI)', 'service': 'openai'},
            {'voice_id': 'openai_onyx', 'name': 'Onyx (OpenAI)', 'service': 'openai'},
            {'voice_id': 'openai_nova', 'name': 'Nova (OpenAI)', 'service': 'openai'},
            {'voice_id': 'openai_shimmer', 'name': 'Shimmer (OpenAI)', 'service': 'openai'}
        ]
        
        voices.extend(fallback_voices)
        return voices

