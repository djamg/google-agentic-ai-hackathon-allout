import os
import json
import time
from google import genai
from dotenv import load_dotenv


# --- 1. CONFIGURATION AND INITIALIZATION ---
def configure_and_load_env():
    """
    Loads API key from .env file and configures the environment.
    """
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in .env")
    print("✅ Environment configured successfully.")
    return api_key


# --- 2. INTENT DETECTION SYSTEM ---
def get_user_intent(user_query):
    """
    Uses Gemini to analyze user query and determine the primary intent.
    Returns the detected intent or 'general_question' as fallback.
    """
    print(f"[Intent Detection] Analyzing user query: '{user_query}'")
    client = genai.Client()

    prompt = f"""
    Analyze the user's query and determine the primary intent.
    The available intents are: 'report_trash', 'report_pothole', 'find_events', 'check_traffic', 'general_question'.
    
    Intent definitions:
    - report_trash: User wants to report garbage, litter, or waste management issues
    - report_pothole: User wants to report potholes, road damage, or road maintenance issues  
    - find_events: User wants to find local events, activities, or happenings
    - check_traffic: User wants traffic information, road conditions, or transportation updates
    - general_question: Any other query or general information request
    
    User Query: "{user_query}"
    
    Return only the single intent name. For example: report_trash
    """

    try:
        start_time = time.time()
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
        )
        elapsed = time.time() - start_time
        intent = response.text.strip().lower()
        print(f"[Intent Detection] Detected intent '{intent}' in {elapsed:.2f} seconds")
        return intent
    except Exception as e:
        print(f"[Intent Detection] ERROR: {e}")
        return "general_question"


# --- 3. AGENT EXECUTION WORKFLOWS ---
def execute_trash_agent_workflow(image_path):
    """
    Executes the complete trash agent workflow.
    """
    try:
        import trash_agent

        print("[Trash Agent] Loading officials data...")
        officials_data = trash_agent.configure_and_load_data()

        print("[Trash Agent] Extracting geolocation from image...")
        lat, lon = trash_agent.get_geolocation(image_path)

        if lat and lon:
            print(f"[Trash Agent] Geolocation found: {lat}, {lon}")
            # Get area from coordinates
            area = trash_agent.get_area_from_latlon(lat, lon)
            if not area:
                area = "HSR Layout"  # Default fallback

            print("[Trash Agent] Analyzing image with Gemini...")
            # Get AI analysis
            analysis_json_str = trash_agent.get_trash_analysis_from_gemini(
                image_path, lat=lat, lon=lon, area=area
            )

            # Parse analysis and find official
            try:
                analysis = json.loads(analysis_json_str)
                ward_name = analysis.get("ward_name", area)
            except json.JSONDecodeError:
                ward_name = area

            print(f"[Trash Agent] Finding official for ward: {ward_name}")
            official_info = trash_agent.find_official_for_ward(
                officials_data, ward_name
            )

            # Generate email content
            location_info = {"area": area, "lat": lat, "lon": lon}
            email_content = trash_agent.generate_email_content(analysis, location_info)

            return {
                "success": True,
                "agent_type": "trash",
                "analysis": analysis_json_str,
                "official_info": official_info,
                "email_content": email_content,
                "area": area,
                "lat": lat,
                "lon": lon,
            }
        else:
            return {
                "success": False,
                "agent_type": "trash",
                "error": "Could not retrieve geolocation data from the image.",
            }

    except ImportError:
        return {
            "success": False,
            "agent_type": "trash",
            "error": "Trash agent module not found. Please ensure trash_agent.py exists.",
        }
    except Exception as e:
        return {
            "success": False,
            "agent_type": "trash",
            "error": f"Workflow execution failed: {e}",
        }


def execute_pothole_agent_workflow(image_path):
    """
    Executes the complete pothole agent workflow.
    """
    try:
        import pothole_agent

        print("[Pothole Agent] Loading officials data...")
        officials_data = pothole_agent.configure_and_load_data()

        print("[Pothole Agent] Extracting geolocation from image...")
        lat, lon = pothole_agent.get_geolocation(image_path)

        if lat and lon:
            print(f"[Pothole Agent] Geolocation found: {lat}, {lon}")
            # Get area from coordinates
            area = pothole_agent.get_area_from_latlon(lat, lon)

            print("[Pothole Agent] Analyzing image with Gemini...")
            # Get AI analysis
            analysis_json_str = pothole_agent.get_pothole_analysis_from_gemini(
                image_path, lat=lat, lon=lon, area=area
            )

            # Parse analysis and find official
            try:
                analysis = json.loads(analysis_json_str)
                ward_name = analysis.get("ward_name", area)
            except json.JSONDecodeError:
                ward_name = area

            print(f"[Pothole Agent] Finding official for ward: {ward_name}")
            official_info = pothole_agent.find_official_for_ward(
                officials_data, ward_name
            )

            # Generate email content
            location_info = {"area": area, "lat": lat, "lon": lon}
            email_content = pothole_agent.generate_email_content(
                analysis, location_info
            )

            return {
                "success": True,
                "agent_type": "pothole",
                "analysis": analysis_json_str,
                "official_info": official_info,
                "email_content": email_content,
                "area": area,
                "lat": lat,
                "lon": lon,
            }
        else:
            return {
                "success": False,
                "agent_type": "pothole",
                "error": "Could not retrieve geolocation data from the image.",
            }

    except ImportError:
        return {
            "success": False,
            "agent_type": "pothole",
            "error": "Pothole agent module not found. Please ensure pothole_agent.py exists.",
        }
    except Exception as e:
        return {
            "success": False,
            "agent_type": "pothole",
            "error": f"Workflow execution failed: {e}",
        }


def handle_general_question(user_query):
    """
    Handles general questions using Gemini for conversational responses.
    """
    print(f"[General Question] Processing: {user_query}")
    client = genai.Client()

    prompt = f"""
    You are Namma City Buddy, a helpful AI assistant for Bengaluru citizens.
    You can help with:
    - Reporting trash and waste management issues
    - Reporting potholes and road problems
    - Finding local events and activities (coming soon)
    - Traffic and transportation information (coming soon)
    - General questions about city services
    
    User asked: "{user_query}"
    
    Provide a helpful, friendly response. If the question relates to city services you can handle, 
    guide them on how to use your specific features. Keep responses concise and actionable.
    """

    try:
        start_time = time.time()
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
        )
        elapsed = time.time() - start_time
        print(f"[General Question] Response generated in {elapsed:.2f} seconds")
        return {
            "success": True,
            "agent_type": "general",
            "response": response.text.strip(),
        }
    except Exception as e:
        print(f"[General Question] ERROR: {e}")
        return {
            "success": False,
            "agent_type": "general",
            "error": f"Failed to generate response: {e}",
        }


# --- 4. MAIN ORCHESTRATION LOGIC ---
def process_request(user_query, image_path=None):
    """
    Main orchestration function that processes user requests and routes to appropriate agents.

    Args:
        user_query (str): The user's query or request
        image_path (str, optional): Path to image file for visual analysis

    Returns:
        dict: Structured response with results from the appropriate agent
    """
    try:
        print(f"[Orchestrator] Processing request: '{user_query}'")

        # Detect user intent
        intent = get_user_intent(user_query)
        print(f"[Orchestrator] Routing to intent: {intent}")

        # Route to appropriate agent based on intent
        if intent == "report_trash":
            if not image_path:
                return {
                    "success": False,
                    "error": "Image required for trash reporting",
                    "intent": intent,
                }
            return execute_trash_agent_workflow(image_path)

        elif intent == "report_pothole":
            if not image_path:
                return {
                    "success": False,
                    "error": "Image required for pothole reporting",
                    "intent": intent,
                }
            return execute_pothole_agent_workflow(image_path)

        elif intent == "find_events":
            return {
                "success": False,
                "agent_type": "events",
                "error": "Event Discovery Agent is currently under development",
                "message": "Coming soon: Local events, cultural activities, and community happenings!",
                "intent": intent,
            }

        elif intent == "check_traffic":
            return {
                "success": False,
                "agent_type": "traffic",
                "error": "Traffic Agent is currently under development",
                "message": "Coming soon: Real-time traffic updates, route optimization, and road conditions!",
                "intent": intent,
            }

        else:  # general_question
            return handle_general_question(user_query)

    except Exception as e:
        print(f"[Orchestrator] ERROR: {e}")
        return {
            "success": False,
            "error": f"Orchestration failed: {e}",
            "intent": "unknown",
        }


# --- 5. COMMAND LINE INTERFACE ---
def main():
    """
    Command line interface for the orchestrator.
    """
    try:
        print("🏙️ Welcome to Namma City Buddy Orchestrator!")
        print("Initializing system...")
        configure_and_load_env()

        print("\n" + "=" * 60)
        print("🤖 Hello! I'm your Namma City Buddy AI Assistant.")
        print("I can help you with:")
        print("  🗑️  Report trash and waste issues")
        print("  🕳️  Report potholes and road problems")
        print("  🎉 Find local events and activities")
        print("  🚦 Get traffic and transportation info")
        print("  💬 Answer general city service questions")
        print("=" * 60)

        user_input = input("\nHow can I help you today? ").strip()

        if not user_input:
            print("❌ Please provide a valid query.")
            return

        # Check if image is needed
        intent_preview = get_user_intent(user_input)
        image_path = None

        if intent_preview in ["report_trash", "report_pothole"]:
            image_path = input("Please provide the path to the image: ").strip()
            if not os.path.exists(image_path):
                print(f"❌ File not found: {image_path}")
                return

        # Process the request
        result = process_request(user_input, image_path)

        # Display results
        print("\n" + "=" * 50)
        print("🌟 NAMMA CITY BUDDY RESULT 🌟")
        print("=" * 50)

        if result.get("success"):
            agent_type = result.get("agent_type", "unknown")

            if agent_type in ["trash", "pothole"]:
                # Display detailed report for visual analysis
                try:
                    analysis = json.loads(result["analysis"])
                    print(f"📍 Location: {result.get('area', 'Unknown')}")
                    print(
                        f"🌍 Coordinates: {result.get('lat', 'N/A')}, {result.get('lon', 'N/A')}"
                    )

                    if agent_type == "trash":
                        print(f"🗑️ Trash Type: {analysis.get('trash_type', 'N/A')}")
                        print(f"📊 Severity: {analysis.get('severity', 'N/A')}")
                        print(
                            f"🔍 Situation: {analysis.get('situation_description', 'N/A')}"
                        )
                        print(f"💡 Advice: {analysis.get('actionable_advice', 'N/A')}")
                    else:  # pothole
                        if analysis.get("is_pothole_present", False):
                            print(
                                f"🔢 Pothole Count: {analysis.get('pothole_count', 'N/A')}"
                            )
                            print(f"📊 Severity: {analysis.get('severity', 'N/A')}")
                            print(
                                f"🔍 Situation: {analysis.get('situation_description', 'N/A')}"
                            )
                            print(
                                f"💡 Advice: {analysis.get('actionable_advice', 'N/A')}"
                            )
                        else:
                            print("✅ No significant pothole detected in the image.")

                    # Official contact info
                    print("\n--- 📞 CONTACT INFORMATION ---")
                    official_info = result.get("official_info")
                    if official_info:
                        print(f"👤 Official: {official_info.get('name', 'N/A')}")
                        print(
                            f"🏢 Designation: {official_info.get('designation', 'N/A')}"
                        )
                        print(f"📱 Phone: {official_info.get('phone', 'N/A')}")
                        print(f"📧 Area: {official_info.get('area', 'N/A')}")
                    else:
                        print("📞 BBMP Helpline: 22660000 or 080-22660000")

                    # Display email information
                    email_content = result.get("email_content")
                    if email_content:
                        print(f"\n--- 📧 Email Support ---")
                        print(f"You can also email this report directly to BBMP:")
                        print(f"📬 To: {email_content['to']}")
                        print(f"📋 Subject: {email_content['subject']}")
                        print(f"\n📝 Email Body Preview:")
                        print("─" * 50)
                        print(email_content["body"][:200] + "...")
                        print("─" * 50)

                except json.JSONDecodeError:
                    print("📋 Raw Analysis:")
                    print(result.get("analysis", "No analysis available"))

            elif agent_type == "general":
                print(f"🤖 Response: {result.get('response')}")

        else:
            print(f"❌ {result.get('error', 'Unknown error occurred')}")
            if result.get("message"):
                print(f"💡 {result.get('message')}")

        print("=" * 50)
        print("\n✨ Thank you for using Namma City Buddy!")
        print("Together, we're making Bengaluru better! 🏙️")

    except KeyboardInterrupt:
        print("\n\n👋 Goodbye! Thanks for using Namma City Buddy!")
    except Exception as e:
        print(f"\n❌ System error: {e}")
        print("Please try again or contact support.")


if __name__ == "__main__":
    main()
