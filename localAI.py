# Local AI Image Generator - No API Keys Required
# Uses Stable Diffusion via diffusers library

from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import os
from datetime import datetime
from PIL import Image
import torch
import gc
import json
import time

app = Flask(__name__)
CORS(app)

# Create images directory
os.makedirs('generated_images', exist_ok=True)

# Global variables
pipe = None
device = None
progress_data = {'step': 0, 'total': 20, 'status': 'idle'}

def initialize_model():
    """Initialize Stable Diffusion model (runs locally)"""
    global pipe, device
    
    try:
        from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler
        
        print("[*] Loading Stable Diffusion model (this may take a few minutes first time)...")
        
        # Check if CUDA is available
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[*] Using device: {device.upper()}")
        
        if device == "cpu":
            print("[!] Running on CPU - generation will be slow (2-5 minutes per image)")
            print("[+] Consider deploying to a GPU server for 10x faster generation")
        
        # Load model - using SD 1.5 (smaller, faster)
        model_id = "runwayml/stable-diffusion-v1-5"
        
        # CPU-specific loading to avoid device mismatch
        if device == "cpu":
            pipe = StableDiffusionPipeline.from_pretrained(
                model_id,
                torch_dtype=torch.float32,
                safety_checker=None,
                requires_safety_checker=False,
                low_cpu_mem_usage=True
            )
        else:
            pipe = StableDiffusionPipeline.from_pretrained(
                model_id,
                torch_dtype=torch.float16,
                safety_checker=None,
                requires_safety_checker=False
            )
        
        # Use faster scheduler
        pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
        
        pipe = pipe.to(device)
        
        # Enable memory optimization
        pipe.enable_attention_slicing()
        if device == "cuda":
            pipe.enable_vae_slicing()
        
        print("[OK] Model loaded successfully!")
        return True
        
    except ImportError:
        print("[ERROR] Required packages not installed!")
        print("Run: pip install diffusers transformers accelerate torch torchvision")
        return False
    except Exception as e:
        print(f"[ERROR] Error loading model: {e}")
        return False

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

@app.route('/api/progress')
def get_progress():
    """Server-sent events endpoint for progress updates"""
    def generate():
        while True:
            yield f"data: {json.dumps(progress_data)}\n\n"
            time.sleep(0.5)
            if progress_data['status'] in ['completed', 'error']:
                break
    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/generate', methods=['POST'])
def generate_image():
    """Generate image using local Stable Diffusion"""
    global pipe, device, progress_data
    
    # Reset progress
    progress_data = {'step': 0, 'total': 20, 'status': 'initializing', 'message': 'Starting generation...'}
    
    # Initialize model if not loaded
    if pipe is None:
        progress_data['message'] = 'Loading AI model (first time only)...'
        if not initialize_model():
            progress_data = {'step': 0, 'total': 20, 'status': 'error', 'message': 'Model failed to load'}
            return jsonify({
                'success': False,
                'error': 'Model not loaded. Install: pip install diffusers transformers accelerate torch'
            }), 500
    
    try:
        data = request.json
        prompt = data.get('prompt', '')
        negative_prompt = data.get('negative_prompt', '')
        
        if not prompt:
            progress_data['status'] = 'error'
            return jsonify({'error': 'Prompt is required'}), 400
        
        print(f"[*] Generating: {prompt[:50]}...")
        progress_data = {'step': 0, 'total': 20, 'status': 'generating', 'message': 'Creating your image...'}
        
        # Progress callback
        def callback(step, timestep, latents):
            progress_data['step'] = step
            progress_data['message'] = f'Processing step {step}/20...'
            print(f"Progress: {step}/20")
        
        # Generate image with progress tracking
        with torch.no_grad():
            result = pipe(
                prompt=prompt,
                negative_prompt=negative_prompt if negative_prompt else None,
                num_inference_steps=20,  # Reduced from 25 for faster generation
                guidance_scale=7.5,
                height=512,
                width=512,
                callback=callback,
                callback_steps=1
            )
        
        progress_data = {'step': 20, 'total': 20, 'status': 'saving', 'message': 'Saving image...'}
        
        # Save image
        image = result.images[0]
        filename = f"generated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join('generated_images', filename)
        image.save(filepath)
        
        # Clear memory
        if device == "cuda":
            torch.cuda.empty_cache()
        gc.collect()
        
        print(f"[OK] Image saved: {filename}")
        progress_data = {'step': 20, 'total': 20, 'status': 'completed', 'message': 'Done!'}
        
        return jsonify({
            'success': True,
            'image_url': f'/generated_images/{filename}',
            'engine': 'Stable Diffusion 1.5 (Local - FREE)',
            'message': 'Image generated successfully!'
        })
        
    except Exception as e:
        print(f"[ERROR] Generation error: {e}")
        import traceback
        traceback.print_exc()
        progress_data = {'step': 0, 'total': 20, 'status': 'error', 'message': str(e)}
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/edit', methods=['POST'])
def edit_image():
    """Placeholder for image editing"""
    return jsonify({
        'success': False,
        'error': 'Image editing not yet implemented for local mode'
    }), 501

if __name__ == '__main__':
    print("=" * 50)
    print("PICLY - LOCAL AI IMAGE GENERATOR")
    print("=" * 50)
    print("")
    print("Server running at: http://localhost:5000")
    print("Open in browser: http://localhost:5000")
    print("")
    print("NO API KEYS REQUIRED!")
    print("Runs 100% on your computer")
    print("Free unlimited generations")
    print("")
    print("=" * 50)
    print("First time setup:")
    print("1. Install dependencies: pip install diffusers transformers accelerate torch torchvision")
    print("2. Model will auto-download on first run (~4GB)")
    print("3. GPU recommended but CPU works too")
    print("")
    print("Note: First generation takes longer as model loads")
    print("=" * 50)
    print("")
    
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
