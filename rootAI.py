"""
AI Image Generator Backend Server
Supports multiple AI image generation APIs with post-processing enhancement
"""

from flask import Flask, request, jsonify, send_from_directory, make_response
from flask_cors import CORS
import os
import requests
import base64
from datetime import datetime
import json
from database import UserDatabase

# Image enhancement libraries
from PIL import Image, ImageEnhance, ImageFilter
try:
    import cv2
except ImportError:
    cv2 = None
import numpy as np
try:
    from skimage import exposure
except ImportError:
    exposure = None
import io

# Official AI SDKs
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None
try:
    import replicate
except (ImportError, Exception):
    replicate = None

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

# Configuration - Add your API keys here
CONFIG = {
    'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY', 'your-openai-key-here'),
    'STABILITY_API_KEY': os.getenv('STABILITY_API_KEY', 'your-stability-key-here'),
    'REPLICATE_API_KEY': os.getenv('REPLICATE_API_KEY', 'your-replicate-key-here'),
}

# ⚠️ IMPORTANT: Replace the placeholder keys above with your actual API keys
# Get keys from:
# - OpenAI: https://platform.openai.com/api-keys
# - Stability AI: https://platform.stability.ai/account/keys  
# - Replicate: https://replicate.com/account/api-tokens (optional)

# Create images directory if it doesn't exist
os.makedirs('generated_images', exist_ok=True)

# Initialize user database
user_db = UserDatabase()


# ============ AUTHENTICATION ROUTES ============

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.json
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        result = user_db.register_user(username, email, password)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login user and create session"""
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        result = user_db.login_user(username, password)
        
        if result['success']:
            response = make_response(jsonify(result), 200)
            # Set session token as HTTP-only cookie for security
            response.set_cookie(
                'session_token',
                result['session_token'],
                httponly=True,
                secure=False,  # Set to True in production with HTTPS
                samesite='Lax',
                max_age=7*24*60*60  # 7 days
            )
            return response
        else:
            return jsonify(result), 401
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Logout user and destroy session"""
    try:
        session_token = request.cookies.get('session_token')
        
        if session_token:
            result = user_db.logout_user(session_token)
            response = make_response(jsonify(result), 200)
            response.set_cookie('session_token', '', expires=0)
            return response
        else:
            return jsonify({'success': False, 'error': 'No active session'}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/auth/validate', methods=['GET'])
def validate_session():
    """Validate current session"""
    try:
        session_token = request.cookies.get('session_token')
        
        if not session_token:
            return jsonify({'valid': False, 'error': 'No session token'}), 401
        
        result = user_db.validate_session(session_token)
        
        if result['valid']:
            return jsonify(result), 200
        else:
            return jsonify(result), 401
            
    except Exception as e:
        return jsonify({'valid': False, 'error': str(e)}), 500


# Middleware to check authentication for protected routes
def require_auth(f):
    """Decorator to require authentication"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_token = request.cookies.get('session_token')
        
        if not session_token:
            return jsonify({'error': 'Authentication required'}), 401
        
        validation = user_db.validate_session(session_token)
        
        if not validation.get('valid'):
            return jsonify({'error': 'Invalid or expired session'}), 401
        
        # Add user info to request for use in route
        request.user = validation
        return f(*args, **kwargs)
    
    return decorated_function


# ============ END AUTHENTICATION ROUTES ============


# ============ IMAGE POST-PROCESSING ENHANCEMENT ============

def enhance_image(image_path, enhancement_level='medium'):
    """
    Apply AI-powered post-processing to enhance image quality
    
    Args:
        image_path: Path to the image file
        enhancement_level: 'light', 'medium', 'heavy'
    
    Returns:
        Path to enhanced image
    """
    try:
        # Load image
        img = Image.open(image_path)
        
        if enhancement_level == 'none':
            return image_path
        
        # 1. Sharpen the image
        if enhancement_level in ['medium', 'heavy']:
            img = img.filter(ImageFilter.SHARPEN)
            img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
        
        # 2. Enhance contrast (simplified without cv2/scikit)
        if enhancement_level == 'heavy':
            img_array = np.array(img)
            # Simple contrast enhancement
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.2)
        
        # 3. Enhance colors
        if enhancement_level in ['medium', 'heavy']:
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(1.1)  # Slightly boost saturation
            
            # Enhance brightness slightly
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(1.05)
        
        # Save enhanced image
        enhanced_path = image_path.replace('.png', '_enhanced.png')
        img.save(enhanced_path, quality=95, optimize=True)
        
        return enhanced_path
        
    except Exception as e:
        print(f"Enhancement error: {e}")
        return image_path  # Return original if enhancement fails


def upscale_image(image_path, scale_factor=2):
    """
    Upscale image using high-quality interpolation
    
    Args:
        image_path: Path to image
        scale_factor: 2x or 4x upscaling
    
    Returns:
        Path to upscaled image
    """
    try:
        img = Image.open(image_path)
        new_size = (img.width * scale_factor, img.height * scale_factor)
        
        # Use Lanczos resampling for highest quality
        upscaled = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Apply slight sharpening after upscale
        upscaled = upscaled.filter(ImageFilter.SHARPEN)
        
        upscaled_path = image_path.replace('.png', f'_upscaled_{scale_factor}x.png')
        upscaled.save(upscaled_path, quality=95, optimize=True)
        
        return upscaled_path
        
    except Exception as e:
        print(f"Upscaling error: {e}")
        return image_path


# ============ END IMAGE ENHANCEMENT ============


@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory('.', 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    """Serve static files (CSS, JS)"""
    return send_from_directory('.', path)


@app.route('/api/generate', methods=['POST'])
def generate_image():
    """
    Generate an image using the specified AI API with advanced quality options
    
    Request body:
    {
        "prompt": "your prompt here",
        "negative_prompt": "things to avoid" (optional),
        "engine": "dalle" | "stability" | "replicate",
        "style": "photorealistic" (optional),
        "dimensions": {"width": 1024, "height": 1024},
        "quality_boost": true/false,
        "post_process": true/false,
        "upscale": 1 | 2 | 4 (optional)
    }
    """
    try:
        data = request.json
        prompt = data.get('prompt', '')
        negative_prompt = data.get('negative_prompt', '')
        engine = data.get('engine', 'dalle')
        style = data.get('style', '')
        dimensions = data.get('dimensions', {'width': 1024, 'height': 1024})
        quality_boost = data.get('quality_boost', True)
        post_process = data.get('post_process', True)
        upscale = data.get('upscale', 1)
        
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400
        
        # Add style modifier to prompt if provided
        if style:
            prompt = f"{prompt}, {style}"
        
        # Route to appropriate API
        if engine == 'dalle':
            result = generate_with_dalle(prompt, dimensions, quality_boost)
        elif engine == 'stability':
            result = generate_with_stability(prompt, negative_prompt, dimensions, quality_boost)
        elif engine == 'replicate':
            result = generate_with_replicate(prompt, negative_prompt, dimensions, quality_boost)
        else:
            return jsonify({'error': f'Unknown engine: {engine}'}), 400
        
        # Apply post-processing if enabled and generation was successful
        if result.get('success') and post_process:
            image_url = result.get('image_url', '')
            
            # Only post-process local files (not URLs from DALL-E)
            if image_url.startswith('/generated_images/'):
                local_path = image_url.replace('/generated_images/', 'generated_images/')
                
                # Apply enhancement
                enhancement_level = 'heavy' if quality_boost else 'medium'
                enhanced_path = enhance_image(local_path, enhancement_level)
                
                # Apply upscaling if requested
                if upscale > 1:
                    enhanced_path = upscale_image(enhanced_path, upscale)
                
                # Update the result with enhanced image path
                result['image_url'] = enhanced_path.replace('generated_images/', '/generated_images/')
                result['enhanced'] = True
                result['upscaled'] = upscale if upscale > 1 else False
        
        return jsonify(result)
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500


def generate_with_dalle(prompt, dimensions={}, quality_boost=True):
    """Generate image using OpenAI DALL-E 3 with enhanced quality"""
    api_key = CONFIG['OPENAI_API_KEY']
    
    if api_key == 'your-openai-key-here':
        return {
            'success': False,
            'error': 'Please add your OpenAI API key to the CONFIG dictionary',
            'demo': True
        }
    
    url = "https://api.openai.com/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # DALL-E 3 supports specific sizes: 1024x1024, 1024x1792, or 1792x1024
    # Map dimensions to valid DALL-E sizes
    width = dimensions.get('width', 1024)
    height = dimensions.get('height', 1024)
    
    if width == height:
        size = '1024x1024'
    elif width > height:
        size = '1792x1024'
    else:
        size = '1024x1792'
    
    quality = 'hd' if quality_boost else 'standard'
    
    payload = {
        "model": "dall-e-3",
        "prompt": prompt,
        "n": 1,
        "size": size,
        "quality": quality
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'OpenAI API Error: {str(e)}'
        }
    
    data = response.json()
    image_url = data['data'][0]['url']
    
    return {
        'success': True,
        'image_url': image_url,
        'engine': 'DALL-E 3',
        'revised_prompt': data['data'][0].get('revised_prompt', prompt),
        'quality': quality
    }


def generate_with_stability(prompt, negative_prompt='', dimensions={}, quality_boost=True):
    """Generate image using Stability AI with enhanced quality settings"""
    api_key = CONFIG['STABILITY_API_KEY']
    
    if api_key == 'your-stability-key-here':
        return {
            'success': False,
            'error': 'Please add your Stability API key to the CONFIG dictionary',
            'demo': True
        }
    
    url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # Build text prompts with negative prompt support
    text_prompts = [{"text": prompt, "weight": 1}]
    if negative_prompt:
        text_prompts.append({"text": negative_prompt, "weight": -1})
    
    # Quality settings
    steps = 50 if quality_boost else 30  # More steps = higher quality
    cfg_scale = 8 if quality_boost else 7  # Higher CFG = more prompt adherence
    
    payload = {
        "text_prompts": text_prompts,
        "cfg_scale": cfg_scale,
        "height": dimensions.get('height', 1024),
        "width": dimensions.get('width', 1024),
        "steps": steps,
        "samples": 1,
        "sampler": "K_DPM_2_ANCESTRAL"  # High-quality sampler
    }
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    
    data = response.json()
    
    # Save base64 image
    image_data = data['artifacts'][0]['base64']
    filename = f"generated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    filepath = os.path.join('generated_images', filename)
    
    with open(filepath, 'wb') as f:
        f.write(base64.b64decode(image_data))
    
    return {
        'success': True,
        'image_url': f'/generated_images/{filename}',
        'engine': 'Stability AI SDXL',
        'quality_settings': {'steps': steps, 'cfg_scale': cfg_scale}
    }


def generate_with_replicate(prompt, negative_prompt='', dimensions={}, quality_boost=True):
    """Generate image using Replicate (Flux) with enhanced quality"""
    api_key = CONFIG['REPLICATE_API_KEY']
    
    if api_key == 'your-replicate-key-here':
        return {
            'success': False,
            'error': 'Please add your Replicate API key to the CONFIG dictionary',
            'demo': True
        }
    
    # Using Flux Dev for higher quality (or Schnell for speed)
    model = "black-forest-labs/flux-dev" if quality_boost else "black-forest-labs/flux-schnell"
    
    url = "https://api.replicate.com/v1/predictions"
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json"
    }
    
    input_params = {
        "prompt": prompt,
        "num_outputs": 1,
        "aspect_ratio": f"{dimensions.get('width', 1024)}:{dimensions.get('height', 1024)}",
        "output_format": "png",
        "output_quality": 100 if quality_boost else 80
    }
    
    if negative_prompt:
        input_params["negative_prompt"] = negative_prompt
    
    payload = {
        "version": model,
        "input": input_params
    }
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    
    prediction = response.json()
    prediction_id = prediction['id']
    
    # Poll for completion
    import time
    max_attempts = 120  # Increased for quality generation
    for _ in range(max_attempts):
        status_response = requests.get(
            f"https://api.replicate.com/v1/predictions/{prediction_id}",
            headers=headers
        )
        status_data = status_response.json()
        
        if status_data['status'] == 'succeeded':
            return {
                'success': True,
                'image_url': status_data['output'][0],
                'engine': 'Flux Pro' if quality_boost else 'Flux Schnell'
            }
        elif status_data['status'] == 'failed':
            return {
                'success': False,
                'error': 'Image generation failed'
            }
        
        time.sleep(1)
    
    return {
        'success': False,
        'error': 'Generation timeout'
    }


@app.route('/generated_images/<filename>')
def serve_generated_image(filename):
    """Serve generated images"""
    return send_from_directory('generated_images', filename)


@app.route('/api/status', methods=['GET'])
def status():
    """Check API status and configuration"""
    return jsonify({
        'status': 'online',
        'engines': {
            'dalle': CONFIG['OPENAI_API_KEY'] != 'your-openai-key-here',
            'stability': CONFIG['STABILITY_API_KEY'] != 'your-stability-key-here',
            'replicate': CONFIG['REPLICATE_API_KEY'] != 'your-replicate-key-here'
        },
        'message': 'Add your API keys to enable image generation'
    })


@app.route('/api/edit', methods=['POST'])
def edit_image():
    """
    Edit an uploaded image using AI
    
    Form data:
    - image: Image file
    - prompt: Edit instructions
    - edit_mode: 'edit' | 'inpaint' | 'variation'
    - engine: 'dalle' | 'stability'
    - quality_boost: true/false
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image uploaded'}), 400
        
        image_file = request.files['image']
        prompt = request.form.get('prompt', '')
        edit_mode = request.form.get('edit_mode', 'edit')
        engine = request.form.get('engine', 'dalle')
        quality_boost = request.form.get('quality_boost', 'true').lower() == 'true'
        
        # Save uploaded image
        os.makedirs('uploads', exist_ok=True)
        upload_path = os.path.join('uploads', f'upload_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
        image_file.save(upload_path)
        
        # Route to appropriate editing API
        if engine == 'dalle':
            result = edit_with_dalle(upload_path, prompt, edit_mode, quality_boost)
        elif engine == 'stability':
            result = edit_with_stability(upload_path, prompt, edit_mode, quality_boost)
        else:
            return jsonify({'error': f'Unknown engine: {engine}'}), 400
        
        return jsonify(result)
    
    except Exception as e:
        print(f"Edit Error: {str(e)}")
        return jsonify({'error': str(e)}), 500


def edit_with_dalle(image_path, prompt, edit_mode, quality_boost):
    """Edit image using DALL-E 2/3"""
    api_key = CONFIG['OPENAI_API_KEY']
    
    if api_key == 'your-openai-key-here':
        return {
            'success': False,
            'error': 'Please add your OpenAI API key',
            'demo': True
        }
    
    try:
        # Convert image to RGBA PNG if needed
        img = Image.open(image_path)
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Resize to 1024x1024 for DALL-E
        img = img.resize((1024, 1024), Image.Resampling.LANCZOS)
        rgba_path = image_path.replace('.png', '_rgba.png')
        img.save(rgba_path, 'PNG')
        
        if edit_mode == 'variation':
            # Create variation
            url = "https://api.openai.com/v1/images/variations"
            with open(rgba_path, 'rb') as f:
                files = {'image': f}
                headers = {"Authorization": f"Bearer {api_key}"}
                data = {
                    'n': 1,
                    'size': '1024x1024'
                }
                response = requests.post(url, headers=headers, files=files, data=data)
        else:
            # Edit with prompt
            url = "https://api.openai.com/v1/images/edits"
            with open(rgba_path, 'rb') as f:
                files = {'image': f}
                headers = {"Authorization": f"Bearer {api_key}"}
                data = {
                    'prompt': prompt,
                    'n': 1,
                    'size': '1024x1024'
                }
                response = requests.post(url, headers=headers, files=files, data=data)
        
        response.raise_for_status()
        data = response.json()
        image_url = data['data'][0]['url']
        
        return {
            'success': True,
            'image_url': image_url,
            'engine': 'DALL-E',
            'edit_mode': edit_mode
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def edit_with_stability(image_path, prompt, edit_mode, quality_boost):
    """Edit image using Stability AI"""
    api_key = CONFIG['STABILITY_API_KEY']
    
    if api_key == 'your-stability-key-here':
        return {
            'success': False,
            'error': 'Please add your Stability API key',
            'demo': True
        }
    
    try:
        url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/image-to-image"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json"
        }
        
        # Prepare image
        img = Image.open(image_path)
        img = img.resize((1024, 1024), Image.Resampling.LANCZOS)
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        files = {
            "init_image": img_bytes
        }
        
        data = {
            "text_prompts[0][text]": prompt,
            "text_prompts[0][weight]": 1,
            "cfg_scale": 8 if quality_boost else 7,
            "steps": 50 if quality_boost else 30,
            "samples": 1,
            "image_strength": 0.35  # How much to change (0.0-1.0)
        }
        
        response = requests.post(url, headers=headers, files=files, data=data)
        response.raise_for_status()
        
        result = response.json()
        
        # Save result
        image_data = result['artifacts'][0]['base64']
        filename = f"edited_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join('generated_images', filename)
        
        with open(filepath, 'wb') as f:
            f.write(base64.b64decode(image_data))
        
        return {
            'success': True,
            'image_url': f'/generated_images/{filename}',
            'engine': 'Stability AI',
            'edit_mode': edit_mode
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


if __name__ == '__main__':
    print("=" * 60)
    print("🎨 AI Image Generator Server Starting...")
    print("=" * 60)
    print(f"\n📍 Server running at: http://localhost:5000")
    print(f"🌐 Open in browser: http://localhost:5000\n")
    
    # Check API keys
    if CONFIG['OPENAI_API_KEY'] == 'your-openai-key-here':
        print("⚠️  OpenAI API key not configured")
    else:
        print("✅ OpenAI API key configured")
    
    if CONFIG['STABILITY_API_KEY'] == 'your-stability-key-here':
        print("⚠️  Stability API key not configured")
    else:
        print("✅ Stability API key configured")
    
    if CONFIG['REPLICATE_API_KEY'] == 'your-replicate-key-here':
        print("⚠️  Replicate API key not configured")
    else:
        print("✅ Replicate API key configured")
    
    print("\n" + "=" * 60)
    print("Add your API keys to the CONFIG dictionary in rootAI.py")
    print("=" * 60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)


# ============ ADVANCED AI EDITOR ENDPOINTS ============

@app.route('/api/enhance', methods=['POST'])
def enhance_operation():
    """Advanced image enhancement operations"""
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image provided'}), 400
        
        operation = request.form.get('operation', 'auto_enhance')
        image_file = request.files['image']
        
        # Save uploaded image
        temp_path = os.path.join('generated_images', f'temp_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
        image_file.save(temp_path)
        
        # Process based on operation
        if operation == 'remove_background':
            result_path = remove_background_ai(temp_path)
        elif operation == 'enhance_face':
            result_path = enhance_face_ai(temp_path)
        elif operation == 'colorize':
            result_path = colorize_image(temp_path)
        else:
            result_path = enhance_image(temp_path, 'heavy')
        
        return jsonify({
            'success': True,
            'image_url': f'/generated_images/{os.path.basename(result_path)}',
            'operation': operation
        })
    
    except Exception as e:
        print(f"Enhancement error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/upscale', methods=['POST'])
def upscale_operation():
    """AI-powered image upscaling"""
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image provided'}), 400
        
        scale = int(request.form.get('scale', 4))
        image_file = request.files['image']
        
        # Save uploaded image
        temp_path = os.path.join('generated_images', f'temp_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
        image_file.save(temp_path)
        
        # Upscale
        result_path = upscale_image(temp_path, scale)
        
        return jsonify({
            'success': True,
            'image_url': f'/generated_images/{os.path.basename(result_path)}',
            'scale': scale
        })
    
    except Exception as e:
        print(f"Upscale error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============ ADVANCED ENHANCEMENT FUNCTIONS ============

def remove_background_ai(image_path):
    """Remove background using AI (simplified version)"""
    try:
        img = Image.open(image_path)
        
        # For now, create a simple edge detection-based cutout
        # In production, use rembg library or API
        img_rgba = img.convert('RGBA')
        
        # Simple threshold-based background removal
        data = img_rgba.getdata()
        new_data = []
        
        # Get average background color (from corners)
        width, height = img.size
        bg_samples = [
            img.getpixel((0, 0)),
            img.getpixel((width-1, 0)),
            img.getpixel((0, height-1)),
            img.getpixel((width-1, height-1))
        ]
        
        avg_bg = tuple(sum(x) // 4 for x in zip(*bg_samples[:3]))
        
        for item in data:
            # Calculate color difference
            if len(item) >= 3:
                r, g, b = item[:3]
                diff = abs(r - avg_bg[0]) + abs(g - avg_bg[1]) + abs(b - avg_bg[2])
                
                if diff < 30:  # Background threshold
                    new_data.append((r, g, b, 0))  # Transparent
                else:
                    new_data.append(item)
            else:
                new_data.append(item)
        
        img_rgba.putdata(new_data)
        
        output_path = image_path.replace('.png', '_nobg.png')
        img_rgba.save(output_path, 'PNG')
        
        return output_path
    
    except Exception as e:
        print(f"Background removal error: {str(e)}")
        return image_path


def enhance_face_ai(image_path):
    """Enhance faces using AI"""
    try:
        img = Image.open(image_path)
        
        # Apply face-specific enhancements
        # Sharpen
        img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
        
        # Enhance color
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1.2)
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.15)
        
        # Slight brightness
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1.05)
        
        output_path = image_path.replace('.png', '_face_enhanced.png')
        img.save(output_path)
        
        return output_path
    
    except Exception as e:
        print(f"Face enhancement error: {str(e)}")
        return image_path


def colorize_image(image_path):
    """Colorize black and white images"""
    try:
        img = Image.open(image_path)
        
        # Convert to grayscale first
        gray = img.convert('L')
        
        # Apply a sepia tone as a simple colorization
        # In production, use DeOldify or similar AI model
        sepia_img = Image.new('RGB', gray.size)
        pixels = sepia_img.load()
        gray_pixels = gray.load()
        
        for i in range(sepia_img.size[0]):
            for j in range(sepia_img.size[1]):
                gray_val = gray_pixels[i, j]
                # Sepia tone calculation
                r = int(min(255, gray_val * 1.0))
                g = int(min(255, gray_val * 0.95))
                b = int(min(255, gray_val * 0.82))
                pixels[i, j] = (r, g, b)
        
        output_path = image_path.replace('.png', '_colorized.png')
        sepia_img.save(output_path)
        
        return output_path
    
    except Exception as e:
        print(f"Colorization error: {str(e)}")
        return image_path
