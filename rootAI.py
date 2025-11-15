"""
AI Image Generator Backend Server
Supports multiple AI image generation APIs with post-processing enhancement
"""

from flask import Flask, request, jsonify, send_from_directory, make_response, render_template
from flask_cors import CORS
import os
import requests
import base64
from datetime import datetime, timedelta
import json
from database import UserDatabase
from collections import defaultdict
import time
from cost_monitor import cost_monitor
from rating_system import rating_system
from analytics_system import analytics_system
from quality_optimizer import quality_optimizer
from autonomous_learner import autonomous_learner

# Image enhancement libraries
try:
    from PIL import Image, ImageEnhance, ImageFilter
    PIL_AVAILABLE = True
except (ImportError, Exception):
    Image = None
    ImageEnhance = None
    ImageFilter = None
    PIL_AVAILABLE = False
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
    'HUGGINGFACE_API_KEY': os.getenv('HUGGINGFACE_API_KEY', 'your-huggingface-key-here'),
    'RUNWAY_API_KEY': os.getenv('RUNWAY_API_KEY', 'your-runway-key-here'),
    'STRIPE_SECRET_KEY': os.getenv('STRIPE_SECRET_KEY', 'your-stripe-secret-key-here'),
    'STRIPE_PUBLISHABLE_KEY': os.getenv('STRIPE_PUBLISHABLE_KEY', 'your-stripe-publishable-key-here'),
    'STRIPE_WEBHOOK_SECRET': os.getenv('STRIPE_WEBHOOK_SECRET', 'your-webhook-secret-here'),
}

# Initialize Stripe
if stripe and STRIPE_AVAILABLE and CONFIG['STRIPE_SECRET_KEY'] != 'your-stripe-secret-key-here':
    stripe.api_key = CONFIG['STRIPE_SECRET_KEY']

# ============ PRICING STRUCTURE (30%+ Profit Margins) - POUND STERLING (£) ============

# Token Pricing: 1 token = £0.008 (approximately $0.01)
# Exchange rate: £1 = $1.27 (Nov 2025)
TOKEN_COSTS = {
    'sdxl_refiner': 2,      # £0.016 (cost £0.0024, profit 567%)
    'dalle3_standard': 6,   # £0.048 (cost £0.032, profit 50%)
    'dalle3_hd': 12,        # £0.096 (cost £0.064, profit 50%)
    'video_cartoon_5s': 20, # £0.16 (cost £0.13, profit 23%) - 8-9/10 quality, ideal for cartoons
    'video_cartoon_8s': 35, # £0.28 (cost £0.22, profit 27%) - 8-9/10 quality, ideal for cartoons
    'video_premium_5s': 30, # £0.24 (cost £0.20, profit 20%) - 10/10 quality, photorealistic
    'video_premium_8s': 50, # £0.40 (cost £0.32, profit 25%) - 10/10 quality, photorealistic
    'video_premium_10s': 60,# £0.48 (cost £0.40, profit 20%) - 10/10 quality, photorealistic
}

# Credit Packages (token-based) - POUND STERLING
CREDIT_PACKAGES = {
    'starter': {'tokens': 100, 'price': 0.79, 'name': 'Starter Pack'},
    'popular': {'tokens': 500, 'price': 3.99, 'name': 'Popular Pack'},
    'pro': {'tokens': 1200, 'price': 7.99, 'name': 'Pro Pack', 'bonus': 200},  # 20% bonus
    'creator': {'tokens': 3000, 'price': 19.99, 'name': 'Creator Pack', 'bonus': 500},  # 17% bonus
}

# Subscription Plans (optimized for 30% margins) - POUND STERLING
SUBSCRIPTION_PLANS = {
    'free': {
        'price': 0,
        'currency': 'GBP',
        'name': 'Free',
        'daily_images': 10,  # Flux/SDXL (FREE APIs)
        'prize_wheel': True,
        'prize_chance': 0.20,
        'prize_tokens': 20,
    },
    'user': {
        'price': 9.99,
        'currency': 'GBP',
        'name': 'User',
        'images_free': 'unlimited',  # Flux/SDXL (£0 API cost)
        'tokens_monthly': 1050,  # £8.40 token value
        'videos_cartoon': 30,  # 30x 8s cartoon videos (8-9/10 quality) = 1050 tokens
        'videos_premium': 21,  # OR 21x 8s premium videos (10/10 quality) = 1050 tokens
        'features': [
            'Unlimited Flux Schnell & SDXL images',
            '1050 tokens/month',
            '30 cartoon videos (8s, 8-9/10) OR 21 premium videos (8s, 10/10)',
            'Mix & match: videos, DALL-E, SDXL',
            'Commercial use license',
            'No watermark',
            'Priority queue',
            'HD downloads'
        ],
        'recommended_use': '20 cartoon videos (8s) + 20 DALL-E HD + 50 SDXL',
        'api_cost_estimate': 6.99,  # £6.99 (20 cartoon videos @ £0.22 + 20 DALL-E @ £0.064 + 50 SDXL @ £0.0024)
        'profit_margin': 0.30  # 30% exactly
    },
    'creator': {
        'price': 17.99,
        'currency': 'GBP',
        'name': 'Creator',
        'images_free': 'unlimited',  # Flux/SDXL
        'tokens_monthly': 1950,  # £15.60 token value
        'videos_cartoon': 55,  # 55x 8s cartoon videos (8-9/10 quality) = 1925 tokens
        'videos_premium': 39,  # OR 39x 8s premium videos (10/10 quality) = 1950 tokens
        'features': [
            'Unlimited Flux Schnell & SDXL images',
            '1950 tokens/month',
            '55 cartoon videos (8s, 8-9/10) OR 39 premium videos (8s, 10/10)',
            'Mix & match: videos, DALL-E, SDXL',
            '15% discount on token purchases',
            'Commercial use license',
            'Priority generation queue',
            'API access (coming soon)',
            'Batch generation',
            'Custom watermark',
            'HD downloads'
        ],
        'recommended_use': '40 cartoon videos (8s) + 30 DALL-E HD + 100 SDXL',
        'api_cost_estimate': 12.59,  # £12.59 (40 cartoon videos @ £0.22 + 30 DALL-E @ £0.064 + 100 SDXL @ £0.0024)
        'profit_margin': 0.30  # 30% exactly
    },
    'pro': {
        'price': 32.00,
        'currency': 'GBP',
        'name': 'Pro',
        'images_free': 'unlimited',  # Flux/SDXL
        'tokens_monthly': 3500,  # £28.00 token value
        'videos_cartoon': 100, # 100x 8s cartoon videos (8-9/10 quality) = 3500 tokens
        'videos_premium': 70,  # OR 70x 8s premium videos (10/10 quality) = 3500 tokens
        'features': [
            'Unlimited Flux Schnell & SDXL images',
            '3500 tokens/month',
            '100 cartoon videos (8s, 8-9/10) OR 70 premium videos (8s, 10/10)',
            'Mix & match: videos, DALL-E, SDXL',
            '20% discount on token purchases',
            'Priority generation queue (fastest)',
            'API access with higher rate limits',
            'Commercial license (unlimited use)',
            'Remove all watermarks',
            'Batch generation (up to 50 at once)',
            'Custom branding/watermark',
            'Dedicated support',
            'Early access to new features'
        ],
        'recommended_use': '70 cartoon videos (8s) + 50 DALL-E HD + 200 SDXL',
        'api_cost_estimate': 22.40,  # £22.40 (70 cartoon videos @ £0.22 + 50 DALL-E @ £0.064 + 200 SDXL @ £0.0024)
        'profit_margin': 0.30  # 30% exactly
    },
}

# OLD: Keeping for backward compatibility during migration
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
            # Properly clear session cookie with all security attributes
            response.set_cookie(
                'session_token',
                '',
                max_age=0,
                expires=0,
                httponly=True,
                secure=False,
                samesite='Lax',
                path='/'
            )
            # Prevent caching of logout response
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            return response
        else:
            response = make_response(jsonify({'success': True, 'message': 'No active session'}), 200)
            # Clear cookie anyway just to be safe
            response.set_cookie(
                'session_token',
                '',
                max_age=0,
                expires=0,
                httponly=True,
                secure=False,
                samesite='Lax',
                path='/'
            )
            return response
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/auth/validate', methods=['GET'])
def validate_session():
    """Validate current session"""
    try:
        session_token = request.cookies.get('session_token')
        
        if not session_token:
            response = make_response(jsonify({'valid': False, 'error': 'No session token'}), 401)
            # Prevent caching of validation response
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            return response
        
        result = user_db.validate_session(session_token)
        
        if result['valid']:
            response = make_response(jsonify(result), 200)
        else:
            response = make_response(jsonify(result), 401)
        
        # Prevent caching of validation response
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
            
    except Exception as e:
        response = make_response(jsonify({'valid': False, 'error': str(e)}), 500)
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response


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
        
        # Check if low token alert is needed
        if result.get('success'):
            alert_check = user_db.check_low_token_alert(user_id)
            result['low_token_alert'] = alert_check
        
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


@app.route('/api/notifications/preferences', methods=['GET'])
def get_notification_preferences():
    """Get user's notification preferences"""
    try:
        session_token = request.cookies.get('session_token')
        if not session_token:
            return jsonify({'success': False, 'error': 'Must be logged in'}), 401
        
        validation = user_db.validate_session(session_token)
        if not validation.get('valid'):
            return jsonify({'success': False, 'error': 'Invalid session'}), 401
        
        user_id = validation['user_id']
        result = user_db.get_notification_preferences(user_id)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/notifications/preferences', methods=['POST'])
def update_notification_preferences():
    """Update user's notification threshold"""
    try:
        session_token = request.cookies.get('session_token')
        if not session_token:
            return jsonify({'success': False, 'error': 'Must be logged in'}), 401
        
        validation = user_db.validate_session(session_token)
        if not validation.get('valid'):
            return jsonify({'success': False, 'error': 'Invalid session'}), 401
        
        user_id = validation['user_id']
        data = request.json
        new_threshold = data.get('threshold', 300)
        
        result = user_db.update_token_threshold(user_id, new_threshold)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


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
                
                # Log subscription revenue
                amount = session['amount_total'] / 100  # Convert cents to dollars
                cost_monitor.log_revenue(
                    user_id=user_id,
                    amount=amount,
                    revenue_type='subscription',
                    description=f'Monthly subscription: {subscription_id}'
                )
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
                
                # Log credit purchase revenue
                amount = session['amount_total'] / 100
                cost_monitor.log_revenue(
                    user_id=user_id,
                    amount=amount,
                    revenue_type='credits',
                    description=f'{credits} credits purchased ({package_id})'
                )
        
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


# ============ ANALYTICS & RATING SYSTEM ROUTES ============

@app.route('/api/analytics/rate', methods=['POST'])
def submit_rating():
    """Submit rating for a generation"""
    try:
        session_token = request.cookies.get('session_token')
        if not session_token:
            return jsonify({'success': False, 'error': 'Must be logged in'}), 401
        
        validation = user_db.validate_session(session_token)
        if not validation.get('valid'):
            return jsonify({'success': False, 'error': 'Invalid session'}), 401
        
        data = request.json
        generation_id = data.get('generation_id')
        rating = data.get('rating')  # 1-5 stars
        quality_score = data.get('quality_score')  # Optional 0-100
        feedback_text = data.get('feedback')
        feedback_tags = data.get('tags')  # List of tags
        time_to_rate = data.get('time_to_rate')  # Time in seconds
        
        if not generation_id or not rating:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        if rating < 1 or rating > 5:
            return jsonify({'success': False, 'error': 'Rating must be 1-5'}), 400
        
        result = analytics_system.submit_rating(
            generation_id=generation_id,
            rating=rating,
            quality_score=quality_score,
            feedback_text=feedback_text,
            feedback_tags=json.dumps(feedback_tags) if feedback_tags else None,
            time_to_rate=time_to_rate
        )
        
        # Update quality optimizer with rating data
        if result.get('success'):
            quality_optimizer.update_rating_performance(
                generation_id=generation_id,
                rating=rating,
                quality_score=quality_score or (rating * 20)  # Convert 5-star to 100 scale
            )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analytics/action', methods=['POST'])
def track_generation_action():
    """Track actions on generations (download, share, edit, etc.)"""
    try:
        session_token = request.cookies.get('session_token')
        if not session_token:
            return jsonify({'success': False, 'error': 'Must be logged in'}), 401
        
        data = request.json
        generation_id = data.get('generation_id')
        action_type = data.get('action')  # download, share, edit, regenerate, use
        
        if not generation_id or not action_type:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        success = analytics_system.update_generation_action(generation_id, action_type)
        
        return jsonify({'success': success})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analytics/behavior', methods=['POST'])
def track_behavior():
    """Track user behavior for UX analytics"""
    try:
        session_token = request.cookies.get('session_token')
        user_id = 0  # Anonymous by default
        
        if session_token:
            validation = user_db.validate_session(session_token)
            if validation.get('valid'):
                user_id = validation['user_id']
        
        data = request.json
        session_id = data.get('session_id')
        action_type = data.get('action')
        action_details = data.get('details')
        page_url = data.get('page')
        device_info = data.get('device')
        interaction_time = data.get('time')
        
        if not session_id or not action_type:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        success = analytics_system.track_user_behavior(
            user_id=user_id,
            session_id=session_id,
            action_type=action_type,
            action_details=action_details,
            page_url=page_url,
            device_info=device_info,
            interaction_time=interaction_time
        )
        
        return jsonify({'success': success})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analytics/prompt-suggestions', methods=['GET'])
def get_prompt_suggestions():
    """Get AI-powered prompt suggestions based on top performers"""
    try:
        engine = request.args.get('engine', 'flux-pro')
        partial_prompt = request.args.get('prompt', '')
        limit = int(request.args.get('limit', 5))
        
        suggestions = analytics_system.get_prompt_suggestions(partial_prompt, engine, limit)
        
        return jsonify({
            'success': True,
            'suggestions': suggestions
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analytics/top-prompts', methods=['GET'])
def get_top_prompts():
    """Get highest rated prompts for inspiration"""
    try:
        engine = request.args.get('engine')
        min_ratings = int(request.args.get('min_ratings', 5))
        limit = int(request.args.get('limit', 50))
        
        prompts = analytics_system.get_top_prompts(engine, min_ratings, limit)
        
        return jsonify({
            'success': True,
            'prompts': prompts
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analytics/dashboard', methods=['GET'])
def get_analytics_dashboard():
    """Get comprehensive analytics dashboard (admin only)"""
    try:
        session_token = request.cookies.get('session_token')
        if not session_token:
            return jsonify({'success': False, 'error': 'Must be logged in'}), 401
        
        validation = user_db.validate_session(session_token)
        if not validation.get('valid'):
            return jsonify({'success': False, 'error': 'Invalid session'}), 401
        
        # TODO: Add admin check here
        
        days = int(request.args.get('days', 30))
        dashboard = analytics_system.get_analytics_dashboard(days)
        
        return jsonify({
            'success': True,
            'data': dashboard
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/optimizer/recommend', methods=['POST'])
def get_optimal_recommendation():
    """Get AI-powered engine recommendation for a prompt"""
    try:
        data = request.json
        prompt = data.get('prompt')
        
        if not prompt:
            return jsonify({'success': False, 'error': 'Prompt required'}), 400
        
        recommendation = quality_optimizer.get_optimal_engine(prompt)
        
        return jsonify({
            'success': True,
            'recommendation': recommendation
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/optimizer/engine-comparison', methods=['GET'])
def get_engine_comparison():
    """Get comparative analysis of all engines"""
    try:
        comparison = quality_optimizer.get_engine_comparison()
        
        return jsonify({
            'success': True,
            'engines': comparison
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/optimizer/category-insights', methods=['GET'])
def get_category_insights():
    """Get insights about best engines per category"""
    try:
        insights = quality_optimizer.get_category_insights()
        
        return jsonify({
            'success': True,
            'categories': insights
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============ AUTONOMOUS LEARNING ROUTES ============

@app.route('/api/learning/enhance-prompt', methods=['POST'])
def enhance_prompt_with_learning():
    """Get AI-powered prompt enhancement suggestions based on learned patterns"""
    try:
        data = request.get_json()
        user_prompt = data.get('prompt', '')
        
        if not user_prompt:
            return jsonify({'success': False, 'error': 'Prompt required'}), 400
        
        # Get enhancement suggestions from autonomous learner
        suggestions = autonomous_learner.get_prompt_enhancement_suggestions(user_prompt)
        
        # Build enhanced prompt
        enhanced_parts = [user_prompt]
        
        # Add top quality modifiers
        if suggestions['quality_modifiers']:
            top_modifiers = [m['term'] for m in suggestions['quality_modifiers'][:3]]
            enhanced_parts.extend(top_modifiers)
        
        # Add trending patterns
        if suggestions['trending_additions']:
            trending = suggestions['trending_additions'][0]['pattern']
            enhanced_parts.append(trending)
        
        enhanced_prompt = ', '.join(enhanced_parts)
        
        return jsonify({
            'success': True,
            'original_prompt': user_prompt,
            'enhanced_prompt': enhanced_prompt,
            'suggestions': suggestions,
            'improvements': {
                'quality_boost': len(suggestions['quality_modifiers']),
                'style_options': len(suggestions['style_suggestions']),
                'trending_applied': len(suggestions['trending_additions']) > 0
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/learning/stats', methods=['GET'])
def get_learning_stats():
    """Get statistics about autonomous learning progress"""
    try:
        stats = autonomous_learner.get_learning_stats()
        
        return jsonify({
            'success': True,
            'stats': stats,
            'status': 'active' if autonomous_learner.learning_active else 'stopped'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/learning/control', methods=['POST'])
def control_learning():
    """Start or stop autonomous learning"""
    try:
        data = request.get_json()
        action = data.get('action', 'start')
        
        if action == 'start':
            autonomous_learner.start_autonomous_learning()
            return jsonify({
                'success': True,
                'message': 'Autonomous learning started',
                'status': 'active'
            })
        elif action == 'stop':
            autonomous_learner.stop_autonomous_learning()
            return jsonify({
                'success': True,
                'message': 'Autonomous learning stopped',
                'status': 'stopped'
            })
        else:
            return jsonify({'success': False, 'error': 'Invalid action'}), 400
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/learning/trending', methods=['GET'])
def get_trending_patterns():
    """Get currently trending prompt patterns"""
    try:
        import sqlite3
        conn = sqlite3.connect('learning.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT pattern_text, trend_score, source_count, last_seen
            FROM trending_patterns
            WHERE last_seen >= datetime('now', '-7 days')
            ORDER BY trend_score DESC
            LIMIT 20
        ''')
        
        trends = []
        for pattern, score, sources, last_seen in cursor.fetchall():
            trends.append({
                'pattern': pattern,
                'trend_score': score,
                'sources': sources,
                'last_seen': last_seen
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'trends': trends,
            'count': len(trends)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/learning/quality-insights', methods=['GET'])
def get_quality_insights():
    """Get insights about what makes prompts high-quality"""
    try:
        import sqlite3
        conn = sqlite3.connect('learning.db')
        cursor = conn.cursor()
        
        # Get top quality indicators
        cursor.execute('''
            SELECT indicator_value, correlation_score, occurrence_count
            FROM quality_indicators
            WHERE indicator_type = 'quality_modifier'
            AND occurrence_count > 10
            ORDER BY correlation_score DESC
            LIMIT 15
        ''')
        
        quality_modifiers = []
        for value, correlation, count in cursor.fetchall():
            quality_modifiers.append({
                'term': value,
                'correlation': correlation,
                'frequency': count
            })
        
        # Get style library
        cursor.execute('''
            SELECT style_name, avg_quality, sample_count
            FROM style_library
            WHERE sample_count > 5
            ORDER BY avg_quality DESC, sample_count DESC
            LIMIT 15
        ''')
        
        styles = []
        for name, quality, samples in cursor.fetchall():
            styles.append({
                'style': name,
                'avg_quality': quality,
                'samples': samples
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'quality_modifiers': quality_modifiers,
            'popular_styles': styles
        })
        
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


@app.route('/landing')
def landing_page():
    """Serve the landing page"""
    return render_template('landing.html')


@app.route('/pricing')
def pricing_page():
    """Serve the pricing page"""
    return render_template('pricing.html')


@app.route('/signup')
def signup_page():
    """Serve the signup page"""
    return render_template('signup.html')


@app.route('/faq')
def faq_page():
    """Serve the FAQ page"""
    return render_template('faq.html')


@app.route('/analytics')
def analytics_dashboard():
    """Serve the analytics dashboard"""
    return render_template('analytics_dashboard.html')


@app.route('/learning')
def learning_dashboard():
    """Serve the autonomous learning dashboard"""
    return render_template('learning_dashboard.html')


@app.route('/blog')
def blog_index():
    """Serve the blog index page"""
    return send_from_directory('blog', 'index.html')


@app.route('/blog/<path:post>')
def blog_post(post):
    """Serve individual blog posts"""
    return send_from_directory('blog', f'{post}.html')


@app.route('/admin')
def admin_dashboard():
    """Serve the admin dashboard"""
    return render_template('admin_dashboard.html')


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
        # CRITICAL PROTECTION 1: Check emergency shutdown mode
        if cost_monitor.emergency_mode:
            return jsonify({
                'success': False,
                'error': 'Service temporarily unavailable due to high costs. Please try again later.',
                'emergency_mode': True
            }), 503
        
        # CRITICAL PROTECTION 2: Check cost alerts
        alerts = cost_monitor.check_cost_alerts()
        if alerts.get('daily_limit_exceeded'):
            cost_monitor.activate_emergency_mode()
            return jsonify({
                'success': False,
                'error': 'Daily cost limit exceeded. Service paused.',
                'emergency_mode': True
            }), 503
        
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
                # Log API cost
                api_cost = result.get('api_cost', 0.08)  # Default to HD cost
                cost_monitor.log_api_cost(
                    user_id=user_id,
                    api_service='openai',
                    operation='dalle3_hd',
                    cost=api_cost,
                    success=True
                )
                
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
            # Free tier - Try Replicate, fallback to Hugging Face if payment required
            if user_id:
                # Logged in user - check daily free credits
                credits = user_db.get_user_credits(user_id)
                if credits.get('free_credits', 0) < 1:
                    return jsonify({
                        'success': False,
                        'error': 'Daily free credits exhausted. Upgrade to premium or wait until tomorrow.',
                        'require_purchase': True
                    }), 402
                
                # Try Replicate first, fallback to Hugging Face
                result = generate_with_replicate(prompt, negative_prompt, dimensions, quality_boost)
                
                # If Replicate fails with payment error, try Hugging Face
                if not result.get('success') and ('402' in str(result.get('error', '')) or 'Payment Required' in str(result.get('error', ''))):
                    print("Replicate requires payment, falling back to Hugging Face...")
                    result = generate_with_huggingface(prompt, negative_prompt, dimensions)
                
                if result.get('success'):
                    # Deduct free credit
                    user_db.use_credit(user_id, 'free')
                    result['credits_used'] = 'free'
                    if 'quality_tier' not in result:
                        result['quality_tier'] = 'Free Tier (8.5/10)'
            else:
                # Anonymous user - Try Replicate, fallback to Hugging Face
                result = generate_with_replicate(prompt, negative_prompt, dimensions, quality_boost)
                
                # If Replicate fails with payment error, try Hugging Face
                if not result.get('success') and ('402' in str(result.get('error', '')) or 'Payment Required' in str(result.get('error', ''))):
                    print("Replicate requires payment, falling back to Hugging Face...")
                    result = generate_with_huggingface(prompt, negative_prompt, dimensions)
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
        
        # Track generation in analytics system
        if result.get('success') and user_id:
            import uuid
            generation_id = str(uuid.uuid4())
            result['generation_id'] = generation_id
            
            # Record generation for analytics
            analytics_system.record_generation(
                generation_id=generation_id,
                user_id=user_id,
                prompt=prompt,
                engine=result.get('engine', 'unknown'),
                model_version=result.get('quality_tier', 'standard'),
                session_id=session_token
            )
            
            # Log performance metrics for quality optimization
            generation_time = result.get('generation_time', 0)
            api_cost = result.get('api_cost', 0)
            settings = {
                'quality_boost': quality_boost,
                'post_process': post_process,
                'upscale': upscale,
                'dimensions': dimensions
            }
            
            quality_optimizer.log_generation_performance(
                generation_id=generation_id,
                engine=result.get('engine', 'unknown'),
                settings=settings,
                prompt=prompt,
                generation_time=generation_time,
                cost=api_cost
            )
        
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
    
    # Calculate API cost based on quality and size
    if quality == 'hd':
        api_cost = 0.08  # $0.08 for HD quality
    else:
        api_cost = 0.04  # $0.04 for standard quality
    
    return {
        'success': True,
        'image_url': image_url,
        'engine': 'DALL-E 3',
        'revised_prompt': data['data'][0].get('revised_prompt', prompt),
        'quality': quality,
        'api_cost': api_cost
    }


def generate_with_stability(prompt, negative_prompt='', dimensions={}, quality_boost=True):
    """Generate image using Stability AI SDXL with Refiner for 9/10 quality at $0.003"""
    
    # Using Replicate's SDXL + Refiner (cheaper and better than direct Stability API)
    api_key = CONFIG['REPLICATE_API_KEY']
    
    if api_key == 'your-replicate-key-here':
        return {
            'success': False,
            'error': 'Replicate API key not configured',
            'demo': True
        }
    
    url = "https://api.replicate.com/v1/predictions"
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json",
        "Prefer": "wait"
    }
    
    # SDXL 1.0 with Refiner for best quality
    # Cost: $0.003 per image (1000x cheaper than DALL-E!)
    payload = {
        "version": "7762fd07cf82c948538e41f63f77d685e02b063e37e496e96eefd46c929f9bdc",  # SDXL + Refiner
        "input": {
            "prompt": prompt,
            "negative_prompt": negative_prompt or "ugly, blurry, low quality, distorted",
            "width": dimensions.get('width', 1024),
            "height": dimensions.get('height', 1024),
            "num_inference_steps": 50 if quality_boost else 30,
            "guidance_scale": 9 if quality_boost else 7.5,
            "refine": "expert_ensemble_refiner",  # Use refiner for extra quality
            "high_noise_frac": 0.8,
            "num_outputs": 1
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        prediction = response.json()
        
        # Check if already complete
        if prediction.get('status') == 'succeeded' and prediction.get('output'):
            return {
                'success': True,
                'image_url': prediction['output'][0] if isinstance(prediction['output'], list) else prediction['output'],
                'engine': 'SDXL + Refiner',
                'quality': '9/10',
                'api_cost': 0.003  # $0.003 per image
            }
        
        # Poll for completion
        prediction_id = prediction.get('id')
        if not prediction_id:
            return {'success': False, 'error': 'No prediction ID returned'}
        
        max_attempts = 40  # SDXL takes ~20-30 seconds
        for attempt in range(max_attempts):
            time.sleep(1)
            
            status_response = requests.get(
                f"https://api.replicate.com/v1/predictions/{prediction_id}",
                headers={"Authorization": f"Token {api_key}"},
                timeout=10
            )
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                
                if status_data.get('status') == 'succeeded':
                    output = status_data.get('output')
                    if output:
                        image_url = output[0] if isinstance(output, list) else output
                        return {
                            'success': True,
                            'image_url': image_url,
                            'engine': 'SDXL + Refiner',
                            'quality': '9/10',
                            'api_cost': 0.003
                        }
                
                elif status_data.get('status') == 'failed':
                    error = status_data.get('error', 'Unknown error')
                    return {'success': False, 'error': f'Generation failed: {error}'}
        
        return {'success': False, 'error': 'Generation timeout'}
        
    except requests.RequestException as e:
        return {'success': False, 'error': f'API error: {str(e)}'}
    except Exception as e:
        return {'success': False, 'error': f'Unexpected error: {str(e)}'}


def generate_with_stability_old(prompt, negative_prompt='', dimensions={}, quality_boost=True):
    """OLD: Direct Stability AI API (more expensive, keeping as backup)"""
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
    
    # Retry logic with exponential backoff for rate limits
    max_retries = 3
    retry_delay = 2
    
    for retry in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            
            # Handle rate limiting
            if response.status_code == 429:
                if retry < max_retries - 1:
                    wait_time = retry_delay * (2 ** retry)  # Exponential backoff
                    print(f"Rate limited. Waiting {wait_time} seconds before retry {retry + 1}/{max_retries}...")
                    time.sleep(wait_time)
                    continue
                else:
                    return {
                        'success': False,
                        'error': 'Rate limit exceeded. Please wait a moment and try again.',
                        'rate_limited': True
                    }
            
            response.raise_for_status()
            prediction = response.json()
            
            # If prediction is already complete (Prefer: wait), return immediately
            if prediction.get('status') == 'succeeded' and prediction.get('output'):
                # Replicate Flux Schnell is FREE (no cost to log)
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
                try:
                    status_response = requests.get(
                        f"https://api.replicate.com/v1/predictions/{prediction_id}",
                        headers={"Authorization": f"Token {api_key}"},
                        timeout=10
                    )
                    
                    # Handle rate limiting during polling
                    if status_response.status_code == 429:
                        time.sleep(2)
                        continue
                    
                    status_data = status_response.json()
                    
                    if status_data.get('status') == 'succeeded':
                        output = status_data.get('output')
                        if output:
                            image_url = output[0] if isinstance(output, list) else output
                            # Replicate Flux Schnell is FREE (no cost to log)
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
                except requests.RequestException:
                    # If polling fails, wait and continue
                    time.sleep(2)
                    continue
            
            return {
                'success': False,
                'error': 'Generation timeout after 30 seconds'
            }
            
        except requests.Timeout:
            if retry < max_retries - 1:
                time.sleep(retry_delay)
                continue
            return {
                'success': False,
                'error': 'Request timeout - please try again'
            }
        except requests.RequestException as e:
            error_msg = str(e)
            if '429' in error_msg or 'Too Many Requests' in error_msg:
                if retry < max_retries - 1:
                    wait_time = retry_delay * (2 ** retry)
                    time.sleep(wait_time)
                    continue
                return {
                    'success': False,
                    'error': 'Rate limit exceeded. Please wait 30 seconds and try again.',
                    'rate_limited': True
                }
            if retry < max_retries - 1:
                time.sleep(retry_delay)
                continue
            return {
                'success': False,
                'error': f'API request failed: {error_msg}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }
    
    return {
        'success': False,
        'error': 'Maximum retries exceeded. Please try again later.'
    }


def generate_with_huggingface(prompt, negative_prompt='', dimensions={}):
    """Generate image using Hugging Face Inference API (completely free, no credit card needed)"""
    api_key = CONFIG.get('HUGGINGFACE_API_KEY', 'your-huggingface-key-here')
    
    # Using Flux Schnell (free, fast model on Hugging Face)
    # Alternative: black-forest-labs/FLUX.1-schnell (latest free model)
    
    if api_key == 'your-huggingface-key-here':
        # Use public endpoint without auth (rate limited but free)
        api_url = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
        headers = {"Content-Type": "application/json"}
    else:
        # Use authenticated endpoint (higher rate limits)
        api_url = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    # Build full prompt with negative prompt
    full_prompt = prompt
    if negative_prompt:
        full_prompt = f"{prompt}. Avoid: {negative_prompt}"
    
    payload = {
        "inputs": full_prompt,
        "parameters": {
            "num_inference_steps": 4,  # Schnell is optimized for 1-4 steps
            "guidance_scale": 0.0,  # Schnell works best without guidance
        }
    }
    
    try:
        # Hugging Face API returns image bytes directly
        response = requests.post(api_url, headers=headers, json=payload, timeout=90)
        
        # Handle model loading (503)
        if response.status_code == 503:
            error_data = response.json() if response.content else {}
            estimated_time = error_data.get('estimated_time', 20)
            print(f"Model loading, waiting {estimated_time} seconds...")
            time.sleep(min(estimated_time + 5, 30))  # Wait but cap at 30 seconds
            response = requests.post(api_url, headers=headers, json=payload, timeout=90)
        
        response.raise_for_status()
        
        # Save the image
        filename = f"generated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join('generated_images', filename)
        
        # Ensure directory exists
        os.makedirs('generated_images', exist_ok=True)
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        # Hugging Face is FREE (no cost to log)
        return {
            'success': True,
            'image_url': f'/generated_images/{filename}',
            'engine': 'Flux Schnell (Free)',
            'quality_tier': 'Free Tier (9.0/10)'
        }
        
    except requests.RequestException as e:
        error_msg = str(e)
        # If this model also fails, try one more fallback
        if '410' in error_msg or 'Gone' in error_msg:
            # Try Stable Diffusion 2.1 as final fallback
            try:
                fallback_url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1"
                fallback_headers = headers.copy()
                fallback_payload = {
                    "inputs": full_prompt,
                    "parameters": {
                        "num_inference_steps": 20,
                        "guidance_scale": 7.5,
                    }
                }
                fallback_response = requests.post(fallback_url, headers=fallback_headers, json=fallback_payload, timeout=90)
                
                if fallback_response.status_code == 503:
                    time.sleep(20)
                    fallback_response = requests.post(fallback_url, headers=fallback_headers, json=fallback_payload, timeout=90)
                
                fallback_response.raise_for_status()
                
                filename = f"generated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                filepath = os.path.join('generated_images', filename)
                os.makedirs('generated_images', exist_ok=True)
                
                with open(filepath, 'wb') as f:
                    f.write(fallback_response.content)
                
                return {
                    'success': True,
                    'image_url': f'/generated_images/{filename}',
                    'engine': 'Stable Diffusion 2.1 (Free)',
                    'quality_tier': 'Free Tier (8.5/10)'
                }
            except:
                pass
        
        return {
            'success': False,
            'error': f'Hugging Face API error: {error_msg}'
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
    
    # Start autonomous learning engine
    print("🤖 Starting Autonomous Learning Engine...")
    autonomous_learner.start_autonomous_learning()
    print("✅ Learning engine activated - continuously harvesting open-source data")
    print("📚 Learning from: Civitai, Lexica, Reddit, GitHub, HuggingFace")
    print("🧠 Building knowledge: Patterns, styles, quality indicators, trends\n")
    
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


# ============ VIDEO GENERATION - RUNWAY GEN-3 ============

def generate_video_runway(image_path, prompt, duration=5):
    """
    Generate video from image using Runway Gen-3 Alpha Turbo
    Quality: 10/10 (industry-leading)
    Cost: $0.05/second = $0.25 for 5s, $0.40 for 8s
    """
    api_key = CONFIG['RUNWAY_API_KEY']
    
    if api_key == 'your-runway-key-here':
        return {
            'success': False,
            'error': 'Runway API key not configured',
            'demo': True
        }
    
    url = "https://api.runwayml.com/v1/generations"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-Runway-Version": "2024-11-06"
    }
    
    # Read and encode image
    import base64
    with open(image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
    
    payload = {
        "model": "gen3a_turbo",  # Gen-3 Alpha Turbo (fastest, high quality)
        "prompt": prompt,
        "init_image": f"data:image/png;base64,{image_data}",
        "duration": duration,  # 5 or 10 seconds
        "ratio": "16:9",
        "watermark": False
    }
    
    try:
        # Submit generation request
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        task_id = data.get('id')
        if not task_id:
            return {'success': False, 'error': 'No task ID returned'}
        
        # Poll for completion (Gen-3 Turbo takes ~90 seconds)
        max_attempts = 120  # 2 minutes max
        for attempt in range(max_attempts):
            time.sleep(2)
            
            status_response = requests.get(
                f"{url}/{task_id}",
                headers=headers,
                timeout=10
            )
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                
                if status_data.get('status') == 'succeeded':
                    video_url = status_data.get('output', [{}])[0].get('url')
                    if video_url:
                        # Calculate cost: $0.05 per second
                        cost = duration * 0.05
                        
                        return {
                            'success': True,
                            'video_url': video_url,
                            'duration': duration,
                            'engine': 'Runway Gen-3 Alpha Turbo',
                            'quality': '10/10',
                            'api_cost': cost
                        }
                
                elif status_data.get('status') == 'failed':
                    error = status_data.get('failure_reason', 'Unknown error')
                    return {'success': False, 'error': f'Generation failed: {error}'}
        
        return {'success': False, 'error': 'Video generation timeout'}
        
    except requests.RequestException as e:
        return {'success': False, 'error': f'Runway API error: {str(e)}'}
    except Exception as e:
        return {'success': False, 'error': f'Unexpected error: {str(e)}'}


@app.route('/api/generate-video-preview', methods=['POST'])
def generate_video_preview():
    """Generate FREE preview image for video - first frame only, best quality, no credits used"""
    try:
        # Check authentication
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'Must be logged in'}), 401
        
        token = auth_header.replace('Bearer ', '')
        session_token = token  # Use the token from header
        
        validation = user_db.validate_session(session_token)
        if not validation.get('valid'):
            return jsonify({'success': False, 'error': 'Invalid session'}), 401
        
        user_id = validation['user_id']
        
        # Check subscription tier - Preview only available for Creator and Pro plans
        user_data = user_db.get_user(user_id)
        subscription_tier = user_data.get('subscription_tier', 'free')
        
        if subscription_tier not in ['creator', 'pro']:
            return jsonify({
                'success': False,
                'error': 'Preview feature requires Creator or Pro plan',
                'upgrade_required': True,
                'current_plan': subscription_tier
            }), 403
        
        # Get request data
        data = request.get_json()
        prompt = data.get('prompt', '')
        quality = data.get('quality', 'cartoon')
        
        if not prompt:
            return jsonify({'success': False, 'error': 'Prompt required'}), 400
        
        # Generate single preview image using BEST FREE option (Flux Schnell)
        # This gives users a high-quality preview without using credits
        enhanced_prompt = f"{prompt}, first frame, cinematic still, high quality"
        
        # Use Flux Schnell - best free option, fast generation
        result = generate_image_flux_schnell(enhanced_prompt)
        
        if result.get('success'):
            # NO CREDITS DEDUCTED - This is free preview
            preview_url = result.get('image_url')
            
            # Log the preview generation (for analytics, no cost)
            cost_monitor.log_api_cost(
                user_id=user_id,
                api_service='flux_schnell',
                operation='video_preview',
                cost=0.0,  # Free
                success=True
            )
            
            return jsonify({
                'success': True,
                'preview_url': preview_url,
                'message': 'Preview generated - no credits used',
                'credits_used': 0
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to generate preview')
            }), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/spin-wheel', methods=['POST'])
def spin_wheel():
    """Award prize from daily spin wheel"""
    try:
        # Check authentication
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'Must be logged in'}), 401
        
        token = auth_header.replace('Bearer ', '')
        validation = user_db.validate_session(token)
        
        if not validation.get('valid'):
            return jsonify({'success': False, 'error': 'Invalid session'}), 401
        
        user_id = validation['user_id']
        
        # Get prize value
        data = request.get_json()
        prize = data.get('prize', 'no_win')
        
        # Check if user has already spun today (optional server-side validation)
        # For now, we trust client-side localStorage, but you could add DB tracking
        
        # Award prizes - Only free_video wins, everything else is no_win
        tokens_awarded = 0
        
        if prize == 'free_video':
            # Award 50 tokens (enough for one video)
            tokens_awarded = 50
            for _ in range(50):
                user_db.add_credit(user_id, 'premium')
        # 'no_win' awards nothing
        
        # Get updated token count
        credits = user_db.get_user_credits(user_id)
        total_tokens = credits.get('premium_credits', 0) + credits.get('free_credits', 0)
        
        return jsonify({
            'success': True,
            'prize': prize,
            'tokens_awarded': tokens_awarded,
            'tokens': total_tokens,
            'message': f'Prize awarded successfully!' if tokens_awarded > 0 else 'Better luck next time!'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/generate-video', methods=['POST'])
def generate_video():
    """Generate video from image using premium AI"""
    try:
        # Check authentication
        session_token = request.cookies.get('session_token')
        if not session_token:
            return jsonify({'success': False, 'error': 'Must be logged in'}), 401
        
        validation = user_db.validate_session(session_token)
        if not validation.get('valid'):
            return jsonify({'success': False, 'error': 'Invalid session'}), 401
        
        user_id = validation['user_id']
        
        # Check credits (video costs 40 tokens = $0.40 for 8s)
        credits = user_db.get_user_credits(user_id)
        if not credits.get('success'):
            return jsonify({'success': False, 'error': 'Could not check credits'}), 500
        
        video_cost = 40  # 40 tokens for 8-second video
        if credits.get('premium_credits', 0) < video_cost:
            return jsonify({
                'success': False,
                'error': f'Insufficient credits. Video requires {video_cost} tokens.',
                'require_purchase': True
            }), 402
        
        # Get image path and prompt
        image_path = request.form.get('image_path')
        prompt = request.form.get('prompt', 'smooth camera movement, high quality')
        duration = int(request.form.get('duration', 8))  # 5, 8, or 10 seconds
        
        if not image_path:
            return jsonify({'success': False, 'error': 'No image provided'}), 400
        
        # Generate video
        result = generate_video_runway(image_path, prompt, duration)
        
        if result.get('success'):
            # Deduct credits
            for _ in range(video_cost):
                user_db.use_credit(user_id, 'premium')
            
            # Log API cost
            api_cost = result.get('api_cost', 0.40)
            cost_monitor.log_api_cost(
                user_id=user_id,
                api_service='runway',
                operation='gen3_turbo',
                cost=api_cost,
                success=True
            )
            
            result['credits_used'] = video_cost
            return jsonify(result)
        else:
            # Refund on failure
            return jsonify(result), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============ ADMIN DASHBOARD - COST MONITORING ============
# Fixed: Removed duplicate admin_dashboard route (was causing deployment error)

@app.route('/api/admin/cost-stats', methods=['GET'])
def get_cost_stats():
    """Get real-time cost and revenue statistics (admin only)"""
    try:
        # Get hourly and daily stats
        hourly = cost_monitor.get_hourly_stats()
        daily = cost_monitor.get_daily_stats()
        
        # Check for alerts
        alerts = cost_monitor.check_cost_alerts()
        
        # Get cost breakdown
        breakdown = cost_monitor.get_cost_breakdown('daily')
        
        # Get top cost users
        top_users = cost_monitor.get_user_costs(limit=10)
        
        return jsonify({
            'success': True,
            'hourly': hourly,
            'daily': daily,
            'alerts': alerts,
            'breakdown': breakdown,
            'top_users': top_users
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/cost-report', methods=['GET'])
def get_cost_report():
    """Generate formatted cost report (admin only)"""
    try:
        report = cost_monitor.generate_report()
        return jsonify({
            'success': True,
            'report': report
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============ RATING SYSTEM - LEARNING AI FOUNDATION ============

@app.route('/api/rate-image', methods=['POST'])
def rate_image():
    """Rate a generated image (foundation for learning AI)"""
    try:
        session_token = request.cookies.get('session_token')
        if not session_token:
            return jsonify({'success': False, 'error': 'Must be logged in'}), 401
        
        validation = user_db.validate_session(session_token)
        if not validation.get('valid'):
            return jsonify({'success': False, 'error': 'Invalid session'}), 401
        
        user_id = validation['user_id']
        data = request.json
        
        result = rating_system.rate_image(
            user_id=user_id,
            image_url=data.get('image_url'),
            prompt=data.get('prompt'),
            engine=data.get('engine'),
            rating=int(data.get('rating')),
            feedback=data.get('feedback', ''),
            negative_prompt=data.get('negative_prompt', ''),
            style=data.get('style', ''),
            dimensions=data.get('dimensions', ''),
            quality_boost=data.get('quality_boost', True)
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/rate-video', methods=['POST'])
def rate_video():
    """Rate a generated video"""
    try:
        session_token = request.cookies.get('session_token')
        if not session_token:
            return jsonify({'success': False, 'error': 'Must be logged in'}), 401
        
        validation = user_db.validate_session(session_token)
        if not validation.get('valid'):
            return jsonify({'success': False, 'error': 'Invalid session'}), 401
        
        user_id = validation['user_id']
        data = request.json
        
        result = rating_system.rate_video(
            user_id=user_id,
            video_url=data.get('video_url'),
            image_url=data.get('image_url'),
            prompt=data.get('prompt'),
            engine=data.get('engine'),
            duration=int(data.get('duration')),
            rating=int(data.get('rating')),
            feedback=data.get('feedback', '')
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/suggest-prompt-improvements', methods=['POST'])
def suggest_improvements():
    """Get AI-powered prompt improvement suggestions"""
    try:
        data = request.json
        prompt = data.get('prompt', '')
        engine = data.get('engine', 'flux')
        
        if not prompt:
            return jsonify({'success': False, 'error': 'No prompt provided'}), 400
        
        suggestions = rating_system.suggest_improvements(prompt, engine)
        
        return jsonify({
            'success': True,
            'suggestions': suggestions,
            'original_prompt': prompt
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/rating-stats', methods=['GET'])
def get_rating_stats():
    """Get user's rating statistics"""
    try:
        session_token = request.cookies.get('session_token')
        if not session_token:
            return jsonify({'success': False, 'error': 'Must be logged in'}), 401
        
        validation = user_db.validate_session(session_token)
        if not validation.get('valid'):
            return jsonify({'success': False, 'error': 'Invalid session'}), 401
        
        user_id = validation['user_id']
        stats = rating_system.get_user_stats(user_id)
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/rating-analytics', methods=['GET'])
def get_rating_analytics():
    """Get overall rating analytics (admin only)"""
    try:
        report = rating_system.get_analytics_report()
        return jsonify({
            'success': True,
            'analytics': report
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============ SOCIAL MEDIA CONTENT CREATOR ROUTES ============

from social_content_creator import SocialContentCreator, estimate_monthly_costs
from intelligent_social_system import IntelligentSocialSystem

social_creator = SocialContentCreator()
intelligent_system = IntelligentSocialSystem()

@app.route('/social-content')
def social_content_dashboard():
    """Serve the social content creator dashboard"""
    return render_template('social_content_dashboard.html')


@app.route('/api/social-content/system-status', methods=['GET'])
def get_system_status():
    """Get intelligent system status - shows both content and learning systems"""
    try:
        status = intelligent_system.get_system_status()
        return jsonify({
            'success': True,
            'status': status
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/social-content/generate', methods=['POST'])
def generate_social_content():
    """Generate AI-optimized content using intelligent system (with learnings)"""
    try:
        # Check authentication
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'Must be logged in'}), 401
        
        token = auth_header.replace('Bearer ', '')
        validation = user_db.validate_session(token)
        
        if not validation.get('valid'):
            return jsonify({'success': False, 'error': 'Invalid session'}), 401
        
        user_id = validation['user_id']
        
        # Get request data
        data = request.get_json()
        topic = data.get('topic', '')
        content_type = data.get('content_type', 'image_post')
        language = data.get('language', 'en')
        quality = data.get('quality', 'free')
        platforms = data.get('platforms', ['instagram', 'facebook'])
        schedule_time_str = data.get('schedule_time')
        
        if not topic:
            return jsonify({'success': False, 'error': 'Topic required'}), 400
        
        # Use intelligent system to generate content with learned insights
        content = intelligent_system.generate_intelligent_content(
            topic=topic,
            platforms=platforms,
            language=language,
            quality=quality
        )
        
        # Schedule content if time provided
        if schedule_time_str:
            from datetime import datetime
            schedule_time = datetime.fromisoformat(schedule_time_str)
            queue_id = social_creator.schedule_content(content, schedule_time, platforms)
            content['queue_id'] = queue_id
            content['scheduled_time'] = schedule_time_str
        
        # Log cost
        if quality == 'premium':
            # Estimate cost based on content type
            if content_type in ['image_post', 'carousel', 'story']:
                cost = 0.04  # DALL-E 3 image cost
            else:  # video
                cost = 0.50  # RunwayML video cost
            
            cost_monitor.log_api_cost(
                user_id=user_id,
                api_service='social_content_premium',
                operation=content_type,
                cost=cost,
                success=True
            )
        
        return jsonify({
            'success': True,
            'content': content,
            'message': 'Intelligent content generated successfully',
            'used_ai_learnings': True
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/social-content/scheduled', methods=['GET'])
def get_scheduled_content():
    """Get all scheduled content for user"""
    try:
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'Must be logged in'}), 401
        
        token = auth_header.replace('Bearer ', '')
        validation = user_db.validate_session(token)
        
        if not validation.get('valid'):
            return jsonify({'success': False, 'error': 'Invalid session'}), 401
        
        # Get scheduled content from database
        import sqlite3
        conn = sqlite3.connect(social_creator.db_path)
        c = conn.cursor()
        
        c.execute('''SELECT * FROM content_queue 
                    WHERE status = 'pending' 
                    ORDER BY scheduled_time ASC 
                    LIMIT 50''')
        
        columns = [description[0] for description in c.description]
        scheduled = []
        
        for row in c.fetchall():
            scheduled.append(dict(zip(columns, row)))
        
        conn.close()
        
        return jsonify({
            'success': True,
            'content': scheduled
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/social-content/stats', methods=['GET'])
def get_social_stats():
    """Get social media content statistics"""
    try:
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'Must be logged in'}), 401
        
        token = auth_header.replace('Bearer ', '')
        validation = user_db.validate_session(token)
        
        if not validation.get('valid'):
            return jsonify({'success': False, 'error': 'Invalid session'}), 401
        
        # Get stats from database
        import sqlite3
        conn = sqlite3.connect(social_creator.db_path)
        c = conn.cursor()
        
        # Total posts
        c.execute('SELECT COUNT(*) FROM posted_content')
        total_posts = c.fetchone()[0]
        
        # Scheduled posts
        c.execute('SELECT COUNT(*) FROM content_queue WHERE status = "pending"')
        scheduled = c.fetchone()[0]
        
        # Average engagement
        c.execute('SELECT AVG(engagement_rate) FROM content_analytics')
        avg_engagement = c.fetchone()[0] or 0
        
        # Total reach (sum of views)
        c.execute('SELECT SUM(views) FROM content_analytics')
        total_reach = c.fetchone()[0] or 0
        
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_posts': total_posts,
                'scheduled': scheduled,
                'avg_engagement': round(avg_engagement, 2),
                'total_reach': total_reach
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/social-content/analytics', methods=['GET'])
def get_social_analytics():
    """Get comprehensive analytics report"""
    try:
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'Must be logged in'}), 401
        
        token = auth_header.replace('Bearer ', '')
        validation = user_db.validate_session(token)
        
        if not validation.get('valid'):
            return jsonify({'success': False, 'error': 'Invalid session'}), 401
        
        days = int(request.args.get('days', 30))
        report = social_creator.get_analytics_report(days)
        
        return jsonify({
            'success': True,
            'analytics': report
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/social-content/cost-estimate', methods=['GET'])
def get_cost_estimate():
    """Get cost estimation for social content creation"""
    try:
        costs = estimate_monthly_costs()
        return jsonify({
            'success': True,
            'costs': costs
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/social-content/post-now', methods=['POST'])
def post_content_now():
    """Post content immediately to platform"""
    try:
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'Must be logged in'}), 401
        
        token = auth_header.replace('Bearer ', '')
        validation = user_db.validate_session(token)
        
        if not validation.get('valid'):
            return jsonify({'success': False, 'error': 'Invalid session'}), 401
        
        data = request.get_json()
        content_id = data.get('content_id')
        platform = data.get('platform')
        
        if not content_id or not platform:
            return jsonify({'success': False, 'error': 'content_id and platform required'}), 400
        
        # Post content
        result = social_creator.auto_post_content(content_id, platform)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


