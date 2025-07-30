from flask import Blueprint, jsonify, request, send_file
from flask_cors import cross_origin
import os
import uuid
import json
from werkzeug.utils import secure_filename
from datetime import datetime
from src.services.dzongkha_service import DzongkhaService

dzongkha_bp = Blueprint('dzongkha', __name__)

# Initialize Dzongkha service
dzongkha_service = DzongkhaService()

@dzongkha_bp.route('/dzongkha/capabilities', methods=['GET'])
@cross_origin()
def get_dzongkha_capabilities():
    """Get available Dzongkha processing capabilities"""
    try:
        capabilities = dzongkha_service.get_dzongkha_capabilities()
        return jsonify({
            'capabilities': capabilities,
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dzongkha_bp.route('/dzongkha/text-to-speech', methods=['POST'])
@cross_origin()
def dzongkha_text_to_speech():
    """Convert Dzongkha text to speech"""
    try:
        data = request.json
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        
        # Validate Dzongkha text
        validation = dzongkha_service.validate_dzongkha_text(text)
        if not validation['is_valid'] and validation['confidence'] < 0.3:
            return jsonify({
                'error': 'Text does not appear to be in Dzongkha script',
                'validation': validation
            }), 400
        
        # Generate speech
        audio_path = dzongkha_service.text_to_speech_dzongkha(text)
        
        if audio_path and os.path.exists(audio_path):
            return send_file(
                audio_path,
                as_attachment=True,
                download_name=f"dzongkha_speech_{hash(text)}.wav",
                mimetype='audio/wav'
            )
        else:
            return jsonify({'error': 'Failed to generate speech'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dzongkha_bp.route('/dzongkha/speech-to-text', methods=['POST'])
@cross_origin()
def dzongkha_speech_to_text():
    """Convert Dzongkha speech to text"""
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'Audio file is required'}), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'error': 'No audio file selected'}), 400
        
        # Save uploaded audio file
        filename = secure_filename(audio_file.filename)
        audio_path = os.path.join(dzongkha_service.temp_dir, f'upload_{uuid.uuid4()}_{filename}')
        audio_file.save(audio_path)
        
        # Transcribe audio
        result = dzongkha_service.speech_to_text_dzongkha(audio_path)
        
        # Clean up uploaded file
        try:
            os.remove(audio_path)
        except:
            pass
        
        return jsonify({
            'transcription': result,
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dzongkha_bp.route('/dzongkha/translate', methods=['POST'])
@cross_origin()
def translate_text():
    """Translate text between Dzongkha and English"""
    try:
        data = request.json
        text = data.get('text', '')
        source_lang = data.get('source_lang', 'dz')
        target_lang = data.get('target_lang', 'en')
        
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        
        # Perform translation
        result = dzongkha_service.translate_text(text, source_lang, target_lang)
        
        return jsonify({
            'translation': result,
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dzongkha_bp.route('/dzongkha/detect-language', methods=['POST'])
@cross_origin()
def detect_language():
    """Detect if text is in Dzongkha"""
    try:
        data = request.json
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        
        # Detect language
        result = dzongkha_service.detect_language(text)
        
        return jsonify({
            'detection': result,
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dzongkha_bp.route('/dzongkha/validate-text', methods=['POST'])
@cross_origin()
def validate_dzongkha_text():
    """Validate Dzongkha text"""
    try:
        data = request.json
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        
        # Validate text
        result = dzongkha_service.validate_dzongkha_text(text)
        
        return jsonify({
            'validation': result,
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dzongkha_bp.route('/dzongkha/generate-video-script', methods=['POST'])
@cross_origin()
def generate_dzongkha_video_script():
    """Generate Dzongkha video script from English"""
    try:
        data = request.json
        english_script = data.get('english_script', '')
        
        if not english_script:
            return jsonify({'error': 'English script is required'}), 400
        
        # Generate Dzongkha script
        result = dzongkha_service.generate_dzongkha_video_script(english_script)
        
        return jsonify({
            'script_generation': result,
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dzongkha_bp.route('/dzongkha/transcription-history', methods=['GET'])
@cross_origin()
def get_transcription_history():
    """Get recent Dzongkha transcription history"""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        history = dzongkha_service.get_transcription_history(limit)
        
        return jsonify({
            'history': history,
            'count': len(history),
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dzongkha_bp.route('/dzongkha/generate-video-with-dzongkha', methods=['POST'])
@cross_origin()
def generate_video_with_dzongkha():
    """Generate video with Dzongkha script"""
    try:
        data = request.json
        dzongkha_script = data.get('dzongkha_script', '')
        english_script = data.get('english_script', '')
        voice_preference = data.get('voice_preference', 'dzongkha')
        style = data.get('style', 'traditional')
        title = data.get('title', 'Dzongkha Video')
        
        if not dzongkha_script and not english_script:
            return jsonify({'error': 'Either Dzongkha or English script is required'}), 400
        
        # If only English script provided, attempt to generate Dzongkha
        if not dzongkha_script and english_script:
            script_result = dzongkha_service.generate_dzongkha_video_script(english_script)
            dzongkha_script = script_result.get('dzongkha_script', english_script)
        
        # Validate Dzongkha script
        validation = dzongkha_service.validate_dzongkha_text(dzongkha_script)
        
        # Generate Dzongkha audio
        audio_path = None
        if voice_preference == 'dzongkha' and validation['is_valid']:
            try:
                audio_path = dzongkha_service.text_to_speech_dzongkha(dzongkha_script)
            except Exception as e:
                print(f"Dzongkha TTS failed: {e}")
        
        # Prepare video generation data
        video_data = {
            'script': dzongkha_script,
            'english_script': english_script,
            'audio_path': audio_path,
            'style': style,
            'title': title,
            'language': 'dzongkha',
            'validation': validation
        }
        
        # For now, return the prepared data
        # In a full implementation, this would integrate with the video generation service
        return jsonify({
            'video_data': video_data,
            'job_id': f'dzongkha_video_{uuid.uuid4()}',
            'status': 'prepared',
            'message': 'Dzongkha video data prepared successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dzongkha_bp.route('/dzongkha/test-integration', methods=['GET'])
@cross_origin()
def test_dzongkha_integration():
    """Test Dzongkha service integration"""
    try:
        # Test text
        test_text = "བཀྲ་ཤིས་བདེ་ལེགས།"  # "Tashi Delek" in Dzongkha
        
        # Test language detection
        detection = dzongkha_service.detect_language(test_text)
        
        # Test text validation
        validation = dzongkha_service.validate_dzongkha_text(test_text)
        
        # Test TTS (if available)
        tts_result = None
        try:
            if dzongkha_service.tts_available:
                audio_path = dzongkha_service.text_to_speech_dzongkha(test_text)
                tts_result = {"status": "success", "audio_generated": os.path.exists(audio_path)}
            else:
                tts_result = {"status": "not_available", "message": "TTS model not loaded"}
        except Exception as e:
            tts_result = {"status": "error", "message": str(e)}
        
        # Get capabilities
        capabilities = dzongkha_service.get_dzongkha_capabilities()
        
        return jsonify({
            'test_results': {
                'language_detection': detection,
                'text_validation': validation,
                'tts_test': tts_result,
                'capabilities': capabilities
            },
            'test_text': test_text,
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

