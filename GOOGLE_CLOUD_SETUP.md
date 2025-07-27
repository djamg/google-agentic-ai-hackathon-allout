# Google Cloud Setup Guide for Bangalore Buzz

This guide will help you set up Google Cloud Storage and Firestore for storing images and report metadata.

## 🔧 Quick Setup Steps

### 1. Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "New Project" or select an existing project
3. Note your **Project ID** (you'll need this)

### 2. Enable Required APIs
```bash
# Enable Cloud Storage API
gcloud services enable storage.googleapis.com

# Enable Firestore API  
gcloud services enable firestore.googleapis.com
```

Or enable via the console:
- Go to "APIs & Services" → "Library"
- Search and enable: "Cloud Storage API"
- Search and enable: "Firestore API"

### 3. Create Service Account
1. Go to "IAM & Admin" → "Service Accounts"
2. Click "Create Service Account"
3. Name: `bangalore-buzz-service`
4. Add these roles:
   - **Storage Admin** (for uploading images)
   - **Cloud Datastore User** (for Firestore)
5. Click "Create Key" → "JSON"
6. Save the downloaded JSON file as `key.json` in your project root

### 4. Create Cloud Storage Bucket
```bash
# Create bucket (replace YOUR_BUCKET_NAME)
gsutil mb gs://your-bucket-name

# Make bucket publicly readable (for image access)
gsutil iam ch allUsers:objectViewer gs://your-bucket-name
```

Or via console:
- Go to "Cloud Storage" → "Buckets"
- Click "Create Bucket"
- Choose a unique name
- Select region (preferably close to your users)
- Set access control to "Uniform"

### 5. Initialize Firestore
1. Go to "Firestore Database"
2. Click "Create Database"
3. Choose "Native Mode"
4. Select your preferred region
5. Set security rules (start with test mode for development)

### 6. Configure Environment Variables
Create a `.env` file in your project root:

```bash
# Copy from template
cp env_template.txt .env
```

Edit `.env` with your actual values:
```env
GEMINI_API_KEY=your_actual_gemini_api_key
GOOGLE_CLOUD_PROJECT_ID=your-actual-project-id
GOOGLE_CLOUD_STORAGE_BUCKET=your-actual-bucket-name
GOOGLE_APPLICATION_CREDENTIALS=./key.json
```

## 🧪 Test the Setup

After configuration, restart your Flask app and test:

```bash
# Test trash reporting with image upload
curl -X POST -F 'image=@garbage_sample.jpg' http://localhost:5500/report/trash
```

**Expected Success Indicators:**
- `"image_storage": "google_cloud_storage"` (not "local_temporary")
- `"firestore_id": "some-document-id"` in response
- Image URL starting with `https://storage.googleapis.com/`

## 🔍 Troubleshooting

### Common Issues:

1. **"key.json not found"**
   - Ensure the JSON key file is in your project root
   - Check the file path in `GOOGLE_APPLICATION_CREDENTIALS`

2. **"Permission denied"**
   - Verify service account has correct roles
   - Check if APIs are enabled

3. **"Bucket not found"**
   - Verify bucket name in `.env` matches actual bucket
   - Ensure bucket exists and is accessible

4. **"Firestore permission denied"**
   - Check Firestore security rules
   - Verify service account has Datastore User role

### Debug Commands:
```bash
# Check if credentials file exists
ls -la key.json

# Test Google Cloud authentication
gcloud auth list

# Verify project configuration
gcloud config list
```

## 📊 Verification Checklist

✅ **Google Cloud Project created**  
✅ **APIs enabled** (Storage + Firestore)  
✅ **Service Account created** with proper roles  
✅ **key.json downloaded** and placed in project root  
✅ **Storage Bucket created** and publicly accessible  
✅ **Firestore Database initialized**  
✅ **.env file configured** with actual values  
✅ **Flask app restarted** after configuration  

## 🚀 Expected Results

After proper setup:
- **Images**: Uploaded to Google Cloud Storage with persistent URLs
- **Metadata**: Stored in Firestore with report tracking
- **API Response**: Shows `"image_storage": "google_cloud_storage"`
- **Report IDs**: Firestore document IDs for tracking reports

## 💡 Development vs Production

### Development:
- Use test mode for Firestore security rules
- Single region bucket is fine
- Service account key file approach

### Production:
- Configure proper Firestore security rules
- Use multi-region buckets for better performance
- Consider using IAM roles instead of service account keys
- Enable logging and monitoring

---

🔗 **Useful Links:**
- [Google Cloud Console](https://console.cloud.google.com/)
- [Cloud Storage Documentation](https://cloud.google.com/storage/docs)
- [Firestore Documentation](https://firebase.google.com/docs/firestore)
- [Service Accounts Guide](https://cloud.google.com/iam/docs/service-accounts) 