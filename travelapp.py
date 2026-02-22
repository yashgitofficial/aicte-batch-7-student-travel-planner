import streamlit as st
from google import genai
from google.genai import types
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
import pandas as pd
import json
import re

# ==========================================
# 1. Helper Functions
# ==========================================

@st.cache_data(show_spinner=False)
def geocode_address(address):
    """
    Converts an address string to latitude and longitude.
    Uses st.cache_data to prevent hitting Geopy API limits for repeated addresses.
    """
    geolocator = Nominatim(user_agent="student_ai_travel_planner")
    try:
        # Timeout set to 5 seconds to avoid hanging on slow network requests
        location = geolocator.geocode(address, timeout=5)
        if location:
            return location.latitude, location.longitude
    except (GeocoderTimedOut, GeocoderUnavailable):
        return None
    return None

def parse_gemini_json(response_text):
    """
    Safely parses the JSON output from Gemini, stripping any accidental markdown formatting.
    """
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        # Fallback: remove markdown backticks if the model includes them despite mime_type
        cleaned_text = re.sub(r'^```json\s*|\s*```$', '', response_text.strip(), flags=re.IGNORECASE)
        try:
            return json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            st.error(f"Failed to parse AI response. Raw output:\n{response_text}")
            return None


    
def generate_itinerary(api_key, destination, duration, budget, interests):
    """
    Calls the Gemini API to generate the structured JSON itinerary using the new google-genai SDK.
    """
    # 1. Initialize the new Client with your API key
    client = genai.Client(api_key=api_key)
    
    interests_str = ", ".join(interests) if interests else "General exploring"
    
    prompt = f"""
    You are a budget-savvy student travel expert. 
    Create a {duration}-day travel itinerary for a student visiting {destination}.
    Their maximum total budget is ${budget} USD.
    Their interests are: {interests_str}.
    
    You MUST return the output strictly as a valid JSON object matching this exact schema. Do not include any markdown formatting or introductory text.
    {{
      "trip_summary": "A brief, exciting summary of the trip.",
      "estimated_total_cost": 150,
      "itinerary": [
        {{
          "day": 1,
          "activities": [
            {{
              "time": "Morning",
              "place_name": "Specific place name",
              "description": "Activity description and why it fits the budget.",
              "estimated_cost": 10,
              "address_for_geocoding": "Full verifiable address or highly specific landmark name for map plotting"
            }}
          ]
        }}
      ]
    }}
    """
    
    try:
        # 2. Use the new client.models.generate_content syntax
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.7
            )
        )
        return parse_gemini_json(response.text)
    except Exception as e:
        st.error(f"An error occurred while communicating with the Gemini API: {e}")
        return None

def create_itinerary_map(itinerary_data):
    """
    Generates a Folium map with markers for each activity in the itinerary.
    """
    # Available Folium marker colors to differentiate days
    colors = ['blue', 'green', 'red', 'purple', 'orange', 'darkred', 'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue', 'darkpurple', 'pink', 'lightblue', 'lightgreen', 'gray', 'black']
    
    m = folium.Map(location=[0, 0], zoom_start=2)
    coordinates_list = []

    for day_data in itinerary_data.get("itinerary", []):
        day_num = day_data.get("day", 1)
        # Cycle through colors if the trip is longer than the color list
        marker_color = colors[(day_num - 1) % len(colors)] 
        
        for activity in day_data.get("activities", []):
            address = activity.get("address_for_geocoding")
            place_name = activity.get("place_name", "Unknown Place")
            
            if address:
                coords = geocode_address(address)
                if coords:
                    lat, lon = coords
                    coordinates_list.append([lat, lon])
                    
                    popup_html = f"<b>{place_name}</b><br>Day {day_num} - {activity.get('time')}<br>Cost: ${activity.get('estimated_cost', 0)}"
                    folium.Marker(
                        location=[lat, lon],
                        popup=folium.Popup(popup_html, max_width=250),
                        tooltip=place_name,
                        icon=folium.Icon(color=marker_color, icon="info-sign")
                    ).add_to(m)

    # Automatically zoom and center the map to fit all markers
    if coordinates_list:
        m.fit_bounds(coordinates_list)
    else:
        st.warning("Could not map the locations. The addresses provided by the AI might be too vague.")
        
    return m

# ==========================================
# 2. Streamlit UI Layout
# ==========================================

st.set_page_config(page_title="Student AI Travel Planner", page_icon="🌍", layout="wide")

# Securely fetch the API key from Streamlit Secrets
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("API key is missing! Please configure it in the Streamlit Cloud Settings.")
    st.stop()
    
# Main UI
st.title("🎒 Student AI Travel Planner")
st.write("Plan a budget-friendly, personalized trip powered by Google Gemini and interactive maps.")

with st.form("travel_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        destination = st.text_input("Where do you want to go?", placeholder="e.g., Tokyo, Japan")
        duration = st.number_input("How many days?", min_value=1, max_value=14, value=3)
        
    with col2:
        budget = st.number_input("Maximum Budget (USD)", min_value=50, max_value=5000, value=300, step=50)
        interests = st.multiselect(
            "Travel Style / Interests",
            ["Art & Museums", "Street Food", "Fine Dining", "Adventure & Nature", "Nightlife", "Historical Sites", "Budget/Free Activities"],
            default=["Budget/Free Activities", "Street Food"]
        )
        
    submitted = st.form_submit_button("Generate Itinerary", disabled=not api_key, use_container_width=True)

# ==========================================
# 3. Processing and Output
# ==========================================

if submitted:
    if not destination:
        st.error("Please enter a destination.")
    else:
        with st.spinner(f"Planning your {duration}-day student trip to {destination}..."):
            
            # Step 1: Generate AI Data
            itinerary_data = generate_itinerary(api_key, destination, duration, budget, interests)
            
            if itinerary_data:
                st.success("Itinerary generated successfully!")
                
                # Step 2: Budget Tracker Metrics
                st.subheader("📊 Trip Overview")
                st.write(itinerary_data.get("trip_summary", ""))
                
                est_cost = itinerary_data.get("estimated_total_cost", 0)
                delta = budget - est_cost
                
                metric_col1, metric_col2, metric_col3 = st.columns(3)
                metric_col1.metric("Your Budget", f"${budget}")
                metric_col2.metric("Estimated Cost", f"${est_cost}", delta=f"${delta} remaining", delta_color="normal")
                
                if est_cost > budget:
                    st.warning("Warning: The AI estimated cost slightly exceeds your strict budget. Review the activities below to cut costs!")

                st.markdown("---")
                
                # Step 3: Map Integration
                st.subheader("🗺️ Your Travel Map")
                with st.spinner("Plotting locations on the map..."):
                    travel_map = create_itinerary_map(itinerary_data)
                    st_folium(travel_map, width=1000, height=500, returned_objects=[])
                
                st.markdown("---")
                
                # Step 4: Day-by-Day Itinerary Layout
                st.subheader("📅 Daily Itinerary")
                
                for day in itinerary_data.get("itinerary", []):
                    day_num = day.get("day")
                    with st.expander(f"Day {day_num} Itinerary", expanded=True):
                        
                        # Convert activities to a Pandas DataFrame for clean tabular display
                        activities = day.get("activities", [])
                        if activities:
                            df = pd.DataFrame(activities)
                            # Reorder and rename columns for a cleaner UI
                            df = df[["time", "place_name", "description", "estimated_cost"]]
                            df.columns = ["Time", "Place", "Description", "Estimated Cost ($)"]
                            st.dataframe(df, use_container_width=True, hide_index=True)
                        else:
                            st.write("No activities scheduled for this day.")