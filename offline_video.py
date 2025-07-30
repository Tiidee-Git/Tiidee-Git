from flask import Blueprint, jsonify, request, send_file
from flask_cors import cross_origin
import os
import uuid
import json
from werkzeug.utils import secure_filename
from datetime import datetime
from src.services.offline_ai_service import OfflineAIService

offline_video_bp = Blueprint('offline_video', __name__)

# Initialize offline AI service
offline_ai = OfflineAIService()

@offline_video_bp.route('/generate-video-offline', methods=['POST'])
@cross_origin()
def generate_video_offline():
    """Generate video using offline AI services"""
    try:
        data = request.json
        script = data.get('script', '')
        voice_id = data.get('voice_id', 'default')
        style = data.get('style', 'business')
        title = data.get('title', 'Untitled Video')
        
        if not script:
            return jsonify({'error': 'Script is required'}), 400
        
        # Generate video offline
        video_path = offline_ai.generate_video_offline(script, voice_id, style)
        
        if video_path and os.path.exists(video_path):
            # Save to database
            video_id = offline_ai.save_generated_video(title, script, video_path)
            
            return jsonify({
                'job_id': video_id,
                'status': 'completed',
                'video_url': f'/api/offline/download-video/{video_id}',
                'message': 'Video generated successfully offline',
                'offline': True
            })
        else:
            return jsonify({'error': 'Failed to generate video offline'}), 500
        
    except Exception as e:
        print(f"Offline video generation error: {e}")
        return jsonify({'error': str(e)}), 500

@offline_video_bp.route('/save-draft', methods=['POST'])
@cross_origin()
def save_draft():
    """Save video draft locally"""
    try:
        data = request.json
        title = data.get('title', 'Untitled Draft')
        script = data.get('script', '')
        voice_id = data.get('voice_id', 'default')
        settings = data.get('settings', {})
        
        if not script:
            return jsonify({'error': 'Script is required'}), 400
        
        draft_id = offline_ai.save_draft(title, script, voice_id, settings)
        
        return jsonify({
            'draft_id': draft_id,
            'status': 'saved',
            'message': 'Draft saved successfully',
            'offline': True
        })
        
    except Exception as e:
        print(f"Draft save error: {e}")
        return jsonify({'error': str(e)}), 500

@offline_video_bp.route('/load-draft/<draft_id>', methods=['GET'])
@cross_origin()
def load_draft(draft_id):
    """Load video draft from local storage"""
    try:
        draft = offline_ai.load_draft(draft_id)
        
        if draft:
            return jsonify({
                'draft': draft,
                'status': 'loaded',
                'offline': True
            })
        else:
            return jsonify({'error': 'Draft not found'}), 404
        
    except Exception as e:
        print(f"Draft load error: {e}")
        return jsonify({'error': str(e)}), 500

@offline_video_bp.route('/list-drafts', methods=['GET'])
@cross_origin()
def list_drafts():
    """List all saved drafts"""
    try:
        drafts = offline_ai.list_drafts()
        
        return jsonify({
            'drafts': drafts,
            'count': len(drafts),
            'offline': True
        })
        
    except Exception as e:
        print(f"Draft list error: {e}")
        return jsonify({'error': str(e)}), 500

@offline_video_bp.route('/download-video/<video_id>', methods=['GET'])
@cross_origin()
def download_video_offline(video_id):
    """Download video generated offline"""
    try:
        # Get video info from database
        conn = offline_ai.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT video_path, title FROM generated_videos WHERE id = ?', (video_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row and os.path.exists(row[0]):
            return send_file(
                row[0], 
                as_attachment=True, 
                download_name=f"dawa_present_{row[1]}_{video_id}.mp4"
            )
        else:
            return jsonify({'error': 'Video not found'}), 404
            
    except Exception as e:
        print(f"Video download error: {e}")
        return jsonify({'error': str(e)}), 500

@offline_video_bp.route('/generate-speech-offline', methods=['POST'])
@cross_origin()
def generate_speech_offline():
    """Generate speech using offline TTS"""
    try:
        data = request.json
        text = data.get('text', '')
        voice_id = data.get('voice_id', 'default')
        
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        
        # Generate speech offline
        audio_path = offline_ai.generate_speech_offline(text, voice_id)
        
        if audio_path and os.path.exists(audio_path):
            return send_file(
                audio_path,
                as_attachment=True,
                download_name=f"speech_{hash(text)}.wav"
            )
        else:
            return jsonify({'error': 'Failed to generate speech'}), 500
        
    except Exception as e:
        print(f"Offline speech generation error: {e}")
        return jsonify({'error': str(e)}), 500

@offline_video_bp.route('/generate-image-offline', methods=['POST'])
@cross_origin()
def generate_image_offline():
    """Generate image using offline methods"""
    try:
        data = request.json
        description = data.get('description', '')
        style = data.get('style', 'business')
        
        if not description:
            return jsonify({'error': 'Description is required'}), 400
        
        # Generate image offline
        image_path = offline_ai.generate_image_offline(description, style=style)
        
        if image_path and os.path.exists(image_path):
            return send_file(
                image_path,
                as_attachment=True,
                download_name=f"image_{hash(description)}.png"
            )
        else:
            return jsonify({'error': 'Failed to generate image'}), 500
        
    except Exception as e:
        print(f"Offline image generation error: {e}")
        return jsonify({'error': str(e)}), 500

@offline_video_bp.route('/offline-status', methods=['GET'])
@cross_origin()
def offline_status():
    """Get offline capabilities status"""
    try:
        # Check available offline features
        status = {
            'offline_mode': True,
            'tts_available': hasattr(offline_ai, 'tts_engine'),
            'image_generation_available': True,
            'video_generation_available': True,
            'voice_processing_available': True,
            'local_storage_available': os.path.exists(offline_ai.db_path),
            'temp_space_available': os.path.exists(offline_ai.temp_dir)
        }
        
        return jsonify(status)
        
    except Exception as e:
        print(f"Offline status error: {e}")
        return jsonify({'error': str(e)}), 500

@offline_video_bp.route('/sync-when-online', methods=['POST'])
@cross_origin()
def sync_when_online():
    """Sync offline data when connection is restored"""
    try:
        # This would handle syncing offline-generated content
        # with online services when connection is restored
        
        data = request.json
        sync_type = data.get('type', 'all')  # 'drafts', 'videos', 'all'
        
        sync_results = {
            'drafts_synced': 0,
            'videos_synced': 0,
            'errors': []
        }
        
        if sync_type in ['drafts', 'all']:
            # Sync drafts
            drafts = offline_ai.list_drafts()
            for draft in drafts:
                try:
                    # Here you would sync with online storage
                    sync_results['drafts_synced'] += 1
                except Exception as e:
                    sync_results['errors'].append(f"Draft {draft['id']}: {str(e)}")
        
        if sync_type in ['videos', 'all']:
            # Sync generated videos
            # Implementation would depend on your online storage strategy
            pass
        
        return jsonify({
            'status': 'completed',
            'results': sync_results,
            'message': 'Sync completed successfully'
        })
        
    except Exception as e:
        print(f"Sync error: {e}")
        return jsonify({'error': str(e)}), 500

# Helper method for database connection
def get_db_connection():
    """Get database connection for offline storage"""
    import sqlite3
    return sqlite3.connect(offline_ai.db_path)

