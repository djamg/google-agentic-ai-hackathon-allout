import requests
import json
import io
import time

# Configuration
API_BASE_URL = "http://localhost:5500"


def test_health_check():
    """Test the health check endpoint."""
    print("1. Testing health check endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")


def test_api_documentation():
    """Test the API documentation endpoint."""
    print("\n2. Testing API documentation endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/")
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Service: {data.get('service')}")
        print(f"Endpoints: {list(data.get('endpoints', {}).keys())}")
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")


def test_chat_endpoint():
    """Test the chat endpoint."""
    print("\n3. Testing chat endpoint...")

    # Test with valid message
    try:
        data = {"message": "Hello, what can you help me with?"}
        response = requests.post(f"{API_BASE_URL}/chat", json=data)
        print(f"Chat with message - Status: {response.status_code}")
        print(f"Response excerpt: {str(response.json())[:200]}...")
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")

    # Test without message
    try:
        response = requests.post(f"{API_BASE_URL}/chat", json={})
        print(f"Chat without message - Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")


def test_analyze_endpoint():
    """Test the general analyze endpoint."""
    print("\n4. Testing analyze endpoint...")

    # Test with text-only query
    try:
        data = {"query": "I want to know about traffic in Bengaluru"}
        response = requests.post(f"{API_BASE_URL}/analyze", data=data)
        print(f"Text-only query - Status: {response.status_code}")
        print(f"Response excerpt: {str(response.json())[:200]}...")
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")

    # Test with query and dummy image
    try:
        dummy_image = io.BytesIO(b"fake image content")
        files = {"image": ("test.jpg", dummy_image, "image/jpeg")}
        data = {"query": "Analyze this image for issues"}
        response = requests.post(f"{API_BASE_URL}/analyze", files=files, data=data)
        print(f"With image - Status: {response.status_code}")
        print(f"Response excerpt: {str(response.json())[:200]}...")
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")


def test_trash_reporting():
    """Test trash reporting endpoint."""
    print("\n5. Testing trash reporting endpoint...")

    # Test without image
    try:
        response = requests.post(f"{API_BASE_URL}/report/trash")
        print(f"Without image - Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")

    # Test with dummy image data
    try:
        dummy_image = io.BytesIO(b"fake image content")
        files = {"image": ("trash.jpg", dummy_image, "image/jpeg")}
        data = {"description": "Garbage pile on street"}
        response = requests.post(f"{API_BASE_URL}/report/trash", files=files, data=data)
        print(f"With dummy image - Status: {response.status_code}")
        print(f"Response excerpt: {str(response.json())[:200]}...")
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")


def test_pothole_reporting():
    """Test pothole reporting endpoint."""
    print("\n6. Testing pothole reporting endpoint...")

    # Test without image
    try:
        response = requests.post(f"{API_BASE_URL}/report/pothole")
        print(f"Without image - Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")

    # Test with dummy image data
    try:
        dummy_image = io.BytesIO(b"fake image content")
        files = {"image": ("pothole.jpg", dummy_image, "image/jpeg")}
        data = {"description": "Large pothole on main road"}
        response = requests.post(
            f"{API_BASE_URL}/report/pothole", files=files, data=data
        )
        print(f"With dummy image - Status: {response.status_code}")
        print(f"Response excerpt: {str(response.json())[:200]}...")
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")


def test_electricity_reporting():
    """Test electricity/street light reporting endpoint."""
    print("\n7. Testing electricity reporting endpoint...")

    # Test without image
    try:
        response = requests.post(f"{API_BASE_URL}/report/electricity")
        print(f"Without image - Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")

    # Test with dummy image data
    try:
        dummy_image = io.BytesIO(b"fake image content")
        files = {"image": ("streetlight.jpg", dummy_image, "image/jpeg")}
        data = {"description": "Street light not working"}
        response = requests.post(
            f"{API_BASE_URL}/report/electricity", files=files, data=data
        )
        print(f"With dummy image - Status: {response.status_code}")
        print(f"Response excerpt: {str(response.json())[:200]}...")
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")


def test_error_handling():
    """Test error handling."""
    print("\n8. Testing error handling...")

    # Test non-existent endpoint
    try:
        response = requests.get(f"{API_BASE_URL}/nonexistent")
        print(f"Non-existent endpoint - Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")

    # Test unsupported method
    try:
        response = requests.delete(f"{API_BASE_URL}/health")
        print(f"Unsupported method - Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")


def main():
    """Run all tests."""
    print("🧪 BANGALORE BUZZ API TESTING")
    print("=" * 40)
    print(f"Testing API at: {API_BASE_URL}")
    print("=" * 40)

    # Run all tests
    test_health_check()
    test_api_documentation()
    test_chat_endpoint()
    test_analyze_endpoint()
    test_trash_reporting()
    test_pothole_reporting()
    test_electricity_reporting()
    test_error_handling()

    print("\n" + "=" * 40)
    print("✅ All tests completed!")
    print("=" * 40)
    print("\n💡 Notes:")
    print("- Tests with dummy images will likely fail image processing")
    print("- For real testing, use actual images with GPS data")
    print("- Check server logs for detailed error information")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️ Testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Testing failed with error: {e}")
