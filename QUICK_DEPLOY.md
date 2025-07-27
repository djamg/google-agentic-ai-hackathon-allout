# ⚡ Quick Deploy - Bangalore Buzz

**Want to deploy ASAP?** Follow these steps:

## 🚀 **Option 1: App Engine (Easiest)**

```bash
# 1. Setup environment
cp env_template.txt .env
# Edit .env with your values

# 2. Download service account key as key1.json

# 3. Deploy
./deploy_app_engine.sh
```

## 🐳 **Option 2: Cloud Run (Advanced)**

```bash
# 1. Setup environment (same as above)
cp env_template.txt .env

# 2. Deploy  
./deploy_cloud_run.sh
```

## 📝 **Required .env Values**

```env
GEMINI_API_KEY=your_gemini_api_key
GOOGLE_CLOUD_PROJECT_ID=your-project-id  
GOOGLE_CLOUD_STORAGE_BUCKET=your-bucket-name
GOOGLE_APPLICATION_CREDENTIALS=./key1.json
```

## ✅ **Before Deploying**

- [ ] Google Cloud project created
- [ ] Billing enabled
- [ ] `gcloud` CLI installed
- [ ] Service account with Storage Admin + Firestore User roles
- [ ] APIs enabled: App Engine/Cloud Run, Storage, Firestore

## 🔗 **Need Help?**

👉 **Full Guide**: See `DEPLOYMENT_GUIDE.md`  
👉 **Google Cloud Setup**: See `GOOGLE_CLOUD_SETUP.md`  
👉 **Troubleshooting**: Run `python setup_google_cloud.py`

---
**Deployment time:** ~5-10 minutes 🕐 