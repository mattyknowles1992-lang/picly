"""
User Authentication Database for Picly
Handles user registration, login, and session management with encrypted passwords
"""

import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
import os

class UserDatabase:
    def __init__(self, db_path='users.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Create users table if it doesn't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                premium_credits INTEGER DEFAULT 0,
                free_credits_today INTEGER DEFAULT 10,
                last_free_reset DATE,
                referral_code TEXT UNIQUE,
                referred_by INTEGER,
                total_generations INTEGER DEFAULT 0,
                subscription_status TEXT DEFAULT 'none',
                subscription_id TEXT,
                subscription_expires_at TIMESTAMP,
                low_token_threshold INTEGER DEFAULT 300,
                low_token_notified BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                FOREIGN KEY (referred_by) REFERENCES users (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_token TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                stripe_payment_id TEXT,
                amount REAL NOT NULL,
                credits INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                achievement_type TEXT NOT NULL,
                credits_awarded INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, achievement_type)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL UNIQUE,
                total_generations INTEGER DEFAULT 0,
                free_generations INTEGER DEFAULT 0,
                premium_generations INTEGER DEFAULT 0,
                revenue REAL DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password, salt=None):
        """Hash password with salt using SHA-256"""
        if salt is None:
            salt = secrets.token_hex(32)
        
        # Hash password with salt
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # iterations
        ).hex()
        
        return password_hash, salt
    
    def register_user(self, username, email, password):
        """Register a new user"""
        try:
            # Validate input
            if not username or not email or not password:
                return {'success': False, 'error': 'All fields are required'}
            
            if len(password) < 8:
                return {'success': False, 'error': 'Password must be at least 8 characters'}
            
            # Hash password
            password_hash, salt = self.hash_password(password)
            
            # Generate unique referral code
            referral_code = secrets.token_urlsafe(8)
            
            # Insert into database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, salt, referral_code, last_free_reset)
                VALUES (?, ?, ?, ?, ?, DATE('now'))
            ''', (username, email, password_hash, salt, referral_code))
            
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            
            return {
                'success': True,
                'message': 'Account created successfully',
                'user_id': user_id
            }
            
        except sqlite3.IntegrityError as e:
            if 'username' in str(e):
                return {'success': False, 'error': 'Username already exists'}
            elif 'email' in str(e):
                return {'success': False, 'error': 'Email already registered'}
            else:
                return {'success': False, 'error': 'Registration failed'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def login_user(self, username, password):
        """Authenticate user and create session"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get user data
            cursor.execute('''
                SELECT id, username, password_hash, salt
                FROM users
                WHERE username = ? OR email = ?
            ''', (username, username))
            
            user = cursor.fetchone()
            
            if not user:
                conn.close()
                return {'success': False, 'error': 'Invalid username or password'}
            
            user_id, username, stored_hash, salt = user
            
            # Verify password
            password_hash, _ = self.hash_password(password, salt)
            
            if password_hash != stored_hash:
                conn.close()
                return {'success': False, 'error': 'Invalid username or password'}
            
            # Create session token
            session_token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(days=7)  # 7 day session
            
            cursor.execute('''
                INSERT INTO sessions (user_id, session_token, expires_at)
                VALUES (?, ?, ?)
            ''', (user_id, session_token, expires_at))
            
            # Update last login
            cursor.execute('''
                UPDATE users SET last_login = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (user_id,))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'message': 'Login successful',
                'session_token': session_token,
                'username': username,
                'expires_at': expires_at.isoformat()
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def validate_session(self, session_token):
        """Validate session token"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT s.user_id, u.username, s.expires_at
                FROM sessions s
                JOIN users u ON s.user_id = u.id
                WHERE s.session_token = ?
            ''', (session_token,))
            
            session = cursor.fetchone()
            conn.close()
            
            if not session:
                return {'valid': False, 'error': 'Invalid session'}
            
            user_id, username, expires_at = session
            expires_dt = datetime.fromisoformat(expires_at)
            
            if datetime.now() > expires_dt:
                return {'valid': False, 'error': 'Session expired'}
            
            return {
                'valid': True,
                'user_id': user_id,
                'username': username
            }
            
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    def logout_user(self, session_token):
        """Delete session token"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM sessions WHERE session_token = ?', (session_token,))
            
            conn.commit()
            conn.close()
            
            return {'success': True, 'message': 'Logged out successfully'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM sessions WHERE expires_at < CURRENT_TIMESTAMP')
            
            conn.commit()
            deleted = cursor.rowcount
            conn.close()
            
            return {'success': True, 'deleted': deleted}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_user_credits(self, user_id):
        """Get user's credit balance (resets daily free credits)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if daily free credits need reset
            cursor.execute('''
                SELECT premium_credits, free_credits_today, last_free_reset,
                       referral_code, total_generations, subscription_status,
                       subscription_expires_at
                FROM users WHERE id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            if not result:
                conn.close()
                return {'success': False, 'error': 'User not found'}
            
            premium, free, last_reset, ref_code, total_gens, sub_status, sub_expires = result
            
            # Check if subscription expired
            if sub_status == 'active':
                from datetime import datetime
                if sub_expires and datetime.fromisoformat(sub_expires) < datetime.now():
                    cursor.execute('''
                        UPDATE users SET subscription_status = 'expired'
                        WHERE id = ?
                    ''', (user_id,))
                    sub_status = 'expired'
                    conn.commit()
            
            # Reset daily free credits if new day
            from datetime import date
            today = str(date.today())
            
            if last_reset != today:
                free = 10  # Reset to 10 free credits
                cursor.execute('''
                    UPDATE users 
                    SET free_credits_today = 10, last_free_reset = DATE('now')
                    WHERE id = ?
                ''', (user_id,))
                conn.commit()
            
            conn.close()
            
            return {
                'success': True,
                'premium_credits': premium,
                'free_credits': free,
                'referral_code': ref_code,
                'total_generations': total_gens,
                'subscription_status': sub_status,
                'subscription_expires': sub_expires,
                'has_unlimited': sub_status == 'active'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def use_credit(self, user_id, credit_type='free'):
        """Deduct one credit from user (free or premium)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if credit_type == 'free':
                cursor.execute('''
                    UPDATE users 
                    SET free_credits_today = free_credits_today - 1,
                        total_generations = total_generations + 1
                    WHERE id = ? AND free_credits_today > 0
                ''', (user_id,))
            else:  # premium
                cursor.execute('''
                    UPDATE users 
                    SET premium_credits = premium_credits - 1,
                        total_generations = total_generations + 1
                    WHERE id = ? AND premium_credits > 0
                ''', (user_id,))
            
            if cursor.rowcount == 0:
                conn.close()
                return {'success': False, 'error': 'Insufficient credits'}
            
            conn.commit()
            conn.close()
            
            return {'success': True, 'message': 'Credit deducted'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def add_credits(self, user_id, credits, transaction_id=None, amount=0):
        """Add premium credits to user and log transaction"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users SET premium_credits = premium_credits + ?
                WHERE id = ?
            ''', (credits, user_id))
            
            # Log transaction
            if transaction_id:
                cursor.execute('''
                    INSERT INTO transactions (user_id, stripe_payment_id, amount, credits, status)
                    VALUES (?, ?, ?, ?, 'completed')
                ''', (user_id, transaction_id, amount, credits))
            
            conn.commit()
            conn.close()
            
            return {'success': True, 'message': f'{credits} credits added'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def apply_referral(self, user_id, referral_code):
        """Apply referral code: Give 10 credits to referrer, 5 to new user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Find referrer
            cursor.execute('SELECT id FROM users WHERE referral_code = ?', (referral_code,))
            referrer = cursor.fetchone()
            
            if not referrer:
                conn.close()
                return {'success': False, 'error': 'Invalid referral code'}
            
            referrer_id = referrer[0]
            
            # Give 10 credits to referrer
            cursor.execute('''
                UPDATE users SET premium_credits = premium_credits + 10
                WHERE id = ?
            ''', (referrer_id,))
            
            # Give 5 extra credits to new user
            cursor.execute('''
                UPDATE users 
                SET premium_credits = premium_credits + 5,
                    free_credits_today = free_credits_today + 5,
                    referred_by = ?
                WHERE id = ?
            ''', (referrer_id, user_id))
            
            conn.commit()
            conn.close()
            
            return {'success': True, 'message': 'Referral applied! +15 total credits'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def award_achievement(self, user_id, achievement_type, credits):
        """Award achievement credits (one-time per achievement)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO achievements (user_id, achievement_type, credits_awarded)
                VALUES (?, ?, ?)
            ''', (user_id, achievement_type, credits))
            
            cursor.execute('''
                UPDATE users SET premium_credits = premium_credits + ?
                WHERE id = ?
            ''', (credits, user_id))
            
            conn.commit()
            conn.close()
            
            return {'success': True, 'message': f'Achievement unlocked! +{credits} credits'}
            
        except sqlite3.IntegrityError:
            return {'success': False, 'error': 'Achievement already claimed'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def activate_subscription(self, user_id, subscription_id):
        """Activate unlimited subscription for user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            from datetime import datetime, timedelta
            expires_at = datetime.now() + timedelta(days=30)
            
            cursor.execute('''
                UPDATE users 
                SET subscription_status = 'active',
                    subscription_id = ?,
                    subscription_expires_at = ?
                WHERE id = ?
            ''', (subscription_id, expires_at.isoformat(), user_id))
            
            conn.commit()
            conn.close()
            
            return {'success': True, 'message': 'Unlimited subscription activated!'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def deactivate_subscription(self, subscription_id):
        """Deactivate subscription when cancelled"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users 
                SET subscription_status = 'cancelled'
                WHERE subscription_id = ?
            ''', (subscription_id,))
            
            conn.commit()
            conn.close()
            
            return {'success': True, 'message': 'Subscription cancelled'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def increment_generations(self, user_id):
        """Increment generation count for unlimited users"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users 
                SET total_generations = total_generations + 1
                WHERE id = ?
            ''', (user_id,))
            
            conn.commit()
            conn.close()
            
            return {'success': True}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def check_low_token_alert(self, user_id):
        """Check if user needs low token notification"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT premium_credits, free_credits_today, low_token_threshold, 
                       low_token_notified, subscription_status
                FROM users WHERE id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            if not result:
                conn.close()
                return {'needs_alert': False}
            
            premium, free, threshold, notified, sub_status = result
            
            # Don't alert unlimited users
            if sub_status == 'active':
                conn.close()
                return {'needs_alert': False}
            
            total_tokens = premium + free
            
            # Mandatory alert at 100 tokens or custom threshold
            critical_alert = total_tokens <= 100 and not notified
            custom_alert = total_tokens <= threshold and total_tokens > 100 and not notified
            
            if critical_alert or custom_alert:
                # Mark as notified
                cursor.execute('''
                    UPDATE users SET low_token_notified = 1 WHERE id = ?
                ''', (user_id,))
                conn.commit()
                conn.close()
                
                return {
                    'needs_alert': True,
                    'total_tokens': total_tokens,
                    'threshold': threshold,
                    'is_critical': critical_alert
                }
            
            # Reset notification flag if tokens go above threshold
            if total_tokens > threshold and notified:
                cursor.execute('''
                    UPDATE users SET low_token_notified = 0 WHERE id = ?
                ''', (user_id,))
                conn.commit()
            
            conn.close()
            return {'needs_alert': False}
            
        except Exception as e:
            return {'needs_alert': False, 'error': str(e)}
    
    def update_token_threshold(self, user_id, new_threshold):
        """Update user's custom low token notification threshold"""
        try:
            # Validate threshold (minimum 100, maximum 1000)
            if new_threshold < 100:
                new_threshold = 100
            elif new_threshold > 1000:
                new_threshold = 1000
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users 
                SET low_token_threshold = ?, low_token_notified = 0
                WHERE id = ?
            ''', (new_threshold, user_id))
            
            conn.commit()
            conn.close()
            
            return {'success': True, 'threshold': new_threshold}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_notification_preferences(self, user_id):
        """Get user's notification preferences"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT low_token_threshold FROM users WHERE id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {'success': True, 'threshold': result[0]}
            return {'success': False, 'error': 'User not found'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

