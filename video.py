from flask import Blueprint, jsonify, request, send_file
from flask_cors import cross_origin
import os
import uuid
import json
from werkzeug.utils import secure_filename
import tempfile
import subprocess
from datetime import datetime
from src.services.voice_cloning import VoiceCloningService
from src.services.image_generation import ImageGenerationService

video_bp = Blueprint('video', __name__)

# Configuration
UPLOAD_FOLDER = '/tmp/uploads'
OUTPUT_FOLDER = '/tmp/outputs'
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'mp4', 'avi', 'mov', 'm4a', 'aac'}

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Initialize services
voice_service = VoiceCloningService()
image_service = ImageGenerationService()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@video_bp.route('/generate-video', methods=['POST'])
@cross_origin()
def generate_video():
    """Generate video from text script"""
    try:
        data = request.json
        script = data.get('script', '')
        voice_id = data.get('voice_id', 'default')
        
        if not script:
            return jsonify({'error': 'Script is required'}), 400
        
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Process script and generate video
        video_path = process_video_generation(script, voice_id, job_id)
        
        return jsonify({
            'job_id': job_id,
            'status': 'completed',
            'video_url': f'/api/download-video/{job_id}',
            'message': 'Video generated successfully'
        })
        
    except Exception as e:
        print(f"Video generation error: {e}")
        return jsonify({'error': str(e)}), 500

@video_bp.route('/upload-voice-sample', methods=['POST'])
@cross_origin()
def upload_voice_sample():
    """Upload voice sample for cloning"""
    try:
        if 'voice_file' not in request.files:
            return jsonify({'error': 'No voice file provided'}), 400
        
        file = request.files['voice_file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            voice_id = str(uuid.uuid4())
            file_path = os.path.join(UPLOAD_FOLDER, f"{voice_id}_{filename}")
            file.save(file_path)
            
            # Process voice cloning
            cloned_voice_id = voice_service.clone_voice_from_sample(file_path, f"user_voice_{voice_id}")
            
            return jsonify({
                'voice_id': cloned_voice_id,
                'status': 'success',
                'message': 'Voice sample uploaded and processed successfully'
            })
        
        return jsonify({'error': 'Invalid file type. Please upload audio files (wav, mp3, m4a, aac)'}), 400
        
    except Exception as e:
        print(f"Voice upload error: {e}")
        return jsonify({'error': str(e)}), 500

@video_bp.route('/download-video/<job_id>', methods=['GET'])
@cross_origin()
def download_video(job_id):
    """Download generated video"""
    try:
        video_path = os.path.join(OUTPUT_FOLDER, f"{job_id}.mp4")
        if os.path.exists(video_path):
            return send_file(video_path, as_attachment=True, download_name=f"dawa_present_video_{job_id}.mp4")
        else:
            return jsonify({'error': 'Video not found'}), 404
    except Exception as e:
        print(f"Download error: {e}")
        return jsonify({'error': str(e)}), 500

@video_bp.route('/job-status/<job_id>', methods=['GET'])
@cross_origin()
def get_job_status(job_id):
    """Get video generation job status"""
    try:
        video_path = os.path.join(OUTPUT_FOLDER, f"{job_id}.mp4")
        if os.path.exists(video_path):
            return jsonify({
                'job_id': job_id,
                'status': 'completed',
                'video_url': f'/api/download-video/{job_id}'
            })
        else:
            return jsonify({
                'job_id': job_id,
                'status': 'processing'
            })
    except Exception as e:
        print(f"Status check error: {e}")
        return jsonify({'error': str(e)}), 500

@video_bp.route('/available-voices', methods=['GET'])
@cross_origin()
def get_available_voices():
    """Get list of available voices"""
    try:
        voices = voice_service.list_available_voices()
        return jsonify({'voices': voices})
    except Exception as e:
        print(f"Voice list error: {e}")
        return jsonify({'error': str(e)}), 500

def process_video_generation(script, voice_id, job_id):
    """Process video generation from script"""
    try:
        print(f"Starting video generation for job {job_id}")
        
        # Split script into segments for better processing
        segments = split_script_into_segments(script)
        print(f"Split script into {len(segments)} segments")
        
        # Generate audio for each segment
        audio_files = []
        for i, segment in enumerate(segments):
            if segment.strip():  # Only process non-empty segments
                audio_file = os.path.join(OUTPUT_FOLDER, f"{job_id}_audio_{i}.wav")
                voice_service.generate_speech(segment, voice_id, audio_file)
                audio_files.append(audio_file)
                print(f"Generated audio for segment {i}")
        
        # Generate images for each segment
        image_files = []
        for i, segment in enumerate(segments):
            if segment.strip():  # Only process non-empty segments
                image_file = os.path.join(OUTPUT_FOLDER, f"{job_id}_image_{i}.png")
                image_service.generate_image_from_text(segment, image_file)
                image_files.append(image_file)
                print(f"Generated image for segment {i}")
        
        # Combine audio and images into video
        video_path = combine_media_to_video(audio_files, image_files, job_id)
        print(f"Video generation completed: {video_path}")
        
        return video_path
        
    except Exception as e:
        print(f"Video generation failed: {e}")
        raise Exception(f"Video generation failed: {str(e)}")

def split_script_into_segments(script):
    """Split script into logical segments"""
    import re
    
    # Split by sentences, but keep reasonable length
    sentences = re.split(r'[.!?]+', script)
    segments = []
    current_segment = ""
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # If adding this sentence would make the segment too long, start a new one
        if len(current_segment) + len(sentence) > 200 and current_segment:
            segments.append(current_segment.strip())
            current_segment = sentence
        else:
            if current_segment:
                current_segment += ". " + sentence
            else:
                current_segment = sentence
    
    # Add the last segment
    if current_segment.strip():
        segments.append(current_segment.strip())
    
    # If no segments, use the whole script
    if not segments:
        segments = [script]
    
    return segments

def combine_media_to_video(audio_files, image_files, job_id):
    """Combine audio and images into final video"""
    video_path = os.path.join(OUTPUT_FOLDER, f"{job_id}.mp4")
    
    try:
        if not audio_files or not image_files:
            raise Exception("No audio or image files to combine")
        
        # Create a video for each audio-image pair
        segment_videos = []
        
        for i, (audio_file, image_file) in enumerate(zip(audio_files, image_files)):
            if os.path.exists(audio_file) and os.path.exists(image_file):
                segment_video = os.path.join(OUTPUT_FOLDER, f"{job_id}_segment_{i}.mp4")
                
                # Create video segment with image and audio
                cmd = [
                    'ffmpeg', '-y',
                    '-loop', '1', '-i', image_file,
                    '-i', audio_file,
                    '-c:v', 'libx264', '-c:a', 'aac',
                    '-shortest', '-pix_fmt', 'yuv420p',
                    '-vf', 'scale=1280:720',
                    segment_video
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"FFmpeg error for segment {i}: {result.stderr}")
                    continue
                
                segment_videos.append(segment_video)
                print(f"Created segment video {i}: {segment_video}")
        
        if not segment_videos:
            raise Exception("No video segments were created successfully")
        
        # If only one segment, just copy it
        if len(segment_videos) == 1:
            subprocess.run(['cp', segment_videos[0], video_path], check=True)
        else:
            # Concatenate all segments
            concat_file = os.path.join(OUTPUT_FOLDER, f"{job_id}_concat.txt")
            with open(concat_file, 'w') as f:
                for segment in segment_videos:
                    f.write(f"file '{segment}'\n")
            
            cmd = [
                'ffmpeg', '-y',
                '-f', 'concat', '-safe', '0', '-i', concat_file,
                '-c', 'copy', video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"FFmpeg concatenation error: {result.stderr}")
                # Fallback: just use the first segment
                subprocess.run(['cp', segment_videos[0], video_path], check=True)
        
        # Clean up temporary files
        for segment in segment_videos:
            try:
                os.remove(segment)
            except:
                pass
        
        return video_path
        
    except Exception as e:
        print(f"Video combination error: {e}")
        # Create a simple fallback video
        if audio_files and image_files:
            cmd = [
                'ffmpeg', '-y',
                '-loop', '1', '-i', image_files[0],
                '-i', audio_files[0],
                '-c:v', 'libx264', '-c:a', 'aac',
                '-shortest', '-pix_fmt', 'yuv420p',
                '-vf', 'scale=1280:720',
                video_path
            ]
            subprocess.run(cmd, capture_output=True)
        
        return video_path

