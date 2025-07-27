import os
import pandas as pd
from datetime import datetime, timedelta
import json
from dotenv import load_dotenv


# --- 1. CONFIGURATION AND DATA LOADING ---
def configure_and_load_data():
    """
    Loads API key from .env file and reads the events CSV into memory.
    """
    load_dotenv()  # Loads the .env file

    # Load the events database
    try:
        df = pd.read_csv("events.csv", on_bad_lines="skip")
        # Clean up column names for easier access
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
        print(f"Events database loaded successfully. {len(df)} events loaded.")
        return df
    except FileNotFoundError:
        raise FileNotFoundError("Make sure 'events.csv' is in the same folder.")
    except Exception as e:
        print(f"Error loading events.csv: {e}")
        # Try loading with different parameters
        try:
            df = pd.read_csv(
                "events.csv", on_bad_lines="skip", quotechar='"', skipinitialspace=True
            )
            df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
            print(
                f"Events database loaded with fallback method. {len(df)} events loaded."
            )
            return df
        except Exception as e2:
            raise Exception(f"Could not load events.csv: {e2}")


# --- 2. EVENT FILTERING AND PROCESSING ---
def get_upcoming_events(
    events_df, days_ahead=7, category_filter=None, location_filter=None
):
    """
    Get upcoming events within specified days, optionally filtered by category or location.

    Args:
        events_df (DataFrame): Events data
        days_ahead (int): Number of days ahead to look for events
        category_filter (str): Filter by category (optional)
        location_filter (str): Filter by location (optional)

    Returns:
        DataFrame: Filtered upcoming events
    """
    try:
        # Make a copy to avoid modifying original
        events_copy = events_df.copy()

        # Clean and convert date column
        events_copy["date"] = (
            events_copy["date"].astype(str).str.replace("‑", "-", regex=False)
        )  # Replace unicode dash
        events_copy["date"] = pd.to_datetime(
            events_copy["date"], errors="coerce", format="%Y-%m-%d"
        )

        # Filter for upcoming events
        today = pd.Timestamp.now().normalize()
        end_date = today + pd.Timedelta(days=days_ahead)

        # Filter by date range
        upcoming = events_copy[
            (events_copy["date"] >= today) & (events_copy["date"] <= end_date)
        ].copy()

        # Apply category filter if specified
        if category_filter:
            upcoming = upcoming[
                upcoming["category"].str.contains(category_filter, case=False, na=False)
            ]

        # Apply location filter if specified
        if location_filter:
            upcoming = upcoming[
                upcoming["venue"].str.contains(location_filter, case=False, na=False)
            ]

        # Sort by date and time
        upcoming = upcoming.sort_values(["date", "time"])

        return upcoming

    except Exception as e:
        print(f"Error filtering events: {e}")
        return pd.DataFrame()


def get_event_locations_for_map(events_df):
    """
    Extract unique locations from events for map display.

    Args:
        events_df (DataFrame): Events data

    Returns:
        list: Unique venues/locations
    """
    try:
        # Get unique venues, excluding empty ones
        locations = events_df["venue"].dropna().unique().tolist()

        # Clean up location names
        cleaned_locations = []
        for loc in locations:
            if loc and str(loc).strip():
                cleaned_locations.append(str(loc).strip())

        return cleaned_locations

    except Exception as e:
        print(f"Error extracting locations: {e}")
        return []


def categorize_events_by_type(events_df):
    """
    Group events by category for better organization.

    Args:
        events_df (DataFrame): Events data

    Returns:
        dict: Events grouped by category
    """
    try:
        categories = {}

        for _, event in events_df.iterrows():
            category = event.get("category", "Other")
            if category not in categories:
                categories[category] = []

            categories[category].append(event.to_dict())

        return categories

    except Exception as e:
        print(f"Error categorizing events: {e}")
        return {}


# --- 3. EVENT SEARCH AND QUERY PROCESSING ---
def search_events(events_df, query, days_ahead=14):
    """
    Search events based on user query.

    Args:
        events_df (DataFrame): Events data
        query (str): User search query
        days_ahead (int): Days to look ahead

    Returns:
        dict: Search results with events and metadata
    """
    try:
        # Get upcoming events
        upcoming_events = get_upcoming_events(events_df, days_ahead)

        if upcoming_events.empty:
            return {
                "events": [],
                "total_count": 0,
                "message": "No upcoming events found in the next {} days.".format(
                    days_ahead
                ),
                "locations": [],
                "categories": [],
            }

        # Analyze query for filters
        query_lower = query.lower()
        category_filter = None
        location_filter = None

        # Check for category keywords
        category_keywords = {
            "tech": "Tech",
            "startup": "Startup",
            "networking": "Networking",
            "music": "Music",
            "cultural": "Cultural",
            "fitness": "Fitness",
            "wellness": "Wellness",
            "gaming": "Gaming",
            "dance": "Dance",
            "nature": "Nature",
        }

        for keyword, category in category_keywords.items():
            if keyword in query_lower:
                category_filter = category
                break

        # Check for location keywords
        location_keywords = [
            "cubbon",
            "hsr",
            "whitefield",
            "koramangala",
            "indiranagar",
            "jayanagar",
            "malleshwaram",
        ]

        for location in location_keywords:
            if location in query_lower:
                location_filter = location
                break

        # Apply filters
        filtered_events = get_upcoming_events(
            events_df, days_ahead, category_filter, location_filter
        )

        # Convert to list for JSON serialization
        events_list = []
        for _, event in filtered_events.iterrows():
            event_dict = event.to_dict()
            # Format date for display
            if pd.notna(event_dict["date"]):
                event_dict["formatted_date"] = event["date"].strftime("%Y-%m-%d")
                event_dict["day_of_week"] = event["date"].strftime("%A")
            events_list.append(event_dict)

        # Get locations and categories for map
        locations = get_event_locations_for_map(filtered_events)
        categories = list(filtered_events["category"].unique())

        return {
            "events": events_list,
            "total_count": len(events_list),
            "message": f"Found {len(events_list)} upcoming events",
            "locations": locations,
            "categories": categories,
            "query_filters": {
                "category": category_filter,
                "location": location_filter,
                "days_ahead": days_ahead,
            },
        }

    except Exception as e:
        print(f"Error searching events: {e}")
        return {
            "events": [],
            "total_count": 0,
            "message": f"Error searching events: {str(e)}",
            "locations": [],
            "categories": [],
        }


def generate_events_response(search_results, user_query="events"):
    """
    Generate a formatted response for events query.

    Args:
        search_results (dict): Results from search_events
        user_query (str): Original user query

    Returns:
        dict: Formatted response for frontend
    """
    try:
        events = search_results.get("events", [])
        total_count = search_results.get("total_count", 0)
        locations = search_results.get("locations", [])
        categories = search_results.get("categories", [])

        if total_count == 0:
            return {
                "success": True,
                "agent_type": "events",
                "message": "No upcoming events found matching your criteria. Try searching for 'tech events', 'music events', or events in specific areas like 'Cubbon Park'.",
                "events": [],
                "locations": [],
                "categories": [],
                "display_type": "list",
            }

        # Truncate events list if too long (for better chat display)
        display_events = events[:10] if len(events) > 10 else events

        return {
            "success": True,
            "agent_type": "events",
            "message": f"🎉 Found {total_count} upcoming events in Bengaluru!",
            "events": display_events,
            "locations": locations,
            "categories": categories,
            "total_count": total_count,
            "display_type": "map_and_list",
            "query": user_query,
        }

    except Exception as e:
        return {
            "success": False,
            "agent_type": "events",
            "error": f"Error generating events response: {str(e)}",
        }


# --- 4. MAIN EXECUTION LOGIC ---
if __name__ == "__main__":
    # Test the events agent
    print("🎉 Testing Events Agent...")

    try:
        # Load data
        events_data = configure_and_load_data()
        print(f"Loaded {len(events_data)} events")

        # Test searches
        test_queries = [
            "upcoming events",
            "tech events",
            "events in Cubbon Park",
            "startup networking events",
            "music events this weekend",
        ]

        for query in test_queries:
            print(f"\n--- Testing: '{query}' ---")
            search_results = search_events(events_data, query)
            response = generate_events_response(search_results, query)

            if response["success"]:
                print(f"✅ Found {response['total_count']} events")
                print(f"📍 Locations: {', '.join(response['locations'][:3])}...")
                print(f"🏷️ Categories: {', '.join(response['categories'][:3])}...")
            else:
                print(f"❌ Error: {response.get('error')}")

    except Exception as e:
        print(f"❌ Error testing events agent: {e}")

    print("\n🎯 Events Agent testing completed!")
