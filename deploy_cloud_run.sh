#!/bin/bash

# Bangalore Buzz - Google Cloud Run Deployment Script
# This script builds and deploys the application to Google Cloud Run

set -e  # Exit on any error

echo "🏙️ Bangalore Buzz - Cloud Run Deployment"
echo "========================================"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI is not installed"
    echo "Please install: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed"
    echo "Please install: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found"
    echo "Please create .env file from env_template.txt"
    exit 1
fi

# Load environment variables
source .env

# Validate required environment variables
if [ -z "$GOOGLE_CLOUD_PROJECT_ID" ]; then
    echo "❌ Error: GOOGLE_CLOUD_PROJECT_ID not set in .env"
    exit 1
fi

# Configuration
SERVICE_NAME="bangalore-buzz"
REGION="us-central1"
IMAGE_NAME="gcr.io/$GOOGLE_CLOUD_PROJECT_ID/$SERVICE_NAME"

echo "🔧 Configuration:"
echo "📋 Project ID: $GOOGLE_CLOUD_PROJECT_ID"
echo "🏷️ Service Name: $SERVICE_NAME"
echo "🌍 Region: $REGION"
echo "🐳 Image: $IMAGE_NAME"

# Set the project
gcloud config set project $GOOGLE_CLOUD_PROJECT_ID

# Enable required APIs
echo "🔌 Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Build the Docker image
echo "🏗️ Building Docker image..."
gcloud builds submit --tag $IMAGE_NAME

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars FLASK_ENV=production \
    --set-env-vars GOOGLE_CLOUD_PROJECT_ID=$GOOGLE_CLOUD_PROJECT_ID \
    --set-env-vars GOOGLE_CLOUD_STORAGE_BUCKET=$GOOGLE_CLOUD_STORAGE_BUCKET \
    --set-env-vars GEMINI_API_KEY=$GEMINI_API_KEY \
    --memory 2Gi \
    --cpu 2 \
    --max-instances 10 \
    --timeout 300

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)')

echo ""
echo "✅ Deployment successful!"
echo "🌐 Your app is live at: $SERVICE_URL"
echo ""
echo "📊 Useful commands:"
echo "  View logs: gcloud run logs tail --service=$SERVICE_NAME --region=$REGION"
echo "  Update service: ./deploy_cloud_run.sh"
echo "  Delete service: gcloud run services delete $SERVICE_NAME --region=$REGION"
echo ""
echo "🔧 Service details:"
echo "  gcloud run services describe $SERVICE_NAME --region=$REGION" 