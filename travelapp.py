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
              "address_for_geocoding": "Strict, official location name and city ONLY (e.g., 'Eiffel Tower, Paris'). NO descriptive words."
            }}
          ]
        }}
      ]
    }}
    """
    
    try:
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

def create_itinerary_map(itinerary_data, destination_city, style_choice="Standard"):
    """
    Generates a Folium map with markers, premium themes, and fallback geocoding.
    """
    tiles_mapping = {
        "Standard": "OpenStreetMap",
        "Dark Mode": "CartoDB dark_matter",
        "Terrain": "OpenTopoMap"
    }
    selected_tile = tiles_mapping.get(style_choice, "OpenStreetMap")

    colors = ['blue', 'green', 'red', 'purple', 'orange', 'darkred', 'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue', 'darkpurple', 'pink', 'lightblue', 'lightgreen', 'gray', 'black']
    
    m = folium.Map(location=[0, 0], zoom_start=2, tiles=selected_tile)
    coordinates_list = []

    for day_data in itinerary_data.get("itinerary", []):
        day_num = day_data.get("day", 1)
        marker_color = colors[(day_num - 1) % len(colors)] 
        
        for activity in day_data.get("activities", []):
            address = activity.get("address_for_geocoding")
            place_name = activity.get("place_name", "Unknown Place")
            
            coords = None
            if address:
                coords = geocode_address(address)
            if not coords and place_name:
                coords = geocode_address(f"{place_name}, {destination_city}")
            if not coords:
                coords = geocode_address(destination_city)

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

    if coordinates_list:
        m.fit_bounds(coordinates_list)
    else:
        st.warning("Could not map the locations. The addresses provided by the AI might be too vague.")
        
    return m

def generate_download_text(itinerary_data, destination, duration, budget):
    """Formats the JSON data into a clean, readable text file for download."""
    text = f"🎒 TRAVEL ITINERARY: {destination.upper()} ({duration} DAYS)\n"
    text += f"{'='*50}\n"
    text += f"Budget: ${budget} | Estimated Cost: ${itinerary_data.get('estimated_total_cost')}\n\n"
    text += f"TRIP SUMMARY:\n{itinerary_data.get('trip_summary')}\n\n"
    text += f"{'='*50}\n\n"
    
    for day in itinerary_data.get("itinerary", []):
        text += f"DAY {day.get('day')}\n"
        text += f"{'-'*20}\n"
        for act in day.get("activities", []):
            text += f"[{act.get('time')}] {act.get('place_name')} - Est. Cost: ${act.get('estimated_cost')}\n"
            text += f"Details: {act.get('description')}\n"
            text += f"Address: {act.get('address_for_geocoding')}\n\n"
    return text

# ==========================================
# 2. Streamlit UI Layout & State Setup
# ==========================================

st.set_page_config(page_title="Student AI Travel Planner", page_icon="🌍", layout="wide")

# Initialize session state for Notes
if 'user_notes' not in st.session_state:
    st.session_state['user_notes'] = ""

try:
    api_key = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("API key is missing! Please configure it in the Streamlit Cloud Settings.")
    st.stop()
    
st.title("🎒 Student AI Travel Planner")
st.write("Plan a budget-friendly, personalized trip powered by Google Gemini and interactive maps.")

# Setup Tabs for Planner vs Notes
tab_planner, tab_notes = st.tabs(["🗺️ Trip Planner", "📝 Key Notes & Planner Book"])

# --- TAB 1: MAIN PLANNER ---
with tab_planner:
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

    if submitted:
        if not destination:
            st.error("Please enter a destination.")
        else:
            with st.spinner(f"Planning your {duration}-day student trip to {destination}..."):
                
                itinerary_data = generate_itinerary(api_key, destination, duration, budget, interests)
                
                if itinerary_data:
                    st.success("Itinerary generated successfully!")
                    
                    # Layout: Trip Overview & Download Button
                    st.subheader("📊 Trip Overview")
                    st.write(itinerary_data.get("trip_summary", ""))
                    
                    est_cost = itinerary_data.get("estimated_total_cost", 0)
                    delta = budget - est_cost
                    
                    metric_col1, metric_col2, metric_col3 = st.columns(3)
                    metric_col1.metric("Your Budget", f"${budget}")
                    metric_col2.metric("Estimated Cost", f"${est_cost}", delta=f"${delta} remaining", delta_color="normal")
                    
                    if est_cost > budget:
                        st.warning("Warning: The AI estimated cost slightly exceeds your strict budget. Review the activities below to cut costs!")

                    # Download Button
                    download_text = generate_download_text(itinerary_data, destination, duration, budget)
                    st.download_button(
                        label="📄 Download Itinerary (Text File)",
                        data=download_text,
                        file_name=f"{destination.replace(' ', '_')}_itinerary.txt",
                        mime="text/plain"
                    )

                    st.markdown("---")
                    
                    # Map Integration with Theme Selector
                    st.subheader("🗺️ Your Travel Map")
                    map_style = st.radio("Select Map Theme:", ["Standard", "Dark Mode", "Terrain"], horizontal=True)
                    
                    with st.spinner("Plotting locations on the map..."):
                        travel_map = create_itinerary_map(itinerary_data, destination, map_style)
                        st_folium(travel_map, width=1000, height=500, returned_objects=[])
                    
                    st.markdown("---")
                    
                    # Day-by-Day Itinerary Layout
                    st.subheader("📅 Daily Itinerary")
                    for day in itinerary_data.get("itinerary", []):
                        day_num = day.get("day")
                        with st.expander(f"Day {day_num} Itinerary", expanded=True):
                            activities = day.get("activities", [])
                            if activities:
                                df = pd.DataFrame(activities)
                                df = df[["time", "place_name", "description", "estimated_cost"]]
                                df.columns = ["Time", "Place", "Description", "Estimated Cost ($)"]
                                st.dataframe(df, use_container_width=True, hide_index=True)
                            else:
                                st.write("No activities scheduled for this day.")

# --- TAB 2: KEY NOTES ---
with tab_notes:
    st.subheader("📝 Travel Notebook")
    st.write("Use this space to jot down flight numbers, hotel ideas, packing lists, or specific links. *Note: Data stays saved as long as your browser tab is open.*")
    
    user_input = st.text_area("Your Notes:", value=st.session_state['user_notes'], height=300)
    
    if st.button("Save Notes", type="primary"):
        st.session_state['user_notes'] = user_input
        st.success("Notes saved successfully to this session!")
