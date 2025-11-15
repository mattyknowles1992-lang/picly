"""
Rating System & Learning AI Foundation
Tracks user ratings to improve prompt quality over time
"""

import sqlite3
from datetime import datetime
from collections import defaultdict

class RatingSystem:
    def __init__(self, db_path='ratings.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Create rating tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Image ratings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS image_ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER,
                image_url TEXT,
                prompt TEXT,
                negative_prompt TEXT,
                engine TEXT,
                style TEXT,
                rating INTEGER CHECK(rating >= 1 AND rating <= 5),
                feedback TEXT,
                dimensions TEXT,
                quality_boost BOOLEAN
            )
        ''')
        
        # Video ratings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS video_ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER,
                video_url TEXT,
                image_url TEXT,
                prompt TEXT,
                engine TEXT,
                duration INTEGER,
                rating INTEGER CHECK(rating >= 1 AND rating <= 5),
                feedback TEXT
            )
        ''')
        
        # Prompt analytics (learning data)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prompt_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt_keywords TEXT,
                style TEXT,
                engine TEXT,
                avg_rating REAL,
                total_ratings INTEGER,
                success_rate REAL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # User preferences (for personalized recommendations)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id INTEGER PRIMARY KEY,
                favorite_styles TEXT,
                favorite_engines TEXT,
                avg_rating_given REAL,
                total_generations INTEGER,
                high_rated_prompts TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def rate_image(self, user_id, image_url, prompt, engine, rating, feedback='', **kwargs):
        """Record image rating"""
        if not 1 <= rating <= 5:
            return {'success': False, 'error': 'Rating must be 1-5 stars'}
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO image_ratings 
            (user_id, image_url, prompt, negative_prompt, engine, style, rating, feedback, dimensions, quality_boost)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            image_url,
            prompt,
            kwargs.get('negative_prompt', ''),
            engine,
            kwargs.get('style', ''),
            rating,
            feedback,
            kwargs.get('dimensions', ''),
            kwargs.get('quality_boost', True)
        ))
        
        conn.commit()
        conn.close()
        
        # Update analytics in background
        self._update_prompt_analytics(prompt, engine, rating)
        self._update_user_preferences(user_id, rating, prompt, kwargs.get('style', ''), engine)
        
        return {'success': True, 'message': 'Rating recorded'}
    
    def rate_video(self, user_id, video_url, image_url, prompt, engine, duration, rating, feedback=''):
        """Record video rating"""
        if not 1 <= rating <= 5:
            return {'success': False, 'error': 'Rating must be 1-5 stars'}
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO video_ratings 
            (user_id, video_url, image_url, prompt, engine, duration, rating, feedback)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, video_url, image_url, prompt, engine, duration, rating, feedback))
        
        conn.commit()
        conn.close()
        
        return {'success': True, 'message': 'Video rating recorded'}
    
    def _update_prompt_analytics(self, prompt, engine, rating):
        """Update prompt performance analytics"""
        # Extract keywords (simple version - can enhance with NLP later)
        keywords = ' '.join(sorted(set(prompt.lower().split())))[:200]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if analytics exist
        cursor.execute('''
            SELECT avg_rating, total_ratings 
            FROM prompt_analytics 
            WHERE prompt_keywords = ? AND engine = ?
        ''', (keywords, engine))
        
        result = cursor.fetchone()
        
        if result:
            avg_rating, total_ratings = result
            new_total = total_ratings + 1
            new_avg = ((avg_rating * total_ratings) + rating) / new_total
            
            cursor.execute('''
                UPDATE prompt_analytics 
                SET avg_rating = ?, total_ratings = ?, last_updated = CURRENT_TIMESTAMP
                WHERE prompt_keywords = ? AND engine = ?
            ''', (new_avg, new_total, keywords, engine))
        else:
            cursor.execute('''
                INSERT INTO prompt_analytics (prompt_keywords, engine, avg_rating, total_ratings, success_rate)
                VALUES (?, ?, ?, 1, 1.0)
            ''', (keywords, engine, rating))
        
        conn.commit()
        conn.close()
    
    def _update_user_preferences(self, user_id, rating, prompt, style, engine):
        """Update user preferences for personalized recommendations"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get existing preferences
        cursor.execute('SELECT * FROM user_preferences WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        if result:
            # Update existing
            cursor.execute('''
                UPDATE user_preferences 
                SET total_generations = total_generations + 1,
                    last_updated = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (user_id,))
        else:
            # Create new
            cursor.execute('''
                INSERT INTO user_preferences (user_id, total_generations)
                VALUES (?, 1)
            ''', (user_id,))
        
        conn.commit()
        conn.close()
    
    def get_top_prompts(self, engine=None, min_ratings=5, limit=20):
        """Get highest-rated prompts for learning"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if engine:
            cursor.execute('''
                SELECT prompt_keywords, engine, avg_rating, total_ratings
                FROM prompt_analytics
                WHERE engine = ? AND total_ratings >= ?
                ORDER BY avg_rating DESC, total_ratings DESC
                LIMIT ?
            ''', (engine, min_ratings, limit))
        else:
            cursor.execute('''
                SELECT prompt_keywords, engine, avg_rating, total_ratings
                FROM prompt_analytics
                WHERE total_ratings >= ?
                ORDER BY avg_rating DESC, total_ratings DESC
                LIMIT ?
            ''', (min_ratings, limit))
        
        results = cursor.fetchall()
        conn.close()
        
        return [{
            'keywords': row[0],
            'engine': row[1],
            'avg_rating': row[2],
            'total_ratings': row[3]
        } for row in results]
    
    def get_user_stats(self, user_id):
        """Get user rating statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Image stats
        cursor.execute('''
            SELECT COUNT(*), AVG(rating), MIN(rating), MAX(rating)
            FROM image_ratings
            WHERE user_id = ?
        ''', (user_id,))
        image_stats = cursor.fetchone()
        
        # Video stats
        cursor.execute('''
            SELECT COUNT(*), AVG(rating)
            FROM video_ratings
            WHERE user_id = ?
        ''', (user_id,))
        video_stats = cursor.fetchone()
        
        # Recent high-rated prompts
        cursor.execute('''
            SELECT prompt, rating, engine, timestamp
            FROM image_ratings
            WHERE user_id = ? AND rating >= 4
            ORDER BY timestamp DESC
            LIMIT 10
        ''', (user_id,))
        top_prompts = cursor.fetchall()
        
        conn.close()
        
        return {
            'images': {
                'total': image_stats[0] or 0,
                'avg_rating': round(image_stats[1], 2) if image_stats[1] else 0,
                'min_rating': image_stats[2] or 0,
                'max_rating': image_stats[3] or 0
            },
            'videos': {
                'total': video_stats[0] or 0,
                'avg_rating': round(video_stats[1], 2) if video_stats[1] else 0
            },
            'top_prompts': [{
                'prompt': row[0],
                'rating': row[1],
                'engine': row[2],
                'timestamp': row[3]
            } for row in top_prompts]
        }
    
    def suggest_improvements(self, prompt, engine):
        """Suggest prompt improvements based on learned data"""
        # Get top-performing similar prompts
        top_prompts = self.get_top_prompts(engine=engine, min_ratings=3, limit=10)
        
        suggestions = []
        
        # Simple keyword analysis (can enhance with AI later)
        prompt_words = set(prompt.lower().split())
        
        for top in top_prompts:
            top_words = set(top['keywords'].split())
            common_words = prompt_words & top_words
            
            if len(common_words) >= 2:  # At least 2 words in common
                unique_words = top_words - prompt_words
                if unique_words:
                    suggestions.append({
                        'add_keywords': list(unique_words)[:5],
                        'avg_rating': top['avg_rating'],
                        'confidence': len(common_words) / max(len(prompt_words), 1)
                    })
        
        return suggestions[:3]  # Top 3 suggestions
    
    def get_analytics_report(self):
        """Generate analytics report"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Overall stats
        cursor.execute('SELECT COUNT(*), AVG(rating) FROM image_ratings')
        total_images, avg_image_rating = cursor.fetchone()
        
        cursor.execute('SELECT COUNT(*), AVG(rating) FROM video_ratings')
        total_videos, avg_video_rating = cursor.fetchone()
        
        # Engine performance
        cursor.execute('''
            SELECT engine, AVG(rating), COUNT(*)
            FROM image_ratings
            GROUP BY engine
            ORDER BY AVG(rating) DESC
        ''')
        engine_stats = cursor.fetchall()
        
        conn.close()
        
        return {
            'total_ratings': (total_images or 0) + (total_videos or 0),
            'images': {
                'total': total_images or 0,
                'avg_rating': round(avg_image_rating, 2) if avg_image_rating else 0
            },
            'videos': {
                'total': total_videos or 0,
                'avg_rating': round(avg_video_rating, 2) if avg_video_rating else 0
            },
            'engine_performance': [{
                'engine': row[0],
                'avg_rating': round(row[1], 2),
                'total_ratings': row[2]
            } for row in engine_stats]
        }


# Global instance
rating_system = RatingSystem()
