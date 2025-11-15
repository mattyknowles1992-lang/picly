# ✅ YOUR TO-DO CHECKLIST

## 🎯 Complete These Steps to Launch Monetization

### **1. Create Stripe Account** ⏱️ 10 minutes
- [ ] Go to https://stripe.com/register
- [ ] Complete signup (use your email)
- [ ] Verify identity (may take 1-2 business days)
- [ ] Enable your account

### **2. Get Stripe API Keys** ⏱️ 5 minutes
- [ ] Dashboard → Developers → API Keys
- [ ] Copy **Publishable Key** (pk_test_XXXX for testing)
- [ ] Copy **Secret Key** (sk_test_XXXX for testing)
- [ ] Save these keys somewhere safe

### **3. Setup Stripe Webhook** ⏱️ 3 minutes
- [ ] Dashboard → Developers → Webhooks
- [ ] Click "Add endpoint"
- [ ] URL: `https://picly.onrender.com/api/stripe/webhook`
- [ ] Events: Select `checkout.session.completed`
- [ ] Copy **Webhook Secret** (whsec_XXXX)

### **4. Get Replicate API Key** ⏱️ 3 minutes
- [ ] Go to https://replicate.com/account/api-tokens
- [ ] Sign up/Login
- [ ] Create new token
- [ ] Copy token (r8_XXXX)
- [ ] **Free $10 credit included!**

### **5. Add Keys to Render** ⏱️ 5 minutes
- [ ] Go to https://dashboard.render.com
- [ ] Select your Picly web service
- [ ] Click "Environment"
- [ ] Add each key as environment variable:

```
REPLICATE_API_KEY=r8_XXXXXXXXXXXXXX
STRIPE_SECRET_KEY=sk_test_XXXXXXXXXXXXXX
STRIPE_PUBLISHABLE_KEY=pk_test_XXXXXXXXXXXXXX
STRIPE_WEBHOOK_SECRET=whsec_XXXXXXXXXXXXXX
```

- [ ] Click "Save Changes" (Render will auto-redeploy)

### **6. Optional: Get OpenAI Key** ⏱️ 5 minutes
*(Only needed if you want DALL-E 3 premium tier)*

- [ ] Go to https://platform.openai.com/api-keys
- [ ] Create new secret key
- [ ] Copy key (sk-XXXXXX)
- [ ] Add $10 credit at https://platform.openai.com/settings/organization/billing
- [ ] Add to Render:
```
OPENAI_API_KEY=sk-XXXXXXXXXXXXXX
```

### **7. Test Payment Flow** ⏱️ 10 minutes
- [ ] Visit your deployed site
- [ ] Register a test account
- [ ] Try generating with free tier (Flux Dev)
- [ ] Click "Buy Credits"
- [ ] Use Stripe test card: `4242 4242 4242 4242`
- [ ] Expiry: Any future date, CVC: 123
- [ ] Complete purchase
- [ ] Check if credits appear
- [ ] Generate with premium tier
- [ ] Check Stripe dashboard for payment

### **8. Switch to Live Mode** ⏱️ 3 minutes
*(After testing works)*

- [ ] Stripe Dashboard → Toggle "Live Mode"
- [ ] Copy LIVE keys (pk_live_, sk_live_)
- [ ] Update Render environment variables with LIVE keys
- [ ] Remove TEST keys
- [ ] Test one real payment ($0.80 minimum)
- [ ] Done! 🎉

---

## 📊 WHAT'S ALREADY DONE FOR YOU

✅ Complete database with credit system
✅ User authentication
✅ Stripe payment integration
✅ Webhook handlers
✅ Credit checking before generation
✅ Free tier (10 daily credits - Flux Dev)
✅ Premium tier (DALL-E 3 HD)
✅ Referral system (10 credits per referral)
✅ Achievement system (60 bonus credits)
✅ Daily credit reset
✅ Transaction logging
✅ All backend code complete

---

## 💰 PRICING SUMMARY

**Free Tier:**
- 10 credits/day
- Flux Dev (9.0/10 quality)
- Your cost: $0.03/day per user

**Premium Packages:**
- Starter: 10 credits = $0.80 (50% profit)
- Popular: 50 credits = $3.50 (43% profit)
- Pro: 100 credits = $6.00 (33% profit)
- Creator: 500 credits = $25 (20% profit)

**Your Costs:**
- Replicate: $0.003 per free image
- OpenAI: $0.04 per premium image (charged ONLY when user has paid)
- Render: $9/month
- Stripe: 2.9% + $0.30 per transaction

**Profit Example (100 paid users):**
- Revenue: $360
- Costs: $104
- **Profit: $256/month** (71% margin)

---

## 🎯 ESTIMATED TIME TO COMPLETE

**Total: 40-60 minutes** (excluding Stripe verification wait time)

- Stripe signup: 10 min
- Get API keys: 8 min
- Add to Render: 5 min
- Testing: 15 min
- Going live: 3 min
- **Reading docs: 10 min**

---

## 🚨 COMMON ISSUES & FIXES

### "Stripe not configured" error
✅ Make sure keys are added to Render environment variables
✅ Redeploy after adding keys
✅ Check for typos in key names

### "Invalid session" error
✅ Make sure user is logged in
✅ Clear cookies and try again
✅ Check database.py is properly updated

### Webhook not working
✅ URL must be: `https://picly.onrender.com/api/stripe/webhook`
✅ Must select `checkout.session.completed` event
✅ Webhook secret must match in Render

### Credits not deducting
✅ Check Render logs for errors
✅ Verify database tables were created
✅ Test /api/credits/balance endpoint

---

## 📞 NEED HELP?

Read the full guide: `MONETIZATION_SETUP.md`

**Quick Links:**
- Stripe Testing: https://stripe.com/docs/testing
- Replicate Docs: https://replicate.com/docs
- Render Logs: Your dashboard → Logs tab

---

## 🎉 YOU'RE ALMOST THERE!

Once you complete the checklist above, your site will be:

✅ Accepting real payments
✅ Generating passive income
✅ Scaling automatically
✅ Profitable from day one

**Start with Step 1: Create Stripe Account** 🚀

Good luck! You've got this! 💪
