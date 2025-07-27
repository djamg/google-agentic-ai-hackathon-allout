# 🚀 Bangalore Buzz - Google Cloud Deployment Guide

This guide provides step-by-step instructions to deploy your Bangalore Buzz application to Google Cloud using either **App Engine** (recommended for beginners) or **Cloud Run** (recommended for advanced users).

## 📋 Pre-Deployment Checklist

### ✅ **1. Prerequisites**
- [ ] Google Cloud account with billing enabled
- [ ] `gcloud` CLI installed ([Install Guide](https://cloud.google.com/sdk/docs/install))
- [ ] Docker installed (for Cloud Run deployment)
- [ ] Git repository ready

### ✅ **2. Environment Setup**
- [ ] `.env` file configured (copy from `env_template.txt`)
- [ ] Service account key downloaded as `key1.json`
- [ ] All required APIs enabled (Storage, Firestore, etc.)

### ✅ **3. Test Locally First**
```bash
# Install dependencies
pip install -r requirements.txt

# Test the application
python app.py

# Verify at http://localhost:5500
```

---

## 🎯 **Option 1: Google App Engine Deployment (Recommended)**

### **Why App Engine?**
✅ **Fully managed** - No infrastructure management  
✅ **Auto-scaling** - Handles traffic spikes automatically  
✅ **Built-in load balancing**  
✅ **Integrated monitoring**  
✅ **Easy SSL certificates**  

### **Step-by-Step Deployment**

#### **1. Prepare Your Environment**
```bash
# Create .env file from template
cp env_template.txt .env

# Edit .env with your actual values
nano .env
```

Required `.env` variables:
```env
GEMINI_API_KEY=your_actual_gemini_api_key
GOOGLE_CLOUD_PROJECT_ID=your-project-id
GOOGLE_CLOUD_STORAGE_BUCKET=your-bucket-name
GOOGLE_APPLICATION_CREDENTIALS=./key1.json
```

#### **2. Download Service Account Key**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **IAM & Admin** → **Service Accounts**
3. Create or select your service account
4. Click **Keys** → **Add Key** → **JSON**
5. Save as `key1.json` in your project root

#### **3. Deploy with Automated Script**
```bash
# Make script executable (if not already)
chmod +x deploy_app_engine.sh

# Deploy to App Engine
./deploy_app_engine.sh
```

#### **4. Manual Deployment (Alternative)**
```bash
# Set your project
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable appengine.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# Create App Engine app (first time only)
gcloud app create --region=us-central1

# Deploy the application
gcloud app deploy app.yaml

# Open in browser
gcloud app browse
```

---

## 🐳 **Option 2: Google Cloud Run Deployment (Advanced)**

### **Why Cloud Run?**
✅ **Containerized** - Full control over the runtime  
✅ **Pay-per-use** - Only pay when requests are served  
✅ **Custom domains** easily  
✅ **Regional deployment**  
✅ **Better for microservices**  

### **Step-by-Step Deployment**

#### **1. Prepare Environment (Same as App Engine)**
```bash
cp env_template.txt .env
# Edit .env with your values
```

#### **2. Deploy with Automated Script**
```bash
# Make script executable (if not already)
chmod +x deploy_cloud_run.sh

# Deploy to Cloud Run
./deploy_cloud_run.sh
```

#### **3. Manual Deployment (Alternative)**
```bash
# Set project and enable APIs
gcloud config set project YOUR_PROJECT_ID
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com

# Build and submit the container
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/bangalore-buzz

# Deploy to Cloud Run
gcloud run deploy bangalore-buzz \
    --image gcr.io/YOUR_PROJECT_ID/bangalore-buzz \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars FLASK_ENV=production \
    --set-env-vars GOOGLE_CLOUD_PROJECT_ID=YOUR_PROJECT_ID \
    --memory 2Gi \
    --max-instances 10
```

---

## 🔧 **Environment Variables for Production**

Add these to your cloud deployment:

```env
# Required
FLASK_ENV=production
GOOGLE_CLOUD_PROJECT_ID=your-project-id
GOOGLE_CLOUD_STORAGE_BUCKET=your-bucket-name
GEMINI_API_KEY=your-gemini-api-key

# Optional  
PORT=8080
PYTHON_ENV=production
```

---

## 📊 **Post-Deployment Verification**

### **1. Health Check**
```bash
# Replace YOUR_APP_URL with your actual deployment URL
curl https://YOUR_APP_URL/health
```

Expected response:
```json
{
  "status": "healthy",
  "environment": "production",
  "google_cloud": "enabled"
}
```

### **2. Test Core Functionality**
```bash
# Test chat endpoint
curl -X POST https://YOUR_APP_URL/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'

# Test file upload (with a sample image)
curl -X POST https://YOUR_APP_URL/report/trash \
  -F "image=@garbage_sample.jpg"
```

### **3. Verify Integrations**
- [ ] **Firestore**: Reports are being stored
- [ ] **Cloud Storage**: Images are being uploaded
- [ ] **Gemini AI**: AI responses are working
- [ ] **Frontend**: Web interface loads correctly

---

## 🚨 **Troubleshooting Common Issues**

### **1. "Application failed to start"**
```bash
# Check logs
gcloud app logs tail -s default          # App Engine logs
gcloud run logs tail --service=bangalore-buzz  # Cloud Run logs
```

**Common fixes:**
- Verify all environment variables are set
- Check service account permissions
- Ensure all required APIs are enabled

### **2. "Permission denied" errors**
- Verify service account has required roles:
  - **Storage Admin**
  - **Cloud Datastore User**
  - **Service Account User**

### **3. "Module not found" errors**
- Check `requirements.txt` has all dependencies
- Verify Python version compatibility (Python 3.9+)

### **4. "Firestore connection failed"**
```bash
# Test Firestore connectivity
python setup_google_cloud.py
```

### **5. Image upload issues**
- Verify bucket exists and is publicly accessible
- Check CORS settings on the bucket
- Ensure service account has Storage Admin role

---

## 🔐 **Security Best Practices**

### **1. Environment Variables**
- ✅ Never commit `.env` files to version control
- ✅ Use Google Secret Manager for sensitive data in production
- ✅ Rotate API keys regularly

### **2. Firestore Security Rules**
```javascript
// Production Firestore rules
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /citizen_reports/{document} {
      allow read, write: if request.auth != null;
    }
  }
}
```

### **3. Cloud Storage Security**
- Enable uniform bucket-level access
- Set appropriate IAM policies
- Consider signed URLs for sensitive content

---

## 📈 **Monitoring and Maintenance**

### **1. Set up Monitoring**
```bash
# Enable logging
gcloud services enable logging.googleapis.com

# View application logs
gcloud logging read "resource.type=gae_app" --limit 50
```

### **2. Performance Monitoring**
- Set up **Cloud Monitoring** dashboards
- Configure **Error Reporting**
- Enable **Cloud Trace** for request tracing

### **3. Regular Updates**
```bash
# Update dependencies
pip list --outdated
pip install -r requirements.txt --upgrade

# Redeploy
./deploy_app_engine.sh  # or ./deploy_cloud_run.sh
```

---

## 📞 **Support and Resources**

### **Useful Commands**
```bash
# View App Engine versions
gcloud app versions list

# Delete old versions
gcloud app versions delete VERSION_ID

# View Cloud Run services
gcloud run services list

# Scale Cloud Run service
gcloud run services update bangalore-buzz --max-instances=20
```

### **Documentation Links**
- [Google App Engine Documentation](https://cloud.google.com/appengine/docs)
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Flask Deployment Guide](https://flask.palletsprojects.com/en/2.3.x/deploying/)
- [Google Cloud SDK Reference](https://cloud.google.com/sdk/gcloud/reference)

### **Cost Optimization**
- **App Engine**: Use automatic scaling with appropriate instance classes
- **Cloud Run**: Set appropriate CPU and memory limits
- **Storage**: Use lifecycle policies to delete old images
- **Firestore**: Monitor read/write operations

---

## ✅ **Deployment Checklist**

- [ ] **Environment configured** (`.env` file)
- [ ] **Service account key** downloaded (`key1.json`)
- [ ] **APIs enabled** (App Engine/Cloud Run, Storage, Firestore)
- [ ] **Dependencies installed** (`requirements.txt`)
- [ ] **Local testing** completed
- [ ] **Deployment script** executed successfully
- [ ] **Health check** passed
- [ ] **Core functionality** tested
- [ ] **Monitoring** set up
- [ ] **Security rules** configured

---

🎉 **Congratulations!** Your Bangalore Buzz application is now live on Google Cloud!

**Next Steps:**
1. Test all features thoroughly
2. Set up monitoring and alerts
3. Configure custom domain (optional)
4. Implement CI/CD pipeline (optional)
5. Set up backup strategies

For support, refer to the troubleshooting section or check the Google Cloud documentation. 