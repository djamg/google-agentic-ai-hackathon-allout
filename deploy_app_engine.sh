#!/bin/bash

# Bangalore Buzz - Google App Engine Deployment Script
# This script deploys the application to Google App Engine

set -e  # Exit on any error

echo "🏙️ Bangalore Buzz - App Engine Deployment"
echo "=========================================="

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI is not installed"
    echo "Please install: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found"
    echo "Please create .env file from env_template.txt"
    exit 1
fi

# Check if service account key exists
if [ ! -f "key1.json" ]; then
    echo "❌ Error: Service account key (key1.json) not found"
    echo "Please download your service account key from Google Cloud Console"
    exit 1
fi

# Load environment variables
source .env

# Validate required environment variables
if [ -z "$GOOGLE_CLOUD_PROJECT_ID" ]; then
    echo "❌ Error: GOOGLE_CLOUD_PROJECT_ID not set in .env"
    exit 1
fi

echo "🔧 Preparing deployment..."
echo "📋 Project ID: $GOOGLE_CLOUD_PROJECT_ID"

# Set the project
gcloud config set project $GOOGLE_CLOUD_PROJECT_ID

# Enable required APIs
echo "🔌 Enabling required APIs..."
gcloud services enable appengine.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# Create App Engine app if it doesn't exist
if ! gcloud app describe --quiet > /dev/null 2>&1; then
    echo "🏗️ Creating App Engine app..."
    gcloud app create --region=us-central1
fi

# Deploy the application
echo "🚀 Deploying to App Engine..."
gcloud app deploy app.yaml --quiet

# Get the URL
APP_URL=$(gcloud app describe --format="value(defaultHostname)")

echo ""
echo "✅ Deployment successful!"
echo "🌐 Your app is live at: https://$APP_URL"
echo ""
echo "📊 Useful commands:"
echo "  View logs: gcloud app logs tail -s default"
echo "  Open browser: gcloud app browse"
echo "  View versions: gcloud app versions list"
echo ""
echo "🔧 To update:"
echo "  Just run this script again: ./deploy_app_engine.sh" 