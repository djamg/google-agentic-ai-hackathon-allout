#!/usr/bin/env python3
"""
Test script for the Bangalore Buzz frontend interface.
This script starts the server temporarily and tests if the frontend loads correctly.
"""

import subprocess
import time
import requests
import sys
from threading import Thread


def test_frontend():
    """Test the frontend interface"""
    print("🧪 TESTING BANGALORE BUZZ FRONTEND")
    print("=" * 50)

    try:
        # Test frontend endpoint
        print("1. Testing frontend endpoint...")
        response = requests.get("http://localhost:5500/", timeout=10)
        if response.status_code == 200:
            print("   ✅ Frontend loads successfully!")
            print(f"   📄 Response size: {len(response.text)} bytes")

            # Check for key elements
            content = response.text
            if "Bangalore Buzz" in content:
                print("   ✅ Title found in HTML")
            if "chat-messages" in content:
                print("   ✅ Chat interface elements found")
            if "Quick Actions" in content:
                print("   ✅ Quick action buttons found")
            if "style.css" in content:
                print("   ✅ CSS stylesheet linked")

        else:
            print(f"   ❌ Frontend failed to load (Status: {response.status_code})")
            return False

        # Test API info endpoint
        print("\n2. Testing API info endpoint...")
        response = requests.get("http://localhost:5500/api", timeout=10)
        if response.status_code == 200:
            print("   ✅ API info endpoint works!")
            data = response.json()
            print(f"   📊 Service: {data.get('service', 'Unknown')}")
            print(f"   📦 Version: {data.get('version', 'Unknown')}")
        else:
            print(f"   ❌ API info endpoint failed (Status: {response.status_code})")

        # Test health endpoint
        print("\n3. Testing health endpoint...")
        response = requests.get("http://localhost:5500/health", timeout=10)
        if response.status_code == 200:
            print("   ✅ Health endpoint works!")
            data = response.json()
            print(f"   🏥 Status: {data.get('status', 'Unknown')}")
        else:
            print(f"   ❌ Health endpoint failed (Status: {response.status_code})")

        print("\n" + "=" * 50)
        print("✅ FRONTEND TESTING COMPLETED!")
        print("🌐 Open http://localhost:5500 in your browser to use the interface")
        print("=" * 50)
        return True

    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Is it running on http://localhost:5500?")
        print("\n💡 To start the server, run: python app.py")
        return False
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False


def start_server_temporarily():
    """Start the server for testing"""
    print("🚀 Starting server for testing...")
    print("⏳ Please wait while the server initializes...")

    # Give server time to start
    time.sleep(3)

    # Run tests
    success = test_frontend()

    return success


if __name__ == "__main__":
    try:
        # Check if server is already running
        try:
            response = requests.get("http://localhost:5500/health", timeout=2)
            print("🔍 Server is already running!")
            test_frontend()
        except requests.exceptions.ConnectionError:
            print("🔍 Server not running. Please start it manually:")
            print("   1. Run: source venv/bin/activate")
            print("   2. Run: python app.py")
            print("   3. Open: http://localhost:5500")
            print("\n   Then you can test the frontend interface!")

    except KeyboardInterrupt:
        print("\n\n⏹️ Testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Testing failed: {e}")
        sys.exit(1)
