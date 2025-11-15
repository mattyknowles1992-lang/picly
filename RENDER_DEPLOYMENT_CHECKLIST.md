# Picly Deployment Checklist - Render.com

## ✅ Pre-Deployment Complete
- [x] Code optimized for quality (HD mode, vivid style)
- [x] Code pushed to GitHub
- [x] Quality settings at industry best practices

## 🚀 Render.com Deployment Steps

### Step 1: Create Web Service
1. Go to https://dashboard.render.com
2. Click **"New +"** → **"Web Service"**
3. Connect GitHub and select `mattyknowles1992-lang/picly`

### Step 2: Configure Service
**Basic Settings:**
- Name: `picly`
- Region: **Frankfurt** (closest to UK)
- Branch: `main`
- Runtime: **Python 3**

**Build & Deploy:**
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn rootAI:app --bind 0.0.0.0:$PORT`

**Instance Type:**
- Select: **Starter** ($7/month)
- Why: Better performance, no cold starts

### Step 3: Environment Variables
Click **"Advanced"** → **"Add Environment Variable"**

Add these (leave OPENAI_API_KEY empty for now):
```
PORT = 5000
OPENAI_API_KEY = (add after getting key)
```

### Step 4: Deploy
1. Click **"Create Web Service"**
2. Wait 5-10 minutes for build
3. Watch logs for "Server running"
4. Note your URL: `https://picly.onrender.com`

### Step 5: Get OpenAI API Key
1. Go to https://platform.openai.com/signup
2. Sign up / Log in
3. Go to https://platform.openai.com/api-keys
4. Click **"Create new secret key"**
5. Name it "Picly Production"
6. Copy the key (starts with `sk-proj-...`)

### Step 6: Add Billing to OpenAI
1. Go to https://platform.openai.com/account/billing
2. Click **"Add payment method"**
3. Add credit card
4. **Add credit**: $10 (will last ~250 images)
5. Set spending limit: $50/month

### Step 7: Add API Key to Render
1. Back in Render dashboard
2. Go to your `picly` service
3. Click **"Environment"**
4. Edit `OPENAI_API_KEY` variable
5. Paste your OpenAI key
6. Click **"Save Changes"**
7. Service will auto-redeploy

### Step 8: Test Your Site
1. Visit `https://picly.onrender.com`
2. Enter prompt: "a beautiful sunset over mountains, photorealistic"
3. Click Generate
4. Should take 15-20 seconds
5. Image should appear in HD quality!

### Step 9: Connect Custom Domain (picly.co.uk)

**In Render:**
1. Go to your service → **"Settings"**
2. Scroll to **"Custom Domains"**
3. Click **"Add Custom Domain"**
4. Enter: `picly.co.uk`
5. Also add: `www.picly.co.uk`
6. Render will show DNS records needed

**In IONOS (your domain registrar):**
1. Go to Domains → picly.co.uk → **DNS**
2. Delete any existing A records
3. Add CNAME record:
   - Type: **CNAME**
   - Name: **www**
   - Points to: `picly.onrender.com`
   - TTL: 3600
4. Add A record (Render will show the IP):
   - Type: **A**
   - Name: **@** (or blank)
   - Points to: [IP from Render]
   - TTL: 3600
5. Save changes

### Step 10: Enable SSL (Automatic)
- Render automatically provisions SSL
- Wait 5-30 minutes after DNS setup
- Your site will be: `https://picly.co.uk` ✅

## 📊 Post-Deployment Checks

### Test These Features:
- [ ] Homepage loads at picly.co.uk
- [ ] Logo displays correctly
- [ ] Generate image works (DALL-E 3)
- [ ] Quality Boost toggle works
- [ ] Different aspect ratios work
- [ ] Style selector works
- [ ] Prompt library works
- [ ] Image download works
- [ ] Mobile responsive

### Monitor These:
- [ ] OpenAI API usage: https://platform.openai.com/usage
- [ ] Render metrics: Check CPU/Memory
- [ ] Domain propagation: https://dnschecker.org

## 💰 Cost Tracking

**Monthly Costs:**
- Render Starter: $7
- OpenAI API: ~$0.04 per image
  - 100 images = $4
  - 500 images = $20
  - 1000 images = $40

**Set Budget Alerts:**
1. OpenAI: Set limit at $50/month
2. Render: Fixed $7/month

## 🚨 Troubleshooting

### If build fails:
- Check logs in Render dashboard
- Ensure requirements.txt is correct
- Verify Python version compatibility

### If images don't generate:
- Check OpenAI API key is set
- Verify billing is active in OpenAI
- Check API usage limits

### If domain doesn't connect:
- Wait 1 hour for DNS propagation
- Use https://dnschecker.org to verify
- Check IONOS DNS settings match Render

## ✅ Success Criteria

You're done when:
- ✅ Site loads at https://picly.co.uk
- ✅ Images generate in 15-20 seconds
- ✅ Images are HD quality (1024x1024+)
- ✅ SSL shows green padlock
- ✅ All features work on mobile

---

**Need help?** Check the logs in Render dashboard or OpenAI usage page.

**Current Status:** Ready to deploy! Follow steps 1-10 above.
