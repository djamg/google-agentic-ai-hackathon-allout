#!/usr/bin/env python3
"""
Google Cloud Setup Validation Script for Bangalore Buzz
Run this script to check your Google Cloud configuration.
"""

import os
import json
from dotenv import load_dotenv


def check_environment_setup():
    """Check if environment variables are properly configured"""

    print("🔍 CHECKING GOOGLE CLOUD CONFIGURATION")
    print("=" * 60)

    # Load environment variables
    load_dotenv()

    # Required environment variables
    required_vars = {
        "GEMINI_API_KEY": "Gemini API key for AI processing",
        "GOOGLE_CLOUD_PROJECT_ID": "Google Cloud Project ID",
        "GOOGLE_CLOUD_STORAGE_BUCKET": "Cloud Storage bucket name",
        "GOOGLE_APPLICATION_CREDENTIALS": "Path to service account key file",
    }

    print("\n1. Environment Variables:")
    all_vars_present = True

    for var_name, description in required_vars.items():
        value = os.getenv(var_name)
        if value:
            if var_name == "GEMINI_API_KEY":
                display_value = value[:10] + "..." if len(value) > 10 else value
            else:
                display_value = value
            print(f"   ✅ {var_name}: {display_value}")
        else:
            print(f"   ❌ {var_name}: NOT SET ({description})")
            all_vars_present = False

    return all_vars_present


def check_service_account_key():
    """Check if service account key file exists and is valid"""

    print("\n2. Service Account Key:")

    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not credentials_path:
        print("   ❌ GOOGLE_APPLICATION_CREDENTIALS not set")
        return False

    if not os.path.exists(credentials_path):
        print(f"   ❌ Key file not found: {credentials_path}")
        return False

    try:
        with open(credentials_path, "r") as f:
            key_data = json.load(f)

        required_fields = ["type", "project_id", "private_key", "client_email"]
        missing_fields = [field for field in required_fields if field not in key_data]

        if missing_fields:
            print(f"   ❌ Key file missing fields: {missing_fields}")
            return False

        print(f"   ✅ Key file valid: {credentials_path}")
        print(f"      Project: {key_data.get('project_id')}")
        print(f"      Service Account: {key_data.get('client_email')}")
        return True

    except json.JSONDecodeError:
        print(f"   ❌ Invalid JSON in key file: {credentials_path}")
        return False
    except Exception as e:
        print(f"   ❌ Error reading key file: {e}")
        return False


def test_google_cloud_connection():
    """Test connection to Google Cloud services"""

    print("\n3. Google Cloud Services:")

    try:
        from google.cloud import storage, firestore

        # Test Storage client
        try:
            credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")

            if credentials_path and os.path.exists(credentials_path):
                storage_client = storage.Client.from_service_account_json(
                    credentials_path, project=project_id
                )
            else:
                storage_client = storage.Client(project=project_id)

            # Try to list buckets (minimal permission test)
            bucket_name = os.getenv("GOOGLE_CLOUD_STORAGE_BUCKET")
            bucket = storage_client.bucket(bucket_name)

            # This will fail if bucket doesn't exist or no permissions
            bucket.reload()
            print(f"   ✅ Cloud Storage: Connected to bucket '{bucket_name}'")
            storage_ok = True

        except Exception as e:
            print(f"   ❌ Cloud Storage: {e}")
            storage_ok = False

        # Test Firestore client
        try:
            if credentials_path and os.path.exists(credentials_path):
                firestore_client = firestore.Client.from_service_account_json(
                    credentials_path, project=project_id
                )
            else:
                firestore_client = firestore.Client(project=project_id)

            # Try to access a collection (minimal permission test)
            firestore_client.collection("test").limit(1).get()
            print(f"   ✅ Firestore: Connected to project '{project_id}'")
            firestore_ok = True

        except Exception as e:
            print(f"   ❌ Firestore: {e}")
            firestore_ok = False

        return storage_ok and firestore_ok

    except ImportError:
        print("   ❌ Google Cloud libraries not installed")
        print("      Run: pip install google-cloud-storage google-cloud-firestore")
        return False


def provide_setup_guidance():
    """Provide guidance on how to fix configuration issues"""

    print("\n" + "=" * 60)
    print("🛠️  SETUP GUIDANCE")
    print("=" * 60)

    if not os.path.exists(".env"):
        print("\n📋 Step 1: Create .env file")
        print("   cp env_template.txt .env")
        print("   # Then edit .env with your actual values")

    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "./key.json")
    if not os.path.exists(credentials_path):
        print(f"\n🔑 Step 2: Add service account key")
        print("   1. Go to Google Cloud Console")
        print("   2. IAM & Admin → Service Accounts")
        print("   3. Create service account with these roles:")
        print("      - Storage Admin")
        print("      - Cloud Datastore User")
        print("   4. Create JSON key and save as 'key.json'")

    print(f"\n🗂️  Step 3: Create Cloud Storage bucket")
    print("   1. Go to Cloud Storage in Google Cloud Console")
    print("   2. Create a new bucket with a unique name")
    print("   3. Set access control to 'Uniform'")
    print("   4. Make bucket publicly readable:")
    print("      gsutil iam ch allUsers:objectViewer gs://YOUR_BUCKET_NAME")

    print(f"\n📊 Step 4: Initialize Firestore")
    print("   1. Go to Firestore Database in Google Cloud Console")
    print("   2. Create database in 'Native Mode'")
    print("   3. Choose your preferred region")
    print("   4. Start in test mode for development")

    print(f"\n🔄 Step 5: Restart Flask app")
    print("   After configuration, restart your Flask application")

    print(f"\n📖 For detailed instructions, see: GOOGLE_CLOUD_SETUP.md")


def main():
    """Main setup validation function"""

    env_ok = check_environment_setup()
    key_ok = check_service_account_key() if env_ok else False
    services_ok = test_google_cloud_connection() if key_ok else False

    print("\n" + "=" * 60)
    print("📊 CONFIGURATION STATUS")
    print("=" * 60)

    status_items = [
        ("Environment Variables", "✅" if env_ok else "❌"),
        ("Service Account Key", "✅" if key_ok else "❌"),
        ("Google Cloud Services", "✅" if services_ok else "❌"),
    ]

    for item, status in status_items:
        print(f"   {status} {item}")

    if all([env_ok, key_ok, services_ok]):
        print("\n🎉 CONFIGURATION COMPLETE!")
        print("   Google Cloud Storage and Firestore are ready to use.")
        print("   Restart your Flask app to use cloud storage.")
    else:
        print("\n⚠️  CONFIGURATION INCOMPLETE")
        provide_setup_guidance()


if __name__ == "__main__":
    main()
