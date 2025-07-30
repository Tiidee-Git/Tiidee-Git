import os
import requests
import json
import subprocess
import tempfile
from datetime import datetime
from openai import OpenAI
import moviepy.editor as mp
from PIL import Image, ImageDraw, ImageFont
import numpy as np

class AdvancedVideoGenerationService:
    def __init__(self):
        self.openai_client = OpenAI()
        self.temp_dir = "/tmp/video_generation"
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def generate_video_from_script(self, script, options=None):
        """
        Generate video from script with advanced options
        """
        if options is None:
            options = {}
        
        style = options.get('style', 'realistic')
        duration_per_scene = options.get('duration_per_scene', 3)
        resolution = options.get('resolution', '1280x720')
        fps = options.get('fps', 30)
        voice_id = options.get('voice_id', 'default')
        include_subtitles = options.get('include_subtitles', True)
        background_music = options.get('background_music', False)
        
        # Parse script into scenes
        scenes = self._parse_script_into_scenes(script)
        
        # Generate content for each scene
        video_clips = []
        for i, scene in enumerate(scenes):
            clip = self._generate_scene_clip(
                scene, i, style, duration_per_scene, 
                resolution, fps, voice_id, include_subtitles
            )
            video_clips.append(clip)
        
        # Combine clips into final video
        final_video = self._combine_clips(video_clips, background_music)
        
        return final_video
    
    def generate_ai_avatar_video(self, script, avatar_config):
        """
        Generate video with AI avatar presenter
        """
        avatar_style = avatar_config.get('style', 'professional')
        avatar_gender = avatar_config.get('gender', 'neutral')
        avatar_ethnicity = avatar_config.get('ethnicity', 'diverse')
        background = avatar_config.get('background', 'office')
        
        # Generate avatar images for different expressions
        avatar_images = self._generate_avatar_images(
            avatar_style, avatar_gender, avatar_ethnicity, background
        )
        
        # Generate lip-sync animation (simplified)
        animated_avatar = self._create_avatar_animation(avatar_images, script)
        
        return animated_avatar
    
    def generate_slideshow_video(self, content_points, template='modern'):
        """
        Generate slideshow-style video from content points
        """
        slides = []
        
        for i, point in enumerate(content_points):
            slide = self._create_slide(point, template, i)
            slides.append(slide)
        
        # Combine slides with transitions
        slideshow = self._combine_slides_with_transitions(slides)
        
        return slideshow
    
    def generate_animated_explainer(self, concept, style='whiteboard'):
        """
        Generate animated explainer video
        """
        # Break down concept into visual elements
        visual_elements = self._analyze_concept_for_visuals(concept)
        
        # Generate animations for each element
        animations = []
        for element in visual_elements:
            animation = self._create_animation(element, style)
            animations.append(animation)
        
        # Combine animations into explainer video
        explainer_video = self._combine_animations(animations)
        
        return explainer_video
    
    def generate_social_media_video(self, content, platform='instagram'):
        """
        Generate platform-optimized social media video
        """
        platform_specs = {
            'instagram': {'aspect_ratio': '9:16', 'duration': 30, 'style': 'trendy'},
            'youtube': {'aspect_ratio': '16:9', 'duration': 60, 'style': 'professional'},
            'tiktok': {'aspect_ratio': '9:16', 'duration': 15, 'style': 'dynamic'},
            'linkedin': {'aspect_ratio': '16:9', 'duration': 45, 'style': 'corporate'}
        }
        
        specs = platform_specs.get(platform, platform_specs['instagram'])
        
        # Generate content optimized for platform
        optimized_video = self._create_platform_optimized_video(content, specs)
        
        return optimized_video
    
    def add_video_effects(self, video_path, effects):
        """
        Add various effects to existing video
        """
        effects_to_apply = []
        
        for effect in effects:
            if effect['type'] == 'transition':
                effects_to_apply.append(self._create_transition_effect(effect))
            elif effect['type'] == 'filter':
                effects_to_apply.append(self._create_filter_effect(effect))
            elif effect['type'] == 'text_overlay':
                effects_to_apply.append(self._create_text_overlay(effect))
            elif effect['type'] == 'animation':
                effects_to_apply.append(self._create_animation_effect(effect))
        
        # Apply effects to video
        enhanced_video = self._apply_effects_to_video(video_path, effects_to_apply)
        
        return enhanced_video
    
    def generate_video_with_music(self, video_path, music_style='upbeat'):
        """
        Add AI-generated or selected background music
        """
        # Generate or select appropriate music
        music_file = self._generate_background_music(music_style)
        
        # Sync music with video
        synced_video = self._sync_music_with_video(video_path, music_file)
        
        return synced_video
    
    def create_video_montage(self, media_files, theme='dynamic'):
        """
        Create video montage from multiple media files
        """
        # Analyze media files
        analyzed_media = self._analyze_media_files(media_files)
        
        # Create montage based on theme
        montage = self._create_themed_montage(analyzed_media, theme)
        
        return montage
    
    def _parse_script_into_scenes(self, script):
        """Parse script into individual scenes"""
        # Use AI to intelligently break script into scenes
        prompt = f"""
        Break this script into logical scenes for video generation. Each scene should be 1-3 sentences.
        Return as JSON array with 'text' and 'visual_description' for each scene.
        
        Script: {script}
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            scenes_data = json.loads(response.choices[0].message.content)
            return scenes_data.get('scenes', [{'text': script, 'visual_description': script}])
        except:
            # Fallback: simple sentence splitting
            sentences = script.split('. ')
            return [{'text': s.strip() + '.', 'visual_description': s.strip()} for s in sentences if s.strip()]
    
    def _generate_scene_clip(self, scene, index, style, duration, resolution, fps, voice_id, include_subtitles):
        """Generate video clip for a single scene"""
        scene_dir = os.path.join(self.temp_dir, f"scene_{index}")
        os.makedirs(scene_dir, exist_ok=True)
        
        # Generate visuals for scene
        visual_path = os.path.join(scene_dir, f"visual_{index}.png")
        self._generate_scene_visual(scene['visual_description'], visual_path, style)
        
        # Generate audio for scene
        audio_path = os.path.join(scene_dir, f"audio_{index}.wav")
        self._generate_scene_audio(scene['text'], audio_path, voice_id)
        
        # Create video clip
        clip_path = os.path.join(scene_dir, f"clip_{index}.mp4")
        self._create_video_clip(visual_path, audio_path, clip_path, duration, resolution, fps)
        
        # Add subtitles if requested
        if include_subtitles:
            subtitled_path = os.path.join(scene_dir, f"subtitled_{index}.mp4")
            self._add_subtitles_to_clip(clip_path, scene['text'], subtitled_path)
            return subtitled_path
        
        return clip_path
    
    def _generate_scene_visual(self, description, output_path, style):
        """Generate visual for scene using AI"""
        try:
            # Enhance description for better image generation
            enhanced_prompt = f"{description}, {style} style, cinematic lighting, high quality, 16:9 aspect ratio"
            
            response = self.openai_client.images.generate(
                model="dall-e-3",
                prompt=enhanced_prompt,
                size="1792x1024",
                quality="hd",
                n=1
            )
            
            # Download and save image
            image_url = response.data[0].url
            image_response = requests.get(image_url)
            
            with open(output_path, 'wb') as f:
                f.write(image_response.content)
                
        except Exception as e:
            print(f"Image generation failed: {e}")
            # Create fallback image
            self._create_fallback_image(description, output_path)
    
    def _generate_scene_audio(self, text, output_path, voice_id):
        """Generate audio for scene"""
        try:
            response = self.openai_client.audio.speech.create(
                model="tts-1-hd",
                voice="alloy" if voice_id == 'default' else voice_id,
                input=text
            )
            
            response.stream_to_file(output_path)
            
        except Exception as e:
            print(f"Audio generation failed: {e}")
            # Create silent audio as fallback
            duration = len(text) * 0.1
            subprocess.run([
                'ffmpeg', '-f', 'lavfi', '-i', f'anullsrc=duration={duration}',
                '-y', output_path
            ], capture_output=True)
    
    def _create_video_clip(self, visual_path, audio_path, output_path, duration, resolution, fps):
        """Create video clip from visual and audio"""
        cmd = [
            'ffmpeg', '-y',
            '-loop', '1', '-i', visual_path,
            '-i', audio_path,
            '-c:v', 'libx264', '-c:a', 'aac',
            '-shortest', '-pix_fmt', 'yuv420p',
            '-vf', f'scale={resolution.replace("x", ":")}',
            '-r', str(fps),
            output_path
        ]
        
        subprocess.run(cmd, capture_output=True)
    
    def _add_subtitles_to_clip(self, video_path, text, output_path):
        """Add subtitles to video clip"""
        # Create subtitle file
        srt_path = video_path.replace('.mp4', '.srt')
        with open(srt_path, 'w') as f:
            f.write(f"1\n00:00:00,000 --> 00:00:10,000\n{text}\n\n")
        
        # Add subtitles to video
        cmd = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-vf', f"subtitles={srt_path}:force_style='FontSize=24,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=2'",
            '-c:a', 'copy',
            output_path
        ]
        
        subprocess.run(cmd, capture_output=True)
    
    def _combine_clips(self, video_clips, background_music=False):
        """Combine multiple video clips into final video"""
        if not video_clips:
            return None
        
        # Create concat file
        concat_file = os.path.join(self.temp_dir, 'concat_list.txt')
        with open(concat_file, 'w') as f:
            for clip in video_clips:
                if os.path.exists(clip):
                    f.write(f"file '{clip}'\n")
        
        # Combine videos
        final_path = os.path.join(self.temp_dir, 'final_video.mp4')
        cmd = [
            'ffmpeg', '-y',
            '-f', 'concat', '-safe', '0', '-i', concat_file,
            '-c', 'copy',
            final_path
        ]
        
        subprocess.run(cmd, capture_output=True)
        
        # Add background music if requested
        if background_music:
            music_path = self._generate_background_music('cinematic')
            final_with_music = os.path.join(self.temp_dir, 'final_with_music.mp4')
            self._add_background_music(final_path, music_path, final_with_music)
            return final_with_music
        
        return final_path
    
    def _generate_avatar_images(self, style, gender, ethnicity, background):
        """Generate AI avatar images"""
        avatar_prompts = [
            f"{style} {gender} person of {ethnicity} ethnicity in {background} setting, neutral expression, professional headshot",
            f"{style} {gender} person of {ethnicity} ethnicity in {background} setting, smiling, professional headshot",
            f"{style} {gender} person of {ethnicity} ethnicity in {background} setting, speaking, professional headshot"
        ]
        
        avatar_images = []
        for i, prompt in enumerate(avatar_prompts):
            try:
                response = self.openai_client.images.generate(
                    model="dall-e-3",
                    prompt=prompt,
                    size="1024x1024",
                    quality="hd",
                    n=1
                )
                
                image_path = os.path.join(self.temp_dir, f'avatar_{i}.png')
                image_url = response.data[0].url
                image_response = requests.get(image_url)
                
                with open(image_path, 'wb') as f:
                    f.write(image_response.content)
                
                avatar_images.append(image_path)
                
            except Exception as e:
                print(f"Avatar generation failed: {e}")
                # Create fallback avatar
                fallback_path = os.path.join(self.temp_dir, f'avatar_fallback_{i}.png')
                self._create_fallback_avatar(fallback_path)
                avatar_images.append(fallback_path)
        
        return avatar_images
    
    def _create_fallback_image(self, description, output_path):
        """Create a simple fallback image"""
        img = Image.new('RGB', (1792, 1024), color='lightblue')
        draw = ImageDraw.Draw(img)
        
        # Try to load a font, fallback to default if not available
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        except:
            font = ImageFont.load_default()
        
        # Add text to image
        text = description[:50] + "..." if len(description) > 50 else description
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (1792 - text_width) // 2
        y = (1024 - text_height) // 2
        
        draw.text((x, y), text, fill='white', font=font)
        img.save(output_path)
    
    def _create_fallback_avatar(self, output_path):
        """Create a simple fallback avatar"""
        img = Image.new('RGB', (1024, 1024), color='lightgray')
        draw = ImageDraw.Draw(img)
        
        # Draw simple avatar shape
        draw.ellipse([200, 200, 824, 824], fill='darkgray', outline='black', width=5)
        draw.ellipse([400, 350, 624, 574], fill='white', outline='black', width=3)  # Face
        draw.ellipse([450, 400, 500, 450], fill='black')  # Left eye
        draw.ellipse([524, 400, 574, 450], fill='black')  # Right eye
        draw.arc([475, 475, 549, 525], 0, 180, fill='black', width=3)  # Smile
        
        img.save(output_path)
    
    def _generate_background_music(self, style):
        """Generate or select background music"""
        # For now, create a simple tone as placeholder
        # In production, you would integrate with music generation APIs
        music_path = os.path.join(self.temp_dir, f'music_{style}.wav')
        
        # Create a simple background tone
        cmd = [
            'ffmpeg', '-y',
            '-f', 'lavfi', '-i', 'sine=frequency=440:duration=30',
            '-af', 'volume=0.1',
            music_path
        ]
        
        subprocess.run(cmd, capture_output=True)
        return music_path
    
    def _add_background_music(self, video_path, music_path, output_path):
        """Add background music to video"""
        cmd = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-i', music_path,
            '-filter_complex', '[1:a]volume=0.3[music];[0:a][music]amix=inputs=2[audio]',
            '-map', '0:v', '-map', '[audio]',
            '-c:v', 'copy', '-c:a', 'aac',
            output_path
        ]
        
        subprocess.run(cmd, capture_output=True)

