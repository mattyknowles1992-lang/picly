# Picly - GPU Server Deployment Guide (Vast.ai)
# Fast, High-Quality AI Image Generation

## WHY GPU SERVER?
- 🚀 Generate images in 10-30 seconds (vs 5+ minutes on CPU)
- 💎 Better quality models (SDXL support)
- 🌍 Access from any device
- 💰 Only ~$7-20/month

---

## STEP-BY-STEP SETUP (Vast.ai)

### Step 1: Create Vast.ai Account
1. Go to https://vast.ai
2. Sign up (email or GitHub)
3. Add credit ($10 minimum - lasts weeks)
4. Go to "Billing" → "Add Credit"

### Step 2: Find a GPU Instance
1. Click "Search" in top menu
2. Filter settings:
   - GPU: RTX 3060 or better
   - RAM: 16GB+
   - Disk: 50GB+
   - DLPerf: 50+
3. Sort by "$/hour" (cheapest first)
4. Look for ~$0.15-0.25/hour

### Step 3: Launch Instance
1. Click "Rent" on a good option
2. Choose "Docker Image": `pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime`
3. Click "Select & Deploy Instance"
4. Wait 2-5 minutes for startup

### Step 4: Connect & Setup
Once running, you'll get an SSH command like:
```bash
ssh -p 12345 root@123.456.789.10
```

Run this on your computer (PowerShell):
```powershell
# Connect to your server
ssh -p YOUR_PORT root@YOUR_IP
# (Accept fingerprint, no password needed)
```

### Step 5: Install Picly on Server
Copy and paste these commands one by one:

```bash
# Update system
apt update && apt install -y git python3-pip nginx

# Clone your files (we'll upload them)
mkdir /app
cd /app

# Install Python packages
pip3 install flask flask-cors pillow torch torchvision diffusers transformers accelerate
```

### Step 6: Upload Your Files
On your local computer (PowerShell):
```powershell
# Compress your files
cd "c:\AI image site"
Compress-Archive -Path * -DestinationPath picly.zip

# Upload to server (replace with your details)
scp -P YOUR_PORT picly.zip root@YOUR_IP:/app/

# Back on server, unzip
ssh -p YOUR_PORT root@YOUR_IP
cd /app
apt install -y unzip
unzip picly.zip
```

### Step 7: Configure for Production
On the server:
```bash
# Edit localAI.py to bind to all interfaces
nano localAI.py
# Change the last line to:
# app.run(host='0.0.0.0', port=5000, debug=False)
```

### Step 8: Setup Nginx (Public Access)
```bash
# Create nginx config
cat > /etc/nginx/sites-available/picly << 'EOF'
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
EOF

# Enable site
ln -sf /etc/nginx/sites-available/picly /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx
```

### Step 9: Run Picly
```bash
cd /app
python3 localAI.py
```

Your server is now live at: `http://YOUR_SERVER_IP`

### Step 10: Connect Your Domain (picly.co.uk)

**In IONOS Dashboard:**
1. Go to Domains → picly.co.uk → DNS
2. Click "Add Record"
3. Add A Record:
   - Type: A
   - Name: @ (or blank)
   - Points to: YOUR_SERVER_IP
   - TTL: 3600
4. Add another A Record:
   - Type: A  
   - Name: www
   - Points to: YOUR_SERVER_IP
   - TTL: 3600
5. Save and wait 5-30 minutes

Your site will be live at: **http://picly.co.uk**

### Step 11: Add HTTPS (Free SSL)
On server:
```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d picly.co.uk -d www.picly.co.uk
# Follow prompts, enter your email
```

Now accessible at: **https://picly.co.uk** ✅

---

## KEEP SERVER RUNNING (Auto-Start)

Create systemd service:
```bash
cat > /etc/systemd/system/picly.service << 'EOF'
[Unit]
Description=Picly AI Generator
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/app
ExecStart=/usr/bin/python3 localAI.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable picly
systemctl start picly
systemctl status picly
```

---

## COST CALCULATION
- GPU instance: $0.20/hour
- 24/7 for 1 month: $0.20 × 24 × 30 = $144/month
- **OR** only run when needed: ~$5-20/month

**Tip**: Stop instance when not in use to save money!

---

## UPGRADE TO SDXL (Better Quality)

Once working, edit localAI.py:
```python
# Change line:
model_id = "runwayml/stable-diffusion-v1-5"
# To:
model_id = "stabilityai/stable-diffusion-xl-base-1.0"
```

SDXL produces higher quality images (1024x1024) but needs more GPU RAM.

---

## NEXT STEPS

1. ✅ Sign up for Vast.ai
2. ✅ Rent GPU instance ($0.15-0.25/hour)
3. ✅ Follow steps above
4. ✅ Connect domain picly.co.uk
5. ✅ Test image generation
6. 🎉 Share your site!

Need help? Let me know which step you're on!
