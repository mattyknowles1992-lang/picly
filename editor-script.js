// AI Image Editor Pro - Main Script
// Superior to ComfyUI with intuitive interface and advanced AI features

// ============ STATE MANAGEMENT ============
const state = {
    currentTool: 'select',
    currentImage: null,
    layers: [],
    currentLayer: 0,
    history: [],
    historyIndex: -1,
    zoom: 1,
    isDrawing: false,
    brushSize: 50,
    opacity: 100,
    hardness: 50,
    adjustments: {
        brightness: 0,
        contrast: 0,
        saturation: 0,
        sharpness: 0
    }
};

// Canvas references
let canvas, ctx, overlayCanvas, overlayCtx;
const API_URL = 'http://localhost:5000';

// ============ INITIALIZATION ============
document.addEventListener('DOMContentLoaded', () => {
    initializeCanvas();
    initializeEventListeners();
    initializeTools();
    initializeAdjustments();
    setupDragAndDrop();
});

function initializeCanvas() {
    canvas = document.getElementById('main-canvas');
    ctx = canvas.getContext('2d', { willReadFrequently: true });
    overlayCanvas = document.getElementById('overlay-canvas');
    overlayCtx = overlayCanvas.getContext('2d');
    
    // Set default canvas size
    canvas.width = 800;
    canvas.height = 600;
    overlayCanvas.width = 800;
    overlayCanvas.height = 600;
}

// ============ EVENT LISTENERS ============
function initializeEventListeners() {
    // File input
    document.getElementById('file-input').addEventListener('change', handleFileSelect);
    
    // Canvas mouse events
    canvas.addEventListener('mousedown', startDrawing);
    canvas.addEventListener('mousemove', draw);
    canvas.addEventListener('mouseup', stopDrawing);
    canvas.addEventListener('mouseleave', stopDrawing);
    
    // Keyboard shortcuts
    document.addEventListener('keydown', handleKeyboard);
    
    // Prevent context menu on canvas
    canvas.addEventListener('contextmenu', (e) => e.preventDefault());
}

function initializeTools() {
    const toolButtons = document.querySelectorAll('.tool-btn');
    toolButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            toolButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            state.currentTool = btn.dataset.tool;
        });
    });
}

function initializeAdjustments() {
    // Brush settings
    const brushSize = document.getElementById('brush-size');
    brushSize.addEventListener('input', (e) => {
        state.brushSize = e.target.value;
        document.getElementById('brush-size-value').textContent = e.target.value;
    });
    
    const opacity = document.getElementById('opacity');
    opacity.addEventListener('input', (e) => {
        state.opacity = e.target.value;
        document.getElementById('opacity-value').textContent = e.target.value;
    });
    
    const hardness = document.getElementById('hardness');
    hardness.addEventListener('input', (e) => {
        state.hardness = e.target.value;
        document.getElementById('hardness-value').textContent = e.target.value;
    });
    
    // Image adjustments
    ['brightness', 'contrast', 'saturation', 'sharpness'].forEach(prop => {
        const slider = document.getElementById(prop);
        slider.addEventListener('input', (e) => {
            state.adjustments[prop] = parseFloat(e.target.value);
            document.getElementById(`${prop}-value`).textContent = e.target.value;
            applyAdjustments();
        });
    });
}

// ============ FILE HANDLING ============
function openImage() {
    document.getElementById('file-input').click();
}

function handleFileSelect(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (e) => {
        const img = new Image();
        img.onload = () => {
            loadImageToCanvas(img);
            updateProperties(img, file);
            document.getElementById('empty-state').style.display = 'none';
        };
        img.src = e.target.result;
    };
    reader.readAsDataURL(file);
}

function loadImageToCanvas(img) {
    // Resize canvas to fit image
    canvas.width = img.width;
    canvas.height = img.height;
    overlayCanvas.width = img.width;
    overlayCanvas.height = img.height;
    
    // Draw image
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(img, 0, 0);
    
    state.currentImage = img;
    saveToHistory();
    fitToScreen();
}

function updateProperties(img, file) {
    document.getElementById('dimensions').textContent = `${img.width} × ${img.height}px`;
    document.getElementById('file-size').textContent = formatFileSize(file.size);
    document.getElementById('file-format').textContent = file.type.split('/')[1].toUpperCase();
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / 1048576).toFixed(2) + ' MB';
}

// ============ DRAG AND DROP ============
function setupDragAndDrop() {
    const canvasWrapper = document.getElementById('canvas-wrapper');
    
    canvasWrapper.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.stopPropagation();
        canvasWrapper.style.opacity = '0.7';
    });
    
    canvasWrapper.addEventListener('dragleave', (e) => {
        e.preventDefault();
        e.stopPropagation();
        canvasWrapper.style.opacity = '1';
    });
    
    canvasWrapper.addEventListener('drop', (e) => {
        e.preventDefault();
        e.stopPropagation();
        canvasWrapper.style.opacity = '1';
        
        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = (event) => {
                const img = new Image();
                img.onload = () => {
                    loadImageToCanvas(img);
                    updateProperties(img, file);
                    document.getElementById('empty-state').style.display = 'none';
                };
                img.src = event.target.result;
            };
            reader.readAsDataURL(file);
        }
    });
}

// ============ DRAWING TOOLS ============
function startDrawing(e) {
    if (!state.currentImage) return;
    
    state.isDrawing = true;
    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left) / state.zoom;
    const y = (e.clientY - rect.top) / state.zoom;
    
    if (state.currentTool === 'brush') {
        ctx.beginPath();
        ctx.moveTo(x, y);
    }
}

function draw(e) {
    if (!state.isDrawing) return;
    
    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left) / state.zoom;
    const y = (e.clientY - rect.top) / state.zoom;
    
    // Show brush cursor on overlay
    overlayCtx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
    overlayCtx.beginPath();
    overlayCtx.arc(x, y, state.brushSize / 2, 0, Math.PI * 2);
    overlayCtx.strokeStyle = '#667eea';
    overlayCtx.lineWidth = 2;
    overlayCtx.stroke();
    
    if (state.currentTool === 'brush') {
        ctx.lineTo(x, y);
        ctx.strokeStyle = '#000000';
        ctx.lineWidth = state.brushSize;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        ctx.globalAlpha = state.opacity / 100;
        ctx.stroke();
    } else if (state.currentTool === 'eraser') {
        ctx.clearRect(x - state.brushSize / 2, y - state.brushSize / 2, state.brushSize, state.brushSize);
    }
}

function stopDrawing() {
    if (state.isDrawing) {
        state.isDrawing = false;
        saveToHistory();
    }
}

// ============ HISTORY (UNDO/REDO) ============
function saveToHistory() {
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    state.history = state.history.slice(0, state.historyIndex + 1);
    state.history.push(imageData);
    state.historyIndex++;
    
    // Limit history to 50 steps
    if (state.history.length > 50) {
        state.history.shift();
        state.historyIndex--;
    }
}

function undo() {
    if (state.historyIndex > 0) {
        state.historyIndex--;
        const imageData = state.history[state.historyIndex];
        ctx.putImageData(imageData, 0, 0);
    }
}

function redo() {
    if (state.historyIndex < state.history.length - 1) {
        state.historyIndex++;
        const imageData = state.history[state.historyIndex];
        ctx.putImageData(imageData, 0, 0);
    }
}

// ============ ZOOM CONTROLS ============
function zoomIn() {
    state.zoom = Math.min(state.zoom + 0.1, 5);
    updateZoom();
}

function zoomOut() {
    state.zoom = Math.max(state.zoom - 0.1, 0.1);
    updateZoom();
}

function fitToScreen() {
    const container = canvas.parentElement.parentElement;
    const scaleX = (container.clientWidth - 40) / canvas.width;
    const scaleY = (container.clientHeight - 40) / canvas.height;
    state.zoom = Math.min(scaleX, scaleY, 1);
    updateZoom();
}

function updateZoom() {
    canvas.style.transform = `scale(${state.zoom})`;
    overlayCanvas.style.transform = `scale(${state.zoom})`;
    document.getElementById('zoom-level').textContent = Math.round(state.zoom * 100) + '%';
}

// ============ IMAGE ADJUSTMENTS ============
function applyAdjustments() {
    if (!state.currentImage) return;
    
    // Reset to original
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(state.currentImage, 0, 0);
    
    // Get image data
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const data = imageData.data;
    
    const brightness = state.adjustments.brightness;
    const contrast = state.adjustments.contrast;
    const saturation = state.adjustments.saturation;
    
    for (let i = 0; i < data.length; i += 4) {
        // Brightness
        data[i] += brightness * 2.55;
        data[i + 1] += brightness * 2.55;
        data[i + 2] += brightness * 2.55;
        
        // Contrast
        const factor = (259 * (contrast + 255)) / (255 * (259 - contrast));
        data[i] = factor * (data[i] - 128) + 128;
        data[i + 1] = factor * (data[i + 1] - 128) + 128;
        data[i + 2] = factor * (data[i + 2] - 128) + 128;
        
        // Saturation
        const gray = 0.2989 * data[i] + 0.5870 * data[i + 1] + 0.1140 * data[i + 2];
        const sat = saturation / 100;
        data[i] = gray + sat * (data[i] - gray);
        data[i + 1] = gray + sat * (data[i + 1] - gray);
        data[i + 2] = gray + sat * (data[i + 2] - gray);
        
        // Clamp values
        data[i] = Math.max(0, Math.min(255, data[i]));
        data[i + 1] = Math.max(0, Math.min(255, data[i + 1]));
        data[i + 2] = Math.max(0, Math.min(255, data[i + 2]));
    }
    
    ctx.putImageData(imageData, 0, 0);
}

function resetAdjustments() {
    state.adjustments = { brightness: 0, contrast: 0, saturation: 0, sharpness: 0 };
    ['brightness', 'contrast', 'saturation', 'sharpness'].forEach(prop => {
        document.getElementById(prop).value = 0;
        document.getElementById(`${prop}-value`).textContent = '0';
    });
    applyAdjustments();
}

// ============ FILTERS ============
function applyFilter(filterType) {
    if (!state.currentImage) return;
    
    showLoading('Applying filter...');
    
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const data = imageData.data;
    
    switch(filterType) {
        case 'bw':
            for (let i = 0; i < data.length; i += 4) {
                const gray = 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2];
                data[i] = data[i + 1] = data[i + 2] = gray;
            }
            break;
        case 'sepia':
            for (let i = 0; i < data.length; i += 4) {
                const r = data[i], g = data[i + 1], b = data[i + 2];
                data[i] = Math.min(255, r * 0.393 + g * 0.769 + b * 0.189);
                data[i + 1] = Math.min(255, r * 0.349 + g * 0.686 + b * 0.168);
                data[i + 2] = Math.min(255, r * 0.272 + g * 0.534 + b * 0.131);
            }
            break;
        case 'vivid':
            for (let i = 0; i < data.length; i += 4) {
                data[i] = Math.min(255, data[i] * 1.3);
                data[i + 1] = Math.min(255, data[i + 1] * 1.3);
                data[i + 2] = Math.min(255, data[i + 2] * 1.3);
            }
            break;
    }
    
    ctx.putImageData(imageData, 0, 0);
    saveToHistory();
    
    setTimeout(hideLoading, 500);
}

// ============ AI FEATURES ============
async function removeBackground() {
    if (!state.currentImage) {
        alert('Please load an image first!');
        return;
    }
    
    showLoading('Removing background with AI...');
    
    try {
        const formData = new FormData();
        const blob = await canvasToBlob();
        formData.append('image', blob, 'image.png');
        formData.append('operation', 'remove_background');
        
        const response = await fetch(`${API_URL}/api/enhance`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        if (result.success) {
            loadImageFromURL(result.image_url);
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        console.error('Error removing background:', error);
        alert('Failed to remove background. Please try again.');
    } finally {
        hideLoading();
    }
}

async function enhanceFace() {
    if (!state.currentImage) {
        alert('Please load an image first!');
        return;
    }
    
    showLoading('Enhancing face with AI...');
    
    try {
        const formData = new FormData();
        const blob = await canvasToBlob();
        formData.append('image', blob, 'image.png');
        formData.append('operation', 'enhance_face');
        
        const response = await fetch(`${API_URL}/api/enhance`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        if (result.success) {
            loadImageFromURL(result.image_url);
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        console.error('Error enhancing face:', error);
        alert('Failed to enhance face. Please try again.');
    } finally {
        hideLoading();
    }
}

async function upscaleImage() {
    if (!state.currentImage) {
        alert('Please load an image first!');
        return;
    }
    
    showLoading('Upscaling image to 4x resolution...');
    
    try {
        const formData = new FormData();
        const blob = await canvasToBlob();
        formData.append('image', blob, 'image.png');
        formData.append('scale', '4');
        
        const response = await fetch(`${API_URL}/api/upscale`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        if (result.success) {
            loadImageFromURL(result.image_url);
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        console.error('Error upscaling:', error);
        alert('Failed to upscale image. Please try again.');
    } finally {
        hideLoading();
    }
}

async function styleTransfer() {
    document.getElementById('modal-title').textContent = 'Style Transfer';
    document.getElementById('ai-prompt').placeholder = 'E.g., "Van Gogh painting", "anime style", "oil painting"';
    document.getElementById('ai-modal').style.display = 'flex';
}

async function autoEnhance() {
    if (!state.currentImage) {
        alert('Please load an image first!');
        return;
    }
    
    showLoading('Auto-enhancing image...');
    
    // Apply optimal adjustments
    state.adjustments.brightness = 10;
    state.adjustments.contrast = 15;
    state.adjustments.saturation = 20;
    state.adjustments.sharpness = 30;
    
    applyAdjustments();
    saveToHistory();
    
    setTimeout(hideLoading, 1000);
}

async function colorize() {
    if (!state.currentImage) {
        alert('Please load an image first!');
        return;
    }
    
    showLoading('Colorizing image with AI...');
    
    try {
        const formData = new FormData();
        const blob = await canvasToBlob();
        formData.append('image', blob, 'image.png');
        formData.append('operation', 'colorize');
        
        const response = await fetch(`${API_URL}/api/enhance`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        if (result.success) {
            loadImageFromURL(result.image_url);
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        console.error('Error colorizing:', error);
        alert('Failed to colorize image. Please try again.');
    } finally {
        hideLoading();
    }
}

// ============ HELPER FUNCTIONS ============
async function canvasToBlob() {
    return new Promise((resolve) => {
        canvas.toBlob(resolve, 'image/png');
    });
}

function loadImageFromURL(url) {
    const img = new Image();
    img.onload = () => {
        loadImageToCanvas(img);
    };
    img.src = url;
}

function showLoading(text = 'Processing...') {
    document.getElementById('loading-text').textContent = text;
    document.getElementById('loading-overlay').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loading-overlay').style.display = 'none';
}

// ============ SAVE/EXPORT ============
function saveImage() {
    if (!state.currentImage) {
        alert('No image to save!');
        return;
    }
    
    canvas.toBlob((blob) => {
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.download = `edited-${Date.now()}.png`;
        link.href = url;
        link.click();
        URL.revokeObjectURL(url);
    }, 'image/png');
}

function exportImage() {
    saveImage();
}

// ============ LAYERS ============
function addLayer() {
    alert('Layer system coming in next update!');
}

function deleteLayer() {
    alert('Layer system coming in next update!');
}

function duplicateLayer() {
    alert('Layer system coming in next update!');
}

function mergeDown() {
    alert('Layer system coming in next update!');
}

// ============ MODAL ============
function closeModal() {
    document.getElementById('ai-modal').style.display = 'none';
}

async function processAI() {
    const prompt = document.getElementById('ai-prompt').value;
    if (!prompt) {
        alert('Please enter a prompt!');
        return;
    }
    
    closeModal();
    showLoading('Processing with AI...');
    
    try {
        const formData = new FormData();
        const blob = await canvasToBlob();
        formData.append('image', blob, 'image.png');
        formData.append('prompt', prompt);
        formData.append('strength', document.getElementById('ai-strength').value / 100);
        formData.append('mode', 'edit');
        
        const response = await fetch(`${API_URL}/api/edit`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        if (result.success) {
            loadImageFromURL(result.image_url);
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        console.error('Error processing AI:', error);
        alert('Failed to process with AI. Please try again.');
    } finally {
        hideLoading();
    }
}

// ============ KEYBOARD SHORTCUTS ============
function handleKeyboard(e) {
    // Ctrl+Z - Undo
    if (e.ctrlKey && e.key === 'z') {
        e.preventDefault();
        undo();
    }
    // Ctrl+Y - Redo
    if (e.ctrlKey && e.key === 'y') {
        e.preventDefault();
        redo();
    }
    // Ctrl+S - Save
    if (e.ctrlKey && e.key === 's') {
        e.preventDefault();
        saveImage();
    }
    // Tool shortcuts
    const toolKeys = {
        'v': 'select',
        'b': 'brush',
        'e': 'eraser',
        'i': 'inpaint',
        'r': 'object-remove',
        's': 'clone',
        'w': 'magic-wand',
        't': 'text'
    };
    if (toolKeys[e.key.toLowerCase()]) {
        document.querySelector(`[data-tool="${toolKeys[e.key.toLowerCase()]}"]`).click();
    }
}

console.log('🎨 AI Image Editor Pro loaded successfully!');
console.log('Keyboard shortcuts: V=Select, B=Brush, E=Eraser, I=Inpaint, R=Remove, S=Clone, W=Magic, T=Text');
console.log('Ctrl+Z=Undo, Ctrl+Y=Redo, Ctrl+S=Save');
