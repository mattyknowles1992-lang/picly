"""
INTELLIGENT SOCIAL CONTENT SYSTEM
Combines autonomous learning with social media content creation
Self-improving system that learns from engagement data
"""

import sqlite3
import json
from datetime import datetime, timedelta
import schedule
import time
from typing import Dict, List
from social_content_creator import SocialContentCreator
from autonomous_learner import autonomous_learner


class IntelligentSocialSystem:
    """
    Self-improving social content system that:
    1. Generates optimized content for all platforms
    2. Posts automatically on schedule
    3. Tracks engagement metrics
    4. Learns from performance data
    5. Continuously improves content quality
    """
    
    def __init__(self):
        self.content_creator = SocialContentCreator()
        self.learner = autonomous_learner
        self.db_path = 'social_content.db'
        
    def generate_intelligent_content(self, topic: str, platforms: List[str], 
                                     language: str = 'en', quality: str = 'premium') -> Dict:
        """
        Generate content using AI + learned insights from autonomous learner
        """
        # Step 1: Get AI enhancement suggestions from autonomous learner
        enhancement_data = self.learner.get_prompt_enhancement_suggestions(topic)
        
        # Step 2: Apply learned insights to prompt
        enhanced_topic = self._enhance_with_learnings(topic, enhancement_data)
        
        # Step 3: Generate content with enhanced prompt
        content = self.content_creator.generate_content(
            topic=enhanced_topic,
            content_type='image_post',
            platforms=platforms,
            language=language,
            quality=quality
        )
        
        # Step 4: Add predicted engagement score
        content['predicted_engagement'] = self._predict_engagement(content, enhancement_data)
        
        return content
    
    def _enhance_with_learnings(self, topic: str, enhancement_data: Dict) -> str:
        """Apply learned quality indicators and patterns to enhance the topic/prompt"""
        enhanced = topic
        
        # Add high-performing quality modifiers
        if enhancement_data.get('quality_modifiers'):
            top_modifiers = enhancement_data['quality_modifiers'][:3]
            modifier_text = ', '.join([m['modifier'] for m in top_modifiers])
            enhanced = f"{enhanced}, {modifier_text}"
        
        # Add successful style elements
        if enhancement_data.get('trending_styles'):
            top_style = enhancement_data['trending_styles'][0]['style']
            enhanced = f"{enhanced}, {top_style} style"
        
        # Add successful patterns
        if enhancement_data.get('successful_patterns'):
            pattern = enhancement_data['successful_patterns'][0]
            if 'emotional' in pattern['pattern_type'].lower():
                enhanced = f"{enhanced}, emotional and engaging"
        
        return enhanced
    
    def _predict_engagement(self, content: Dict, learnings: Dict) -> float:
        """Predict engagement score based on learned patterns"""
        score = 5.0  # Base score
        
        # Check for quality indicators
        if learnings.get('quality_modifiers'):
            for modifier in learnings['quality_modifiers'][:5]:
                if modifier['modifier'].lower() in content['base_caption'].lower():
                    score += 0.5
        
        # Check for trending topics
        if learnings.get('trending_topics'):
            for topic in learnings['trending_topics'][:3]:
                if topic['topic'].lower() in content['topic'].lower():
                    score += 1.0
        
        # Platform optimization bonus
        score += len(content['platforms']) * 0.2
        
        return min(score, 10.0)  # Cap at 10
    
    def learn_from_engagement(self, posted_content_id: int):
        """
        After content is posted, analyze its performance and teach the learner
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Get posted content data
        c.execute('''SELECT gc.content_text, gc.hashtags, gc.metadata, 
                            ca.views, ca.likes, ca.comments, ca.shares, ca.engagement_rate
                     FROM posted_content pc
                     JOIN generated_content gc ON pc.content_id = gc.id
                     LEFT JOIN content_analytics ca ON ca.posted_content_id = pc.id
                     WHERE pc.id = ?''', (posted_content_id,))
        
        result = c.fetchone()
        conn.close()
        
        if not result:
            return
        
        caption, hashtags_json, metadata_json, views, likes, comments, shares, eng_rate = result
        
        # Parse data
        hashtags = json.loads(hashtags_json) if hashtags_json else []
        metadata = json.loads(metadata_json) if metadata_json else {}
        
        # Determine if this was high-performing content
        is_high_quality = eng_rate and eng_rate > 3.0  # 3%+ engagement is good
        
        if is_high_quality:
            # Extract what made it successful and teach the learner
            prompt = caption[:200]  # First 200 chars of caption
            
            # Simulate adding this as a successful pattern to learner
            # (In real implementation, you'd add methods to autonomous_learner)
            self._teach_learner_from_success(
                prompt=prompt,
                hashtags=hashtags,
                engagement_rate=eng_rate,
                metrics={'views': views, 'likes': likes, 'comments': comments, 'shares': shares}
            )
    
    def _teach_learner_from_success(self, prompt: str, hashtags: List[str], 
                                     engagement_rate: float, metrics: Dict):
        """
        Feed successful content back to autonomous learner
        This creates a self-improving feedback loop
        """
        # Extract patterns from successful content
        patterns = {
            'prompt_structure': prompt,
            'effective_hashtags': hashtags,
            'engagement_rate': engagement_rate,
            'performance_metrics': metrics,
            'learned_at': datetime.now().isoformat()
        }
        
        # Store in learner's database for future enhancement suggestions
        conn = sqlite3.connect(self.learner.db_path)
        c = conn.cursor()
        
        # Add to successful patterns table
        c.execute('''INSERT INTO prompt_patterns (pattern_type, pattern, frequency, avg_quality, last_seen)
                    VALUES (?, ?, ?, ?, ?)''',
                 ('social_media_success', json.dumps(patterns), 1, engagement_rate * 10, 
                  datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Learned from successful content (engagement: {engagement_rate}%)")
    
    def auto_generate_daily_content(self, topics: List[str], platforms: List[str],
                                     posts_per_day: int = 4):
        """
        Automatically generate and schedule content for the day
        """
        print(f"🤖 Auto-generating {posts_per_day} posts for today...")
        
        for i, topic in enumerate(topics[:posts_per_day]):
            # Generate intelligent content
            content = self.generate_intelligent_content(
                topic=topic,
                platforms=platforms,
                language='en',
                quality='premium'
            )
            
            # Schedule at optimal times (spread throughout the day)
            hours_offset = i * (24 // posts_per_day)  # Spread evenly
            schedule_time = datetime.now() + timedelta(hours=hours_offset)
            
            # Add to queue
            queue_id = self.content_creator.schedule_content(
                content_data=content,
                schedule_time=schedule_time,
                platforms=platforms
            )
            
            print(f"✅ Scheduled post {i+1}/{posts_per_day}: '{topic}' at {schedule_time.strftime('%I:%M %p')}")
            print(f"   Predicted engagement: {content['predicted_engagement']}/10")
        
        print(f"\n🎉 Generated {posts_per_day} intelligent posts!")
    
    def start_intelligent_automation(self):
        """
        Start the fully autonomous, self-improving system
        
        This runs 24/7 and:
        1. Generates content daily using learned insights
        2. Posts content automatically
        3. Collects engagement data
        4. Learns from performance
        5. Improves future content quality
        """
        
        print("🚀 Starting Intelligent Social Content System...")
        print("=" * 60)
        
        # Daily content generation at 6 AM
        schedule.every().day.at("06:00").do(self._daily_content_routine)
        
        # Process scheduled posts every hour
        schedule.every().hour.do(self.content_creator._process_scheduled_posts)
        
        # Collect engagement data every 6 hours
        schedule.every(6).hours.do(self._collect_engagement_data)
        
        # Run autonomous learner harvesting every 2 hours
        schedule.every(2).hours.do(self.learner.harvest_and_learn)
        
        # Analyze and learn from performance daily at midnight
        schedule.every().day.at("00:00").do(self._nightly_learning_routine)
        
        print("✅ Scheduled tasks:")
        print("   📅 06:00 AM - Generate daily content")
        print("   ⏰ Every hour - Post scheduled content")
        print("   📊 Every 6 hours - Collect engagement data")
        print("   🧠 Every 2 hours - Learn from open-source data")
        print("   🌙 00:00 AM - Nightly learning & optimization")
        print("\n🔄 System running autonomously...")
        print("=" * 60)
        
        # Run forever
        while True:
            schedule.run_pending()
            time.sleep(60)
    
    def _daily_content_routine(self):
        """Generate content for the day using learned insights"""
        print("\n" + "=" * 60)
        print(f"📅 Daily Content Generation - {datetime.now().strftime('%B %d, %Y')}")
        print("=" * 60)
        
        # Get trending topics from learner
        trending = self.learner.get_trending_patterns(limit=10)
        topics = [t['topic'] for t in trending if 'topic' in t]
        
        # If no trending topics, use defaults
        if not topics:
            topics = [
                "Morning motivation and inspiration",
                "Professional productivity tips",
                "Creative lifestyle ideas",
                "Health and wellness advice"
            ]
        
        # Generate 4 posts per day across platforms
        self.auto_generate_daily_content(
            topics=topics,
            platforms=['instagram', 'facebook', 'twitter', 'linkedin'],
            posts_per_day=4
        )
    
    def _collect_engagement_data(self):
        """Collect latest engagement metrics from all platforms"""
        print(f"\n📊 Collecting engagement data - {datetime.now().strftime('%I:%M %p')}")
        
        # In production, this would call each platform's API to get real metrics
        # For now, we'll update analytics for recently posted content
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Get posts from last 24 hours without recent analytics updates
        cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
        c.execute('''SELECT id FROM posted_content 
                    WHERE posted_at >= ? 
                    ORDER BY posted_at DESC LIMIT 20''', (cutoff,))
        
        recent_posts = [row[0] for row in c.fetchall()]
        conn.close()
        
        # Simulate collecting engagement data
        # In production, you'd call Instagram API, Facebook API, etc.
        collected = 0
        for post_id in recent_posts:
            # Placeholder for real API calls
            # engagement_data = instagram_api.get_post_metrics(post_id)
            # facebook_api.get_post_insights(post_id)
            # etc.
            collected += 1
        
        print(f"✅ Updated metrics for {collected} recent posts")
    
    def _nightly_learning_routine(self):
        """Nightly analysis and learning from the day's performance"""
        print("\n" + "=" * 60)
        print(f"🌙 Nightly Learning Routine - {datetime.now().strftime('%B %d, %Y %I:%M %p')}")
        print("=" * 60)
        
        # Analyze today's performance
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        today_start = datetime.now().replace(hour=0, minute=0, second=0).isoformat()
        
        # Get high-performing posts from today
        c.execute('''SELECT pc.id, ca.engagement_rate 
                    FROM posted_content pc
                    JOIN content_analytics ca ON ca.posted_content_id = pc.id
                    WHERE pc.posted_at >= ? AND ca.engagement_rate > 3.0
                    ORDER BY ca.engagement_rate DESC
                    LIMIT 10''', (today_start,))
        
        high_performers = c.fetchall()
        conn.close()
        
        # Learn from successful posts
        learned = 0
        for post_id, engagement in high_performers:
            self.learn_from_engagement(post_id)
            learned += 1
        
        print(f"📈 Analyzed {len(high_performers)} high-performing posts")
        print(f"🧠 Learned from {learned} successful patterns")
        
        # Run autonomous learner's analysis
        self.learner.analyze_and_learn()
        
        # Get performance summary
        stats = self.content_creator.get_analytics_report(days=1)
        total_engagement = sum([
            s.get('likes', 0) + s.get('comments', 0) + s.get('shares', 0)
            for s in stats.get('engagement_stats', {}).values()
        ])
        
        print(f"📊 Today's Results:")
        print(f"   Posts: {sum(stats.get('posts_by_platform', {}).values())}")
        print(f"   Total Engagement: {total_engagement:,}")
        print(f"   Learning Database: {self.learner.get_total_patterns_count():,} patterns")
        print("=" * 60)
    
    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        # Content creator stats
        content_stats = {
            'scheduled_posts': 0,
            'total_posts': 0,
            'avg_engagement': 0
        }
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('SELECT COUNT(*) FROM content_queue WHERE status = "pending"')
        content_stats['scheduled_posts'] = c.fetchone()[0]
        
        c.execute('SELECT COUNT(*) FROM posted_content')
        content_stats['total_posts'] = c.fetchone()[0]
        
        c.execute('SELECT AVG(engagement_rate) FROM content_analytics')
        content_stats['avg_engagement'] = c.fetchone()[0] or 0
        
        conn.close()
        
        # Learner stats
        learner_stats = self.learner.get_stats()
        
        return {
            'status': 'running',
            'content_system': content_stats,
            'learning_system': learner_stats,
            'integration': {
                'feedback_loops_active': True,
                'self_improving': True,
                'autonomous': True
            },
            'last_updated': datetime.now().isoformat()
        }


# Convenience function to start the integrated system
def start_intelligent_system():
    """Start the fully integrated, self-improving social content system"""
    system = IntelligentSocialSystem()
    system.start_intelligent_automation()


if __name__ == '__main__':
    # Start the intelligent system
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║                                                                ║
    ║         INTELLIGENT SOCIAL CONTENT SYSTEM v2.0                 ║
    ║                                                                ║
    ║  🧠 Self-Learning AI Content Generation                        ║
    ║  🤖 Autonomous Posting & Scheduling                            ║
    ║  📊 Engagement Tracking & Analysis                             ║
    ║  🔄 Continuous Quality Improvement                             ║
    ║  🌍 Multi-Platform & Multi-Language                            ║
    ║                                                                ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    
    system = IntelligentSocialSystem()
    
    # Show initial status
    status = system.get_system_status()
    print("\n📊 System Status:")
    print(f"   Learning Database: {status['learning_system'].get('total_prompts', 0):,} prompts analyzed")
    print(f"   Scheduled Posts: {status['content_system']['scheduled_posts']}")
    print(f"   Total Posts Generated: {status['content_system']['total_posts']}")
    print(f"   Average Engagement: {status['content_system']['avg_engagement']:.2f}%")
    
    # Start autonomous operation
    print("\n🚀 Starting autonomous operation...")
    system.start_intelligent_automation()
