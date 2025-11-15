# Install Local AI Dependencies
# This will install everything needed to run AI image generation locally

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "🎨 PICLY LOCAL AI - INSTALLATION" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Installing AI libraries (this may take 5-10 minutes)..." -ForegroundColor Yellow
Write-Host ""

# Install PyTorch (CPU version - works on any computer)
Write-Host "📦 Installing PyTorch..." -ForegroundColor Green
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Install diffusers and dependencies
Write-Host "📦 Installing Diffusers (Stable Diffusion)..." -ForegroundColor Green
pip install diffusers transformers accelerate

# Install other requirements
Write-Host "📦 Installing other dependencies..." -ForegroundColor Green
pip install flask flask-cors pillow

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "✅ INSTALLATION COMPLETE!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To start the local AI server:" -ForegroundColor Yellow
Write-Host "  python localAI.py" -ForegroundColor White
Write-Host ""
Write-Host "Note: First image generation will download the AI model (~4GB)" -ForegroundColor Yellow
Write-Host "      Subsequent generations will be fast!" -ForegroundColor Yellow
Write-Host ""
