import os
import json
import time
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from dotenv import load_dotenv
import orchestrator
from google.cloud import storage, firestore
import uuid
from datetime import datetime


# --- 1. FLASK APPLICATION CONFIGURATION ---
def create_app():
    """
    Creates and configures the Flask application.
    """
    app = Flask(__name__)

    # Configuration
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size
    app.config["UPLOAD_FOLDER"] = "uploads"
    app.config["ALLOWED_EXTENSIONS"] = {"png", "jpg", "jpeg", "gif"}

    # Create upload directory if it doesn't exist
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    return app


app = create_app()


# --- 2. GOOGLE CLOUD CONFIGURATION ---
def initialize_google_cloud():
    """
    Initialize Google Cloud Storage and Firestore clients.
    """
    try:
        # Load environment variables
        load_dotenv()

        # Get configuration from environment
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
        bucket_name = os.getenv("GOOGLE_CLOUD_STORAGE_BUCKET")
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

        if not all([project_id, bucket_name]):
            print(
                "⚠️ Warning: Google Cloud not fully configured. Using local storage fallback."
            )
            return None, None, None

        # Initialize clients
        if credentials_path and os.path.exists(credentials_path):
            storage_client = storage.Client.from_service_account_json(
                credentials_path, project=project_id
            )
            firestore_client = firestore.Client.from_service_account_json(
                credentials_path, project=project_id
            )
        else:
            # Try using default credentials (if running on GCP)
            storage_client = storage.Client(project=project_id)
            firestore_client = firestore.Client(project=project_id)

        bucket = storage_client.bucket(bucket_name)
        print(f"✅ Google Cloud Storage initialized: {bucket_name}")
        print(f"✅ Firestore initialized: {project_id}")
        return storage_client, bucket, firestore_client

    except Exception as e:
        print(f"⚠️ Warning: Could not initialize Google Cloud services: {e}")
        print("Using local storage fallback.")
        return None, None, None


# Initialize Google Cloud services
gcs_client, gcs_bucket, firestore_db = initialize_google_cloud()


def upload_to_gcs(file, filename):
    """
    Upload file to Google Cloud Storage.

    Args:
        file: File object to upload
        filename: Name for the file in storage

    Returns:
        str: Public URL of uploaded file or None if failed
    """
    if not gcs_bucket:
        return None

    try:
        # Create a unique filename with timestamp and UUID
        timestamp = str(int(time.time()))
        unique_id = str(uuid.uuid4())[:8]
        file_extension = filename.rsplit(".", 1)[1].lower()
        gcs_filename = f"citizen-reports/{timestamp}_{unique_id}.{file_extension}"

        # Upload file to GCS
        blob = gcs_bucket.blob(gcs_filename)
        file.seek(0)  # Reset file pointer
        blob.upload_from_file(file, content_type=f"image/{file_extension}")

        # For uniform bucket-level access, don't set individual object ACLs
        # The bucket should be configured with public access policy
        print(f"[GCS] Uploaded file: {gcs_filename}")

        # Try to return public URL first (if bucket is public)
        try:
            # Return the public URL (works if bucket has public access policy)
            return f"https://storage.googleapis.com/{gcs_bucket.name}/{gcs_filename}"
        except Exception:
            # If public access fails, generate a signed URL (24 hour expiry)
            print("[GCS] Public access not available, generating signed URL")
            return generate_signed_url(blob)

    except Exception as e:
        print(f"[GCS] Upload failed: {e}")
        return None


def generate_signed_url(blob, expiration_hours=24):
    """
    Generate a signed URL for private bucket access.

    Args:
        blob: GCS blob object
        expiration_hours: URL expiration in hours

    Returns:
        str: Signed URL or None if failed
    """
    try:
        from datetime import timedelta

        # Generate signed URL with 24-hour expiration
        url = blob.generate_signed_url(
            expiration=datetime.utcnow() + timedelta(hours=expiration_hours),
            method="GET",
        )
        print(f"[GCS] Generated signed URL (expires in {expiration_hours}h)")
        return url

    except Exception as e:
        print(f"[GCS] Failed to generate signed URL: {e}")
        return f"https://storage.googleapis.com/{blob.bucket.name}/{blob.name}"


def download_from_gcs(public_url, local_path):
    """
    Download file from GCS public URL to local path for processing.

    Args:
        public_url: Public URL of the GCS file
        local_path: Local path to save the file

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        import requests

        response = requests.get(public_url, stream=True, timeout=30)
        response.raise_for_status()

        with open(local_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"[GCS] Downloaded file to: {local_path}")
        return True

    except Exception as e:
        print(f"[GCS] Download failed: {e}")
        return False


def store_report_in_firestore(report_data):
    """
    Store citizen report data in Firestore.

    Args:
        report_data (dict): Complete report data including analysis, image URL, etc.

    Returns:
        str: Document ID of the stored report or None if failed
    """
    if not firestore_db:
        print("[Firestore] Database not initialized, skipping storage")
        return None

    try:
        # Add timestamp and generate unique ID
        report_data["created_at"] = datetime.utcnow()
        report_data["status"] = "submitted"

        # Store in Firestore
        doc_ref = firestore_db.collection("citizen_reports").add(report_data)
        doc_id = doc_ref[1].id

        print(f"[Firestore] Stored report with ID: {doc_id}")
        return doc_id

    except Exception as e:
        print(f"[Firestore] Failed to store report: {e}")
        return None


def get_report_from_firestore(report_id):
    """
    Retrieve a report from Firestore by ID.

    Args:
        report_id (str): Document ID of the report

    Returns:
        dict: Report data or None if not found
    """
    if not firestore_db:
        return None

    try:
        doc_ref = firestore_db.collection("citizen_reports").document(report_id)
        doc = doc_ref.get()

        if doc.exists:
            return doc.to_dict()
        else:
            return None

    except Exception as e:
        print(f"[Firestore] Failed to retrieve report: {e}")
        return None


def update_report_status(report_id, status, notes=None):
    """
    Update the status of a report in Firestore.

    Args:
        report_id (str): Document ID of the report
        status (str): New status (submitted, in_progress, resolved, etc.)
        notes (str, optional): Additional notes

    Returns:
        bool: True if successful, False otherwise
    """
    if not firestore_db:
        return False

    try:
        doc_ref = firestore_db.collection("citizen_reports").document(report_id)
        update_data = {"status": status, "updated_at": datetime.utcnow()}

        if notes:
            update_data["status_notes"] = notes

        doc_ref.update(update_data)
        print(f"[Firestore] Updated report {report_id} status to: {status}")
        return True

    except Exception as e:
        print(f"[Firestore] Failed to update report status: {e}")
        return False


# --- 3. UTILITY FUNCTIONS ---
def allowed_file(filename):
    """
    Check if the uploaded file has an allowed extension.
    """
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]
    )


def save_uploaded_file(file):
    """
    Saves uploaded file locally and optionally to GCS.

    Args:
        file: FileStorage object from request.files

    Returns:
        dict: Contains local_path, gcs_url, and processing_path
    """
    if not file or not allowed_file(file.filename):
        return None

    filename = secure_filename(file.filename)
    timestamp = str(int(time.time()))
    filename = f"{timestamp}_{filename}"

    # Save locally first
    local_filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(local_filepath)

    # Try to upload to GCS
    gcs_url = None
    if gcs_bucket:
        with open(local_filepath, "rb") as f:
            gcs_url = upload_to_gcs(f, filename)

    return {
        "local_path": local_filepath,
        "gcs_url": gcs_url,
        "processing_path": local_filepath,  # Use local path for processing
        "filename": filename,
    }


def cleanup_uploaded_file(file_info):
    """
    Removes local uploaded file after processing.

    Args:
        file_info (dict): File information dictionary
    """
    if not file_info:
        return

    try:
        local_path = file_info.get("local_path")
        if local_path and os.path.exists(local_path):
            os.remove(local_path)
            print(f"[Cleanup] Removed temporary file: {local_path}")
    except Exception as e:
        print(f"[Cleanup] Warning: Could not remove file: {e}")


def prepare_firestore_report_data(result, file_info, user_query=None):
    """
    Prepare report data for Firestore storage.

    Args:
        result (dict): Result from orchestrator
        file_info (dict): File information including GCS URL
        user_query (str, optional): Original user query

    Returns:
        dict: Structured data for Firestore
    """
    # Parse analysis if it's a JSON string
    analysis_data = {}
    if result.get("analysis"):
        try:
            import json

            analysis_data = json.loads(result["analysis"])
        except (json.JSONDecodeError, TypeError):
            analysis_data = {"raw_analysis": result["analysis"]}

    # Prepare structured data for Firestore
    firestore_data = {
        "report_type": result.get("agent_type", "unknown"),
        "user_query": user_query,
        "location": {
            "area": result.get("area"),
            "latitude": result.get("lat"),
            "longitude": result.get("lon"),
        },
        "analysis": analysis_data,
        "official_contact": result.get("official_info"),
        "email_template": result.get("email_content"),
        "success": result.get("success", False),
    }

    # Add image information
    if file_info:
        firestore_data["image"] = {
            "filename": file_info.get("filename"),
            "gcs_url": file_info.get("gcs_url"),
            "storage_type": (
                "google_cloud_storage"
                if file_info.get("gcs_url")
                else "local_temporary"
            ),
        }

    return firestore_data


def format_api_response(result, processing_time=None, file_info=None, user_query=None):
    """
    Formats orchestrator results into standardized API responses and stores in Firestore.

    Args:
        result (dict): Result from orchestrator
        processing_time (float, optional): Processing time in seconds
        file_info (dict, optional): File information including GCS URL
        user_query (str, optional): Original user query

    Returns:
        tuple: (response_dict, status_code)
    """
    if result.get("success"):
        response = {"status": "success", "data": result, "timestamp": time.time()}

        # Add file information if available
        if file_info and file_info.get("gcs_url"):
            response["data"]["image_url"] = file_info["gcs_url"]
            response["data"]["image_storage"] = "google_cloud_storage"
        elif file_info:
            response["data"]["image_storage"] = "local_temporary"

        # Store in Firestore
        if firestore_db:
            firestore_data = prepare_firestore_report_data(
                result, file_info, user_query
            )
            doc_id = store_report_in_firestore(firestore_data)
            if doc_id:
                response["data"]["firestore_id"] = doc_id
                response["data"]["firestore_collection"] = "citizen_reports"

        if processing_time:
            response["processing_time"] = f"{processing_time:.2f}s"
        return response, 200
    else:
        response = {
            "status": "error",
            "error": result.get("error", "Unknown error"),
            "agent_type": result.get("agent_type"),
            "intent": result.get("intent"),
            "timestamp": time.time(),
        }
        if result.get("message"):
            response["message"] = result["message"]
        if processing_time:
            response["processing_time"] = f"{processing_time:.2f}s"
        return response, 400


# --- 4. API ENDPOINTS ---
@app.route("/", methods=["GET"])
def home():
    """
    API home endpoint with service information.
    """
    storage_info = {
        "images": "google_cloud_storage" if gcs_bucket else "local_temporary",
        "database": "firestore" if firestore_db else "none",
        "status": (
            "fully_enabled"
            if (gcs_bucket and firestore_db)
            else "partial" if (gcs_bucket or firestore_db) else "fallback_mode"
        ),
    }

    return jsonify(
        {
            "service": "Namma City Buddy API",
            "version": "1.0.0",
            "description": "AI-powered city services assistant for Bengaluru",
            "endpoints": {
                "POST /analyze": "Analyze text query with optional image",
                "POST /report/trash": "Report trash issues with image",
                "POST /report/pothole": "Report pothole issues with image",
                "POST /report/electricity": "Report electricity/street light issues with image",
                "GET /report/<id>": "Retrieve specific report from Firestore",
                "PUT /report/<id>/status": "Update report status in Firestore",
                "POST /chat": "General conversation endpoint",
                "GET /health": "Service health check",
                "GET /": "This information page",
            },
            "capabilities": [
                "Trash reporting and analysis",
                "Pothole detection and reporting",
                "Electricity and street light issue reporting",
                "General city service inquiries",
                "Official contact information lookup",
                "Cloud image storage and processing",
                "Firestore database for report tracking",
                "Persistent report storage and retrieval",
            ],
            "supported_formats": ["PNG", "JPG", "JPEG", "GIF"],
            "max_file_size": "16MB",
            "image_storage": storage_info,
        }
    )


@app.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint.
    """
    try:
        # Test orchestrator initialization
        orchestrator.configure_and_load_env()

        services = {
            "orchestrator": "online",
            "gemini_api": "configured",
            "google_cloud_storage": "enabled" if gcs_bucket else "fallback_mode",
            "firestore": "enabled" if firestore_db else "disabled",
        }

        return jsonify(
            {"status": "healthy", "timestamp": time.time(), "services": services}
        )
    except Exception as e:
        return (
            jsonify({"status": "unhealthy", "error": str(e), "timestamp": time.time()}),
            503,
        )


@app.route("/analyze", methods=["POST"])
def analyze_request():
    """
    General analysis endpoint that handles any user query with optional image.

    Expected form data:
    - query (str): User's question or request
    - image (file, optional): Image file for visual analysis

    Returns:
        JSON response with analysis results and image URL if uploaded to GCS
    """
    start_time = time.time()
    file_info = None

    try:
        # Get query from request
        query = request.form.get("query")
        if not query:
            return (
                jsonify(
                    {
                        "status": "error",
                        "error": "Query parameter is required",
                        "timestamp": time.time(),
                    }
                ),
                400,
            )

        # Handle optional image upload
        if "image" in request.files:
            file = request.files["image"]
            if file.filename != "":
                file_info = save_uploaded_file(file)
                if not file_info:
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "error": "Invalid file format. Supported: PNG, JPG, JPEG, GIF",
                                "timestamp": time.time(),
                            }
                        ),
                        400,
                    )

        # Process request through orchestrator
        processing_path = file_info["processing_path"] if file_info else None
        result = orchestrator.process_request(query, processing_path)
        processing_time = time.time() - start_time

        # Format and return response
        response, status_code = format_api_response(
            result, processing_time, file_info, query
        )
        return jsonify(response), status_code

    except RequestEntityTooLarge:
        return (
            jsonify(
                {
                    "status": "error",
                    "error": "File too large. Maximum size is 16MB",
                    "timestamp": time.time(),
                }
            ),
            413,
        )
    except Exception as e:
        processing_time = time.time() - start_time
        return (
            jsonify(
                {
                    "status": "error",
                    "error": f"Internal server error: {str(e)}",
                    "processing_time": f"{processing_time:.2f}s",
                    "timestamp": time.time(),
                }
            ),
            500,
        )
    finally:
        # Clean up local file
        cleanup_uploaded_file(file_info)


@app.route("/report/trash", methods=["POST"])
def report_trash():
    """
    Dedicated endpoint for trash reporting.

    Expected form data:
    - image (file): Image of trash/garbage issue
    - description (str, optional): Additional description

    Returns:
        JSON response with trash analysis, official contact info, and image URL
    """
    start_time = time.time()
    file_info = None

    try:
        # Check if image is provided
        if "image" not in request.files:
            return (
                jsonify(
                    {
                        "status": "error",
                        "error": "Image file is required for trash reporting",
                        "timestamp": time.time(),
                    }
                ),
                400,
            )

        file = request.files["image"]
        if file.filename == "":
            return (
                jsonify(
                    {
                        "status": "error",
                        "error": "No image file selected",
                        "timestamp": time.time(),
                    }
                ),
                400,
            )

        # Save uploaded file
        file_info = save_uploaded_file(file)
        if not file_info:
            return (
                jsonify(
                    {
                        "status": "error",
                        "error": "Invalid file format. Supported: PNG, JPG, JPEG, GIF",
                        "timestamp": time.time(),
                    }
                ),
                400,
            )

        # Get optional description
        description = request.form.get(
            "description", "User wants to report trash issue"
        )

        # Process through orchestrator
        result = orchestrator.execute_trash_agent_workflow(file_info["processing_path"])
        processing_time = time.time() - start_time

        # Format and return response
        trash_query = f"Report trash issue: {description}"
        response, status_code = format_api_response(
            result, processing_time, file_info, trash_query
        )
        return jsonify(response), status_code

    except RequestEntityTooLarge:
        return (
            jsonify(
                {
                    "status": "error",
                    "error": "File too large. Maximum size is 16MB",
                    "timestamp": time.time(),
                }
            ),
            413,
        )
    except Exception as e:
        processing_time = time.time() - start_time
        return (
            jsonify(
                {
                    "status": "error",
                    "error": f"Internal server error: {str(e)}",
                    "processing_time": f"{processing_time:.2f}s",
                    "timestamp": time.time(),
                }
            ),
            500,
        )
    finally:
        # Clean up local file
        cleanup_uploaded_file(file_info)


@app.route("/report/pothole", methods=["POST"])
def report_pothole():
    """
    Dedicated endpoint for pothole reporting.

    Expected form data:
    - image (file): Image of pothole/road issue
    - description (str, optional): Additional description

    Returns:
        JSON response with pothole analysis, official contact info, and image URL
    """
    start_time = time.time()
    file_info = None

    try:
        # Check if image is provided
        if "image" not in request.files:
            return (
                jsonify(
                    {
                        "status": "error",
                        "error": "Image file is required for pothole reporting",
                        "timestamp": time.time(),
                    }
                ),
                400,
            )

        file = request.files["image"]
        if file.filename == "":
            return (
                jsonify(
                    {
                        "status": "error",
                        "error": "No image file selected",
                        "timestamp": time.time(),
                    }
                ),
                400,
            )

        # Save uploaded file
        file_info = save_uploaded_file(file)
        if not file_info:
            return (
                jsonify(
                    {
                        "status": "error",
                        "error": "Invalid file format. Supported: PNG, JPG, JPEG, GIF",
                        "timestamp": time.time(),
                    }
                ),
                400,
            )

        # Get optional description
        description = request.form.get(
            "description", "User wants to report pothole issue"
        )

        # Process through orchestrator
        result = orchestrator.execute_pothole_agent_workflow(
            file_info["processing_path"]
        )
        processing_time = time.time() - start_time

        # Format and return response
        pothole_query = f"Report pothole issue: {description}"
        response, status_code = format_api_response(
            result, processing_time, file_info, pothole_query
        )
        return jsonify(response), status_code

    except RequestEntityTooLarge:
        return (
            jsonify(
                {
                    "status": "error",
                    "error": "File too large. Maximum size is 16MB",
                    "timestamp": time.time(),
                }
            ),
            413,
        )
    except Exception as e:
        processing_time = time.time() - start_time
        return (
            jsonify(
                {
                    "status": "error",
                    "error": f"Internal server error: {str(e)}",
                    "processing_time": f"{processing_time:.2f}s",
                    "timestamp": time.time(),
                }
            ),
            500,
        )
    finally:
        # Clean up local file
        cleanup_uploaded_file(file_info)


@app.route("/report/electricity", methods=["POST"])
def report_electricity():
    """
    Dedicated endpoint for electricity/street light reporting.

    Expected form data:
    - image (file): Image of electricity/street light issue
    - description (str, optional): Additional description

    Returns:
        JSON response with electricity analysis, official contact info, and image URL
    """
    start_time = time.time()
    file_info = None

    try:
        # Check if image is provided
        if "image" not in request.files:
            return (
                jsonify(
                    {
                        "status": "error",
                        "error": "Image file is required for electricity reporting",
                        "timestamp": time.time(),
                    }
                ),
                400,
            )

        file = request.files["image"]
        if file.filename == "":
            return (
                jsonify(
                    {
                        "status": "error",
                        "error": "No image file selected",
                        "timestamp": time.time(),
                    }
                ),
                400,
            )

        # Save uploaded file
        file_info = save_uploaded_file(file)
        if not file_info:
            return (
                jsonify(
                    {
                        "status": "error",
                        "error": "Invalid file format. Supported: PNG, JPG, JPEG, GIF",
                        "timestamp": time.time(),
                    }
                ),
                400,
            )

        # Get optional description
        description = request.form.get(
            "description", "User wants to report electricity issue"
        )

        # Process through orchestrator
        result = orchestrator.execute_electricity_agent_workflow(
            file_info["processing_path"]
        )
        processing_time = time.time() - start_time

        # Format and return response
        electricity_query = f"Report electricity issue: {description}"
        response, status_code = format_api_response(
            result, processing_time, file_info, electricity_query
        )
        return jsonify(response), status_code

    except RequestEntityTooLarge:
        return (
            jsonify(
                {
                    "status": "error",
                    "error": "File too large. Maximum size is 16MB",
                    "timestamp": time.time(),
                }
            ),
            413,
        )
    except Exception as e:
        processing_time = time.time() - start_time
        return (
            jsonify(
                {
                    "status": "error",
                    "error": f"Internal server error: {str(e)}",
                    "processing_time": f"{processing_time:.2f}s",
                    "timestamp": time.time(),
                }
            ),
            500,
        )
    finally:
        # Clean up local file
        cleanup_uploaded_file(file_info)


@app.route("/chat", methods=["POST"])
def chat():
    """
    General conversation endpoint for text-only interactions.

    Expected JSON body:
    - message (str): User's message or question

    Returns:
        JSON response with conversational reply
    """
    start_time = time.time()

    try:
        # Get JSON data
        data = request.get_json()
        if not data or "message" not in data:
            return (
                jsonify(
                    {
                        "status": "error",
                        "error": "Message field is required in JSON body",
                        "timestamp": time.time(),
                    }
                ),
                400,
            )

        message = data["message"]
        if not message.strip():
            return (
                jsonify(
                    {
                        "status": "error",
                        "error": "Message cannot be empty",
                        "timestamp": time.time(),
                    }
                ),
                400,
            )

        # Process through orchestrator (text-only)
        result = orchestrator.handle_general_question(message)
        processing_time = time.time() - start_time

        # Format and return response
        response, status_code = format_api_response(result, processing_time)
        return jsonify(response), status_code

    except Exception as e:
        processing_time = time.time() - start_time
        return (
            jsonify(
                {
                    "status": "error",
                    "error": f"Internal server error: {str(e)}",
                    "processing_time": f"{processing_time:.2f}s",
                    "timestamp": time.time(),
                }
            ),
            500,
        )


@app.route("/report/<report_id>", methods=["GET"])
def get_report(report_id):
    """
    Retrieve a specific report from Firestore.

    Args:
        report_id (str): Firestore document ID of the report

    Returns:
        JSON response with report data
    """
    try:
        if not firestore_db:
            return (
                jsonify(
                    {
                        "status": "error",
                        "error": "Firestore not configured",
                        "message": "Report tracking is not available",
                        "timestamp": time.time(),
                    }
                ),
                503,
            )

        report_data = get_report_from_firestore(report_id)

        if not report_data:
            return (
                jsonify(
                    {
                        "status": "error",
                        "error": "Report not found",
                        "report_id": report_id,
                        "timestamp": time.time(),
                    }
                ),
                404,
            )

        # Convert datetime objects to strings for JSON serialization
        if "created_at" in report_data:
            report_data["created_at"] = report_data["created_at"].isoformat()
        if "updated_at" in report_data:
            report_data["updated_at"] = report_data["updated_at"].isoformat()

        return jsonify(
            {
                "status": "success",
                "data": report_data,
                "report_id": report_id,
                "timestamp": time.time(),
            }
        )

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "error": f"Failed to retrieve report: {str(e)}",
                    "report_id": report_id,
                    "timestamp": time.time(),
                }
            ),
            500,
        )


@app.route("/report/<report_id>/status", methods=["PUT"])
def update_report_status_endpoint(report_id):
    """
    Update the status of a report.

    Expected JSON body:
    - status (str): New status
    - notes (str, optional): Additional notes

    Returns:
        JSON response confirming status update
    """
    try:
        if not firestore_db:
            return (
                jsonify(
                    {
                        "status": "error",
                        "error": "Firestore not configured",
                        "timestamp": time.time(),
                    }
                ),
                503,
            )

        data = request.get_json()
        if not data or "status" not in data:
            return (
                jsonify(
                    {
                        "status": "error",
                        "error": "Status field is required in JSON body",
                        "timestamp": time.time(),
                    }
                ),
                400,
            )

        new_status = data["status"]
        notes = data.get("notes")

        success = update_report_status(report_id, new_status, notes)

        if success:
            return jsonify(
                {
                    "status": "success",
                    "message": f"Report status updated to: {new_status}",
                    "report_id": report_id,
                    "new_status": new_status,
                    "timestamp": time.time(),
                }
            )
        else:
            return (
                jsonify(
                    {
                        "status": "error",
                        "error": "Failed to update report status",
                        "report_id": report_id,
                        "timestamp": time.time(),
                    }
                ),
                500,
            )

    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "error": f"Internal server error: {str(e)}",
                    "report_id": report_id,
                    "timestamp": time.time(),
                }
            ),
            500,
        )


# --- 5. ERROR HANDLERS ---
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return (
        jsonify(
            {
                "status": "error",
                "error": "Endpoint not found",
                "message": "Please check the API documentation at GET /",
                "timestamp": time.time(),
            }
        ),
        404,
    )


@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors."""
    return (
        jsonify(
            {
                "status": "error",
                "error": "Method not allowed",
                "message": "Please check the allowed methods for this endpoint",
                "timestamp": time.time(),
            }
        ),
        405,
    )


@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large errors."""
    return (
        jsonify(
            {
                "status": "error",
                "error": "File too large",
                "message": "Maximum file size is 16MB",
                "timestamp": time.time(),
            }
        ),
        413,
    )


@app.errorhandler(500)
def internal_server_error(error):
    """Handle 500 errors."""
    return (
        jsonify(
            {
                "status": "error",
                "error": "Internal server error",
                "message": "Please try again or contact support",
                "timestamp": time.time(),
            }
        ),
        500,
    )


# --- 6. APPLICATION STARTUP ---
def initialize_app():
    """
    Initialize the application on startup.
    """
    try:
        print("🏙️ Starting Namma City Buddy API Server...")
        print("Initializing orchestrator...")
        orchestrator.configure_and_load_env()
        print("✅ Orchestrator initialized successfully!")

        # Display storage configuration
        if gcs_bucket and firestore_db:
            print(f"☁️ Google Cloud Storage: ENABLED")
            print(f"   Bucket: {gcs_bucket.name}")
            print("   Images will be stored in the cloud permanently")
            print(f"🔥 Firestore Database: ENABLED")
            print("   Reports will be stored in Firestore for tracking")
        elif gcs_bucket:
            print(f"☁️ Google Cloud Storage: ENABLED")
            print(f"   Bucket: {gcs_bucket.name}")
            print("⚠️ Firestore: DISABLED - Reports won't be stored")
        elif firestore_db:
            print(f"🔥 Firestore Database: ENABLED")
            print("⚠️ Cloud Storage: DISABLED - Using local temporary storage")
        else:
            print("💾 Storage: LOCAL FALLBACK MODE")
            print("   Images will be processed locally and deleted after analysis")
            print("   Reports will not be stored persistently")

        return True
    except Exception as e:
        print(f"❌ Failed to initialize application: {e}")
        return False


if __name__ == "__main__":
    if initialize_app():
        print("\n" + "=" * 60)
        print("🚀 NAMMA CITY BUDDY API SERVER")
        print("=" * 60)
        print("📍 Server starting on http://localhost:5500")
        print("\n🔗 Available Endpoints:")
        print("  GET  /           - API documentation")
        print("  GET  /health     - Health check")
        print("  POST /analyze    - General analysis (query + optional image)")
        print("  POST /report/trash   - Trash reporting (image required)")
        print("  POST /report/pothole - Pothole reporting (image required)")
        print("  POST /report/electricity - Electricity reporting (image required)")
        print("  GET  /report/<id>    - Retrieve specific report from Firestore")
        print("  PUT  /report/<id>/status - Update report status")
        print("  POST /chat       - Text conversation (JSON)")
        print("\n💡 Examples:")
        print(
            "  curl -X POST -F 'query=I want to report trash' -F 'image=@photo.jpg' http://localhost:5500/analyze"
        )
        print("  curl -X POST -F 'image=@trash.jpg' http://localhost:5500/report/trash")
        print(
            "  curl -X POST -F 'image=@streetlight.jpg' http://localhost:5500/report/electricity"
        )
        print(
            "  curl -X POST -H 'Content-Type: application/json' -d '{\"message\":\"Hello\"}' http://localhost:5500/chat"
        )
        print("=" * 60)

        app.run(debug=True, host="0.0.0.0", port=5500)
    else:
        print("❌ Application initialization failed. Exiting.")
        exit(1)
