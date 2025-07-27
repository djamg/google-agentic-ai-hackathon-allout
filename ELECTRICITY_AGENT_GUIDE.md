# ⚡ Electricity Agent Usage Guide

## Overview
The Electricity Agent helps citizens report street light issues, power outages, electrical infrastructure problems, and other electricity-related concerns to BESCOM (Bangalore Electricity Supply Company).

## Features
- 📸 **Image Analysis**: AI-powered analysis of electrical infrastructure issues
- 📍 **Geolocation**: Automatic location extraction from image EXIF data
- 🔍 **Issue Detection**: Identifies various types of electrical problems
- 📧 **Email Templates**: Generates formatted reports for BESCOM officials
- 👮 **Official Lookup**: Finds appropriate BESCOM division contacts

## Issue Types Detected
- 🔆 Street lights not working or damaged
- ⚡ Power lines down or damaged
- 🗼 Electrical poles damaged or leaning
- 🔌 Transformer issues
- 💡 Power outages affecting street lighting
- ⚠️ Exposed electrical wires
- 🏗️ Other electrical infrastructure problems

## Usage Methods

### 1. Standalone Agent
```bash
# Activate virtual environment
source venv/bin/activate

# Run the electricity agent directly
python electricity_agent.py
```
**Note**: Update `electricity_sample.jpg` to your actual image file path in the script.

### 2. Through Orchestrator
```bash
source venv/bin/activate
python orchestrator.py
```
Then type queries like:
- "I want to report a street light issue"
- "There's a damaged electrical pole"
- "Power lines are down"

### 3. Through Flask API
```bash
# Start the server
source venv/bin/activate
python app.py

# In another terminal, test the endpoint
curl -X POST -F 'image=@streetlight.jpg' -F 'description=Street light not working' http://localhost:5500/report/electricity
```

## API Response Format
```json
{
  "status": "success",
  "data": {
    "agent_type": "electricity",
    "area": "Indiranagar",
    "lat": 12.9719,
    "lon": 77.6413,
    "analysis": "{\"issue_present\": true, \"issue_type\": \"Street Light\", \"severity\": \"Medium\"}",
    "official_info": {
      "area": "Indiranagar",
      "designation": "Executive Engineer",
      "phone": "8025207071",
      "e-mail": "eeindiranagar@bescom.co.in"
    },
    "email_content": {
      "to": "eeindiranagar@bescom.co.in",
      "subject": "URGENT: Street Light Issue - Indiranagar (Severity: Medium)",
      "body": "Dear BESCOM Official,\n\nI am writing to report..."
    },
    "image_url": "https://storage.googleapis.com/bangalorebuzz/citizen-reports/...",
    "firestore_id": "abc123def456"
  }
}
```

## BESCOM Division Coverage
The agent can identify and route reports to specific BESCOM divisions including:
- Hebbal Division
- HSR Layout Division  
- Indiranagar Division
- Jalahalli Division
- Jayanagar Division
- And many more...

## Email Templates
The agent generates professional email templates with:
- **Urgent subject lines** for safety issues
- **Detailed location information** (coordinates + area)
- **Issue classification** and severity assessment
- **Professional formatting** for official correspondence
- **Fallback contact** (info@bescom.co.in) when specific official not found

## Testing
```bash
# Run comprehensive API tests
source venv/bin/activate
python test_api.py
```

## Requirements [[memory:4432838]]
- Image with GPS EXIF data for location detection
- Internet connection for Gemini AI analysis
- Valid GEMINI_API_KEY in .env file
- bescom.csv file with BESCOM officials database

## Severity Levels
- **🟢 Low**: Minor issues, routine maintenance
- **🟡 Medium**: Moderate problems, needs attention  
- **🔴 High**: Dangerous or urgent issues, safety risks

## Tips for Best Results
1. **📱 Enable GPS** on your camera when taking photos
2. **📸 Clear images** showing the electrical issue clearly
3. **🎯 Focus on the problem** - center the issue in the frame
4. **⏰ Report urgent issues** immediately for safety
5. **📍 Include landmarks** in the image for better location identification

---
**Note**: For emergency electrical issues posing immediate danger, contact BESCOM emergency helpline: **1912** or **080-22294411** 