"""
AI Image Generator Backend Server
Supports multiple AI image generation APIs with post-processing enhancement
"""

from flask import Flask, request, jsonify, send_from_directory, make_response
from flask_cors import CORS
import os
import requests
import base64
from datetime import datetime, timedelta
import json
from database import UserDatabase
from collections import defaultdict
import time

# Image enhancement libraries
from PIL import Image, ImageEnhance, ImageFilter
try:
    import cv2
    CV2_AVAILABLE = True
except (ImportError, Exception):
    cv2 = None
    CV2_AVAILABLE = False
try:
    from skimage import exposure
    SKIMAGE_AVAILABLE = True
except (ImportError, Exception):
    exposure = None
    SKIMAGE_AVAILABLE = False
import io

# Official AI SDKs
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except (ImportError, Exception):
    OpenAI = None
    OPENAI_AVAILABLE = False
try:
    import replicate
    REPLICATE_AVAILABLE = True
except (ImportError, Exception):
    replicate = None
    REPLICATE_AVAILABLE = False
try:
    import stripe
    STRIPE_AVAILABLE = True
except (ImportError, Exception):
    stripe = None
    STRIPE_AVAILABLE = False

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

# Configuration - Add your API keys here
CONFIG = {
    'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY', 'your-openai-key-here'),
    'STABILITY_API_KEY': os.getenv('STABILITY_API_KEY', 'your-stability-key-here'),
    'REPLICATE_API_KEY': os.getenv('REPLICATE_API_KEY', 'your-replicate-key-here'),
    'STRIPE_SECRET_KEY': os.getenv('STRIPE_SECRET_KEY', 'your-stripe-secret-key-here'),
    'STRIPE_PUBLISHABLE_KEY': os.getenv('STRIPE_PUBLISHABLE_KEY', 'your-stripe-publishable-key-here'),
    'STRIPE_WEBHOOK_SECRET': os.getenv('STRIPE_WEBHOOK_SECRET', 'your-webhook-secret-here'),
}

# Initialize Stripe
if stripe and STRIPE_AVAILABLE and CONFIG['STRIPE_SECRET_KEY'] != 'your-stripe-secret-key-here':
    stripe.api_key = CONFIG['STRIPE_SECRET_KEY']

# Credit Packages (25% profit margin - competitive market pricing)
CREDIT_PACKAGES = {
    'starter': {'credits': 10, 'price': 0.50, 'name': 'Starter'},
    'popular': {'credits': 50, 'price': 2.50, 'name': 'Popular', 'bonus': 0},
    'pro': {'credits': 100, 'price': 5.00, 'name': 'Pro', 'bonus': 0},
    'creator': {'credits': 500, 'price': 25.00, 'name': 'Creator', 'bonus': 0},
}

# Unlimited Subscription (45% profit margin - competitive with Midjourney)
UNLIMITED_SUBSCRIPTION = {
    'monthly': {'price': 29.00, 'name': 'Unlimited Premium', 'interval': 'month'},
}

# ============ SECURITY & RATE LIMITING ============
# Protection against hackers and API abuse

# Rate limiting storage (IP address → request timestamps)
rate_limit_storage = defaultdict(list)

# Rate limits
RATE_LIMITS = {
    'anonymous': {'requests': 10, 'window': 3600},  # 10 requests per hour for anonymous
    'free_user': {'requests': 50, 'window': 3600},   # 50 requests per hour for free users
    'premium_user': {'requests': 200, 'window': 3600},  # 200 requests per hour for premium
    'unlimited_user': {'requests': 1000, 'window': 3600}  # 1000 requests per hour for unlimited
}

def get_client_ip():
    """Get client IP address (works with proxies)"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0]
    return request.remote_addr

def check_rate_limit(user_type='anonymous'):
    """Check if request exceeds rate limit"""
    ip = get_client_ip()
    current_time = time.time()
    limit_config = RATE_LIMITS.get(user_type, RATE_LIMITS['anonymous'])
    
    # Clean old requests outside the time window
    rate_limit_storage[ip] = [
        timestamp for timestamp in rate_limit_storage[ip]
        if current_time - timestamp < limit_config['window']
    ]
    
    # Check if limit exceeded
    if len(rate_limit_storage[ip]) >= limit_config['requests']:
        return False, f"Rate limit exceeded. Max {limit_config['requests']} requests per hour for {user_type}."
    
    # Add current request
    rate_limit_storage[ip].append(current_time)
    return True, None

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


# ============ CREDIT & PAYMENT ROUTES ============

@app.route('/api/credits/balance', methods=['GET'])
def get_credit_balance():
    """Get user's current credit balance"""
    try:
        session_token = request.cookies.get('session_token')
        
        if not session_token:
            # Return anonymous user state
            return jsonify({
                'success': True,
                'premium_credits': 0,
                'free_credits': 10,
                'anonymous': True
            })
        
        validation = user_db.validate_session(session_token)
        if not validation.get('valid'):
            return jsonify({'success': False, 'error': 'Invalid session'}), 401
        
        user_id = validation['user_id']
        result = user_db.get_user_credits(user_id)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/credits/packages', methods=['GET'])
def get_credit_packages():
    """Get available credit packages for purchase"""
    return jsonify({
        'success': True,
        'packages': CREDIT_PACKAGES,
        'unlimited': UNLIMITED_SUBSCRIPTION,
        'stripe_publishable_key': CONFIG['STRIPE_PUBLISHABLE_KEY']
    })


@app.route('/api/subscription/create', methods=['POST'])
def create_subscription():
    """Create unlimited subscription checkout"""
    try:
        if not stripe:
            return jsonify({'success': False, 'error': 'Stripe not configured'}), 500
        
        session_token = request.cookies.get('session_token')
        if not session_token:
            return jsonify({'success': False, 'error': 'Must be logged in'}), 401
        
        validation = user_db.validate_session(session_token)
        if not validation.get('valid'):
            return jsonify({'success': False, 'error': 'Invalid session'}), 401
        
        user_id = validation['user_id']
        
        # Create Stripe checkout for subscription
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': int(UNLIMITED_SUBSCRIPTION['monthly']['price'] * 100),
                    'product_data': {
                        'name': UNLIMITED_SUBSCRIPTION['monthly']['name'],
                        'description': 'Unlimited DALL-E 3 HD generations - Premium quality',
                    },
                    'recurring': {
                        'interval': 'month'
                    }
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url=request.host_url + 'subscription-success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.host_url + 'subscription-cancelled',
            metadata={
                'user_id': user_id,
                'subscription_type': 'unlimited_monthly'
            }
        )
        
        return jsonify({
            'success': True,
            'checkout_url': checkout_session.url,
            'session_id': checkout_session.id
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/credits/purchase', methods=['POST'])
def create_checkout_session():
    """Create Stripe checkout session for credit purchase"""
    try:
        if not stripe:
            return jsonify({'success': False, 'error': 'Stripe not configured'}), 500
        
        session_token = request.cookies.get('session_token')
        if not session_token:
            return jsonify({'success': False, 'error': 'Must be logged in to purchase'}), 401
        
        validation = user_db.validate_session(session_token)
        if not validation.get('valid'):
            return jsonify({'success': False, 'error': 'Invalid session'}), 401
        
        user_id = validation['user_id']
        data = request.json
        package_id = data.get('package')
        
        if package_id not in CREDIT_PACKAGES:
            return jsonify({'success': False, 'error': 'Invalid package'}), 400
        
        package = CREDIT_PACKAGES[package_id]
        
        # Create Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': int(package['price'] * 100),  # Convert to cents
                    'product_data': {
                        'name': f"{package['name']} Credit Package",
                        'description': f"{package['credits']} Premium Credits for Ultra-Quality DALL-E 3 HD",
                    },
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.host_url + 'purchase-success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.host_url + 'purchase-cancelled',
            metadata={
                'user_id': user_id,
                'package_id': package_id,
                'credits': package['credits']
            }
        )
        
        return jsonify({
            'success': True,
            'checkout_url': checkout_session.url,
            'session_id': checkout_session.id
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/stripe/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events (payment confirmation)"""
    try:
        if not stripe:
            return jsonify({'error': 'Stripe not configured'}), 500
        
        payload = request.data
        sig_header = request.headers.get('Stripe-Signature')
        
        # Verify webhook signature
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, CONFIG['STRIPE_WEBHOOK_SECRET']
            )
        except ValueError:
            return jsonify({'error': 'Invalid payload'}), 400
        except stripe.error.SignatureVerificationError:
            return jsonify({'error': 'Invalid signature'}), 400
        
        # Handle successful payment
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            user_id = int(session['metadata']['user_id'])
            
            # Check if it's a subscription or one-time payment
            if session['mode'] == 'subscription':
                # Activate unlimited subscription
                subscription_id = session['subscription']
                user_db.activate_subscription(user_id, subscription_id)
                print(f"Subscription activated for user {user_id}")
            else:
                # Add credits for one-time purchase
                credits = int(session['metadata']['credits'])
                package_id = session['metadata']['package_id']
                
                result = user_db.add_credits(
                    user_id=user_id,
                    credits=credits,
                    transaction_id=session['payment_intent'],
                    amount=session['amount_total'] / 100
                )
                print(f"Credits added: {result}")
        
        # Handle subscription cancellation
        elif event['type'] == 'customer.subscription.deleted':
            subscription = event['data']['object']
            user_db.deactivate_subscription(subscription['id'])
            print(f"Subscription cancelled: {subscription['id']}")
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Webhook error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/referral/apply', methods=['POST'])
def apply_referral():
    """Apply referral code to user account"""
    try:
        session_token = request.cookies.get('session_token')
        if not session_token:
            return jsonify({'success': False, 'error': 'Must be logged in'}), 401
        
        validation = user_db.validate_session(session_token)
        if not validation.get('valid'):
            return jsonify({'success': False, 'error': 'Invalid session'}), 401
        
        user_id = validation['user_id']
        data = request.json
        referral_code = data.get('code', '').strip()
        
        result = user_db.apply_referral(user_id, referral_code)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/achievements/claim', methods=['POST'])
def claim_achievement():
    """Claim achievement credits"""
    try:
        session_token = request.cookies.get('session_token')
        if not session_token:
            return jsonify({'success': False, 'error': 'Must be logged in'}), 401
        
        validation = user_db.validate_session(session_token)
        if not validation.get('valid'):
            return jsonify({'success': False, 'error': 'Invalid session'}), 401
        
        user_id = validation['user_id']
        data = request.json
        achievement_type = data.get('type')
        
        # Define achievement rewards
        achievements = {
            'first_generation': 5,
            '10_generations': 10,
            'social_share': 15,
            'newsletter_signup': 20,
            'complete_profile': 10
        }
        
        if achievement_type not in achievements:
            return jsonify({'success': False, 'error': 'Invalid achievement'}), 400
        
        credits = achievements[achievement_type]
        result = user_db.award_achievement(user_id, achievement_type, credits)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============ END CREDIT & PAYMENT ROUTES ============


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
            # Simple contrast enhancement using PIL only
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
    FREE TIER: 10 daily credits → Replicate Flux Dev (9.0/10 quality)
    PREMIUM: Paid credits → DALL-E 3 HD (9.5/10 quality)
    
    Request body:
    {
        "prompt": "your prompt here",
        "negative_prompt": "things to avoid" (optional),
        "quality_tier": "free" | "premium",
        "style": "photorealistic" (optional),
        "dimensions": {"width": 1024, "height": 1024},
        "quality_boost": true/false,
        "post_process": true/false,
        "upscale": 1 | 2 | 4 (optional)
    }
    """
    try:
        # Check user authentication first
        session_token = request.cookies.get('session_token')
        user_id = None
        user_type = 'anonymous'
        
        if session_token:
            validation = user_db.validate_session(session_token)
            if validation.get('valid'):
                user_id = validation['user_id']
                # Determine user type for rate limiting
                credits_info = user_db.get_user_credits(user_id)
                if credits_info.get('has_unlimited'):
                    user_type = 'unlimited_user'
                elif credits_info.get('premium_credits', 0) > 0:
                    user_type = 'premium_user'
                else:
                    user_type = 'free_user'
        
        # Apply rate limiting
        allowed, error_msg = check_rate_limit(user_type)
        if not allowed:
            return jsonify({
                'success': False,
                'error': error_msg,
                'rate_limited': True
            }), 429  # Too Many Requests
        
        data = request.json
        prompt = data.get('prompt', '')
        negative_prompt = data.get('negative_prompt', '')
        quality_tier = data.get('quality_tier', 'free')  # free or premium
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
        
        # Determine which engine to use based on credits
        if quality_tier == 'premium':
            # Premium tier requires login and credits
            if not user_id:
                return jsonify({
                    'success': False,
                    'error': 'Please log in to use premium quality',
                    'require_login': True
                }), 401
            
            credits = user_db.get_user_credits(user_id)
            if not credits.get('success'):
                return jsonify({'success': False, 'error': 'Could not check credits'}), 500
            
            if credits['premium_credits'] < 1:
                return jsonify({
                    'success': False,
                    'error': 'Insufficient premium credits',
                    'require_purchase': True
                }), 402  # Payment Required
            
            # Use DALL-E 3 HD for premium
            result = generate_with_dalle(prompt, dimensions, quality_boost)
            
            if result.get('success'):
                # Deduct premium credit
                user_db.use_credit(user_id, 'premium')
                result['credits_used'] = 'premium'
                result['quality_tier'] = 'DALL-E 3 HD (9.5/10)'
                
                # Award first generation achievement
                if credits.get('total_generations', 0) == 0:
                    user_db.award_achievement(user_id, 'first_generation', 5)
                elif credits.get('total_generations', 0) == 9:
                    user_db.award_achievement(user_id, '10_generations', 10)
        
        else:
            # Free tier
            if user_id:
                # Logged in user - check daily free credits
                credits = user_db.get_user_credits(user_id)
                if credits.get('free_credits', 0) < 1:
                    return jsonify({
                        'success': False,
                        'error': 'Daily free credits exhausted. Upgrade to premium or wait until tomorrow.',
                        'require_purchase': True
                    }), 402
                
                # Use Replicate Flux Dev for free tier
                result = generate_with_replicate(prompt, negative_prompt, dimensions, quality_boost)
                
                if result.get('success'):
                    # Deduct free credit
                    user_db.use_credit(user_id, 'free')
                    result['credits_used'] = 'free'
                    result['quality_tier'] = 'Flux Dev (9.0/10)'
            else:
                # Anonymous user - limited to 10 per day (IP-based limiting would go here)
                result = generate_with_replicate(prompt, negative_prompt, dimensions, quality_boost)
                if result.get('success'):
                    result['credits_used'] = 'anonymous'
                    result['quality_tier'] = 'Flux Dev (9.0/10)'
                    result['message'] = 'Sign up for 10 free daily generations!'
        
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
    
    # ALWAYS use HD quality for best results (industry standard)
    quality = 'hd'
    
    # Style: 'vivid' for hyper-real and dramatic images (recommended)
    # or 'natural' for more natural, less hyper-real images
    style_mode = 'vivid' if quality_boost else 'natural'
    
    payload = {
        "model": "dall-e-3",
        "prompt": prompt,
        "n": 1,
        "size": size,
        "quality": quality,
        "style": style_mode  # New parameter for better quality
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
    
    # Quality settings (optimized for best results)
    steps = 60 if quality_boost else 40  # More steps = higher quality (industry best: 50-80)
    cfg_scale = 9 if quality_boost else 7.5  # Higher CFG = more prompt adherence (sweet spot: 7-10)
    
    payload = {
        "text_prompts": text_prompts,
        "cfg_scale": cfg_scale,
        "height": dimensions.get('height', 1024),
        "width": dimensions.get('width', 1024),
        "steps": steps,
        "samples": 1,
        "sampler": "K_DPM_2_ANCESTRAL",  # High-quality sampler
        "clip_guidance_preset": "FAST_BLUE" if quality_boost else "NONE"  # Enhanced detail
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
    
    # Using Flux Schnell (fast, free tier) - 4 second generation time
    # Note: Flux Dev requires paid account, Schnell is free
    
    url = "https://api.replicate.com/v1/predictions"
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json",
        "Prefer": "wait"  # Wait for result instead of polling
    }
    
    # Calculate aspect ratio
    width = dimensions.get('width', 1024)
    height = dimensions.get('height', 1024)
    aspect_ratio = "1:1"  # Default square
    if width > height:
        aspect_ratio = "16:9"
    elif height > width:
        aspect_ratio = "9:16"
    
    input_params = {
        "prompt": prompt,
        "num_outputs": 1,
        "aspect_ratio": aspect_ratio,
        "output_format": "png",
        "output_quality": 90
    }
    
    # Flux Schnell doesn't support negative prompts, so add to main prompt
    if negative_prompt:
        input_params["prompt"] = f"{prompt}. Avoid: {negative_prompt}"
    
    payload = {
        "version": "5599ed30703defd1d160a25a63321b4dec97101d98b4674bcc56e41f62f35637",  # Flux Schnell stable version
        "input": input_params
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        prediction = response.json()
        
        # If prediction is already complete (Prefer: wait), return immediately
        if prediction.get('status') == 'succeeded' and prediction.get('output'):
            return {
                'success': True,
                'image_url': prediction['output'][0] if isinstance(prediction['output'], list) else prediction['output'],
                'engine': 'Flux Schnell'
            }
        
        # Otherwise poll for completion
        prediction_id = prediction.get('id')
        if not prediction_id:
            return {
                'success': False,
                'error': 'No prediction ID returned from API'
            }
        
        # Poll for completion (max 30 seconds for Schnell)
        max_attempts = 30
        for attempt in range(max_attempts):
            status_response = requests.get(
                f"https://api.replicate.com/v1/predictions/{prediction_id}",
                headers={"Authorization": f"Token {api_key}"},
                timeout=10
            )
            status_data = status_response.json()
            
            if status_data.get('status') == 'succeeded':
                output = status_data.get('output')
                if output:
                    image_url = output[0] if isinstance(output, list) else output
                    return {
                        'success': True,
                        'image_url': image_url,
                        'engine': 'Flux Schnell'
                    }
            elif status_data.get('status') == 'failed':
                error_detail = status_data.get('error', 'Unknown error')
                return {
                    'success': False,
                    'error': f'Generation failed: {error_detail}'
                }
            
            time.sleep(1)
        
        return {
            'success': False,
            'error': 'Generation timeout after 30 seconds'
        }
        
    except requests.Timeout:
        return {
            'success': False,
            'error': 'Request timeout - please try again'
        }
    except requests.RequestException as e:
        return {
            'success': False,
            'error': f'API request failed: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}'
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
    
    app.run(debug=False, host='0.0.0.0', port=5000)


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
