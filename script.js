// ============================================
// AUTHENTICATION SYSTEM FOR PICLY
// ============================================

// Check authentication on page load
async function checkAuth() {
    try {
        const response = await fetch('/api/auth/validate', {
            method: 'GET',
            credentials: 'include'
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.authenticated) {
                // User is logged in - show credits, hide auth buttons
                document.getElementById('authButtons').style.display = 'none';
                document.getElementById('creditDisplay').style.display = 'flex';
                // Update credit display with user data
                await updateCredits();
            } else {
                // Not logged in - show auth buttons, hide credits
                document.getElementById('authButtons').style.display = 'flex';
                document.getElementById('creditDisplay').style.display = 'none';
            }
        } else {
            // Not logged in - show auth buttons
            document.getElementById('authButtons').style.display = 'flex';
            document.getElementById('creditDisplay').style.display = 'none';
        }
    } catch (error) {
        // Error or not logged in - show auth buttons
        document.getElementById('authButtons').style.display = 'flex';
        document.getElementById('creditDisplay').style.display = 'none';
    }
    
    // Always show main content and nav
    document.getElementById('mainContent').style.display = 'block';
    document.getElementById('navLinks').style.display = 'flex';
}

// Login Modal Handlers
document.addEventListener('DOMContentLoaded', () => {
    // Initialize all DOM elements first
    initializeDOMElements();
    
    checkAuth();
    
    // Initialize page after elements are loaded
    init();
    
    const loginBtn = document.getElementById('loginBtn');
    const registerBtn = document.getElementById('registerBtn');
    const registerBtnNav = document.getElementById('registerBtnNav');
    const logoutBtn = document.getElementById('logoutBtn');
    const loginModal = document.getElementById('loginModal');
    const registerModal = document.getElementById('registerModal');
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const showRegister = document.getElementById('showRegister');
    const showLogin = document.getElementById('showLogin');
    
    // Show modals
    if (loginBtn) {
        loginBtn.addEventListener('click', () => {
            loginModal.classList.add('show');
        });
    }
    
    if (registerBtn) {
        registerBtn.addEventListener('click', () => {
            registerModal.classList.add('show');
        });
    }
    
    if (registerBtnNav) {
        registerBtnNav.addEventListener('click', () => {
            registerModal.classList.add('show');
        });
    }
    
    // Switch between login and register
    if (showRegister) {
        showRegister.addEventListener('click', () => {
            loginModal.classList.remove('show');
            registerModal.classList.add('show');
        });
    }
    
    if (showLogin) {
        showLogin.addEventListener('click', () => {
            registerModal.classList.remove('show');
            loginModal.classList.add('show');
        });
    }
    
    // Close modals
    const closeButtons = document.querySelectorAll('.auth-close');
    closeButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.target.closest('.auth-modal').classList.remove('show');
        });
    });
    
    // Handle login
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const username = document.getElementById('loginUsername').value.trim();
            const password = document.getElementById('loginPassword').value;
            
            // Validate inputs
            if (!username || username.length === 0) {
                showNotification('Please enter your username or email', 'error');
                return;
            }
            
            if (!password || password.length === 0) {
                showNotification('Please enter your password', 'error');
                return;
            }
            
            try {
                const response = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({ username, password })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    loginModal.classList.remove('show');
                    checkAuth();
                    showNotification('Welcome back, ' + data.username + '!');
                } else {
                    showNotification(data.error || 'Login failed');
                }
            } catch (error) {
                showNotification('Login error: ' + error.message);
            }
        });
    }
    
    // Handle registration
    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const username = document.getElementById('regUsername').value.trim();
            const email = document.getElementById('regEmail').value.trim();
            const password = document.getElementById('regPassword').value;
            
            // Validate all fields are filled
            if (!username || username.length === 0) {
                showNotification('Please enter a username', 'error');
                return;
            }
            
            if (!email || email.length === 0) {
                showNotification('Please enter an email address', 'error');
                return;
            }
            
            // Validate email format
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(email)) {
                showNotification('Please enter a valid email address', 'error');
                return;
            }
            
            if (!password || password.length === 0) {
                showNotification('Please enter a password', 'error');
                return;
            }
            
            if (password.length < 8) {
                showNotification('Password must be at least 8 characters long', 'error');
                return;
            }
            
            try {
                const response = await fetch('/api/auth/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, email, password })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    registerModal.classList.remove('show');
                    loginModal.classList.add('show');
                    showNotification('Account created! Please sign in.');
                } else {
                    showNotification(data.error || 'Registration failed');
                }
            } catch (error) {
                showNotification('Registration error: ' + error.message);
            }
        });
    }
    
    // Handle logout
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async () => {
            try {
                await fetch('/api/auth/logout', {
                    method: 'POST',
                    credentials: 'include'
                });
                
                // Show auth buttons, hide credits
                document.getElementById('authButtons').style.display = 'flex';
                document.getElementById('creditDisplay').style.display = 'none';
                
                showNotification('Logged out successfully');
                
                // Reload page to reset state
                setTimeout(() => location.reload(), 1000);
            } catch (error) {
                showNotification('Logout error: ' + error.message, 'error');
            }
        });
    }
});

// Function to update credit display
async function updateCredits() {
    try {
        const response = await fetch('/api/credits/balance', {
            method: 'GET',
            credentials: 'include'
        });
        
        if (response.ok) {
            const data = await response.json();
            const creditCountElement = document.getElementById('creditCount');
            if (creditCountElement) {
                const totalCredits = (data.free_credits || 0) + (data.premium_credits || 0);
                creditCountElement.textContent = totalCredits;
            }
        }
    } catch (error) {
        console.error('Error fetching credits:', error);
    }
}

// ============================================
// PROMPT LIBRARY AND IMAGE GENERATION
// ============================================

// Professional Prompt Library Database - Industry-Leading Prompts (2025)
const promptLibrary = [
    // Portrait Category
    {
        id: 1,
        category: 'portrait',
        title: 'Cinematic Portrait',
        prompt: 'Portrait of a distinguished individual, Hasselblad H6D-400c camera, 85mm f/1.2 Zeiss lens, dramatic Rembrandt lighting with rim light, golden hour ambiance, bokeh depth of field, film grain texture, warm color grading with teal shadows, professional retouching, National Geographic style, hyperrealistic skin detail, 8K RAW, award-winning portrait photography',
        description: 'Museum-quality portrait with Hollywood-level lighting and detail'
    },
    {
        id: 2,
        category: 'portrait',
        title: 'Fantasy Character',
        prompt: 'Epic fantasy warrior portrait, ornate damascus steel armor with gold filigree, ethereal magical aura particles, dynamic heroic pose, volumetric god rays, fantasy matte painting style, octane render quality, subsurface scattering on skin, intricate fabric and metal textures, atmospheric depth, trending on ArtStation, concept art by Greg Rutkowski and Ruan Jia, cinematic composition, 8K unreal engine render',
        description: 'AAA game-quality fantasy character with photorealistic details'
    },
    {
        id: 3,
        category: 'portrait',
        title: 'Professional Headshot',
        prompt: 'Executive corporate headshot, confident professional in tailored business attire, softbox lighting setup with catch lights, neutral grey seamless background, sharp focus on eyes, perfect skin retouching, commercial photography grade, LinkedIn premium quality, shot with Canon EOS R5 + RF 85mm f/1.2L, professional color science, 50 megapixel resolution',
        description: 'C-suite executive quality headshot for professional branding'
    },
    
    // Landscape Category
    {
        id: 4,
        category: 'landscape',
        title: 'Epic Mountain Vista',
        prompt: 'Majestic alpine mountain range at dawn, jagged snow-capped peaks piercing dramatic crepuscular rays, layered atmospheric perspective with misty valleys, volumetric cloud formations, golden hour alpenglow on granite faces, shot with Phase One IQ4 150MP, ultra-wide 14mm lens, focus stacking for infinite depth of field, National Geographic cover quality, Peter Lik photography style, HDR landscape photography, hyperrealistic textures, 16K resolution',
        description: 'Award-winning landscape with cinematic atmospheric depth'
    },
    {
        id: 5,
        category: 'landscape',
        title: 'Serene Beach Sunset',
        prompt: 'Pristine tropical beach at magic hour sunset, silhouetted coconut palms swaying, mirror-like wet sand reflections, graduated sunset colors from amber to deep magenta, gentle foam-tipped waves with motion blur, long exposure seascape technique, foreground interest with tide pool, professional landscape photography by Michael Kenna style, HDR bracketing, polarizing filter effect, velvia color palette, ultra-sharp 8K',
        description: 'Professional seascape with perfect composition and color'
    },
    {
        id: 6,
        category: 'landscape',
        title: 'Mystical Forest',
        prompt: 'Ancient primeval forest with towering redwoods, volumetric god rays penetrating morning mist, bioluminescent mushrooms on moss-covered ground, fairy tale enchanted atmosphere, depth-rich composition with layers, fantasy matte painting quality, Unreal Engine 5 Lumen lighting, subsurface scattering on foliage, photogrammetry quality bark textures, ethereal color grading, cinematic framing, 8K photorealistic render',
        description: 'Cinematic fantasy forest with volumetric lighting effects'
    },
    
    // Fantasy Category
    {
        id: 7,
        category: 'fantasy',
        title: 'Dragon in Sky',
        prompt: 'Colossal elder dragon with iridescent scales soaring through cumulonimbus storm clouds, lightning arcing between wings, hyper-detailed scale patterns with subsurface scattering, volumetric atmospheric fog, dramatic chiaroscuro lighting, cinematic wide-angle hero shot, motion blur on wing edges, epic fantasy concept art by Donato Giancola, matte painting quality, octane render with ray tracing, particle effects, photorealistic creature design, trending on ArtStation front page, 8K Unreal Engine 5',
        description: 'AAA cinematic dragon with Hollywood VFX quality'
    },
    {
        id: 8,
        category: 'fantasy',
        title: 'Magical Castle',
        prompt: 'Impossible floating citadel suspended in nebula clouds, crystalline spires with bioluminescent runes, aurora borealis dancing around gothic towers, waterfalls cascading into void below, surreal architecture blending Escher and Art Nouveau, magical energy particles, tilt-shift perspective, fantasy matte painting masterpiece, James Gurney color theory, atmospheric perspective with depth layers, glowing windows with warm interior light, ethereal dreamscape, digital painting by Raphael Lacoste, 8K concept art',
        description: 'Dreamlike floating fortress with magical atmosphere'
    },
    {
        id: 9,
        category: 'fantasy',
        title: 'Cyberpunk City',
        prompt: 'Neo-Tokyo megacity at night, towering arcology structures with holographic kanji advertisements, neon-lit rain-slicked streets with puddle reflections, flying vehicles with light trails, dense atmospheric fog with volumetric light shafts, Blade Runner 2049 cinematography, cyberpunk street level perspective, intricate architectural greebling, wet asphalt specular highlights, moody color grading with teal and orange, matte painting by Simon Stalenhag, photorealistic rendering, 8K cinematic quality',
        description: 'Blade Runner-quality cyberpunk with atmospheric depth'
    },
    
    // Architecture Category
    {
        id: 10,
        category: 'architecture',
        title: 'Modern Luxury Home',
        prompt: 'Ultra-modern minimalist villa with cantilevered design, floor-to-ceiling structural glazing with minimal frames, infinity edge pool reflecting golden hour sky, concrete and blackened steel materiality, landscaped with Japanese zen garden, architectural photography with tilt-shift lens, perfect symmetry and leading lines, shot during blue hour with interior lights on, professional real estate photography style, Archdaily featured quality, Corona renderer realism, 8K archviz',
        description: 'Architectural Digest-worthy modern home with perfect composition'
    },
    {
        id: 11,
        category: 'architecture',
        title: 'Gothic Cathedral',
        prompt: 'Notre-Dame inspired Gothic cathedral interior, kaleidoscope of stained glass rose windows casting colorful light patterns, soaring ribbed vaulted ceilings disappearing into shadows, dramatic divine ray lighting, ornate stone tracery and carved details, perfect bilateral symmetry, wide-angle architectural photography, shot with Phase One camera, HDR interior technique, reverent atmospheric mood, photorealistic stone textures, National Geographic sacred spaces quality, 12K resolution',
        description: 'Sacred architecture with divine cinematography'
    },
    {
        id: 12,
        category: 'architecture',
        title: 'Futuristic Building',
        prompt: 'Zaha Hadid inspired parametric architecture, flowing biomimetic curves with cellular pattern skin, carbon fiber and smart glass facade, sustainable vertical forest integration, dramatic moody storm clouds, golden hour rim lighting, architectural visualization by MIR studio, photorealistic V-Ray rendering, people for scale, award-winning design by Foster + Partners aesthetic, ultra-detailed material textures, cinematic composition, 8K archviz presentation quality',
        description: 'Visionary architecture with photorealistic rendering'
    },
    
    // Product Category
    {
        id: 13,
        category: 'product',
        title: 'Luxury Watch',
        prompt: 'Swiss luxury watch macro photography, intricate exposed tourbillon movement, dramatic Rembrandt lighting with subtle fill, polished sapphire crystal reflections, brushed titanium case detail, depth of field on mechanical components, floating on gradient black background, professional product photography by Peter McKinnon style, focus stacking for infinite sharpness, commercial Vogue Watches quality, Phase One IQ4 camera, ultra-high resolution macro lens, 100MP detail, advertising campaign grade',
        description: 'Magazine-cover quality luxury product photography'
    },
    {
        id: 14,
        category: 'product',
        title: 'Gourmet Food',
        prompt: 'Michelin-star plated dish, artful culinary composition with microgreens and edible flowers, selective focus on hero ingredient, natural window light with black bounce card for drama, rustic reclaimed wood surface, steam rising with backlight, shallow depth of field f/2.8, professional food styling by props stylist, mouthwatering textures and glistening sauces, warm color temperature, Bon Appétit editorial quality, shot with Canon 5D Mark IV + 100mm macro, 8K commercial food photography',
        description: 'Professional culinary photography with artistic styling'
    },
    {
        id: 15,
        category: 'product',
        title: 'Tech Gadget',
        prompt: 'Premium smartphone floating composition, aerospace-grade aluminum and ceramic materials, studio strobe lighting with gradient background sweep, perfect reflections and specular highlights, Apple keynote presentation aesthetic, minimalist product photography, ultra-sharp focus, professional commercial grade, shot with Hasselblad medium format, clean shadows, tech advertisement quality, behance featured, 8K CGI-level precision',
        description: 'Apple-keynote quality tech product photography'
    },
    
    // Abstract Category
    {
        id: 16,
        category: 'abstract',
        title: 'Fluid Art',
        prompt: 'Macro fluid dynamics abstract art, metallic liquid gold and deep amethyst purple swirls, marbling alcohol ink effect with lacing patterns, organic cellular shapes, high contrast luminosity, iridescent pearlescent finish, ultra-detailed surface tension details, wallpaper quality digital art, procedural Houdini simulation aesthetic, mesmerizing fractal-like patterns, 8K ultra-high resolution, Desktop wallpaper featured quality',
        description: 'Hypnotic fluid dynamics with metallic iridescence'
    },
    {
        id: 17,
        category: 'abstract',
        title: 'Geometric Patterns',
        prompt: 'Sacred geometry mandala with fibonacci spiral, Islamic tessellation patterns, perfect bilateral symmetry, vibrant neon gradients transitioning through spectrum, mathematical precision with golden ratio, intricate fractal details at every zoom level, 3D depth with isometric perspective, bioluminescent glow effect, digital art by Android Jones style, psychedelic visionary art, ultra-sharp vector quality, 8K wallpaper resolution',
        description: 'Mathematically perfect sacred geometry with neon gradients'
    },
    {
        id: 18,
        category: 'abstract',
        title: 'Space Nebula',
        prompt: 'Pillars of Creation nebula in Eagle Nebula, vibrant cosmic gas clouds in purple, teal and gold hues, countless distant stars like diamond dust, deep space astrophotography, James Webb Space Telescope infrared imaging style, Hubble Heritage quality, hydrogen-alpha emission regions, volumetric nebula density, astronomical accuracy with artistic color grading, ultra-detailed star formations, NASA APOD featured quality, 16K resolution cosmic masterpiece',
        description: 'NASA-quality cosmic photography with scientific accuracy'
    }
];

// Featured Examples with simulated images
const featuredExamples = [
    {
        id: 1,
        title: 'Sunset Mountain Peak',
        prompt: 'Majestic snow-capped mountain peak at golden hour, dramatic orange and pink sky, wispy clouds, alpenglow, professional landscape photography, wide angle, highly detailed, 8K',
        category: 'landscape',
        color: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)'
    },
    {
        id: 2,
        title: 'Cyberpunk Samurai',
        prompt: 'Cyberpunk samurai warrior, neon armor, katana sword, futuristic Tokyo street background, rain, neon lights reflection, cinematic, highly detailed, digital art, artstation trending',
        category: 'fantasy',
        color: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)'
    },
    {
        id: 3,
        title: 'Vintage Coffee Shop',
        prompt: 'Cozy vintage coffee shop interior, warm lighting, wooden furniture, books on shelves, steaming coffee cup, afternoon sunlight through window, atmospheric, highly detailed, photorealistic',
        category: 'architecture',
        color: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)'
    },
    {
        id: 4,
        title: 'Ethereal Portrait',
        prompt: 'Ethereal portrait of a woman with flowing hair, soft backlight, dreamy atmosphere, pastel colors, bokeh background, fantasy photography, magical mood, highly detailed, 8K',
        category: 'portrait',
        color: 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)'
    },
    {
        id: 5,
        title: 'Luxury Perfume Bottle',
        prompt: 'Luxury perfume bottle, crystal clear glass, golden accents, soft lighting, elegant composition, product photography, white background, reflections, commercial quality, 8K',
        category: 'product',
        color: 'linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)'
    },
    {
        id: 6,
        title: 'Aurora Abstract',
        prompt: 'Abstract aurora borealis waves, flowing light patterns, purple green and blue, cosmic energy, digital art, smooth gradients, mesmerizing, wallpaper quality, 8K',
        category: 'abstract',
        color: 'linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%)'
    }
];

// Global variables
let uploadedImageFile = null;
let currentMode = 'generate';
let currentCategory = 'all';

// DOM Elements - will be initialized on DOMContentLoaded
let promptInput, negativePrompt, generateBtn, styleSelect, engineSelect, aspectRatio;
let qualityBoost, promptOptimizer, postProcess, upscaleSelect, generatedImage;
let promptGrid, examplesGrid, tabButtons, modal, modalImage, modalPrompt, closeModal;
let modeTabs, generateMode, editMode, imageUpload, uploadBox, imagePreview;
let previewImg, removeImage, editBtn, editedImage;
let imageUploadGenerate, uploadBoxGenerate, imagePreviewGenerate;
let previewImgGenerate, removeImageGenerate;

// Initialize DOM elements
function initializeDOMElements() {
    promptInput = document.getElementById('promptInput');
    negativePrompt = document.getElementById('negativePrompt');
    generateBtn = document.getElementById('generateBtn');
    styleSelect = document.getElementById('styleSelect');
    engineSelect = document.getElementById('engineSelect');
    aspectRatio = document.getElementById('aspectRatio');
    qualityBoost = document.getElementById('qualityBoost');
    promptOptimizer = document.getElementById('promptOptimizer');
    postProcess = document.getElementById('postProcess');
    upscaleSelect = document.getElementById('upscaleSelect');
    generatedImage = document.getElementById('generatedImage');
    promptGrid = document.getElementById('promptGrid');
    examplesGrid = document.getElementById('examplesGrid');
    tabButtons = document.querySelectorAll('.tab-btn');
    modal = document.getElementById('exampleModal');
    modalImage = document.getElementById('modalImage');
    modalPrompt = document.getElementById('modalPrompt');
    closeModal = document.querySelector('.close');
    modeTabs = document.querySelectorAll('.mode-tab');
    generateMode = document.getElementById('generateMode');
    editMode = document.getElementById('editMode');
    imageUpload = document.getElementById('imageUpload');
    uploadBox = document.getElementById('uploadBox');
    imagePreview = document.getElementById('imagePreview');
    previewImg = document.getElementById('previewImg');
    removeImage = document.getElementById('removeImage');
    editBtn = document.getElementById('editBtn');
    editedImage = document.getElementById('editedImage');
    imageUploadGenerate = document.getElementById('imageUploadGenerate');
    uploadBoxGenerate = document.getElementById('uploadBoxGenerate');
    imagePreviewGenerate = document.getElementById('imagePreviewGenerate');
    previewImgGenerate = document.getElementById('previewImgGenerate');
    removeImageGenerate = document.getElementById('removeImageGenerate');
}

// Initialize the page
function init() {
    console.log('Initializing page...');
    try {
        renderPromptLibrary();
        console.log('Prompt library rendered');
    } catch (e) {
        console.error('Error rendering prompt library:', e);
    }
    
    try {
        renderExamples();
        console.log('Examples rendered');
    } catch (e) {
        console.error('Error rendering examples:', e);
    }
    
    try {
        setupEventListeners();
        console.log('Event listeners set up');
    } catch (e) {
        console.error('Error setting up event listeners:', e);
    }
}

// Render Prompt Library
function renderPromptLibrary(category = 'all') {
    const filteredPrompts = category === 'all' 
        ? promptLibrary 
        : promptLibrary.filter(p => p.category === category);
    
    // Example images from Unsplash for each category
    const exampleImages = {
        portrait: [
            'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=400',
            'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400',
            'https://images.unsplash.com/photo-1531746020798-e6953c6e8e04?w=400'
        ],
        landscape: [
            'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400',
            'https://images.unsplash.com/photo-1511884642898-4c92249e20b6?w=400',
            'https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=400'
        ],
        fantasy: [
            'https://images.unsplash.com/photo-1518837695005-2083093ee35b?w=400',
            'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400',
            'https://images.unsplash.com/photo-1579546929518-9e396f3cc809?w=400'
        ],
        product: [
            'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400',
            'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400',
            'https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=400'
        ],
        architecture: [
            'https://images.unsplash.com/photo-1511818966892-d7d671e672a2?w=400',
            'https://images.unsplash.com/photo-1486718448742-163732cd1544?w=400',
            'https://images.unsplash.com/photo-1480074568708-e7b720bb3f09?w=400'
        ],
        abstract: [
            'https://images.unsplash.com/photo-1541701494587-cb58502866ab?w=400',
            'https://images.unsplash.com/photo-1558591710-4b4a1ae0f04d?w=400',
            'https://images.unsplash.com/photo-1550859492-d5da9d8e45f3?w=400'
        ]
    };
    
    promptGrid.innerHTML = filteredPrompts.map((prompt, index) => {
        const categoryImages = exampleImages[prompt.category] || exampleImages.portrait;
        const imageUrl = categoryImages[index % categoryImages.length];
        
        return `
        <div class="prompt-card" data-prompt="${prompt.prompt}">
            <div class="prompt-preview">
                <img src="${imageUrl}" alt="${prompt.title}" loading="lazy">
            </div>
            <span class="category-badge">${prompt.category}</span>
            <h3>${prompt.title}</h3>
            <p>${prompt.description}</p>
            <button class="use-prompt-btn" onclick="usePrompt('${escapeHtml(prompt.prompt)}')">
                Use This Prompt
            </button>
        </div>
    `}).join('');
}

// Render Featured Examples
function renderExamples() {
    examplesGrid.innerHTML = featuredExamples.map(example => `
        <div class="example-card" onclick="showExample(${example.id})">
            <div class="example-image">
                <div class="example-placeholder" style="background: ${example.color}">
                    <span style="font-size: 3rem;">🖼️</span>
                </div>
            </div>
            <div class="example-info">
                <h3>${example.title}</h3>
                <div class="example-prompt">"${example.prompt}"</div>
            </div>
        </div>
    `).join('');
}

// Setup Event Listeners
function setupEventListeners() {
    console.log('Setting up event listeners...');
    console.log('generateBtn:', generateBtn);
    
    if (generateBtn) {
        generateBtn.addEventListener('click', () => {
            console.log('Generate button clicked!');
            generateImage();
        });
        console.log('Generate button listener attached');
    } else {
        console.error('Generate button is null!');
    }
    
    if (editBtn) editBtn.addEventListener('click', editImage);
    
    tabButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            tabButtons.forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            currentCategory = e.target.dataset.category;
            renderPromptLibrary(currentCategory);
        });
    });
    
    // Mode switching
    modeTabs.forEach(tab => {
        tab.addEventListener('click', (e) => {
            modeTabs.forEach(t => t.classList.remove('active'));
            e.target.classList.add('active');
            currentMode = e.target.dataset.mode;
            
            if (currentMode === 'generate') {
                if (generateMode) generateMode.style.display = 'grid';
                if (editMode) editMode.style.display = 'none';
            } else {
                if (generateMode) generateMode.style.display = 'none';
                if (editMode) editMode.style.display = 'grid';
            }
        });
    });
    
    // Image upload for edit mode
    if (imageUpload) {
        imageUpload.addEventListener('change', handleImageUpload);
    }
    
    // Generate mode image upload
    if (imageUploadGenerate) {
        imageUploadGenerate.addEventListener('change', handleImageUploadGenerate);
        if (removeImageGenerate) {
            removeImageGenerate.addEventListener('click', () => {
                imageUploadGenerate.value = '';
                imagePreviewGenerate.style.display = 'none';
                uploadBoxGenerate.parentElement.style.display = 'block';
            });
        }
    }
    
    // Drag and drop for edit mode
    if (uploadBox) {
        uploadBox.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadBox.style.borderColor = 'var(--primary)';
        });
        
        uploadBox.addEventListener('dragleave', (e) => {
            uploadBox.style.borderColor = 'var(--border)';
        });
        
        uploadBox.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadBox.style.borderColor = 'var(--border)';
            const file = e.dataTransfer.files[0];
            if (file && file.type.startsWith('image/')) {
                // Manually trigger the file input
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(file);
                imageUpload.files = dataTransfer.files;
                handleImageUpload({ target: { files: [file] } });
            }
        });
    }
    
    if (removeImage) {
        removeImage.addEventListener('click', () => {
            uploadedImageFile = null;
            imagePreview.style.display = 'none';
            uploadBox.parentElement.style.display = 'block';
            if (editBtn) editBtn.disabled = true;
        });
    }
    
    if (closeModal) {
        closeModal.addEventListener('click', () => {
            if (modal) modal.classList.remove('show');
        });
    }
    
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('show');
            }
        });
    }
    
    if (styleSelect) styleSelect.addEventListener('change', addStyleToPrompt);
}

// Use a prompt
function usePrompt(prompt) {
    promptInput.value = prompt;
    promptInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
    promptInput.focus();
}

// Add style modifier to prompt
function addStyleToPrompt() {
    const style = styleSelect.value;
    if (!style) return;
    
    let currentPrompt = promptInput.value.trim();
    const styleModifiers = {
        'photorealistic': 'photorealistic, professional photography, highly detailed, 8K',
        'digital-art': 'digital art, vibrant colors, artstation quality, concept art',
        'oil-painting': 'oil painting, classical art style, brushstrokes, artistic',
        'watercolor': 'watercolor painting, soft colors, artistic, traditional art',
        '3d-render': '3D render, octane render, highly detailed, realistic lighting',
        'anime': 'anime style, manga art, vibrant colors, Japanese animation',
        'sketch': 'pencil sketch, hand-drawn, artistic line work, black and white',
        'cyberpunk': 'cyberpunk style, neon lights, futuristic, dystopian aesthetic'
    };
    
    if (currentPrompt && !currentPrompt.includes(styleModifiers[style])) {
        promptInput.value = currentPrompt + ', ' + styleModifiers[style];
    }
}

// Prompt Optimizer - Industry-leading enhancement (2025)
function optimizePrompt(prompt) {
    if (!promptOptimizer.checked) return prompt;
    
    // Advanced quality keywords based on AI model best practices
    const qualityBoosts = {
        photography: [
            'shot with Phase One IQ4 150MP',
            'professional color grading',
            'HDR technique',
            'award-winning photography',
            'National Geographic quality',
            'perfect composition',
            'hyperrealistic detail'
        ],
        art: [
            'trending on ArtStation front page',
            'concept art masterpiece',
            'octane render quality',
            'Unreal Engine 5 lighting',
            'photorealistic textures',
            'cinematic composition',
            'matte painting quality'
        ],
        render: [
            'path tracing',
            'ray tracing reflections',
            'subsurface scattering',
            'volumetric lighting',
            'physically based rendering',
            '8K unreal engine',
            'archviz quality'
        ],
        technical: [
            'tilt-shift perspective',
            'bokeh depth of field',
            'focus stacking',
            'long exposure technique',
            'golden ratio composition',
            'rule of thirds',
            'leading lines'
        ]
    };
    
    const lightingTerms = [
        'Rembrandt lighting', 'god rays', 'volumetric fog', 'rim light',
        'crepuscular rays', 'golden hour', 'blue hour', 'chiaroscuro',
        'dramatic lighting', 'soft diffused light', 'studio strobe'
    ];
    
    const detailTerms = [
        'intricate details', 'hyperdetailed textures', 'photorealistic',
        'ultra-sharp', 'infinite depth of field', 'macro photography detail',
        'subsurface scattering', 'perfect specular highlights'
    ];
    
    // Detect content type
    const promptLower = prompt.toLowerCase();
    let enhancements = [];
    
    // Photography detection
    if (promptLower.includes('photo') || promptLower.includes('portrait') || 
        promptLower.includes('landscape') || promptLower.includes('macro')) {
        enhancements.push(...qualityBoosts.photography.slice(0, 3));
        if (!lightingTerms.some(term => promptLower.includes(term.toLowerCase()))) {
            enhancements.push('volumetric lighting');
        }
    }
    
    // Art/Digital art detection
    else if (promptLower.includes('art') || promptLower.includes('painting') || 
             promptLower.includes('concept') || promptLower.includes('fantasy')) {
        enhancements.push(...qualityBoosts.art.slice(0, 3));
    }
    
    // 3D/Render detection
    else if (promptLower.includes('3d') || promptLower.includes('render') || 
             promptLower.includes('cgi') || promptLower.includes('architecture')) {
        enhancements.push(...qualityBoosts.render.slice(0, 3));
    }
    
    // Add detail terms if not present
    if (!detailTerms.some(term => promptLower.includes(term.toLowerCase()))) {
        enhancements.push('hyperrealistic detail', '8K resolution');
    }
    
    // Add quality boost terms
    if (qualityBoost.checked) {
        enhancements.push('professional quality', 'award-winning');
        
        // Add technical photography terms
        if (!qualityBoosts.technical.some(term => promptLower.includes(term.toLowerCase()))) {
            enhancements.push('perfect composition');
        }
    }
    
    // Remove duplicates and join
    enhancements = [...new Set(enhancements)];
    
    return `${prompt}, ${enhancements.join(', ')}`;
}

// Get dimensions based on aspect ratio
function getDimensions(ratio, engine) {
    const dimensions = {
        'dalle': {
            '1:1': { width: 1024, height: 1024, size: '1024x1024' },
            '16:9': { width: 1792, height: 1024, size: '1792x1024' },
            '9:16': { width: 1024, height: 1792, size: '1024x1792' },
            '4:3': { width: 1024, height: 1024, size: '1024x1024' },
            '3:2': { width: 1024, height: 1024, size: '1024x1024' }
        },
        'stability': {
            '1:1': { width: 1024, height: 1024 },
            '16:9': { width: 1344, height: 768 },
            '9:16': { width: 768, height: 1344 },
            '4:3': { width: 1024, height: 768 },
            '3:2': { width: 1024, height: 682 }
        },
        'replicate': {
            '1:1': { width: 1024, height: 1024 },
            '16:9': { width: 1344, height: 768 },
            '9:16': { width: 768, height: 1344 },
            '4:3': { width: 1024, height: 768 },
            '3:2': { width: 1024, height: 682 }
        }
    };
    
    return dimensions[engine][ratio] || dimensions[engine]['1:1'];
}

// Generate Image (Real API)
async function generateImage() {
    console.log('Generate button clicked!'); // Debug log
    
    let prompt = promptInput.value.trim();
    const negative = negativePrompt.value.trim();
    const engine = engineSelect.value;
    const ratio = aspectRatio.value;
    
    console.log('Prompt:', prompt); // Debug log
    
    if (!prompt) {
        alert('Please enter a prompt or select one from the library!');
        return;
    }
    
    // Optimize the prompt
    prompt = optimizePrompt(prompt);
    
    // Show progress bar
    const progressContainer = document.getElementById('progressContainer');
    const progressFill = document.getElementById('progressFill');
    const progressPercentEl = document.getElementById('progressPercent');
    const progressMessage = document.getElementById('progressMessage');
    const progressStep = document.getElementById('progressStep');
    const progressTime = document.getElementById('progressTime');
    
    progressContainer.style.display = 'block';
    generatedImage.style.display = 'none';
    generateBtn.disabled = true;
    generateBtn.textContent = 'Generating...';
    
    // Start progress monitoring
    let startTime = Date.now();
    
    // Simple progress animation (no SSE needed)
    let progressValue = 0;
    const progressInterval = setInterval(() => {
        if (progressValue < 90) {
            progressValue += Math.random() * 10;
            if (progressValue > 90) progressValue = 90;
            progressFill.style.width = progressValue + '%';
            progressPercentEl.textContent = Math.round(progressValue) + '%';
        }
    }, 500);
    
    try {
        const dimensions = getDimensions(ratio, engine);
        const upscale = parseInt(upscaleSelect.value);
        const qualityTier = document.getElementById('qualityTier').value;
        
        // Call AI backend
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({
                prompt: prompt,
                negative_prompt: negative,
                quality_tier: qualityTier,
                style: styleSelect.value,
                dimensions: dimensions,
                quality_boost: qualityBoost.checked,
                post_process: postProcess.checked,
                upscale: upscale
            })
        });
        
        const data = await response.json();
        
        // Stop progress animation
        clearInterval(progressInterval);
        progressFill.style.width = '100%';
        progressPercentEl.textContent = '100%';
        
        // Hide progress bar and show image
        progressContainer.style.display = 'none';
        generatedImage.style.display = 'flex';
        generatedImage.classList.remove('loading');
        
        if (data.success) {
            // Display the generated image
            let qualityBadges = '';
            if (data.enhanced) qualityBadges += '<span style="background: #10b981; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.8rem; margin-right: 5px;">✨ Enhanced</span>';
            if (data.upscaled) qualityBadges += `<span style="background: #3b82f6; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.8rem;">${data.upscaled}x Upscaled</span>`;
            
            generatedImage.innerHTML = `
                <div style="position: relative; width: 100%;">
                    <img src="${data.image_url}" alt="Generated image" style="max-width: 100%; max-height: 800px; width: auto; height: auto; border-radius: 12px; display: block; margin: 0 auto;">
                    <div style="position: absolute; top: 10px; left: 10px;">
                        ${qualityBadges}
                    </div>
                </div>
            `;
            
            // Store current image URL for sharing
            currentGeneratedImageUrl = data.image_url;
            
            // Show action buttons (download & share)
            showImageActions();
            
            showNotification(`✨ High-quality image generated with ${data.engine}!`);
            
            // Show enhanced prompt if it was modified
            if (data.revised_prompt && data.revised_prompt !== promptInput.value) {
                console.log('Enhanced prompt:', data.revised_prompt);
            }
        } else if (data.rate_limited) {
            // Rate limit error
            generatedImage.innerHTML = `
                <div style="width: 100%; height: 400px; background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); border-radius: 12px; display: flex; flex-direction: column; align-items: center; justify-content: center; color: white; padding: 20px; text-align: center;">
                    <div style="font-size: 4rem; margin-bottom: 20px;">⏱️</div>
                    <p style="font-size: 1.2rem; font-weight: 600; margin-bottom: 10px;">Rate Limit Reached</p>
                    <p style="font-size: 0.9rem; opacity: 0.9; max-width: 400px;">${data.error}</p>
                    <p style="font-size: 0.85rem; opacity: 0.8; max-width: 400px; margin-top: 15px;">💡 Tip: Sign up for unlimited generations at $29/month</p>
                </div>
            `;
            showNotification('Rate limit - please wait and try again', 'warning');
        } else if (data.demo) {
            // Show demo message if API keys not configured
            generatedImage.innerHTML = `
                <div style="width: 100%; height: 400px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; display: flex; flex-direction: column; align-items: center; justify-content: center; color: white; padding: 20px; text-align: center;">
                    <div style="font-size: 4rem; margin-bottom: 20px;">🔑</div>
                    <p style="font-size: 1.2rem; font-weight: 600; margin-bottom: 10px;">API Key Required</p>
                    <p style="font-size: 0.9rem; opacity: 0.9; max-width: 400px;">${data.error}</p>
                    <p style="font-size: 0.85rem; opacity: 0.8; max-width: 400px; margin-top: 15px;">Check the terminal for instructions</p>
                </div>
            `;
            showNotification('Add your API keys to enable generation');
        } else if (data.require_login) {
            // Login required for premium
            generatedImage.innerHTML = `
                <div style="width: 100%; height: 400px; background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%); border-radius: 12px; display: flex; flex-direction: column; align-items: center; justify-content: center; color: white; padding: 20px; text-align: center;">
                    <div style="font-size: 4rem; margin-bottom: 20px;">🔐</div>
                    <p style="font-size: 1.2rem; font-weight: 600; margin-bottom: 10px;">Login Required</p>
                    <p style="font-size: 0.9rem; opacity: 0.9; max-width: 400px;">${data.error}</p>
                    <button onclick="document.getElementById('loginBtn').click()" style="margin-top: 20px; padding: 12px 24px; background: white; color: #8b5cf6; border: none; border-radius: 8px; font-weight: 600; cursor: pointer;">Sign In</button>
                </div>
            `;
            showNotification('Please log in to use premium features');
        } else if (data.require_purchase) {
            // Need to buy credits
            generatedImage.innerHTML = `
                <div style="width: 100%; height: 400px; background: linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%); border-radius: 12px; display: flex; flex-direction: column; align-items: center; justify-content: center; color: white; padding: 20px; text-align: center;">
                    <div style="font-size: 4rem; margin-bottom: 20px;">💎</div>
                    <p style="font-size: 1.2rem; font-weight: 600; margin-bottom: 10px;">Credits Needed</p>
                    <p style="font-size: 0.9rem; opacity: 0.9; max-width: 400px;">${data.error}</p>
                    <button onclick="document.querySelector('.buy-credits-btn')?.click()" style="margin-top: 20px; padding: 12px 24px; background: white; color: #ec4899; border: none; border-radius: 8px; font-weight: 600; cursor: pointer;">Buy Credits</button>
                </div>
            `;
            showNotification('Purchase credits to continue generating');
        } else {
            throw new Error(data.error || 'Generation failed');
        }
        
    } catch (error) {
        console.error('Error:', error);
        clearInterval(progressInterval);
        progressContainer.style.display = 'none';
        generatedImage.classList.remove('loading');
        generatedImage.innerHTML = `
            <div style="width: 100%; height: 400px; border-radius: 12px; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #dc2626; padding: 20px; text-align: center;">
                <div style="font-size: 3rem; margin-bottom: 20px;">⚠️</div>
                <p style="font-size: 1.1rem; font-weight: 600; margin-bottom: 10px;">Generation Failed</p>
                <p style="font-size: 0.9rem;">${error.message}</p>
                <p style="font-size: 0.85rem; margin-top: 10px; color: #666;">Check your connection and try again</p>
            </div>
        `;
        showNotification('Error: ' + error.message, 'error');
    } finally {
        generateBtn.disabled = false;
        generateBtn.textContent = 'Generate High-Quality Image';
    }
}

// Edit Image
async function editImage() {
    if (!uploadedImageFile) {
        alert('Please upload an image first!');
        return;
    }
    
    const editType = document.querySelector('input[name="editType"]:checked')?.value;
    if (!editType) {
        alert('Please select an edit type!');
        return;
    }
    
    editBtn.disabled = true;
    editBtn.textContent = 'Processing...';
    
    const editResult = document.getElementById('editResult');
    editResult.innerHTML = `
        <div style="text-align: center; padding: 60px 20px;">
            <div class="loading-spinner" style="width: 50px; height: 50px; margin: 0 auto 20px;"></div>
            <p style="color: #666;">Processing your image...</p>
        </div>
    `;
    
    try {
        const formData = new FormData();
        formData.append('image', uploadedImageFile);
        formData.append('editType', editType);
        
        if (editType === 'enhance') {
            const prompt = document.getElementById('enhancePrompt')?.value || '';
            formData.append('prompt', prompt);
        }
        
        const response = await fetch('/api/edit', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            editResult.innerHTML = `
                <div class="generated-image" style="text-align: center;">
                    <img src="${data.image_url}" alt="Edited Image" style="max-width: 100%; height: auto; max-height: 800px; border-radius: 12px; box-shadow: 0 8px 30px rgba(0,0,0,0.3);">
                    <div style="margin-top: 20px; display: flex; gap: 10px; justify-content: center;">
                        <button onclick="downloadImage('${data.image_url}')" class="btn" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                            Download Image
                        </button>
                    </div>
                </div>
            `;
            showNotification('Image edited successfully!');
        } else {
            throw new Error(data.error || 'Failed to edit image');
        }
    } catch (error) {
        editResult.innerHTML = `
            <div style="text-align: center; padding: 60px 20px; color: #e74c3c;">
                <div style="font-size: 3rem; margin-bottom: 20px;">⚠️</div>
                <p style="font-size: 1.1rem; font-weight: 600; margin-bottom: 10px;">Edit Failed</p>
                <p style="font-size: 0.9rem;">${error.message}</p>
            </div>
        `;
        showNotification('Error: ' + error.message);
    } finally {
        editBtn.disabled = false;
        editBtn.textContent = 'Apply Edit';
    }
}

// Download generated image
function downloadImage(url) {
    const link = document.createElement('a');
    link.href = url;
    link.download = `ai-generated-${Date.now()}.png`;
    link.click();
    showNotification('Image downloaded!');
}

// Show example in modal
function showExample(id) {
    const example = featuredExamples.find(e => e.id === id);
    if (!example) return;
    
    modalPrompt.innerHTML = `<strong>Prompt:</strong> "${example.prompt}"`;
    
    // Create placeholder for modal
    const placeholderDiv = document.createElement('div');
    placeholderDiv.style.cssText = `
        width: 800px;
        height: 600px;
        background: ${example.color};
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 4rem;
    `;
    placeholderDiv.innerHTML = '🖼️';
    
    modalImage.replaceWith(placeholderDiv);
    placeholderDiv.id = 'modalImage';
    
    modal.classList.add('show');
}

// Show notification
function showNotification(message) {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px 25px;
        border-radius: 10px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Utility function to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML.replace(/"/g, '&quot;');
}

// Handle image upload in edit mode
function handleImageUpload(e) {
    const file = e.target.files[0];
    if (file && file.type.startsWith('image/')) {
        uploadedImageFile = file;
        const reader = new FileReader();
        reader.onload = (event) => {
            previewImg.src = event.target.result;
            imagePreview.style.display = 'block';
            uploadBox.parentElement.style.display = 'none';
            if (editBtn) editBtn.disabled = false;
        };
        reader.readAsDataURL(file);
    }
}

// Handle image upload in generate mode
function handleImageUploadGenerate(e) {
    const file = e.target.files[0];
    if (file && file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (event) => {
            previewImgGenerate.src = event.target.result;
            imagePreviewGenerate.style.display = 'block';
            uploadBoxGenerate.parentElement.style.display = 'none';
        };
        reader.readAsDataURL(file);
    }
}

// Add animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// ============================================
// AUTHENTICATION FUNCTIONS
// ============================================

function openAuthModal(formType = 'signIn') {
    const modal = document.getElementById('authModal');
    modal.classList.add('active');
    if (formType === 'register') {
        showRegisterForm();
    } else {
        showSignInForm();
    }
}

function closeAuthModal() {
    const modal = document.getElementById('authModal');
    modal.classList.remove('active');
}

function showSignInForm() {
    document.getElementById('signInForm').style.display = 'block';
    document.getElementById('registerForm').style.display = 'none';
}

function showRegisterForm() {
    document.getElementById('signInForm').style.display = 'none';
    document.getElementById('registerForm').style.display = 'block';
}

function handleSignIn(event) {
    event.preventDefault();
    const email = event.target[0].value;
    const password = event.target[1].value;
    
    // Store user data (in production, call backend API)
    localStorage.setItem('user', JSON.stringify({
        email: email,
        loggedIn: true,
        timestamp: Date.now()
    }));
    
    showNotification('Welcome back! Successfully signed in.', 'success');
    closeAuthModal();
    updateUIForLoggedInUser();
}

function handleRegister(event) {
    event.preventDefault();
    const name = event.target[0].value;
    const email = event.target[1].value;
    const password = event.target[2].value;
    const confirmPassword = event.target[3].value;
    
    if (password !== confirmPassword) {
        showNotification('Passwords do not match!', 'error');
        return;
    }
    
    // Store user data (in production, call backend API)
    localStorage.setItem('user', JSON.stringify({
        name: name,
        email: email,
        loggedIn: true,
        timestamp: Date.now()
    }));
    
    showNotification('Account created successfully! Welcome to AI Studio.', 'success');
    closeAuthModal();
    updateUIForLoggedInUser();
}

function updateUIForLoggedInUser() {
    // Hide auth buttons, show credit display
    document.getElementById('authButtons').style.display = 'none';
    document.getElementById('creditDisplay').style.display = 'flex';
    // Update credits
    updateCredits();
}

// ============================================
// NEWSLETTER POPUP
// ============================================
function showNewsletter() {
    const popup = document.getElementById('newsletterPopup');
    if (popup) {
        popup.classList.add('show');
    }
}

function closeNewsletter() {
    const popup = document.getElementById('newsletterPopup');
    if (popup) {
        popup.classList.remove('show');
        localStorage.setItem('newsletter_dismissed', Date.now());
    }
}

function handleNewsletter(event) {
    event.preventDefault();
    const email = event.target[0].value;
    
    // In production, send to email service API
    console.log('Newsletter signup:', email);
    
    showNotification('🎉 Subscribed! Check your email for exclusive prompts.', 'success');
    closeNewsletter();
    
    // Store that user subscribed
    localStorage.setItem('newsletter_subscribed', true);
}

// Show newsletter popup after 30 seconds if not dismissed recently
window.addEventListener('load', () => {
    const dismissed = localStorage.getItem('newsletter_dismissed');
    const subscribed = localStorage.getItem('newsletter_subscribed');
    
    if (!subscribed && (!dismissed || Date.now() - dismissed > 7 * 24 * 60 * 60 * 1000)) {
        setTimeout(showNewsletter, 30000); // 30 seconds
    }
});

// ============================================
// SOCIAL SHARING FUNCTIONS
// ============================================
let currentGeneratedImageUrl = '';

function shareImage() {
    const popup = document.getElementById('socialSharePopup');
    if (popup) {
        const isVisible = popup.style.display === 'block';
        popup.style.display = isVisible ? 'none' : 'block';
    }
}

function shareToTwitter() {
    const text = encodeURIComponent('Check out this amazing AI-generated image I created! 🎨✨');
    const url = encodeURIComponent(window.location.href);
    const hashtags = encodeURIComponent('AIart,DALLE3,AIImageGenerator');
    window.open(`https://twitter.com/intent/tweet?text=${text}&url=${url}&hashtags=${hashtags}`, '_blank', 'width=600,height=400');
}

function shareToFacebook() {
    const url = encodeURIComponent(window.location.href);
    window.open(`https://www.facebook.com/sharer/sharer.php?u=${url}`, '_blank', 'width=600,height=400');
}

function shareToReddit() {
    const url = encodeURIComponent(window.location.href);
    const title = encodeURIComponent('Amazing AI-Generated Image - AI Image Studio');
    window.open(`https://reddit.com/submit?url=${url}&title=${title}`, '_blank', 'width=800,height=600');
}

function copyImageLink() {
    const url = window.location.href;
    navigator.clipboard.writeText(url).then(() => {
        showNotification('Link copied to clipboard! 📋', 'success');
    }).catch(() => {
        showNotification('Failed to copy link', 'error');
    });
}

function downloadImage() {
    const img = document.querySelector('#generatedImage img');
    if (img && img.src) {
        const link = document.createElement('a');
        link.href = img.src;
        link.download = `ai-image-${Date.now()}.png`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        showNotification('Image downloaded! 📥', 'success');
    }
}

// Show image actions after successful generation
function showImageActions() {
    const actions = document.getElementById('imageActions');
    if (actions) {
        actions.style.display = 'flex';
    }
}

// Close share popup when clicking outside
document.addEventListener('click', (e) => {
    const shareBtn = document.querySelector('.share-btn');
    const sharePopup = document.getElementById('socialSharePopup');
    
    if (sharePopup && shareBtn && 
        !shareBtn.contains(e.target) && 
        !sharePopup.contains(e.target)) {
        sharePopup.style.display = 'none';
    }
});

// Setup auth button listeners
document.getElementById('loginBtn')?.addEventListener('click', () => openAuthModal('signIn'));
document.getElementById('registerBtn')?.addEventListener('click', () => openAuthModal('register'));

// Check if user is logged in on page load
window.addEventListener('load', () => {
    updateUIForLoggedInUser();
});

// Initialize on page load
document.addEventListener('DOMContentLoaded', init);

// ============================================
// CREDIT SYSTEM & MONETIZATION
// ============================================

// Check and display user credits
async function checkCredits() {
    try {
        const response = await fetch('/api/credits/balance');
        const data = await response.json();
        
        if (data.success) {
            // Update credit display
            document.getElementById('freeCredits').textContent = data.free_credits || 0;
            document.getElementById('premiumCredits').textContent = data.premium_credits || 0;
            
            // Show unlimited badge if user has subscription
            const unlimitedBadge = document.getElementById('unlimitedBadge');
            if (data.has_unlimited) {
                unlimitedBadge.style.display = 'flex';
                hideAds(); // Hide ads for unlimited users
            } else {
                unlimitedBadge.style.display = 'none';
            }
            
            // Show credit display
            document.getElementById('creditDisplay').style.display = 'flex';
            
            // Control ad visibility based on user status
            updateAdVisibility(data);
            
            return data;
        }
    } catch (error) {
        console.error('Error checking credits:', error);
    }
    return null;
}

// Update ad visibility based on user status
function updateAdVisibility(creditData) {
    const adContainer = document.getElementById('adContainer');
    
    if (!adContainer) return;
    
    // Hide ads for premium/unlimited users
    if (creditData.has_unlimited || creditData.premium_credits > 0) {
        hideAds();
    } else {
        showAds();
    }
}

// Show ads for free users
function showAds() {
    const adContainer = document.getElementById('adContainer');
    if (adContainer) {
        adContainer.style.display = 'block';
    }
    document.body.classList.remove('premium-user');
}

// Hide ads for premium users
function hideAds() {
    const adContainer = document.getElementById('adContainer');
    if (adContainer) {
        adContainer.style.display = 'none';
    }
    document.body.classList.add('premium-user');
}

// Buy Credits Modal
const buyCreditsModal = document.getElementById('buyCreditsModal');
const buyCreditsBtn = document.getElementById('buyCreditsBtn');

if (buyCreditsBtn) {
    buyCreditsBtn.addEventListener('click', () => {
        buyCreditsModal.classList.add('show');
    });
}

// Handle credit package purchase
document.querySelectorAll('.buy-btn[data-package]').forEach(btn => {
    btn.addEventListener('click', async (e) => {
        const packageId = e.target.dataset.package;
        await purchaseCredits(packageId);
    });
});

// Handle unlimited subscription
document.getElementById('subscribeBtn')?.addEventListener('click', async () => {
    await subscribeUnlimited();
});

// Purchase credits
async function purchaseCredits(packageId) {
    try {
        const response = await fetch('/api/credits/purchase', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ package: packageId })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Redirect to Stripe checkout
            window.location.href = data.checkout_url;
        } else {
            showNotification(data.error || 'Please log in to purchase credits', 'error');
        }
    } catch (error) {
        console.error('Error purchasing credits:', error);
        showNotification('Error processing purchase', 'error');
    }
}

// Subscribe to unlimited plan
async function subscribeUnlimited() {
    try {
        const response = await fetch('/api/subscription/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Redirect to Stripe checkout
            window.location.href = data.checkout_url;
        } else {
            showNotification(data.error || 'Please log in to subscribe', 'error');
        }
    } catch (error) {
        console.error('Error creating subscription:', error);
        showNotification('Error processing subscription', 'error');
    }
}

// Close modals
document.querySelectorAll('.auth-close').forEach(closeBtn => {
    closeBtn.addEventListener('click', (e) => {
        e.target.closest('.auth-modal').classList.remove('show');
    });
});

// Check credits when user logs in
window.addEventListener('load', () => {
    checkCredits();
});

// Show ads to anonymous users by default
showAds();




