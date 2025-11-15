"""
Autonomous Learning Engine for Picly
Continuously harvests open-source data to improve AI quality and capabilities
"""

import sqlite3
import json
import requests
from datetime import datetime, timedelta
import hashlib
import threading
import time
from collections import defaultdict
import re

class AutonomousLearner:
    def __init__(self, db_path='learning.db'):
        self.db_path = db_path
        self.init_database()
        self.learning_active = False
        
        # Open-source data sources
        self.data_sources = {
            'civitai': 'https://civitai.com/api/v1/images',
            'lexica': 'https://lexica.art/api/v1/search',
            'reddit_prompts': 'https://www.reddit.com/r/StableDiffusion/top.json',
            'github_awesome': 'https://api.github.com/repos/awesome-stable-diffusion/awesome-stable-diffusion/contents/prompts',
            'huggingface_datasets': 'https://datasets-server.huggingface.co/search'
        }
        
        # Learning parameters
        self.min_quality_threshold = 4.0  # Only learn from high-quality examples
        self.harvest_interval = 3600  # 1 hour
        self.max_daily_harvests = 10000  # Rate limit
    
    def init_database(self):
        """Create tables for continuous learning"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Harvested prompts from open-source
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS harvested_prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt_text TEXT NOT NULL,
                prompt_hash TEXT UNIQUE NOT NULL,
                source TEXT NOT NULL,
                source_url TEXT,
                quality_indicators TEXT,
                upvotes INTEGER DEFAULT 0,
                engagement_score REAL DEFAULT 0,
                image_url TEXT,
                metadata TEXT,
                learned_patterns TEXT,
                harvested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Pattern library - learned structures
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prompt_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT NOT NULL,
                pattern_template TEXT NOT NULL,
                category TEXT,
                effectiveness_score REAL DEFAULT 0,
                usage_count INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0,
                example_prompts TEXT,
                keywords TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Quality indicators - what makes prompts work
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quality_indicators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                indicator_type TEXT NOT NULL,
                indicator_value TEXT NOT NULL,
                category TEXT,
                correlation_score REAL DEFAULT 0,
                occurrence_count INTEGER DEFAULT 0,
                avg_quality_when_present REAL DEFAULT 0,
                avg_quality_when_absent REAL DEFAULT 0,
                statistical_significance REAL DEFAULT 0
            )
        ''')
        
        # Style library - successful artistic directions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS style_library (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                style_name TEXT UNIQUE NOT NULL,
                style_keywords TEXT NOT NULL,
                style_modifiers TEXT,
                best_engines TEXT,
                avg_quality REAL DEFAULT 0,
                sample_count INTEGER DEFAULT 0,
                example_images TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Negative prompt library
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS negative_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                negative_prompt TEXT NOT NULL,
                category TEXT,
                effectiveness_score REAL DEFAULT 0,
                usage_count INTEGER DEFAULT 0,
                improves_quality_by REAL DEFAULT 0
            )
        ''')
        
        # Knowledge graph - relationships between concepts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS concept_relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                concept_a TEXT NOT NULL,
                concept_b TEXT NOT NULL,
                relationship_type TEXT NOT NULL,
                strength REAL DEFAULT 0,
                co_occurrence_count INTEGER DEFAULT 0,
                avg_quality REAL DEFAULT 0,
                UNIQUE(concept_a, concept_b, relationship_type)
            )
        ''')
        
        # Trending patterns - what's working now
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trending_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_text TEXT NOT NULL,
                trend_score REAL DEFAULT 0,
                velocity REAL DEFAULT 0,
                peak_date DATE,
                category TEXT,
                source_count INTEGER DEFAULT 0,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Learning sessions log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_type TEXT NOT NULL,
                items_processed INTEGER DEFAULT 0,
                patterns_discovered INTEGER DEFAULT 0,
                quality_improvement REAL DEFAULT 0,
                duration_seconds INTEGER DEFAULT 0,
                status TEXT DEFAULT 'completed',
                error_message TEXT,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        ''')
        
        # Initialize common patterns
        self.init_base_patterns(cursor)
        
        conn.commit()
        conn.close()
    
    def init_base_patterns(self, cursor):
        """Initialize foundational prompt patterns"""
        base_patterns = [
            {
                'type': 'quality_modifiers',
                'template': '{subject}, {quality_terms}',
                'category': 'enhancement',
                'keywords': json.dumps(['highly detailed', '4k', '8k', 'professional', 'masterpiece'])
            },
            {
                'type': 'lighting',
                'template': '{subject}, {lighting_type}',
                'category': 'lighting',
                'keywords': json.dumps(['golden hour', 'studio lighting', 'dramatic lighting', 'soft light'])
            },
            {
                'type': 'style',
                'template': '{subject}, in the style of {artist/style}',
                'category': 'artistic',
                'keywords': json.dumps(['cinematic', 'photorealistic', 'oil painting', 'digital art'])
            },
            {
                'type': 'composition',
                'template': '{subject}, {composition_type}',
                'category': 'composition',
                'keywords': json.dumps(['rule of thirds', 'centered', 'wide angle', 'close-up'])
            }
        ]
        
        for pattern in base_patterns:
            cursor.execute('''
                INSERT OR IGNORE INTO prompt_patterns 
                (pattern_type, pattern_template, category, keywords)
                VALUES (?, ?, ?, ?)
            ''', (pattern['type'], pattern['template'], pattern['category'], pattern['keywords']))
    
    def start_autonomous_learning(self):
        """Start background learning thread"""
        if self.learning_active:
            return
        
        self.learning_active = True
        learning_thread = threading.Thread(target=self._learning_loop, daemon=True)
        learning_thread.start()
        print("🤖 Autonomous learning engine started")
    
    def stop_autonomous_learning(self):
        """Stop background learning"""
        self.learning_active = False
        print("🤖 Autonomous learning engine stopped")
    
    def _learning_loop(self):
        """Main learning loop - runs continuously"""
        while self.learning_active:
            try:
                session_id = self._log_session_start('autonomous_harvest')
                
                # Harvest from multiple sources
                total_harvested = 0
                total_harvested += self.harvest_civitai_data()
                time.sleep(5)  # Rate limiting
                total_harvested += self.harvest_lexica_data()
                time.sleep(5)
                total_harvested += self.harvest_reddit_data()
                
                # Analyze and learn patterns
                patterns_found = self.analyze_and_learn()
                
                # Update trending patterns
                self.update_trending_patterns()
                
                # Log session completion
                self._log_session_complete(session_id, total_harvested, patterns_found)
                
                # Sleep until next harvest
                time.sleep(self.harvest_interval)
                
            except Exception as e:
                print(f"Learning error: {e}")
                time.sleep(300)  # Wait 5 minutes on error
    
    def harvest_civitai_data(self):
        """Harvest high-quality prompts from Civitai"""
        try:
            # Civitai has public API with thousands of high-quality images and prompts
            response = requests.get(
                f"{self.data_sources['civitai']}",
                params={'limit': 100, 'sort': 'Most Reactions', 'nsfw': False},
                timeout=10
            )
            
            if response.status_code != 200:
                return 0
            
            data = response.json()
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            count = 0
            
            for item in data.get('items', []):
                if 'meta' in item and 'prompt' in item['meta']:
                    prompt = item['meta']['prompt']
                    prompt_hash = self._hash_text(prompt)
                    
                    quality_indicators = {
                        'reactions': item.get('stats', {}).get('reactions', 0),
                        'comments': item.get('stats', {}).get('comments', 0),
                        'model': item['meta'].get('Model'),
                        'cfg_scale': item['meta'].get('cfgScale'),
                        'steps': item['meta'].get('steps')
                    }
                    
                    engagement = (
                        item.get('stats', {}).get('reactions', 0) * 2 +
                        item.get('stats', {}).get('comments', 0)
                    )
                    
                    cursor.execute('''
                        INSERT OR IGNORE INTO harvested_prompts
                        (prompt_text, prompt_hash, source, source_url, quality_indicators,
                         upvotes, engagement_score, image_url, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (prompt, prompt_hash, 'civitai', item.get('url'),
                          json.dumps(quality_indicators), 
                          item.get('stats', {}).get('reactions', 0),
                          engagement, item.get('url'), json.dumps(item['meta'])))
                    
                    count += 1
            
            conn.commit()
            conn.close()
            print(f"📥 Harvested {count} prompts from Civitai")
            return count
            
        except Exception as e:
            print(f"Civitai harvest error: {e}")
            return 0
    
    def harvest_lexica_data(self):
        """Harvest from Lexica.art prompt library"""
        try:
            response = requests.get(
                f"{self.data_sources['lexica']}",
                params={'q': 'high quality', 'limit': 100},
                timeout=10
            )
            
            if response.status_code != 200:
                return 0
            
            data = response.json()
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            count = 0
            
            for item in data.get('images', []):
                prompt = item.get('prompt', '')
                if not prompt:
                    continue
                
                prompt_hash = self._hash_text(prompt)
                
                cursor.execute('''
                    INSERT OR IGNORE INTO harvested_prompts
                    (prompt_text, prompt_hash, source, source_url, image_url,
                     upvotes, engagement_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (prompt, prompt_hash, 'lexica', item.get('id'),
                      item.get('src'), item.get('likes', 0), item.get('likes', 0)))
                
                count += 1
            
            conn.commit()
            conn.close()
            print(f"📥 Harvested {count} prompts from Lexica")
            return count
            
        except Exception as e:
            print(f"Lexica harvest error: {e}")
            return 0
    
    def harvest_reddit_data(self):
        """Harvest trending prompts from Reddit"""
        try:
            headers = {'User-Agent': 'Picly Learning Bot 1.0'}
            response = requests.get(
                self.data_sources['reddit_prompts'],
                headers=headers,
                params={'limit': 50, 't': 'week'},
                timeout=10
            )
            
            if response.status_code != 200:
                return 0
            
            data = response.json()
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            count = 0
            
            for post in data.get('data', {}).get('children', []):
                post_data = post.get('data', {})
                title = post_data.get('title', '')
                selftext = post_data.get('selftext', '')
                
                # Extract prompts from title and text
                prompts = self._extract_prompts_from_text(title + ' ' + selftext)
                
                for prompt in prompts:
                    if len(prompt) < 20:  # Skip very short prompts
                        continue
                    
                    prompt_hash = self._hash_text(prompt)
                    upvotes = post_data.get('ups', 0)
                    
                    cursor.execute('''
                        INSERT OR IGNORE INTO harvested_prompts
                        (prompt_text, prompt_hash, source, source_url, upvotes, engagement_score)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (prompt, prompt_hash, 'reddit', 
                          f"https://reddit.com{post_data.get('permalink', '')}", 
                          upvotes, upvotes))
                    
                    count += 1
            
            conn.commit()
            conn.close()
            print(f"📥 Harvested {count} prompts from Reddit")
            return count
            
        except Exception as e:
            print(f"Reddit harvest error: {e}")
            return 0
    
    def analyze_and_learn(self):
        """Analyze harvested data and extract learnings"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        patterns_found = 0
        
        # Get high-engagement prompts for analysis
        cursor.execute('''
            SELECT prompt_text, engagement_score, metadata
            FROM harvested_prompts
            WHERE engagement_score > 10
            AND learned_patterns IS NULL
            ORDER BY engagement_score DESC
            LIMIT 1000
        ''')
        
        prompts = cursor.fetchall()
        
        # Extract common patterns
        patterns = defaultdict(int)
        quality_words = defaultdict(int)
        style_words = defaultdict(int)
        
        for prompt_text, score, metadata in prompts:
            # Extract quality modifiers
            quality_terms = ['4k', '8k', 'hd', 'highly detailed', 'professional',
                           'masterpiece', 'best quality', 'ultra detailed', 'sharp focus']
            for term in quality_terms:
                if term in prompt_text.lower():
                    quality_words[term] += 1
            
            # Extract style terms
            style_terms = ['cinematic', 'photorealistic', 'oil painting', 'watercolor',
                          'digital art', 'concept art', 'studio lighting', 'dramatic',
                          'vibrant', 'muted colors', 'bokeh', 'depth of field']
            for term in style_terms:
                if term in prompt_text.lower():
                    style_words[term] += 1
            
            # Extract structural patterns (X by Y, X in the style of Y, etc.)
            if ' by ' in prompt_text:
                patterns['artist_attribution'] += 1
            if 'in the style of' in prompt_text.lower():
                patterns['style_reference'] += 1
            if re.search(r'\d+mm', prompt_text):
                patterns['camera_specs'] += 1
        
        # Store discovered quality indicators
        for word, count in quality_words.items():
            if count > 10:  # Statistically significant
                cursor.execute('''
                    INSERT OR REPLACE INTO quality_indicators
                    (indicator_type, indicator_value, occurrence_count, correlation_score)
                    VALUES (?, ?, ?, ?)
                ''', ('quality_modifier', word, count, count / len(prompts)))
                patterns_found += 1
        
        # Store style patterns
        for style, count in style_words.items():
            if count > 5:
                cursor.execute('''
                    INSERT OR REPLACE INTO style_library
                    (style_name, style_keywords, sample_count)
                    VALUES (?, ?, ?)
                    ON CONFLICT(style_name) DO UPDATE SET
                        sample_count = sample_count + ?
                ''', (style, json.dumps([style]), count, count))
                patterns_found += 1
        
        # Mark prompts as learned
        cursor.execute('''
            UPDATE harvested_prompts
            SET learned_patterns = 'analyzed'
            WHERE learned_patterns IS NULL
            AND engagement_score > 10
        ''')
        
        conn.commit()
        conn.close()
        
        print(f"🧠 Discovered {patterns_found} new patterns")
        return patterns_found
    
    def update_trending_patterns(self):
        """Identify and update trending patterns"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Find patterns appearing frequently in recent harvests
        cursor.execute('''
            SELECT prompt_text, COUNT(*) as frequency, AVG(engagement_score) as avg_engagement
            FROM harvested_prompts
            WHERE harvested_at >= datetime('now', '-7 days')
            GROUP BY prompt_text
            HAVING COUNT(*) > 3
            ORDER BY frequency DESC, avg_engagement DESC
            LIMIT 100
        ''')
        
        trending = cursor.fetchall()
        
        for prompt, frequency, avg_engagement in trending:
            # Extract key phrases (simplified - could use NLP)
            words = prompt.lower().split()
            for i in range(len(words) - 2):
                phrase = ' '.join(words[i:i+3])
                
                cursor.execute('''
                    INSERT OR REPLACE INTO trending_patterns
                    (pattern_text, trend_score, source_count, last_seen)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ''', (phrase, frequency * avg_engagement, frequency))
        
        conn.commit()
        conn.close()
    
    def get_prompt_enhancement_suggestions(self, user_prompt):
        """Suggest enhancements based on learned patterns"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        suggestions = {
            'quality_modifiers': [],
            'style_suggestions': [],
            'trending_additions': [],
            'negative_prompt': ''
        }
        
        # Get top quality modifiers not in prompt
        cursor.execute('''
            SELECT indicator_value, correlation_score
            FROM quality_indicators
            WHERE indicator_type = 'quality_modifier'
            AND occurrence_count > 20
            ORDER BY correlation_score DESC
            LIMIT 5
        ''')
        
        for modifier, score in cursor.fetchall():
            if modifier.lower() not in user_prompt.lower():
                suggestions['quality_modifiers'].append({
                    'term': modifier,
                    'impact': score
                })
        
        # Get relevant styles
        cursor.execute('''
            SELECT style_name, avg_quality, sample_count
            FROM style_library
            WHERE sample_count > 10
            ORDER BY avg_quality DESC, sample_count DESC
            LIMIT 5
        ''')
        
        for style, quality, count in cursor.fetchall():
            if style.lower() not in user_prompt.lower():
                suggestions['style_suggestions'].append({
                    'style': style,
                    'quality': quality,
                    'popularity': count
                })
        
        # Get trending patterns
        cursor.execute('''
            SELECT pattern_text, trend_score
            FROM trending_patterns
            WHERE last_seen >= datetime('now', '-3 days')
            ORDER BY trend_score DESC
            LIMIT 3
        ''')
        
        for pattern, score in cursor.fetchall():
            suggestions['trending_additions'].append({
                'pattern': pattern,
                'trend_score': score
            })
        
        # Get best negative prompt
        cursor.execute('''
            SELECT negative_prompt, effectiveness_score
            FROM negative_patterns
            WHERE effectiveness_score > 0.5
            ORDER BY effectiveness_score DESC
            LIMIT 1
        ''')
        
        result = cursor.fetchone()
        if result:
            suggestions['negative_prompt'] = result[0]
        
        conn.close()
        return suggestions
    
    def get_learning_stats(self):
        """Get statistics about learning progress"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Total harvested prompts
        cursor.execute('SELECT COUNT(*) FROM harvested_prompts')
        stats['total_prompts_harvested'] = cursor.fetchone()[0]
        
        # Patterns discovered
        cursor.execute('SELECT COUNT(*) FROM prompt_patterns')
        stats['patterns_discovered'] = cursor.fetchone()[0]
        
        # Quality indicators
        cursor.execute('SELECT COUNT(*) FROM quality_indicators')
        stats['quality_indicators'] = cursor.fetchone()[0]
        
        # Styles in library
        cursor.execute('SELECT COUNT(*) FROM style_library')
        stats['styles_learned'] = cursor.fetchone()[0]
        
        # Recent sessions
        cursor.execute('''
            SELECT COUNT(*), SUM(items_processed), SUM(patterns_discovered)
            FROM learning_sessions
            WHERE started_at >= datetime('now', '-7 days')
        ''')
        session_data = cursor.fetchone()
        stats['sessions_last_week'] = session_data[0] or 0
        stats['items_processed_week'] = session_data[1] or 0
        stats['patterns_found_week'] = session_data[2] or 0
        
        # Trending patterns
        cursor.execute('''
            SELECT COUNT(*) FROM trending_patterns
            WHERE last_seen >= datetime('now', '-3 days')
        ''')
        stats['active_trends'] = cursor.fetchone()[0]
        
        conn.close()
        return stats
    
    def _extract_prompts_from_text(self, text):
        """Extract potential prompts from text using heuristics"""
        prompts = []
        
        # Look for quoted text
        quoted = re.findall(r'"([^"]+)"', text)
        prompts.extend(quoted)
        
        # Look for "Prompt:" prefix
        prompt_prefix = re.findall(r'[Pp]rompt:\s*(.+?)(?:\n|$)', text)
        prompts.extend(prompt_prefix)
        
        return [p.strip() for p in prompts if len(p) > 20]
    
    def _hash_text(self, text):
        """Create hash of text"""
        return hashlib.sha256(text.encode()).hexdigest()
    
    def _log_session_start(self, session_type):
        """Log start of learning session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO learning_sessions (session_type, status)
            VALUES (?, 'running')
        ''', (session_type,))
        
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return session_id
    
    def _log_session_complete(self, session_id, items, patterns):
        """Log completion of learning session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE learning_sessions
            SET items_processed = ?,
                patterns_discovered = ?,
                status = 'completed',
                completed_at = CURRENT_TIMESTAMP,
                duration_seconds = (julianday(CURRENT_TIMESTAMP) - julianday(started_at)) * 86400
            WHERE id = ?
        ''', (items, patterns, session_id))
        
        conn.commit()
        conn.close()
    
    def get_stats(self):
        """Get comprehensive learning statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total prompts harvested
        cursor.execute('SELECT COUNT(*) FROM harvested_prompts')
        total_prompts = cursor.fetchone()[0]
        
        # Total patterns discovered
        cursor.execute('SELECT COUNT(*) FROM prompt_patterns')
        total_patterns = cursor.fetchone()[0]
        
        # Quality indicators
        cursor.execute('SELECT COUNT(*) FROM quality_indicators')
        quality_indicators = cursor.fetchone()[0]
        
        # Trending patterns (last 7 days)
        cursor.execute('''SELECT COUNT(*) FROM trending_patterns 
                         WHERE last_seen >= datetime('now', '-7 days')''')
        trending = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_prompts': total_prompts,
            'total_patterns': total_patterns,
            'quality_indicators': quality_indicators,
            'trending_patterns': trending,
            'learning_active': self.learning_active
        }
    
    def get_total_patterns_count(self):
        """Get total number of patterns in learning database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM prompt_patterns')
        count = cursor.fetchone()[0]
        conn.close()
        return count

# Initialize global learner
autonomous_learner = AutonomousLearner()
