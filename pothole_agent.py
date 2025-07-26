import os
import pandas as pd
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from google import genai
from dotenv import load_dotenv
import time
import requests
import json


# --- 1. CONFIGURATION AND DATA LOADING ---
def configure_and_load_data():
    """
    Loads API key from .env file and reads the officials CSV into memory.
    """
    load_dotenv()  # Loads the .env file
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found. Please set it in the .env file.")
    # No need to call genai.configure() with the new google-genai client

    # Load the officials database (now from the new complaints file)
    try:
        df = pd.read_csv("bbmp.csv")
        # Let's clean up the column names for easier access
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
        print("Officials database loaded successfully.")
        return df
    except FileNotFoundError:
        raise FileNotFoundError("Make sure 'bbmp.csv' is in the same folder.")


# --- 2. THE AGENT'S "SENSES": IMAGE ANALYSIS ---
def get_geolocation(image_path):
    """
    Extracts latitude and longitude from an image's EXIF data.
    """
    try:
        image = Image.open(image_path)
        exif_data = image._getexif()
        if not exif_data:
            return None, None  # No EXIF data

        # Find the GPS info tag
        gps_info = {}
        for tag, value in exif_data.items():
            decoded_tag = TAGS.get(tag, tag)
            if decoded_tag == "GPSInfo":
                for t in value:
                    sub_decoded = GPSTAGS.get(t, t)
                    gps_info[sub_decoded] = value[t]

        # Convert GPS coordinates to decimal degrees
        lat_data = gps_info.get("GPSLatitude")
        lon_data = gps_info.get("GPSLongitude")

        if lat_data and lon_data:
            lat_deg = lat_data[0] + lat_data[1] / 60.0 + lat_data[2] / 3600.0
            lon_deg = lon_data[0] + lon_data[1] / 60.0 + lon_data[2] / 3600.0
            if gps_info.get("GPSLatitudeRef") == "S":
                lat_deg = -lat_deg
            if gps_info.get("GPSLongitudeRef") == "W":
                lon_deg = -lon_deg
            return lat_deg, lon_deg
        return None, None

    except Exception as e:
        print(f"Could not process image EXIF data: {e}")
        return None, None


# --- 2.1. REVERSE GEOCODING ---
def get_area_from_latlon(lat, lon):
    """
    Uses OpenStreetMap Nominatim to reverse geocode lat/lon to an area/ward name.
    """
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        "lat": lat,
        "lon": lon,
        "format": "json",
        "zoom": 16,  # Adjust for granularity
        "addressdetails": 1,
    }
    headers = {"User-Agent": "PotholeAgent/1.0"}
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()
        # Try to extract the area/ward/neighbourhood
        area = (
            data.get("address", {}).get("neighbourhood")
            or data.get("address", {}).get("suburb")
            or data.get("address", {}).get("city_district")
            or data.get("address", {}).get("city")
        )
        return area
    except Exception as e:
        print(f"[Geocoding] ERROR: Could not reverse geocode: {e}")
        return None


# --- 3. THE AGENT'S "BRAIN": GEMINI ANALYSIS ---
def get_pothole_analysis_from_gemini(image_path, lat=None, lon=None, area=None):
    """
    Sends the image and location info to Gemini and asks for a structured analysis, including the best-matching ward/area name for the officials database.
    """
    print("[Gemini] Starting analysis of the road image...")
    client = genai.Client()

    # Open the image and convert to bytes
    try:
        print(f"[Gemini] Attempting to open image: {image_path}")
        with open(image_path, "rb") as f:
            img_bytes = f.read()
        print("[Gemini] Image opened and read as bytes.")
    except Exception as e:
        print(f"[Gemini] ERROR: Could not open image: {e}")
        return {"error": f"Could not open image: {e}"}

    # Compose the prompt with location info
    location_info = ""
    if lat is not None and lon is not None:
        location_info += f"The photo was taken at latitude {lat}, longitude {lon}.\n"
    if area:
        location_info += f"The geocoding service suggests the area is '{area}'.\n"

    prompt = f"""
    Analyze the attached image of a road surface in Bengaluru, India.\n
    {location_info}
    First, determine if one or more potholes are clearly visible.
    Then, provide a structured JSON response with the following keys:
    - "is_pothole_present": A boolean (true or false).
    - "ward_name": The best-matching BBMP ward/area name for lookup in an officials database. Use the geocoded area as a hint.
    - "pothole_count": An integer for the number of distinct potholes visible.
    - "severity": A rating of 'Low', 'Medium', or 'High' for the worst pothole visible. 'Low' for small/shallow, 'Medium' for moderate size, 'High' for large, deep, or hazardous-looking potholes.
    - "situation_description": A one-sentence summary of the situation (e.g., "A large, water-filled pothole is visible in the center of the road.").
    - "actionable_advice": Suggest a one-sentence action for a citizen (e.g., "This should be reported to the BBMP for urgent road repair.").
    Only output the raw JSON object, with no other text or markdown. If no pothole is present, set "is_pothole_present" to false and provide default values for other keys.
    """

    print("[Gemini] Sending image and prompt to Gemini for pothole analysis...")
    start_time = time.time()
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                {
                    "role": "user",
                    "parts": [
                        {"text": prompt},
                        {"inline_data": {"mime_type": "image/jpeg", "data": img_bytes}},
                    ],
                }
            ],
        )
        elapsed = time.time() - start_time
        print(f"[Gemini] Received response from Gemini in {elapsed:.2f} seconds.")
        cleaned_json = response.text.strip().replace("```json", "").replace("```", "")
        print(f"[Gemini] Cleaned JSON response: {cleaned_json}")
        return cleaned_json
    except Exception as e:
        elapsed = time.time() - start_time
        print(
            f"[Gemini] ERROR: Exception during Gemini API call after {elapsed:.2f} seconds: {e}"
        )
        return {"error": f"Exception during Gemini API call: {e}"}


# --- 4. THE AGENT'S "TOOL": FINDING THE OFFICIAL ---
def find_official_for_ward(officials_df, ward_name):
    """
    Looks up the contact details for a specific BBMP ward.
    """
    # Filter the DataFrame for the correct ward
    ward_official = officials_df[
        (officials_df["department"] == "BBMP (Ward)")
        & (officials_df["area"].str.contains(ward_name, case=False, na=False))
    ]

    if not ward_official.empty:
        # Return the first match found as a dictionary
        return ward_official.iloc[0].to_dict()
    else:
        return None


def generate_email_content(analysis_data, location_info):
    """
    Generates email subject and body for pothole reporting.

    Args:
        analysis_data (dict): Parsed analysis from Gemini
        location_info (dict): Location details including area, lat, lon

    Returns:
        dict: Email content with subject and body
    """
    area = location_info.get("area", "Unknown Area")
    lat = location_info.get("lat", "N/A")
    lon = location_info.get("lon", "N/A")

    # Extract analysis details
    is_pothole = analysis_data.get("is_pothole_present", False)
    severity = analysis_data.get("severity", "N/A")
    count = analysis_data.get("pothole_count", "N/A")
    description = analysis_data.get(
        "situation_description", "Pothole reported by citizen"
    )

    if not is_pothole:
        subject = f"Road Condition Report - {area}"
        body = f"""Dear BBMP Official,

I am writing to report a road condition concern in {area}.

Location Details:
- Area: {area}
- Coordinates: {lat}, {lon}

Issue Description:
No significant pothole was detected in the submitted image, but I would like to bring this road condition to your attention for review.

Please investigate this location and take appropriate action if necessary.

Thank you for your service to our city.

Best regards,
A Concerned Citizen

---
This report was generated through Namma City Buddy AI Assistant.
For technical support, contact the system administrator."""
    else:
        subject = f"URGENT: Pothole Report - {area} (Severity: {severity})"
        body = f"""Dear BBMP Official,

I am writing to report a pothole issue requiring immediate attention in {area}.

Location Details:
- Area: {area}
- Coordinates: {lat}, {lon}

Pothole Details:
- Number of Potholes: {count}
- Severity Level: {severity}
- Description: {description}

This issue poses a safety risk to commuters and requires urgent repair. Please dispatch a maintenance team to assess and fix this problem at the earliest.

I would appreciate an acknowledgment of this report and an estimated timeline for resolution.

Thank you for your prompt attention to this matter.

Best regards,
A Concerned Citizen

---
This report was generated through Namma City Buddy AI Assistant.
For technical support, contact the system administrator."""

    return {"subject": subject, "body": body, "to": "info@bbmp.gov.in"}


# --- 5. MAIN EXECUTION LOGIC ---
if __name__ == "__main__":
    image_file = "pothole_sample.jpg"  # Make sure this image is in your folder

    # Step 1: Load data
    officials_data = configure_and_load_data()

    # Step 2: Get location from image
    lat, lon = get_geolocation(image_file)

    if not lat or not lon:
        print("\n❌ Could not retrieve geolocation data from the image.")
        print(
            "Please use a photo with GPS data enabled or manually provide the location."
        )
    else:
        print(f"\n✅ Geolocation found: Latitude={lat}, Longitude={lon}")
        # Step 2.1: Get area from lat/lon
        area = get_area_from_latlon(lat, lon)
        if area:
            print(f"📍 Area determined from geolocation: {area}")
        else:
            print("📍 Could not determine area. Will rely on Gemini to identify.")

        # Step 3: Get analysis from Gemini
        analysis_json_str = get_pothole_analysis_from_gemini(
            image_file, lat=lat, lon=lon, area=area
        )
        print(f"\n🧠 Gemini's Analysis (JSON):\n{analysis_json_str}")

        # Step 4: Parse the analysis and decide the next step
        try:
            analysis = json.loads(analysis_json_str)
            is_pothole = analysis.get("is_pothole_present", False)

            if not is_pothole:
                print("\n\n--- 🌟 ROAD ANALYSIS REPORT 🌟 ---\n")
                print(
                    "✅ Gemini analysis indicates no significant pothole was detected in the image."
                )
                print("\n------------------------------------\n")
            else:
                # A pothole was found, proceed with reporting
                ward_name = analysis.get("ward_name", area)
                official_info = find_official_for_ward(officials_data, ward_name)

                # Step 5: Generate email content
                location_info = {"area": area, "lat": lat, "lon": lon}
                email_content = generate_email_content(analysis, location_info)

                # Step 6: Synthesize and present the final report
                print("\n\n--- 🌟 YOUR POTHOLE ACTION REPORT 🌟 ---\n")
                print(f"Issue detected from image: {image_file}\n")
                print(f"🔍 Situation: {analysis.get('situation_description', 'N/A')}")
                print(f"🔢 Pothole Count: {analysis.get('pothole_count', 'N/A')}")
                print(f"📊 Severity: {analysis.get('severity', 'N/A')}")
                print(f"💡 Advice: {analysis.get('actionable_advice', 'N/A')}")

                print("\n--- ✅ Recommended Action ---")
                if official_info:
                    print(
                        "Please report this issue to the designated BBMP Nodal Officer for this area:"
                    )
                    print(f"  - Ward: {official_info.get('area', 'N/A')}")
                    print(f"  - Name: {official_info.get('name', 'N/A')}")
                    print(f"  - Designation: {official_info.get('designation', 'N/A')}")
                    print(f"  - Phone: {official_info.get('phone', 'N/A')}")
                else:
                    # print(f"\n🚨 Could not find a specific official for '{ward_name}'.")
                    print("Please contact the main BBMP helpline for assistance:")
                    print("  - BBMP Helpline: 22660000 or 080-22660000")

                print(f"\n--- 📧 Email Support ---")
                print(f"You can also email this report directly to BBMP:")
                print(f"📬 To: {email_content['to']}")
                print(f"📋 Subject: {email_content['subject']}")
                print(f"\n📝 Email Body Preview:")
                print("─" * 50)
                print(email_content["body"][:200] + "...")
                print("─" * 50)

                print("\n--------------------------------------\n")

        except (json.JSONDecodeError, TypeError) as e:
            print(f"\n❌ Error processing Gemini's response: {e}")
            print("Could not generate a report.")
