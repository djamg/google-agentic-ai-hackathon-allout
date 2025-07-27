#!/usr/bin/env python3
"""
Demo script showing the enhanced email display feature in Bangalore Buzz.
This script demonstrates what users will see when they submit a report.
"""

import json


def demo_email_display():
    """Demonstrate the email display feature with sample data"""

    print("🎬 BANGALORE BUZZ - EMAIL DISPLAY DEMO")
    print("=" * 50)
    print()

    # Sample response data that would come from the API
    sample_response = {
        "status": "success",
        "data": {
            "agent_type": "electricity",
            "area": "Indiranagar",
            "lat": 12.9719,
            "lon": 77.6413,
            "analysis": json.dumps(
                {
                    "issue_present": True,
                    "issue_type": "Street Light",
                    "severity": "Medium",
                    "situation_description": "Street light pole is damaged and not functioning properly.",
                    "actionable_advice": "This should be reported to BESCOM immediately for safety reasons.",
                }
            ),
            "official_info": {
                "area": "Indiranagar",
                "designation": "Executive Engineer",
                "name": "BESCOM Official",
                "phone": "8025207071",
                "e-mail": "eeindiranagar@bescom.co.in",
            },
            "email_content": {
                "to": "eeindiranagar@bescom.co.in",
                "subject": "URGENT: Street Light Issue - Indiranagar (Severity: Medium)",
                "body": """Dear BESCOM Official,

I am writing to report an urgent electrical issue requiring immediate attention in Indiranagar.

Location Details:
- Area: Indiranagar
- Coordinates: 12.9719, 77.6413

Issue Details:
- Type of Issue: Street Light
- Severity Level: Medium
- Description: Street light pole is damaged and not functioning properly.

This electrical issue may pose safety risks to residents and requires urgent attention. Please dispatch a maintenance team to assess and resolve this problem at the earliest.

I would appreciate an acknowledgment of this report and an estimated timeline for resolution.

Thank you for your prompt attention to this safety matter.

Best regards,
A Concerned Citizen

---
This report was generated through Bangalore Buzz AI Assistant.
For technical support, contact the system administrator.""",
            },
            "image_url": "https://storage.googleapis.com/bangalorebuzz/citizen-reports/1753570510_a26b4e3c.jpg",
            "firestore_id": "abc123def456789",
        },
    }

    print("📊 SAMPLE API RESPONSE:")
    print("-" * 30)
    print(f"✅ Report Type: {sample_response['data']['agent_type'].title()}")
    print(f"📍 Location: {sample_response['data']['area']}")
    print(f"🆔 Report ID: {sample_response['data']['firestore_id']}")
    print()

    print("📧 EMAIL CONTENT DISPLAY:")
    print("-" * 30)
    email = sample_response["data"]["email_content"]
    print(f"📬 To: {email['to']}")
    print(f"📋 Subject: {email['subject']}")
    print()
    print("📝 Email Body:")
    print("┌" + "─" * 60 + "┐")
    body_lines = email["body"].split("\n")
    for line in body_lines[:10]:  # Show first 10 lines
        print(f"│ {line:<58} │")
    if len(body_lines) > 10:
        print(f"│ {'... (truncated for demo)':^58} │")
    print("└" + "─" * 60 + "┘")
    print()

    print("🎯 FRONTEND FEATURES:")
    print("-" * 30)
    print("✨ What users will see in the web interface:")
    print("  📋 Copy Email - Copies full email content to clipboard")
    print("  📧 Send Email - Opens user's default email application")
    print("  🔗 Open Gmail - Opens Gmail compose in new browser tab")
    print("  📱 Mobile optimized - Responsive design for all devices")
    print("  🎨 Beautiful display - Professional email preview with styling")
    print("  💡 Helpful tips - Instructions on how to use each button")
    print()

    print("🔧 TECHNICAL DETAILS:")
    print("-" * 30)
    print("  🌐 Frontend: HTML5 + CSS3 + Vanilla JavaScript")
    print("  📧 Email handling: mailto: protocol + Gmail web compose")
    print("  📋 Clipboard: Modern Clipboard API with fallback")
    print("  📱 Responsive: Mobile-first design with touch optimization")
    print("  🎭 Animations: Smooth transitions and loading states")
    print("  🔔 Notifications: Toast-style success/error messages")
    print()

    print("🚀 USER WORKFLOW:")
    print("-" * 30)
    print("  1. 📸 User uploads image of electrical issue")
    print("  2. ⚡ Clicks 'Electricity Issue' quick action button")
    print("  3. 🤖 AI analyzes image and generates report")
    print("  4. 📧 Professional email template is displayed")
    print("  5. 👆 User clicks preferred action button:")
    print("     • Copy Email → Paste into any email client")
    print("     • Send Email → Open default email app")
    print("     • Open Gmail → Compose in Gmail web interface")
    print("  6. ✅ Report submitted and tracked in history")
    print()

    print("=" * 50)
    print("🎊 The email display feature provides a complete,")
    print("   professional solution for citizen reporting!")
    print("=" * 50)


if __name__ == "__main__":
    demo_email_display()
