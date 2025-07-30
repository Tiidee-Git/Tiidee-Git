import os
import requests
from openai import OpenAI
import tempfile
import subprocess

class ImageGenerationService:
    def __init__(self):
        # Initialize OpenAI client for DALL-E
        self.openai_client = OpenAI()
    
    def generate_image_from_text(self, text_prompt, output_path, style="realistic"):
        """
        Generate an image from text description
        """
        try:
            # Enhance the prompt based on style
            enhanced_prompt = self._enhance_prompt(text_prompt, style)
            
            # Generate image using DALL-E
            response = self.openai_client.images.generate(
                model="dall-e-3",
                prompt=enhanced_prompt,
                size="1280x720",  # 16:9 aspect ratio for video
                quality="standard",
                n=1
            )
            
            # Download the generated image
            image_url = response.data[0].url
            image_response = requests.get(image_url)
            
            if image_response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(image_response.content)
                return output_path
            else:
                raise Exception(f"Failed to download image: {image_response.status_code}")
                
        except Exception as e:
            print(f"DALL-E image generation failed: {e}")
            return self._generate_fallback_image(text_prompt, output_path)
    
    def _enhance_prompt(self, text_prompt, style):
        """Enhance the text prompt for better image generation"""
        style_modifiers = {
            "realistic": "photorealistic, high quality, detailed",
            "artistic": "artistic, creative, stylized",
            "cartoon": "cartoon style, animated, colorful",
            "minimalist": "minimalist, clean, simple design",
            "cinematic": "cinematic lighting, dramatic, movie-like"
        }
        
        modifier = style_modifiers.get(style, "high quality, detailed")
        enhanced_prompt = f"{text_prompt}, {modifier}, 16:9 aspect ratio"
        
        # Ensure prompt is not too long (DALL-E has limits)
        if len(enhanced_prompt) > 1000:
            enhanced_prompt = enhanced_prompt[:1000]
        
        return enhanced_prompt
    
    def _generate_fallback_image(self, text_prompt, output_path):
        """Generate a simple colored image as fallback"""
        try:
            # Create a simple gradient image with text overlay
            # This is a basic fallback - in production you might want to use other services
            
            # Generate a colored background based on text hash
            color_hash = hash(text_prompt) % 16777215  # RGB color range
            color_hex = f"#{color_hash:06x}"
            
            # Create image using FFmpeg
            subprocess.run([
                'ffmpeg', '-f', 'lavfi', 
                '-i', f'color={color_hex}:size=1280x720:duration=1',
                '-frames:v', '1', '-y', output_path
            ], check=True, capture_output=True)
            
            return output_path
            
        except Exception as e:
            print(f"Fallback image generation failed: {e}")
            # Last resort: create a black image
            subprocess.run([
                'ffmpeg', '-f', 'lavfi', 
                '-i', 'color=black:size=1280x720:duration=1',
                '-frames:v', '1', '-y', output_path
            ], check=True, capture_output=True)
            
            return output_path
    
    def generate_multiple_images(self, text_segments, output_dir, style="realistic"):
        """Generate multiple images for different text segments"""
        image_paths = []
        
        for i, segment in enumerate(text_segments):
            output_path = os.path.join(output_dir, f"image_{i:03d}.png")
            try:
                generated_path = self.generate_image_from_text(segment, output_path, style)
                image_paths.append(generated_path)
            except Exception as e:
                print(f"Failed to generate image for segment {i}: {e}")
                # Use fallback
                fallback_path = self._generate_fallback_image(segment, output_path)
                image_paths.append(fallback_path)
        
        return image_paths
    
    def create_video_thumbnail(self, title_text, output_path):
        """Create a thumbnail image for the video"""
        try:
            prompt = f"Video thumbnail for: {title_text}, professional, eye-catching, YouTube style thumbnail"
            return self.generate_image_from_text(prompt, output_path, "cinematic")
        except Exception as e:
            print(f"Thumbnail generation failed: {e}")
            return self._generate_fallback_image(title_text, output_path)

