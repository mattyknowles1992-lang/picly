"""
Advanced Analytics & Rating System for Picly
State-of-the-art learning AI foundation with comprehensive tracking
"""

import sqlite3
import json
from datetime import datetime, timedelta
from collections import defaultdict
import hashlib
import os

class AnalyticsSystem:
    def __init__(self, db_path='analytics.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Create comprehensive analytics tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Generation Ratings Table - Core learning data
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS generation_ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                generation_id TEXT UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                prompt TEXT NOT NULL,
                prompt_hash TEXT NOT NULL,
                engine TEXT NOT NULL,
                model_version TEXT,
                rating INTEGER CHECK(rating >= 1 AND rating <= 5),
                quality_score REAL,
                feedback_text TEXT,
                feedback_tags TEXT,
                used_in_project BOOLEAN DEFAULT 0,
                downloaded BOOLEAN DEFAULT 0,
                shared BOOLEAN DEFAULT 0,
                regenerated BOOLEAN DEFAULT 0,
                edited BOOLEAN DEFAULT 0,
                time_to_rate INTEGER,
                session_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                rated_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Prompt Analytics - Learn what works
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prompt_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt_hash TEXT NOT NULL,
                prompt_text TEXT NOT NULL,
                engine TEXT NOT NULL,
                total_generations INTEGER DEFAULT 1,
                avg_rating REAL,
                total_ratings INTEGER DEFAULT 0,
                five_star_count INTEGER DEFAULT 0,
                four_star_count INTEGER DEFAULT 0,
                three_star_count INTEGER DEFAULT 0,
                two_star_count INTEGER DEFAULT 0,
                one_star_count INTEGER DEFAULT 0,
                avg_quality_score REAL,
                success_rate REAL,
                download_rate REAL,
                share_rate REAL,
                regeneration_rate REAL,
                avg_time_to_rate INTEGER,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(prompt_hash, engine)
            )
        ''')
        
        # User Behavior Analytics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_behavior (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_id TEXT NOT NULL,
                action_type TEXT NOT NULL,
                action_details TEXT,
                page_url TEXT,
                device_type TEXT,
                browser TEXT,
                screen_resolution TEXT,
                interaction_time INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # A/B Test Experiments
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ab_experiments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_name TEXT UNIQUE NOT NULL,
                description TEXT,
                variant_a TEXT NOT NULL,
                variant_b TEXT NOT NULL,
                metric_to_track TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_date TIMESTAMP,
                winner TEXT,
                confidence_level REAL
            )
        ''')
        
        # A/B Test Assignments
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ab_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                variant TEXT NOT NULL,
                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (experiment_id) REFERENCES ab_experiments (id),
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(experiment_id, user_id)
            )
        ''')
        
        # A/B Test Results
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ab_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                variant TEXT NOT NULL,
                metric_value REAL NOT NULL,
                conversion BOOLEAN DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (experiment_id) REFERENCES ab_experiments (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Feature Usage Analytics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feature_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feature_name TEXT NOT NULL,
                user_id INTEGER,
                usage_count INTEGER DEFAULT 1,
                success_count INTEGER DEFAULT 0,
                error_count INTEGER DEFAULT 0,
                avg_duration REAL,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Conversion Funnel Analytics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversion_funnel (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_id TEXT NOT NULL,
                funnel_stage TEXT NOT NULL,
                stage_order INTEGER NOT NULL,
                time_spent INTEGER,
                completed BOOLEAN DEFAULT 0,
                dropped_off BOOLEAN DEFAULT 0,
                conversion_value REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Model Performance Tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS model_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                engine TEXT NOT NULL,
                model_version TEXT NOT NULL,
                date DATE NOT NULL,
                total_requests INTEGER DEFAULT 0,
                successful_requests INTEGER DEFAULT 0,
                failed_requests INTEGER DEFAULT 0,
                avg_response_time REAL,
                avg_rating REAL,
                avg_quality_score REAL,
                total_cost REAL DEFAULT 0,
                total_revenue REAL DEFAULT 0,
                profit_margin REAL,
                UNIQUE(engine, model_version, date)
            )
        ''')
        
        # Engagement Metrics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS engagement_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date DATE NOT NULL,
                session_count INTEGER DEFAULT 0,
                total_time_spent INTEGER DEFAULT 0,
                generations_created INTEGER DEFAULT 0,
                features_explored INTEGER DEFAULT 0,
                social_shares INTEGER DEFAULT 0,
                feedback_given INTEGER DEFAULT 0,
                help_accessed INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, date)
            )
        ''')
        
        # Cohort Analysis
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_cohorts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                cohort_date DATE NOT NULL,
                acquisition_source TEXT,
                user_segment TEXT,
                initial_plan TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id)
            )
        ''')
        
        # Machine Learning Training Data
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ml_training_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_type TEXT NOT NULL,
                features TEXT NOT NULL,
                label REAL NOT NULL,
                weight REAL DEFAULT 1.0,
                validation_set BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_generation_user ON generation_ratings(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_generation_prompt ON generation_ratings(prompt_hash)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_generation_rating ON generation_ratings(rating)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_prompt_hash ON prompt_analytics(prompt_hash)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_behavior ON user_behavior(user_id, timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_feature_usage ON feature_usage(feature_name, user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_model_perf ON model_performance(engine, date)')
        
        conn.commit()
        conn.close()
    
    def hash_prompt(self, prompt_text):
        """Create hash of prompt for tracking similar prompts"""
        return hashlib.sha256(prompt_text.lower().strip().encode()).hexdigest()
    
    def record_generation(self, generation_id, user_id, prompt, engine, model_version=None, session_id=None):
        """Record a new generation for tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        prompt_hash = self.hash_prompt(prompt)
        
        try:
            cursor.execute('''
                INSERT INTO generation_ratings 
                (generation_id, user_id, prompt, prompt_hash, engine, model_version, session_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (generation_id, user_id, prompt, prompt_hash, engine, model_version, session_id))
            
            # Update prompt analytics
            cursor.execute('''
                INSERT INTO prompt_analytics (prompt_hash, prompt_text, engine)
                VALUES (?, ?, ?)
                ON CONFLICT(prompt_hash, engine) DO UPDATE SET
                    total_generations = total_generations + 1,
                    last_used = CURRENT_TIMESTAMP
            ''', (prompt_hash, prompt, engine))
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error recording generation: {e}")
            return False
        finally:
            conn.close()
    
    def submit_rating(self, generation_id, rating, quality_score=None, feedback_text=None, 
                     feedback_tags=None, time_to_rate=None):
        """Submit user rating for a generation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get generation details
            cursor.execute('''
                SELECT prompt_hash, engine FROM generation_ratings WHERE generation_id = ?
            ''', (generation_id,))
            result = cursor.fetchone()
            
            if not result:
                return {'success': False, 'error': 'Generation not found'}
            
            prompt_hash, engine = result
            
            # Update generation rating
            cursor.execute('''
                UPDATE generation_ratings 
                SET rating = ?, quality_score = ?, feedback_text = ?, 
                    feedback_tags = ?, time_to_rate = ?, rated_at = CURRENT_TIMESTAMP
                WHERE generation_id = ?
            ''', (rating, quality_score, feedback_text, feedback_tags, time_to_rate, generation_id))
            
            # Update prompt analytics
            rating_field = f"{['one', 'two', 'three', 'four', 'five'][rating-1]}_star_count"
            cursor.execute(f'''
                UPDATE prompt_analytics 
                SET total_ratings = total_ratings + 1,
                    {rating_field} = {rating_field} + 1,
                    avg_rating = (
                        (one_star_count * 1.0 + two_star_count * 2.0 + 
                         three_star_count * 3.0 + four_star_count * 4.0 + 
                         five_star_count * 5.0) / 
                        CAST(total_ratings AS REAL)
                    )
                WHERE prompt_hash = ? AND engine = ?
            ''', (prompt_hash, engine))
            
            # Calculate success rate (4-5 stars = success)
            if rating >= 4:
                cursor.execute('''
                    UPDATE prompt_analytics 
                    SET success_rate = CAST((four_star_count + five_star_count) AS REAL) / total_ratings
                    WHERE prompt_hash = ? AND engine = ?
                ''', (prompt_hash, engine))
            
            # Prepare ML training data
            cursor.execute('''
                SELECT prompt_text FROM prompt_analytics WHERE prompt_hash = ? AND engine = ?
            ''', (prompt_hash, engine))
            prompt_text = cursor.fetchone()[0]
            
            # Extract features for ML
            features = {
                'prompt_length': len(prompt_text),
                'word_count': len(prompt_text.split()),
                'has_style_keywords': any(word in prompt_text.lower() for word in 
                    ['realistic', 'artistic', 'cinematic', 'detailed', 'vibrant']),
                'has_quality_keywords': any(word in prompt_text.lower() for word in 
                    ['4k', '8k', 'hd', 'high quality', 'professional']),
                'engine': engine,
                'punctuation_count': sum(1 for char in prompt_text if char in '.,!?;:')
            }
            
            cursor.execute('''
                INSERT INTO ml_training_data (data_type, features, label)
                VALUES ('rating_prediction', ?, ?)
            ''', (json.dumps(features), float(rating)))
            
            conn.commit()
            return {'success': True, 'message': 'Rating submitted successfully'}
            
        except Exception as e:
            conn.rollback()
            print(f"Error submitting rating: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def update_generation_action(self, generation_id, action_type):
        """Track user actions on generations (download, share, edit, etc.)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            field_map = {
                'download': 'downloaded',
                'share': 'shared',
                'edit': 'edited',
                'regenerate': 'regenerated',
                'use': 'used_in_project'
            }
            
            field = field_map.get(action_type)
            if field:
                cursor.execute(f'''
                    UPDATE generation_ratings SET {field} = 1 WHERE generation_id = ?
                ''', (generation_id,))
                
                # Update prompt analytics rates
                cursor.execute('''
                    SELECT prompt_hash, engine FROM generation_ratings WHERE generation_id = ?
                ''', (generation_id,))
                result = cursor.fetchone()
                
                if result:
                    prompt_hash, engine = result
                    rate_field = f"{action_type}_rate"
                    if rate_field in ['download_rate', 'share_rate', 'regeneration_rate']:
                        cursor.execute(f'''
                            UPDATE prompt_analytics 
                            SET {rate_field} = (
                                SELECT CAST(SUM(CASE WHEN {field} = 1 THEN 1 ELSE 0 END) AS REAL) / COUNT(*)
                                FROM generation_ratings 
                                WHERE prompt_hash = ? AND engine = ?
                            )
                            WHERE prompt_hash = ? AND engine = ?
                        ''', (prompt_hash, engine, prompt_hash, engine))
                
                conn.commit()
                return True
        except Exception as e:
            conn.rollback()
            print(f"Error updating action: {e}")
            return False
        finally:
            conn.close()
    
    def track_user_behavior(self, user_id, session_id, action_type, action_details=None,
                           page_url=None, device_info=None, interaction_time=None):
        """Track granular user behavior for UX improvements"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO user_behavior 
                (user_id, session_id, action_type, action_details, page_url, 
                 device_type, browser, screen_resolution, interaction_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, session_id, action_type, json.dumps(action_details) if action_details else None,
                  page_url, device_info.get('type') if device_info else None,
                  device_info.get('browser') if device_info else None,
                  device_info.get('screen') if device_info else None,
                  interaction_time))
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error tracking behavior: {e}")
            return False
        finally:
            conn.close()
    
    def get_top_prompts(self, engine=None, min_ratings=5, limit=100):
        """Get highest rated prompts for learning and suggestions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = '''
            SELECT prompt_text, engine, avg_rating, total_ratings, 
                   success_rate, download_rate, share_rate
            FROM prompt_analytics
            WHERE total_ratings >= ?
        '''
        params = [min_ratings]
        
        if engine:
            query += ' AND engine = ?'
            params.append(engine)
        
        query += ' ORDER BY avg_rating DESC, total_ratings DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        
        return [{
            'prompt': row[0],
            'engine': row[1],
            'avg_rating': row[2],
            'total_ratings': row[3],
            'success_rate': row[4],
            'download_rate': row[5],
            'share_rate': row[6]
        } for row in results]
    
    def get_prompt_suggestions(self, partial_prompt, engine, limit=5):
        """Get AI-powered prompt suggestions based on successful prompts"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT prompt_text, avg_rating, success_rate
            FROM prompt_analytics
            WHERE engine = ? AND total_ratings >= 3 AND avg_rating >= 4.0
            ORDER BY success_rate DESC, avg_rating DESC
            LIMIT ?
        ''', (engine, limit))
        
        results = cursor.fetchall()
        conn.close()
        
        return [{
            'prompt': row[0],
            'avg_rating': row[1],
            'success_rate': row[2]
        } for row in results]
    
    def track_model_performance(self, engine, model_version, success, response_time, cost, revenue):
        """Track model performance metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            today = datetime.now().date()
            cursor.execute('''
                INSERT INTO model_performance 
                (engine, model_version, date, total_requests, successful_requests, 
                 failed_requests, avg_response_time, total_cost, total_revenue)
                VALUES (?, ?, ?, 1, ?, ?, ?, ?, ?)
                ON CONFLICT(engine, model_version, date) DO UPDATE SET
                    total_requests = total_requests + 1,
                    successful_requests = successful_requests + ?,
                    failed_requests = failed_requests + ?,
                    avg_response_time = (avg_response_time * total_requests + ?) / (total_requests + 1),
                    total_cost = total_cost + ?,
                    total_revenue = total_revenue + ?,
                    profit_margin = ((total_revenue - total_cost) / total_revenue) * 100
            ''', (engine, model_version, today, 1 if success else 0, 0 if success else 1,
                  response_time, cost, revenue,
                  1 if success else 0, 0 if success else 1, response_time, cost, revenue))
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error tracking model performance: {e}")
            return False
        finally:
            conn.close()
    
    def get_analytics_dashboard(self, days=30):
        """Get comprehensive analytics for dashboard"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        start_date = (datetime.now() - timedelta(days=days)).date()
        
        # Overall stats
        cursor.execute('''
            SELECT 
                COUNT(*) as total_generations,
                AVG(rating) as avg_rating,
                AVG(quality_score) as avg_quality,
                SUM(downloaded) as total_downloads,
                SUM(shared) as total_shares,
                COUNT(DISTINCT user_id) as active_users
            FROM generation_ratings
            WHERE created_at >= ?
        ''', (start_date,))
        overall = cursor.fetchone()
        
        # Engine performance
        cursor.execute('''
            SELECT 
                engine,
                COUNT(*) as generations,
                AVG(rating) as avg_rating,
                SUM(downloaded) * 100.0 / COUNT(*) as download_rate
            FROM generation_ratings
            WHERE created_at >= ? AND rating IS NOT NULL
            GROUP BY engine
            ORDER BY avg_rating DESC
        ''', (start_date,))
        engines = cursor.fetchall()
        
        # Top prompts
        cursor.execute('''
            SELECT prompt_text, avg_rating, total_ratings, success_rate
            FROM prompt_analytics
            WHERE total_ratings >= 3
            ORDER BY avg_rating DESC, total_ratings DESC
            LIMIT 10
        ''', ())
        top_prompts = cursor.fetchall()
        
        conn.close()
        
        return {
            'overall': {
                'total_generations': overall[0] or 0,
                'avg_rating': round(overall[1], 2) if overall[1] else 0,
                'avg_quality': round(overall[2], 2) if overall[2] else 0,
                'total_downloads': overall[3] or 0,
                'total_shares': overall[4] or 0,
                'active_users': overall[5] or 0
            },
            'engines': [{
                'name': e[0],
                'generations': e[1],
                'avg_rating': round(e[2], 2),
                'download_rate': round(e[3], 1)
            } for e in engines],
            'top_prompts': [{
                'prompt': p[0],
                'rating': round(p[1], 2),
                'ratings': p[2],
                'success_rate': round(p[3] * 100, 1) if p[3] else 0
            } for p in top_prompts]
        }

# Initialize global analytics system
analytics_system = AnalyticsSystem()
