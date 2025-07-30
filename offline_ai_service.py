import os
import subprocess
import json
import tempfile
import sqlite3
from datetime import datetime
import base64
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
import wave
import struct
import math
import random

class OfflineAIService:
    def __init__(self):
        self.temp_dir = "/tmp/offline_ai"
        self.models_dir = "/tmp/ai_models"
        self.db_path = "/tmp/offline_ai.db"
        
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.models_dir, exist_ok=True)
        
        self.init_database()
        self.init_local_models()
    
    def init_database(self):
        """Initialize local database for offline storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables for offline data
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS drafts (
                id TEXT PRIMARY KEY,
                title TEXT,
                script TEXT,
                voice_id TEXT,
                settings TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS generated_videos (
                id TEXT PRIMARY KEY,
                title TEXT,
                script TEXT,
                video_path TEXT,
                thumbnail_path TEXT,
                duration REAL,
                created_at TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS voice_samples (
                id TEXT PRIMARY KEY,
                name TEXT,
                file_path TEXT,
                characteristics TEXT,
                created_at TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS templates (
                id TEXT PRIMARY KEY,
                name TEXT,
                category TEXT,
                settings TEXT,
                preview_path TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def init_local_models(self):
        """Initialize local AI models for offline processing"""
        # Download and setup local models if not present
        self.setup_local_tts()
        self.setup_local_image_generation()
        self.setup_voice_processing()
    
    def setup_local_tts(self):
        """Setup local text-to-speech using espeak or festival"""
        try:
            # Check if espeak is available
            result = subprocess.run(['which', 'espeak'], capture_output=True)
            if result.returncode == 0:
                self.tts_engine = 'espeak'
                return
            
            # Check if festival is available
            result = subprocess.run(['which', 'festival'], capture_output=True)
            if result.returncode == 0:
                self.tts_engine = 'festival'
                return
            
            # Install espeak if neither is available
            subprocess.run(['apt-get', 'update'], capture_output=True)
            subprocess.run(['apt-get', 'install', '-y', 'espeak', 'espeak-data'], capture_output=True)
            self.tts_engine = 'espeak'
            
        except Exception as e:
            print(f"TTS setup failed: {e}")
            self.tts_engine = 'synthetic'  # Fallback to synthetic generation
    
    def setup_local_image_generation(self):
        """Setup local image generation using simple algorithms"""
        # For offline use, we'll use procedural generation and templates
        self.create_image_templates()
    
    def setup_voice_processing(self):
        """Setup voice processing for offline voice cloning"""
        # Simple voice characteristic analysis
        pass
    
    def create_image_templates(self):
        """Create basic image templates for offline use"""
        templates_dir = os.path.join(self.models_dir, 'image_templates')
        os.makedirs(templates_dir, exist_ok=True)
        
        # Create basic templates
        templates = [
            {'name': 'business', 'color': '#2563eb', 'style': 'professional'},
            {'name': 'nature', 'color': '#16a34a', 'style': 'organic'},
            {'name': 'technology', 'color': '#7c3aed', 'style': 'modern'},
            {'name': 'education', 'color': '#dc2626', 'style': 'academic'},
            {'name': 'creative', 'color': '#ea580c', 'style': 'artistic'}
        ]
        
        for template in templates:
            self.create_template_image(template, templates_dir)
    
    def create_template_image(self, template, output_dir):
        """Create a template image"""
        img = Image.new('RGB', (1280, 720), color=template['color'])
        draw = ImageDraw.Draw(img)
        
        # Add gradient effect
        for y in range(720):
            alpha = int(255 * (1 - y / 720) * 0.3)
            color = tuple(max(0, c - alpha) for c in img.getpixel((0, y)))
            draw.line([(0, y), (1280, y)], fill=color)
        
        # Add geometric patterns based on style
        if template['style'] == 'professional':
            self.add_professional_pattern(draw)
        elif template['style'] == 'organic':
            self.add_organic_pattern(draw)
        elif template['style'] == 'modern':
            self.add_modern_pattern(draw)
        
        template_path = os.path.join(output_dir, f"{template['name']}.png")
        img.save(template_path)
        
        return template_path
    
    def add_professional_pattern(self, draw):
        """Add professional geometric pattern"""
        # Add subtle grid lines
        for x in range(0, 1280, 100):
            draw.line([(x, 0), (x, 720)], fill='white', width=1)
        for y in range(0, 720, 100):
            draw.line([(0, y), (1280, y)], fill='white', width=1)
    
    def add_organic_pattern(self, draw):
        """Add organic flowing pattern"""
        # Add curved lines
        for i in range(5):
            y = 150 + i * 120
            points = []
            for x in range(0, 1280, 20):
                wave_y = y + 30 * math.sin(x * 0.01 + i)
                points.append((x, wave_y))
            
            if len(points) > 1:
                for j in range(len(points) - 1):
                    draw.line([points[j], points[j + 1]], fill='white', width=2)
    
    def add_modern_pattern(self, draw):
        """Add modern geometric pattern"""
        # Add diagonal lines and shapes
        for i in range(0, 1280, 200):
            draw.polygon([(i, 0), (i + 100, 0), (i + 150, 100), (i + 50, 100)], 
                        fill='white', outline='white')
    
    def generate_speech_offline(self, text, voice_id='default', output_path=None):
        """Generate speech using offline TTS"""
        if output_path is None:
            output_path = os.path.join(self.temp_dir, f'speech_{hash(text)}.wav')
        
        try:
            if self.tts_engine == 'espeak':
                self.generate_espeak_speech(text, output_path, voice_id)
            elif self.tts_engine == 'festival':
                self.generate_festival_speech(text, output_path)
            else:
                self.generate_synthetic_speech(text, output_path)
            
            return output_path
            
        except Exception as e:
            print(f"Offline TTS failed: {e}")
            return self.generate_synthetic_speech(text, output_path)
    
    def generate_espeak_speech(self, text, output_path, voice_id):
        """Generate speech using espeak"""
        # Map voice_id to espeak voices
        voice_map = {
            'default': 'en',
            'male': 'en+m3',
            'female': 'en+f3',
            'child': 'en+f4'
        }
        
        voice = voice_map.get(voice_id, 'en')
        
        cmd = [
            'espeak', '-v', voice, '-s', '150', '-p', '50',
            '-w', output_path, text
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
    
    def generate_festival_speech(self, text, output_path):
        """Generate speech using festival"""
        # Create festival script
        script_path = output_path.replace('.wav', '.scm')
        with open(script_path, 'w') as f:
            f.write(f'(voice_kal_diphone)\n')
            f.write(f'(utt.save.wave (SayText "{text}") "{output_path}" \'wav)\n')
        
        cmd = ['festival', '-b', script_path]
        subprocess.run(cmd, check=True, capture_output=True)
    
    def generate_synthetic_speech(self, text, output_path):
        """Generate synthetic speech using simple tone generation"""
        # Create a simple beep pattern based on text
        sample_rate = 22050
        duration = len(text) * 0.1  # 0.1 seconds per character
        
        # Generate tone sequence
        frames = []
        for i, char in enumerate(text):
            if char.isalpha():
                # Generate tone based on character
                freq = 200 + (ord(char.lower()) - ord('a')) * 20
                for j in range(int(sample_rate * 0.1)):
                    value = int(32767 * 0.3 * math.sin(2 * math.pi * freq * j / sample_rate))
                    frames.append(struct.pack('<h', value))
            else:
                # Silence for non-alphabetic characters
                for j in range(int(sample_rate * 0.05)):
                    frames.append(struct.pack('<h', 0))
        
        # Write WAV file
        with wave.open(output_path, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(b''.join(frames))
        
        return output_path
    
    def generate_image_offline(self, description, output_path=None, style='business'):
        """Generate image using offline methods"""
        if output_path is None:
            output_path = os.path.join(self.temp_dir, f'image_{hash(description)}.png')
        
        # Load base template
        template_path = os.path.join(self.models_dir, 'image_templates', f'{style}.png')
        
        if os.path.exists(template_path):
            img = Image.open(template_path).copy()
        else:
            # Create basic colored background
            colors = {
                'business': '#2563eb',
                'nature': '#16a34a',
                'technology': '#7c3aed',
                'education': '#dc2626',
                'creative': '#ea580c'
            }
            color = colors.get(style, '#6b7280')
            img = Image.new('RGB', (1280, 720), color=color)
        
        # Add text overlay
        self.add_text_to_image(img, description)
        
        # Add visual elements based on description keywords
        self.add_contextual_elements(img, description)
        
        img.save(output_path)
        return output_path
    
    def add_text_to_image(self, img, text):
        """Add text overlay to image"""
        draw = ImageDraw.Draw(img)
        
        # Try to load a font
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        except:
            font = ImageFont.load_default()
        
        # Wrap text
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] < 1000:  # Max width
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Draw text lines
        y_offset = (720 - len(lines) * 60) // 2
        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (1280 - text_width) // 2
            y = y_offset + i * 60
            
            # Add text shadow
            draw.text((x + 2, y + 2), line, fill='black', font=font)
            draw.text((x, y), line, fill='white', font=font)
    
    def add_contextual_elements(self, img, description):
        """Add visual elements based on description keywords"""
        draw = ImageDraw.Draw(img)
        
        # Define keyword-based visual elements
        keywords = {
            'business': self.add_business_elements,
            'technology': self.add_tech_elements,
            'nature': self.add_nature_elements,
            'education': self.add_education_elements,
            'creative': self.add_creative_elements
        }
        
        description_lower = description.lower()
        
        for keyword, add_func in keywords.items():
            if keyword in description_lower:
                add_func(draw)
                break
    
    def add_business_elements(self, draw):
        """Add business-related visual elements"""
        # Add chart-like elements
        for i in range(5):
            x = 100 + i * 200
            height = 50 + i * 30
            draw.rectangle([x, 600 - height, x + 50, 600], fill='white', outline='gray')
    
    def add_tech_elements(self, draw):
        """Add technology-related visual elements"""
        # Add circuit-like patterns
        for i in range(10):
            x1, y1 = random.randint(50, 1230), random.randint(50, 670)
            x2, y2 = x1 + random.randint(-100, 100), y1 + random.randint(-100, 100)
            draw.line([x1, y1, x2, y2], fill='white', width=2)
            draw.ellipse([x1-5, y1-5, x1+5, y1+5], fill='white')
    
    def add_nature_elements(self, draw):
        """Add nature-related visual elements"""
        # Add tree-like shapes
        for i in range(3):
            x = 200 + i * 400
            # Tree trunk
            draw.rectangle([x-10, 500, x+10, 600], fill='brown')
            # Tree crown
            draw.ellipse([x-50, 400, x+50, 520], fill='green')
    
    def add_education_elements(self, draw):
        """Add education-related visual elements"""
        # Add book-like shapes
        for i in range(3):
            x = 200 + i * 300
            y = 500
            draw.rectangle([x, y, x+80, y+100], fill='white', outline='black', width=2)
            draw.line([x+10, y+20, x+70, y+20], fill='black', width=1)
            draw.line([x+10, y+40, x+70, y+40], fill='black', width=1)
    
    def add_creative_elements(self, draw):
        """Add creative-related visual elements"""
        # Add artistic shapes
        colors = ['red', 'blue', 'yellow', 'green', 'purple']
        for i in range(10):
            x, y = random.randint(100, 1180), random.randint(100, 620)
            size = random.randint(20, 80)
            color = random.choice(colors)
            
            if i % 3 == 0:
                draw.ellipse([x, y, x+size, y+size], fill=color)
            elif i % 3 == 1:
                draw.rectangle([x, y, x+size, y+size], fill=color)
            else:
                points = [(x, y), (x+size, y+size//2), (x, y+size)]
                draw.polygon(points, fill=color)
    
    def generate_video_offline(self, script, voice_id='default', style='business'):
        """Generate complete video offline"""
        try:
            # Split script into segments
            segments = self.split_script(script)
            
            # Generate content for each segment
            video_segments = []
            
            for i, segment in enumerate(segments):
                # Generate audio
                audio_path = self.generate_speech_offline(segment, voice_id)
                
                # Generate image
                image_path = self.generate_image_offline(segment, style=style)
                
                # Create video segment
                segment_path = self.create_video_segment(image_path, audio_path, i)
                video_segments.append(segment_path)
            
            # Combine segments
            final_video = self.combine_video_segments(video_segments)
            
            return final_video
            
        except Exception as e:
            print(f"Offline video generation failed: {e}")
            return None
    
    def split_script(self, script):
        """Split script into logical segments"""
        # Simple sentence splitting
        import re
        sentences = re.split(r'[.!?]+', script)
        return [s.strip() for s in sentences if s.strip()]
    
    def create_video_segment(self, image_path, audio_path, index):
        """Create video segment from image and audio"""
        output_path = os.path.join(self.temp_dir, f'segment_{index}.mp4')
        
        cmd = [
            'ffmpeg', '-y',
            '-loop', '1', '-i', image_path,
            '-i', audio_path,
            '-c:v', 'libx264', '-c:a', 'aac',
            '-shortest', '-pix_fmt', 'yuv420p',
            '-vf', 'scale=1280:720',
            output_path
        ]
        
        subprocess.run(cmd, capture_output=True)
        return output_path
    
    def combine_video_segments(self, segments):
        """Combine video segments into final video"""
        if not segments:
            return None
        
        if len(segments) == 1:
            final_path = os.path.join(self.temp_dir, 'final_video.mp4')
            subprocess.run(['cp', segments[0], final_path])
            return final_path
        
        # Create concat file
        concat_file = os.path.join(self.temp_dir, 'concat.txt')
        with open(concat_file, 'w') as f:
            for segment in segments:
                if os.path.exists(segment):
                    f.write(f"file '{segment}'\n")
        
        final_path = os.path.join(self.temp_dir, 'final_video.mp4')
        cmd = [
            'ffmpeg', '-y',
            '-f', 'concat', '-safe', '0', '-i', concat_file,
            '-c', 'copy',
            final_path
        ]
        
        subprocess.run(cmd, capture_output=True)
        return final_path
    
    def save_draft(self, title, script, voice_id, settings):
        """Save draft to local database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        draft_id = f"draft_{int(datetime.now().timestamp())}"
        
        cursor.execute('''
            INSERT INTO drafts (id, title, script, voice_id, settings, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (draft_id, title, script, voice_id, json.dumps(settings), 
              datetime.now(), datetime.now()))
        
        conn.commit()
        conn.close()
        
        return draft_id
    
    def load_draft(self, draft_id):
        """Load draft from local database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM drafts WHERE id = ?', (draft_id,))
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'title': row[1],
                'script': row[2],
                'voice_id': row[3],
                'settings': json.loads(row[4]) if row[4] else {},
                'created_at': row[5],
                'updated_at': row[6]
            }
        
        return None
    
    def list_drafts(self):
        """List all drafts"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, title, created_at, updated_at FROM drafts ORDER BY updated_at DESC')
        rows = cursor.fetchall()
        
        conn.close()
        
        return [{'id': row[0], 'title': row[1], 'created_at': row[2], 'updated_at': row[3]} 
                for row in rows]
    
    def save_generated_video(self, title, script, video_path):
        """Save generated video to local database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        video_id = f"video_{int(datetime.now().timestamp())}"
        
        # Generate thumbnail
        thumbnail_path = self.generate_video_thumbnail(video_path)
        
        # Get video duration
        duration = self.get_video_duration(video_path)
        
        cursor.execute('''
            INSERT INTO generated_videos (id, title, script, video_path, thumbnail_path, duration, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (video_id, title, script, video_path, thumbnail_path, duration, datetime.now()))
        
        conn.commit()
        conn.close()
        
        return video_id
    
    def generate_video_thumbnail(self, video_path):
        """Generate thumbnail for video"""
        thumbnail_path = video_path.replace('.mp4', '_thumb.png')
        
        cmd = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-ss', '00:00:01',
            '-vframes', '1',
            '-vf', 'scale=320:180',
            thumbnail_path
        ]
        
        subprocess.run(cmd, capture_output=True)
        return thumbnail_path
    
    def get_video_duration(self, video_path):
        """Get video duration in seconds"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            return float(result.stdout.strip())
        except:
            return 0.0

