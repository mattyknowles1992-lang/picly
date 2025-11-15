# 🤖 Autonomous Learning Engine Documentation

## Overview

The **Autonomous Learning Engine** is a groundbreaking system that continuously harvests open-source data from across the internet to automatically improve Picly's AI image generation quality, prompt suggestions, and overall capabilities—without any manual intervention.

## How It Works

### Continuous Data Harvesting

The system runs in the background 24/7, automatically collecting high-quality prompts and image data from multiple sources:

#### Data Sources

1. **Civitai** (https://civitai.com)
   - Largest community AI art platform
   - 100,000+ high-quality prompts with engagement metrics
   - Professional metadata (model settings, CFG scale, steps)
   - Reaction counts and comment data for quality scoring

2. **Lexica.art** (https://lexica.art)
   - Stable Diffusion prompt database
   - Curated high-quality examples
   - Like counts and popularity metrics
   - Searchable by style and quality

3. **Reddit** (r/StableDiffusion, r/midjourney, etc.)
   - Trending prompts from active communities
   - Upvote data for popularity tracking
   - Real-world usage patterns
   - Community-validated quality

4. **GitHub** (Awesome Stable Diffusion)
   - Curated prompt collections
   - Expert-created templates
   - Best practices and techniques

5. **HuggingFace Datasets**
   - ML-ready prompt datasets
   - Professional annotations
   - Academic quality standards

### Intelligent Analysis

#### Pattern Recognition

The system analyzes harvested data to discover:

- **Structural Patterns**: Common prompt templates that work
  - `{subject}, {quality_terms}, {lighting}, {style}`
  - `{subject} by {artist}, {technical_specs}`
  - `{composition_type}, {subject}, {atmosphere}`

- **Quality Modifiers**: Terms that improve results
  - "highly detailed", "4k", "8k", "masterpiece"
  - "professional photography", "studio lighting"
  - "sharp focus", "ultra detailed", "best quality"

- **Style Keywords**: Successful artistic directions
  - "cinematic", "photorealistic", "oil painting"
  - "concept art", "digital art", "watercolor"
  - "bokeh", "depth of field", "golden hour"

- **Category-Specific Optimizations**: What works for each type
  - Portraits: DALL-E 3 with soft lighting
  - Landscapes: Midjourney with wide angles
  - Products: Flux with studio lighting

#### Statistical Learning

The engine tracks:

- **Correlation Scores**: How strongly each term correlates with high engagement
- **Frequency Analysis**: Which patterns appear most often in successful prompts
- **Co-occurrence Patterns**: Which terms work well together
- **Trending Analysis**: What's gaining popularity (velocity tracking)
- **Effectiveness Metrics**: Which suggestions actually improve user results

### Knowledge Database

The system builds 7 specialized tables:

#### 1. Harvested Prompts
```sql
- prompt_text: The actual prompt
- prompt_hash: Unique identifier
- source: Where it came from (Civitai, Lexica, etc.)
- quality_indicators: Engagement, reactions, votes
- engagement_score: Combined quality metric
- metadata: Technical settings used
- learned_patterns: Analysis results
```

#### 2. Prompt Patterns
```sql
- pattern_type: Category (quality, lighting, style, composition)
- pattern_template: Reusable structure
- effectiveness_score: How well it works
- usage_count: Popularity
- success_rate: % of high-quality results
- example_prompts: Real examples
```

#### 3. Quality Indicators
```sql
- indicator_type: What kind (quality_modifier, style, etc.)
- indicator_value: The actual term
- correlation_score: Strength of quality correlation
- occurrence_count: How often seen
- avg_quality_when_present: Average result quality with term
- avg_quality_when_absent: Average quality without
- statistical_significance: Confidence level
```

#### 4. Style Library
```sql
- style_name: Name of the style
- style_keywords: Trigger words
- best_engines: Which AI works best
- avg_quality: Historical performance
- sample_count: Number of examples
- example_images: Reference URLs
```

#### 5. Negative Prompt Library
```sql
- negative_prompt: What to avoid
- category: Type of issue it fixes
- effectiveness_score: How much it helps
- usage_count: Popularity
- improves_quality_by: Quantified improvement
```

#### 6. Concept Relationships
```sql
- concept_a & concept_b: Related terms
- relationship_type: How they relate (enhances, contrasts, etc.)
- strength: Correlation strength
- co_occurrence_count: Times seen together
- avg_quality: Quality when used together
```

#### 7. Trending Patterns
```sql
- pattern_text: The trending pattern
- trend_score: Current popularity
- velocity: Rate of growth
- peak_date: When it peaked
- source_count: How many sources
- first_seen & last_seen: Timeframe
```

## API Endpoints

### Prompt Enhancement

**POST /api/learning/enhance-prompt**

Get AI-powered suggestions to improve any prompt based on learned patterns.

```javascript
// Request
{
  "prompt": "a cat sitting on a chair"
}

// Response
{
  "success": true,
  "original_prompt": "a cat sitting on a chair",
  "enhanced_prompt": "a cat sitting on a chair, highly detailed, professional photography, studio lighting, sharp focus",
  "suggestions": {
    "quality_modifiers": [
      {"term": "highly detailed", "impact": 0.87},
      {"term": "professional photography", "impact": 0.82},
      {"term": "studio lighting", "impact": 0.79}
    ],
    "style_suggestions": [
      {"style": "photorealistic", "quality": 4.7, "popularity": 1243},
      {"style": "cinematic", "quality": 4.6, "popularity": 987}
    ],
    "trending_additions": [
      {"pattern": "soft natural light", "trend_score": 245.5}
    ],
    "negative_prompt": "blurry, low quality, pixelated, distorted"
  },
  "improvements": {
    "quality_boost": 3,
    "style_options": 2,
    "trending_applied": true
  }
}
```

### Learning Statistics

**GET /api/learning/stats**

Get overall learning progress and statistics.

```javascript
// Response
{
  "success": true,
  "stats": {
    "total_prompts_harvested": 15847,
    "patterns_discovered": 342,
    "quality_indicators": 87,
    "styles_learned": 56,
    "active_trends": 23,
    "sessions_last_week": 168,
    "items_processed_week": 12500,
    "patterns_found_week": 145
  },
  "status": "active"
}
```

### Trending Patterns

**GET /api/learning/trending**

Get currently trending prompt patterns.

```javascript
// Response
{
  "success": true,
  "trends": [
    {
      "pattern": "golden hour lighting",
      "trend_score": 487.3,
      "sources": 23,
      "last_seen": "2025-11-15 10:30:00"
    },
    {
      "pattern": "cinematic composition",
      "trend_score": 412.8,
      "sources": 19,
      "last_seen": "2025-11-15 10:25:00"
    }
  ],
  "count": 20
}
```

### Quality Insights

**GET /api/learning/quality-insights**

Get insights about what makes prompts high-quality.

```javascript
// Response
{
  "success": true,
  "quality_modifiers": [
    {
      "term": "highly detailed",
      "correlation": 0.89,
      "frequency": 1543
    },
    {
      "term": "8k",
      "correlation": 0.85,
      "frequency": 1287
    }
  ],
  "popular_styles": [
    {
      "style": "photorealistic",
      "avg_quality": 4.7,
      "samples": 2341
    },
    {
      "style": "cinematic",
      "avg_quality": 4.6,
      "samples": 1987
    }
  ]
}
```

### Learning Control

**POST /api/learning/control**

Start or stop the autonomous learning engine.

```javascript
// Request - Start
{
  "action": "start"
}

// Request - Stop
{
  "action": "stop"
}

// Response
{
  "success": true,
  "message": "Autonomous learning started",
  "status": "active"
}
```

## Frontend Integration

### Prompt Enhancement Button

```javascript
async function enhancePrompt(userPrompt) {
    const response = await fetch('/api/learning/enhance-prompt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: userPrompt })
    });
    
    const data = await response.json();
    
    if (data.success) {
        // Show enhanced version
        promptInput.value = data.enhanced_prompt;
        
        // Show suggestion chips
        showSuggestions(data.suggestions);
    }
}
```

### Auto-Apply Trending Patterns

```javascript
async function applyTrendingPatterns() {
    const response = await fetch('/api/learning/trending');
    const data = await response.json();
    
    if (data.success && data.trends.length > 0) {
        // Get top trend
        const topTrend = data.trends[0];
        
        // Show as suggestion
        showSuggestionBadge(topTrend.pattern, topTrend.trend_score);
    }
}
```

### Display Quality Tips

```javascript
async function showQualityTips() {
    const response = await fetch('/api/learning/quality-insights');
    const data = await response.json();
    
    if (data.success) {
        // Show quality modifier suggestions
        const tipHTML = data.quality_modifiers
            .slice(0, 5)
            .map(mod => `
                <span class="quality-tip" data-term="${mod.term}">
                    ${mod.term} (${(mod.correlation * 100).toFixed(0)}% improvement)
                </span>
            `)
            .join('');
        
        document.getElementById('quality-tips').innerHTML = tipHTML;
    }
}
```

## Configuration

### Harvest Frequency

```python
# In autonomous_learner.py
self.harvest_interval = 3600  # 1 hour (default)

# Change to harvest more/less frequently:
self.harvest_interval = 1800   # 30 minutes
self.harvest_interval = 7200   # 2 hours
```

### Rate Limiting

```python
# Maximum prompts to harvest per day
self.max_daily_harvests = 10000  # Default

# Prevent API rate limits
```

### Quality Threshold

```python
# Only learn from high-quality examples
self.min_quality_threshold = 4.0  # 4+ star ratings only

# Lower to learn from more data:
self.min_quality_threshold = 3.5
```

## Dashboard Access

Visit the learning dashboard at:

```
http://localhost:5000/learning
```

Or in production:

```
https://yourdomain.com/learning
```

### Dashboard Features

- **Real-time Statistics**: Live updates every 30 seconds
- **Trending Patterns**: Currently popular prompt patterns
- **Quality Indicators**: Terms that improve results
- **Popular Styles**: Successfully learned artistic styles
- **Learning Control**: Start/stop/pause the engine
- **Visual Analytics**: Engagement scores, trend graphs

## Benefits

### 1. Continuous Improvement

- System gets smarter every day automatically
- No manual prompt engineering needed
- Learns from millions of successful examples
- Adapts to changing AI trends

### 2. Competitive Intelligence

- Automatically discovers what competitors' users are creating
- Learns successful patterns from across platforms
- Stays current with latest AI art trends
- Identifies emerging styles early

### 3. User Experience

- Better prompt suggestions out-of-the-box
- Higher first-try success rates
- Reduced regenerations needed
- More professional results

### 4. Cost Optimization

- Reduces wasted generations
- Learns which engines work best for each type
- Optimizes quality-per-dollar ratios
- Prevents expensive trial-and-error

### 5. Data-Driven Decisions

- Quantified effectiveness of every pattern
- Statistical validation of quality improvements
- Trend forecasting capabilities
- Evidence-based recommendations

## Advanced Features

### Pattern Templates

The system creates reusable templates:

```
Portrait Template:
"{subject}, professional photography, soft lighting, bokeh background, 85mm lens, f/1.8, golden hour, highly detailed, 8k"

Landscape Template:
"{location}, cinematic wide angle, dramatic lighting, volumetric fog, 4k, highly detailed, {weather}, {time_of_day}"

Product Template:
"{product}, commercial photography, studio lighting, white background, professional quality, sharp focus, product photography"
```

### Smart Categorization

Automatically detects prompt intent:

- **Portraits**: Face, person, character → Suggests soft lighting, bokeh
- **Landscapes**: Nature, scenery, mountains → Suggests wide angle, dramatic
- **Products**: Commercial, advertisement → Suggests studio lighting, clean
- **Artistic**: Abstract, painting → Suggests artistic styles, techniques

### Negative Prompt Generation

Automatically suggests what to avoid:

```python
# For photorealistic portraits
negative_prompt = "cartoon, anime, illustration, low quality, blurry, deformed, distorted face"

# For landscapes
negative_prompt = "people, text, watermark, low quality, oversaturated"

# Learned from thousands of examples
```

### Relationship Mapping

Discovers which concepts work together:

```
"golden hour" + "portrait" = 4.8★ average
"studio lighting" + "product" = 4.7★ average
"cinematic" + "wide angle" = 4.6★ average
```

## Monitoring & Maintenance

### Health Checks

```python
# Check learning status
stats = autonomous_learner.get_learning_stats()

if stats['total_prompts_harvested'] < 1000:
    print("⚠️ Low harvest count - check data sources")

if stats['patterns_discovered'] == 0:
    print("⚠️ No patterns found - check analysis logic")
```

### Database Maintenance

```python
# Clean old data (optional)
conn = sqlite3.connect('learning.db')
cursor = conn.cursor()

# Remove harvests older than 90 days
cursor.execute('''
    DELETE FROM harvested_prompts
    WHERE harvested_at < datetime('now', '-90 days')
    AND learned_patterns IS NOT NULL
''')

conn.commit()
conn.close()
```

### Performance Optimization

```python
# Add indexes for faster queries
cursor.execute('CREATE INDEX IF NOT EXISTS idx_engagement ON harvested_prompts(engagement_score DESC)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_trend_score ON trending_patterns(trend_score DESC)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_correlation ON quality_indicators(correlation_score DESC)')
```

## Privacy & Ethics

### What We Collect

- **Public data only**: All sources are publicly accessible
- **No personal info**: Only prompts and engagement metrics
- **No user tracking**: Harvests aggregate community data
- **Attribution preserved**: Source URLs maintained

### What We Don't Do

- ❌ Scrape private/paid platforms
- ❌ Collect user personal data
- ❌ Violate terms of service
- ❌ Redistribute copyrighted content

### Compliance

- Respects robots.txt
- Implements rate limiting
- Uses public APIs when available
- Provides attribution to sources

## Future Enhancements

### Planned Features

1. **Natural Language Processing**: Better pattern extraction
2. **Image Analysis**: Learn from image characteristics
3. **User Feedback Loop**: Learn from Picly users' ratings
4. **A/B Testing**: Automatically test pattern effectiveness
5. **Personalization**: Learn individual user preferences
6. **Multi-Language**: Support non-English prompts
7. **Video Prompts**: Extend to video generation
8. **Style Transfer**: Learn artistic style transfers

### Experimental Features

- **GPT-4 Integration**: Use LLMs for pattern discovery
- **Diffusion Model Analysis**: Reverse-engineer what works
- **Embedding Similarity**: Find semantically similar prompts
- **Reinforcement Learning**: Optimize through trial-and-error

## Troubleshooting

### Learning Engine Not Starting

```python
# Check if already running
if autonomous_learner.learning_active:
    print("Already running")

# Manually start
autonomous_learner.start_autonomous_learning()
```

### No Data Being Harvested

```python
# Test data sources manually
count = autonomous_learner.harvest_civitai_data()
print(f"Harvested {count} from Civitai")

# Check network connectivity
# Check API rate limits
# Verify data source URLs
```

### Database Errors

```python
# Reinitialize database
autonomous_learner.init_database()

# Check permissions
# Verify disk space
# Check SQLite version
```

## Support & Documentation

- **Dashboard**: http://localhost:5000/learning
- **API Docs**: This file
- **Source Code**: `autonomous_learner.py`
- **Database Schema**: See "Knowledge Database" section above

---

**Built with ❤️ for Picly AI**

*Continuously learning, always improving.*
