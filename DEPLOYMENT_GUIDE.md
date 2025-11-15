# Picly - AI Image Generator
# Production Server Setup Guide

## DEPLOYMENT OPTIONS

### Option A: Quick Deploy with Render.com (Easiest - Free Tier Available)
1. Create account at render.com
2. Connect your GitHub (push this code there first)
3. Create new "Web Service"
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `python localAI.py`
6. Connect your domain in Render settings

### Option B: Deploy with Railway.app (Easy - $5/month)
1. Create account at railway.app
2. "New Project" -> "Deploy from GitHub"
3. Add your domain in settings
4. Railway auto-detects Python and runs it

### Option C: VPS/Cloud Server (Full Control)
**Recommended for GPU: Vast.ai, RunPod, or DigitalOcean**

#### Step 1: Server Setup
```bash
# SSH into your server
ssh root@your-server-ip

# Update system
apt update && apt upgrade -y

# Install Python and dependencies
apt install python3 python3-pip nginx -y

# Install Node.js (optional, for better tooling)
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install nodejs -y
```

#### Step 2: Copy Your Files
```bash
# On your local machine
scp -r "c:\AI image site" root@your-server-ip:/var/www/picly
```

#### Step 3: Install Python Packages
```bash
cd /var/www/picly
pip3 install -r requirements.txt
```

#### Step 4: Setup Nginx (Web Server)
Create file: `/etc/nginx/sites-available/picly`
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Enable site:
```bash
ln -s /etc/nginx/sites-available/picly /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

#### Step 5: Setup SSL (HTTPS)
```bash
apt install certbot python3-certbot-nginx -y
certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

#### Step 6: Run Your App (Production)
Install gunicorn for production:
```bash
pip3 install gunicorn
```

Create service file: `/etc/systemd/system/picly.service`
```ini
[Unit]
Description=Picly AI Image Generator
After=network.target

[Service]
User=root
WorkingDirectory=/var/www/picly
ExecStart=/usr/local/bin/gunicorn -w 4 -b 127.0.0.1:5000 localAI:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Start service:
```bash
systemctl daemon-reload
systemctl start picly
systemctl enable picly
systemctl status picly
```

### Option D: Docker Deployment (Advanced)
See Dockerfile in this directory

---

## DOMAIN CONFIGURATION

### Connect Domain to Server:
1. Go to your domain registrar (GoDaddy, Namecheap, etc.)
2. Find DNS settings
3. Add A record:
   - Type: A
   - Name: @ (or leave blank)
   - Value: YOUR_SERVER_IP
   - TTL: 3600
4. Add CNAME record:
   - Type: CNAME
   - Name: www
   - Value: yourdomain.com
   - TTL: 3600

DNS changes take 5-60 minutes to propagate.

---

## CURRENT STATUS
- Local development server: ✅ Working
- Production deployment: ⏳ Pending your choice
- Domain connection: ⏳ Waiting for server IP

**Next Steps:**
1. Tell me your domain name
2. Choose deployment option (A, B, or C)
3. I'll provide specific instructions for your setup
