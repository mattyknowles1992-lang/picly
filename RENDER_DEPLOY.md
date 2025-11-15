# RENDER.COM DEPLOYMENT GUIDE

## Quick Deploy Steps:

### Step 1: Create GitHub Repository
1. Go to https://github.com/new
2. Name: `picly`
3. Make it Public
4. Click "Create repository"

### Step 2: Upload Your Code to GitHub
In PowerShell on your computer:

```powershell
cd "c:\AI image site"

# Initialize git
git init
git add .
git commit -m "Initial Picly deployment"

# Connect to GitHub (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/picly.git
git branch -M main
git push -u origin main
```

If you don't have git installed:
```powershell
winget install Git.Git
```

### Step 3: Deploy on Render.com
1. Go to https://dashboard.render.com
2. Click **"New +"** → **"Web Service"**
3. Click **"Connect account"** for GitHub
4. Select your `picly` repository
5. Configure:
   - **Name**: picly
   - **Region**: Oregon (or closest to UK)
   - **Branch**: main
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn rootAI:app`
   - **Instance Type**: Free (or Starter $7/month for better performance)

6. Click **"Advanced"** and add Environment Variables:
   - `OPENAI_API_KEY` = your-key-here (get from OpenAI)
   - `PORT` = 5000

7. Click **"Create Web Service"**

### Step 4: Wait for Deployment
- Takes 5-10 minutes
- Watch the logs
- When done, you'll get a URL like: `https://picly.onrender.com`

### Step 5: Test Your Site
- Visit the Render URL
- Try generating an image
- If it works, proceed to connect your domain!

### Step 6: Connect picly.co.uk
1. In Render dashboard, go to your service
2. Click **"Settings"** → **"Custom Domains"**
3. Click **"Add Custom Domain"**
4. Enter: `picly.co.uk`
5. Render will show you DNS records

6. In IONOS:
   - Go to DNS settings
   - Add CNAME record:
     - Name: `www`
     - Value: `picly.onrender.com`
   - Add A records Render provides

7. Wait 5-30 minutes for DNS propagation

### Step 7: Enable SSL (HTTPS)
- Render does this automatically
- Your site will be: `https://picly.co.uk`

## Get OpenAI API Key:
1. Go to https://platform.openai.com/api-keys
2. Sign up / Log in
3. Click "Create new secret key"
4. Copy the key (starts with sk-...)
5. Add $5-10 credit at https://platform.openai.com/account/billing

## Cost Estimate:
- Render hosting: Free (or $7/month Starter)
- OpenAI API: ~$0.04 per image
- 100 images/day = $4/day = $120/month
- 1000 images/day = $40/day = $1200/month

## Alternative: Add Rate Limiting
To control costs, limit users to 5 images/day for free users.

Need help with any step? Let me know!
