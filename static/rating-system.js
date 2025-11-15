/**
 * Advanced Rating & Analytics System - Frontend Component
 * State-of-the-art user feedback collection with ML-ready data
 */

class RatingSystem {
    constructor() {
        this.sessionId = this.generateSessionId();
        this.generationStartTime = {};
    }

    generateSessionId() {
        return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Show rating modal for a generated image
     */
    showRatingModal(generationId, imageUrl) {
        const modal = document.createElement('div');
        modal.className = 'rating-modal';
        modal.innerHTML = `
            <div class="rating-modal-content">
                <div class="rating-modal-header">
                    <h3>Rate This Generation</h3>
                    <button class="close-btn" onclick="this.closest('.rating-modal').remove()">&times;</button>
                </div>
                
                <div class="rating-preview">
                    <img src="${imageUrl}" alt="Generated Image">
                </div>
                
                <div class="rating-stars">
                    <label>How would you rate this result?</label>
                    <div class="stars">
                        ${[1,2,3,4,5].map(star => `
                            <span class="star" data-rating="${star}">★</span>
                        `).join('')}
                    </div>
                    <p class="rating-text"></p>
                </div>
                
                <div class="rating-quality">
                    <label>Quality Score (Optional)</label>
                    <input type="range" min="0" max="100" value="50" class="quality-slider">
                    <span class="quality-value">50/100</span>
                </div>
                
                <div class="rating-tags">
                    <label>What worked well? (Select all that apply)</label>
                    <div class="tag-grid">
                        <button class="tag-btn" data-tag="composition">Composition</button>
                        <button class="tag-btn" data-tag="colors">Colors</button>
                        <button class="tag-btn" data-tag="details">Details</button>
                        <button class="tag-btn" data-tag="lighting">Lighting</button>
                        <button class="tag-btn" data-tag="accuracy">Prompt Accuracy</button>
                        <button class="tag-btn" data-tag="style">Style</button>
                        <button class="tag-btn" data-tag="realism">Realism</button>
                        <button class="tag-btn" data-tag="creative">Creative</button>
                    </div>
                </div>
                
                <div class="rating-feedback">
                    <label>Additional Feedback (Optional)</label>
                    <textarea placeholder="Tell us what you think..."></textarea>
                </div>
                
                <div class="rating-actions">
                    <button class="skip-btn" onclick="this.closest('.rating-modal').remove()">Skip</button>
                    <button class="submit-btn" onclick="ratingSystem.submitRating('${generationId}')">Submit Rating</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        this.initializeRatingInteractions();
        this.generationStartTime[generationId] = Date.now();
    }

    initializeRatingInteractions() {
        // Star rating
        const stars = document.querySelectorAll('.rating-modal .star');
        const ratingText = document.querySelector('.rating-modal .rating-text');
        const ratingDescriptions = {
            1: 'Poor - Not usable',
            2: 'Fair - Needs improvement',
            3: 'Good - Acceptable',
            4: 'Great - Impressive!',
            5: 'Excellent - Perfect!'
        };

        stars.forEach(star => {
            star.addEventListener('click', function() {
                const rating = this.dataset.rating;
                stars.forEach((s, i) => {
                    s.classList.toggle('active', i < rating);
                });
                ratingText.textContent = ratingDescriptions[rating];
            });

            star.addEventListener('mouseenter', function() {
                const rating = this.dataset.rating;
                stars.forEach((s, i) => {
                    s.classList.toggle('hover', i < rating);
                });
            });

            star.addEventListener('mouseleave', function() {
                stars.forEach(s => s.classList.remove('hover'));
            });
        });

        // Quality slider
        const slider = document.querySelector('.rating-modal .quality-slider');
        const qualityValue = document.querySelector('.rating-modal .quality-value');
        slider.addEventListener('input', function() {
            qualityValue.textContent = `${this.value}/100`;
        });

        // Tags
        const tagBtns = document.querySelectorAll('.rating-modal .tag-btn');
        tagBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                this.classList.toggle('active');
            });
        });
    }

    async submitRating(generationId) {
        const modal = document.querySelector('.rating-modal');
        const activeStar = modal.querySelector('.star.active:last-of-type');
        
        if (!activeStar) {
            alert('Please select a star rating');
            return;
        }

        const rating = parseInt(activeStar.dataset.rating);
        const qualityScore = parseInt(modal.querySelector('.quality-slider').value);
        const feedback = modal.querySelector('textarea').value;
        const tags = Array.from(modal.querySelectorAll('.tag-btn.active'))
            .map(btn => btn.dataset.tag);

        const timeToRate = Date.now() - (this.generationStartTime[generationId] || Date.now());

        try {
            const response = await fetch('/api/analytics/rate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    generation_id: generationId,
                    rating: rating,
                    quality_score: qualityScore,
                    feedback: feedback,
                    tags: tags,
                    time_to_rate: Math.floor(timeToRate / 1000)
                })
            });

            const data = await response.json();
            
            if (data.success) {
                modal.remove();
                this.showThankYou(rating);
            } else {
                alert('Error submitting rating: ' + data.error);
            }
        } catch (error) {
            console.error('Rating submission error:', error);
            alert('Failed to submit rating');
        }
    }

    showThankYou(rating) {
        const toast = document.createElement('div');
        toast.className = 'rating-toast';
        toast.innerHTML = `
            <div class="toast-content">
                <span class="toast-icon">✨</span>
                <span>Thank you for your ${rating}-star rating!</span>
            </div>
        `;
        document.body.appendChild(toast);
        
        setTimeout(() => toast.classList.add('show'), 100);
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    /**
     * Track generation action (download, share, edit, etc.)
     */
    async trackAction(generationId, action) {
        try {
            await fetch('/api/analytics/action', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    generation_id: generationId,
                    action: action
                })
            });
        } catch (error) {
            console.error('Action tracking error:', error);
        }
    }

    /**
     * Track user behavior for UX analytics
     */
    async trackBehavior(action, details = null, interactionTime = 0) {
        try {
            await fetch('/api/analytics/behavior', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    session_id: this.sessionId,
                    action: action,
                    details: details,
                    page: window.location.pathname,
                    device: {
                        type: this.getDeviceType(),
                        browser: navigator.userAgent,
                        screen: `${window.screen.width}x${window.screen.height}`
                    },
                    time: interactionTime
                })
            });
        } catch (error) {
            console.error('Behavior tracking error:', error);
        }
    }

    getDeviceType() {
        const width = window.innerWidth;
        if (width < 768) return 'mobile';
        if (width < 1024) return 'tablet';
        return 'desktop';
    }

    /**
     * Get AI-powered prompt suggestions based on top performers
     */
    async getPromptSuggestions(engine = 'flux-pro', limit = 5) {
        try {
            const response = await fetch(`/api/analytics/prompt-suggestions?engine=${engine}&limit=${limit}`);
            const data = await response.json();
            return data.suggestions || [];
        } catch (error) {
            console.error('Error getting suggestions:', error);
            return [];
        }
    }

    /**
     * Get optimal engine recommendation for a prompt
     */
    async getOptimalEngine(prompt) {
        try {
            const response = await fetch('/api/optimizer/recommend', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ prompt })
            });
            const data = await response.json();
            return data.recommendation || null;
        } catch (error) {
            console.error('Error getting recommendation:', error);
            return null;
        }
    }

    /**
     * Get engine performance comparison
     */
    async getEngineComparison() {
        try {
            const response = await fetch('/api/optimizer/engine-comparison');
            const data = await response.json();
            return data.engines || [];
        } catch (error) {
            console.error('Error getting comparison:', error);
            return [];
        }
    }

    /**
     * Get top-rated prompts for inspiration
     */
    async getTopPrompts(engine = null, minRatings = 5, limit = 50) {
        try {
            let url = `/api/analytics/top-prompts?min_ratings=${minRatings}&limit=${limit}`;
            if (engine) url += `&engine=${engine}`;
            
            const response = await fetch(url);
            const data = await response.json();
            return data.prompts || [];
        } catch (error) {
            console.error('Error getting top prompts:', error);
            return [];
        }
    }

    /**
     * Show AI recommendation badge on prompt input
     */
    async showPromptRecommendation(promptInput) {
        const prompt = promptInput.value.trim();
        if (prompt.length < 10) return;

        const recommendation = await this.getOptimalEngine(prompt);
        if (!recommendation) return;

        // Create or update recommendation badge
        let badge = document.querySelector('.ai-recommendation-badge');
        if (!badge) {
            badge = document.createElement('div');
            badge.className = 'ai-recommendation-badge';
            promptInput.parentElement.appendChild(badge);
        }

        const confidence = Math.round(recommendation.confidence * 100);
        badge.innerHTML = `
            <span class="badge-icon">🤖</span>
            <span class="badge-text">
                <strong>AI Suggests:</strong> ${recommendation.engine} 
                (${confidence}% confidence)
            </span>
            <span class="badge-reason">${recommendation.reason}</span>
        `;
        badge.style.display = 'flex';
    }
}

// Initialize global rating system
const ratingSystem = new RatingSystem();

// Track page load
document.addEventListener('DOMContentLoaded', () => {
    ratingSystem.trackBehavior('page_load');
});

// Track page unload (time spent)
let pageLoadTime = Date.now();
window.addEventListener('beforeunload', () => {
    const timeSpent = Math.floor((Date.now() - pageLoadTime) / 1000);
    ratingSystem.trackBehavior('page_unload', {time_spent: timeSpent}, timeSpent);
});
