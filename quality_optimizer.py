"""
Adaptive Quality Optimizer for Picly
AI-powered system that learns to maximize quality while minimizing cost and time
"""

import sqlite3
import json
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

class QualityOptimizer:
    def __init__(self, analytics_db='analytics.db'):
        self.analytics_db = analytics_db
        self.init_optimizer_tables()
        
        # Performance thresholds
        self.min_samples = 10  # Minimum ratings before trusting data
        self.quality_threshold = 4.0  # Target average rating
        self.cost_weight = 0.3  # Balance between quality and cost
        self.speed_weight = 0.2  # Balance for generation speed
    
    def init_optimizer_tables(self):
        """Create tables for quality optimization"""
        conn = sqlite3.connect(self.analytics_db)
        cursor = conn.cursor()
        
        # Engine performance profiles
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS engine_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                engine TEXT NOT NULL,
                settings_hash TEXT NOT NULL,
                settings_json TEXT NOT NULL,
                total_uses INTEGER DEFAULT 0,
                avg_rating REAL DEFAULT 0,
                avg_quality_score REAL DEFAULT 0,
                avg_generation_time REAL DEFAULT 0,
                avg_cost REAL DEFAULT 0,
                success_rate REAL DEFAULT 0,
                quality_per_dollar REAL DEFAULT 0,
                quality_per_second REAL DEFAULT 0,
                overall_score REAL DEFAULT 0,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(engine, settings_hash)
            )
        ''')
        
        # Generation performance logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS generation_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                generation_id TEXT NOT NULL,
                engine TEXT NOT NULL,
                settings_hash TEXT NOT NULL,
                prompt_category TEXT,
                generation_time REAL NOT NULL,
                cost REAL NOT NULL,
                rating INTEGER,
                quality_score REAL,
                success BOOLEAN DEFAULT 1,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (generation_id) REFERENCES generation_ratings (generation_id)
            )
        ''')
        
        # Prompt category patterns
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prompt_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_name TEXT UNIQUE NOT NULL,
                keywords TEXT NOT NULL,
                best_engine TEXT,
                best_settings TEXT,
                avg_rating REAL,
                sample_count INTEGER DEFAULT 0
            )
        ''')
        
        # Real-time optimization cache
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS optimization_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cache_key TEXT UNIQUE NOT NULL,
                recommended_engine TEXT NOT NULL,
                recommended_settings TEXT NOT NULL,
                confidence_score REAL NOT NULL,
                reason TEXT,
                valid_until TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Initialize default prompt categories
        self.init_default_categories(cursor)
        
        conn.commit()
        conn.close()
    
    def init_default_categories(self, cursor):
        """Initialize common prompt categories"""
        categories = [
            {
                'name': 'portrait',
                'keywords': json.dumps(['portrait', 'face', 'person', 'selfie', 'headshot', 'character'])
            },
            {
                'name': 'landscape',
                'keywords': json.dumps(['landscape', 'scenery', 'nature', 'mountain', 'forest', 'ocean', 'sky'])
            },
            {
                'name': 'product',
                'keywords': json.dumps(['product', 'commercial', 'advertisement', 'packaging', 'logo'])
            },
            {
                'name': 'artistic',
                'keywords': json.dumps(['art', 'painting', 'artistic', 'abstract', 'creative', 'surreal'])
            },
            {
                'name': 'photorealistic',
                'keywords': json.dumps(['realistic', 'photorealistic', 'photo', 'real', 'cinematic'])
            },
            {
                'name': 'illustration',
                'keywords': json.dumps(['illustration', 'cartoon', 'drawing', 'sketch', 'anime', 'comic'])
            },
            {
                'name': 'architecture',
                'keywords': json.dumps(['building', 'architecture', 'interior', 'room', 'house'])
            },
            {
                'name': 'fantasy',
                'keywords': json.dumps(['fantasy', 'magical', 'dragon', 'wizard', 'mythical'])
            }
        ]
        
        for cat in categories:
            cursor.execute('''
                INSERT OR IGNORE INTO prompt_categories (category_name, keywords)
                VALUES (?, ?)
            ''', (cat['name'], cat['keywords']))
    
    def categorize_prompt(self, prompt):
        """Automatically categorize prompt based on keywords"""
        conn = sqlite3.connect(self.analytics_db)
        cursor = conn.cursor()
        
        cursor.execute('SELECT category_name, keywords FROM prompt_categories')
        categories = cursor.fetchall()
        conn.close()
        
        prompt_lower = prompt.lower()
        matches = []
        
        for cat_name, keywords_json in categories:
            keywords = json.loads(keywords_json)
            match_count = sum(1 for kw in keywords if kw in prompt_lower)
            if match_count > 0:
                matches.append((cat_name, match_count))
        
        if matches:
            # Return category with most keyword matches
            matches.sort(key=lambda x: x[1], reverse=True)
            return matches[0][0]
        
        return 'general'
    
    def log_generation_performance(self, generation_id, engine, settings, prompt, 
                                   generation_time, cost, category=None):
        """Log performance metrics for a generation"""
        conn = sqlite3.connect(self.analytics_db)
        cursor = conn.cursor()
        
        # Auto-categorize if not provided
        if not category:
            category = self.categorize_prompt(prompt)
        
        # Create settings hash
        settings_hash = self._hash_settings(settings)
        
        cursor.execute('''
            INSERT INTO generation_performance 
            (generation_id, engine, settings_hash, prompt_category, generation_time, cost)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (generation_id, engine, settings_hash, category, generation_time, cost))
        
        # Update engine profile
        cursor.execute('''
            INSERT INTO engine_profiles (engine, settings_hash, settings_json, total_uses, avg_generation_time, avg_cost)
            VALUES (?, ?, ?, 1, ?, ?)
            ON CONFLICT(engine, settings_hash) DO UPDATE SET
                total_uses = total_uses + 1,
                avg_generation_time = (avg_generation_time * total_uses + ?) / (total_uses + 1),
                avg_cost = (avg_cost * total_uses + ?) / (total_uses + 1),
                last_used = CURRENT_TIMESTAMP
        ''', (engine, settings_hash, json.dumps(settings), generation_time, cost,
              generation_time, cost))
        
        conn.commit()
        conn.close()
    
    def update_rating_performance(self, generation_id, rating, quality_score):
        """Update performance metrics when rating is submitted"""
        conn = sqlite3.connect(self.analytics_db)
        cursor = conn.cursor()
        
        # Get generation performance data
        cursor.execute('''
            SELECT engine, settings_hash, prompt_category FROM generation_performance
            WHERE generation_id = ?
        ''', (generation_id,))
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            return
        
        engine, settings_hash, category = result
        
        # Update generation performance
        cursor.execute('''
            UPDATE generation_performance 
            SET rating = ?, quality_score = ?
            WHERE generation_id = ?
        ''', (rating, quality_score, generation_id))
        
        # Update engine profile with new rating data
        cursor.execute('''
            SELECT 
                AVG(rating) as avg_rating,
                AVG(quality_score) as avg_quality,
                AVG(generation_time) as avg_time,
                AVG(cost) as avg_cost,
                COUNT(CASE WHEN rating >= 4 THEN 1 END) * 100.0 / COUNT(*) as success_rate
            FROM generation_performance
            WHERE engine = ? AND settings_hash = ? AND rating IS NOT NULL
        ''', (engine, settings_hash))
        
        stats = cursor.fetchone()
        
        if stats and stats[0]:
            avg_rating, avg_quality, avg_time, avg_cost, success_rate = stats
            
            # Calculate composite scores
            quality_per_dollar = (avg_quality or avg_rating * 20) / max(avg_cost, 0.001)
            quality_per_second = (avg_quality or avg_rating * 20) / max(avg_time, 0.1)
            
            # Overall score: weighted combination
            overall_score = (
                avg_rating * 0.4 +  # 40% from star rating
                (avg_quality / 20) * 0.3 +  # 30% from quality score (normalized)
                (quality_per_dollar / 100) * 0.2 +  # 20% efficiency
                (quality_per_second / 10) * 0.1  # 10% speed
            )
            
            cursor.execute('''
                UPDATE engine_profiles 
                SET avg_rating = ?,
                    avg_quality_score = ?,
                    success_rate = ?,
                    quality_per_dollar = ?,
                    quality_per_second = ?,
                    overall_score = ?
                WHERE engine = ? AND settings_hash = ?
            ''', (avg_rating, avg_quality, success_rate, quality_per_dollar, 
                  quality_per_second, overall_score, engine, settings_hash))
            
            # Update category best engine if this is better
            cursor.execute('''
                SELECT best_engine, avg_rating FROM prompt_categories WHERE category_name = ?
            ''', (category,))
            
            cat_result = cursor.fetchone()
            if not cat_result or not cat_result[1] or avg_rating > cat_result[1]:
                cursor.execute('''
                    UPDATE prompt_categories 
                    SET best_engine = ?,
                        best_settings = ?,
                        avg_rating = ?,
                        sample_count = sample_count + 1
                    WHERE category_name = ?
                ''', (engine, json.dumps({'settings_hash': settings_hash}), avg_rating, category))
        
        # Invalidate optimization cache
        cursor.execute('DELETE FROM optimization_cache WHERE cache_key LIKE ?', (f'%{category}%',))
        
        conn.commit()
        conn.close()
    
    def get_optimal_engine(self, prompt, user_preferences=None):
        """
        Get the optimal engine and settings for a prompt
        Returns: {engine, settings, confidence, reason}
        """
        category = self.categorize_prompt(prompt)
        cache_key = f"{category}_{user_preferences or 'default'}"
        
        conn = sqlite3.connect(self.analytics_db)
        cursor = conn.cursor()
        
        # Check cache first
        cursor.execute('''
            SELECT recommended_engine, recommended_settings, confidence_score, reason
            FROM optimization_cache
            WHERE cache_key = ? AND valid_until > CURRENT_TIMESTAMP
        ''', (cache_key,))
        
        cached = cursor.fetchone()
        if cached:
            conn.close()
            return {
                'engine': cached[0],
                'settings': json.loads(cached[1]),
                'confidence': cached[2],
                'reason': cached[3],
                'category': category
            }
        
        # Get all engine profiles with sufficient data
        cursor.execute('''
            SELECT 
                engine,
                settings_json,
                total_uses,
                avg_rating,
                avg_quality_score,
                avg_generation_time,
                avg_cost,
                success_rate,
                quality_per_dollar,
                quality_per_second,
                overall_score
            FROM engine_profiles
            WHERE total_uses >= ?
            ORDER BY overall_score DESC
        ''', (self.min_samples,))
        
        engines = cursor.fetchall()
        
        # Check category-specific recommendation
        cursor.execute('''
            SELECT best_engine, best_settings, avg_rating, sample_count
            FROM prompt_categories
            WHERE category_name = ? AND sample_count >= ?
        ''', (category, self.min_samples))
        
        category_best = cursor.fetchone()
        
        conn.close()
        
        if not engines:
            # No data yet, use default
            return {
                'engine': 'flux-pro',
                'settings': {'quality_boost': True},
                'confidence': 0.0,
                'reason': 'No performance data yet, using default',
                'category': category
            }
        
        # If category has strong data, prioritize it
        if category_best and category_best[3] >= self.min_samples * 2:
            engine = category_best[0]
            settings = json.loads(category_best[1]) if category_best[1] else {}
            confidence = min(category_best[3] / 100.0, 1.0)
            reason = f'Optimized for {category} category (avg rating: {category_best[2]:.2f})'
        else:
            # Use overall best performer
            best = engines[0]
            engine = best[0]
            settings = json.loads(best[1])
            confidence = min(best[2] / 100.0, 1.0)
            reason = f'Best overall performer (rating: {best[3]:.2f}, quality: {best[4]:.1f})'
        
        # Cache the result
        self._cache_recommendation(cache_key, engine, settings, confidence, reason)
        
        return {
            'engine': engine,
            'settings': settings,
            'confidence': confidence,
            'reason': reason,
            'category': category
        }
    
    def get_engine_comparison(self):
        """Get comparative analysis of all engines"""
        conn = sqlite3.connect(self.analytics_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                engine,
                total_uses,
                avg_rating,
                avg_quality_score,
                avg_generation_time,
                avg_cost,
                success_rate,
                quality_per_dollar,
                overall_score
            FROM engine_profiles
            WHERE total_uses >= ?
            ORDER BY overall_score DESC
        ''', (self.min_samples,))
        
        engines = cursor.fetchall()
        conn.close()
        
        return [{
            'engine': e[0],
            'uses': e[1],
            'rating': round(e[2], 2) if e[2] else 0,
            'quality': round(e[3], 1) if e[3] else 0,
            'speed': round(e[4], 2) if e[4] else 0,
            'cost': round(e[5], 4) if e[5] else 0,
            'success_rate': round(e[6], 1) if e[6] else 0,
            'efficiency': round(e[7], 1) if e[7] else 0,
            'score': round(e[8], 2) if e[8] else 0
        } for e in engines]
    
    def get_category_insights(self):
        """Get insights about which engines work best for each category"""
        conn = sqlite3.connect(self.analytics_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT category_name, best_engine, avg_rating, sample_count
            FROM prompt_categories
            WHERE sample_count >= ?
            ORDER BY avg_rating DESC
        ''', (self.min_samples,))
        
        categories = cursor.fetchall()
        conn.close()
        
        return [{
            'category': c[0],
            'best_engine': c[1],
            'avg_rating': round(c[2], 2) if c[2] else 0,
            'samples': c[3]
        } for c in categories]
    
    def _hash_settings(self, settings):
        """Create a hash of settings dict for comparison"""
        import hashlib
        settings_str = json.dumps(settings, sort_keys=True)
        return hashlib.md5(settings_str.encode()).hexdigest()
    
    def _cache_recommendation(self, cache_key, engine, settings, confidence, reason):
        """Cache an optimization recommendation"""
        conn = sqlite3.connect(self.analytics_db)
        cursor = conn.cursor()
        
        valid_until = datetime.now() + timedelta(hours=6)  # Cache for 6 hours
        
        cursor.execute('''
            INSERT OR REPLACE INTO optimization_cache
            (cache_key, recommended_engine, recommended_settings, confidence_score, reason, valid_until)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (cache_key, engine, json.dumps(settings), confidence, reason, valid_until))
        
        conn.commit()
        conn.close()

# Initialize global optimizer
quality_optimizer = QualityOptimizer()
