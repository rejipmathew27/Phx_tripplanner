import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from datetime import datetime, timedelta
import pandas as pd

# ---------------------------------------------------------
# CONFIGURATION & STYLING
# ---------------------------------------------------------
st.set_page_config(page_title="Southwest Road Trip", page_icon="🌵", layout="wide")

# Notion-like custom CSS for cleaner look
st.markdown("""
<style>
    .stApp {
        background-color: #FFFFFF;
        color: #37352F;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, "Apple Color Emoji", Arial, sans-serif, "Segoe UI Emoji", "Segoe UI Symbol";
    }
    h1, h2, h3 {
        font-weight: 600;
        letter-spacing: -0.02em;
    }
    .itinerary-card {
        background-color: #F7F7F5;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
        border: 1px solid #E0E0E0;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .stButton>button {
        border-radius: 6px;
        border: 1px solid #E0E0E0;
        background-color: white;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# DATA: LOCATIONS & COORDINATES
# ---------------------------------------------------------
LOCATIONS = {
    "Phoenix Airport": {"coords": [33.4352, -112.0101], "type": "start"},
    "Route 93": {"coords": [34.7000, -113.3000], "type": "waypoint"}, # Approximate
    "Henderson": {"coords": [36.0395, -114.9817], "type": "stop"},
    "Hoover Dam": {"coords": [36.0160, -114.7377], "type": "highlight"},
    "Bypass Bridge": {"coords": [36.0145, -114.7390], "type": "waypoint"},
    "Las Vegas Strip": {"coords": [36.1147, -115.1728], "type": "stop"},
    "Grand Canyon West": {"coords": [35.9897, -113.8214], "type": "highlight"},
    "Grand Canyon South": {"coords": [36.0544, -112.1401], "type": "highlight"},
    "Flagstaff": {"coords": [35.1983, -111.6513], "type": "stop"},
    "Sedona": {"coords": [34.8697, -111.7610], "type": "stop"},
    "Cathedral Rock": {"coords": [34.8189, -111.7925], "type": "highlight"},
    "Chapel of Holy Cross": {"coords": [34.8322, -111.7663], "type": "highlight"},
    "Bell Rock": {"coords": [34.8016, -111.7613], "type": "highlight"},
    "Glendale": {"coords": [33.5387, -112.1860], "type": "stop"},
    "St. Thomas Orthodox Church": {"coords": [33.4660, -112.0310], "type": "highlight"}, # Approx near 2317 E Yale St
}

# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------

def get_weather(lat, lon, date):
    """
    Fetches weather data from Open-Meteo API.
    Uses 'forecast' endpoint if date is within range, otherwise fallback.
    """
    try:
        date_str = date.strftime('%Y-%m-%d')
        
        # Determine if we need forecast or historical (simplified logic)
        # Open-Meteo Forecast is good for current/near future
        url = "https://api.open-meteo.com/v1/forecast"
        
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": ["temperature_2m_max", "temperature_2m_min", "weathercode"],
            "temperature_unit": "fahrenheit", # Added Fahrenheit unit
            "timezone": "auto",
            "start_date": date_str,
            "end_date": date_str
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if "daily" in data:
            t_max = data["daily"]["temperature_2m_max"][0]
            t_min = data["daily"]["temperature_2m_min"][0]
            code = data["daily"]["weathercode"][0]
            
            # Simple WMO code mapping
            condition = "Sunny"
            icon = "☀️"
            if code in [1, 2, 3]: condition, icon = "Partly Cloudy", "qw⛅"
            elif code in [45, 48]: condition, icon = "Foggy", "🌫️"
            elif code in [51, 53, 55, 61, 63, 65]: condition, icon = "Rainy", "🌧️"
            elif code in [71, 73, 75]: condition, icon = "Snow", "❄️"
            elif code >= 95: condition, icon = "Stormy", "⚡"
            
            return f"{icon} {condition} | H: {t_max}°F L: {t_min}°F"
        else:
            return "Weather unavailable (Date out of range)"
    except Exception as e:
        return "Weather service offline"

def create_map(day_selection, show_all=False):
    """Creates a Folium map based on the selected day."""
    
    # Center map roughly between Phoenix and Vegas
    m = folium.Map(location=[34.5, -112.5], zoom_start=7, tiles="CartoDB positron")

    routes = []
    
    # Define route segments
    if show_all or day_selection == "Day 1":
        routes.append({
            "name": "Day 1: PHX to Vegas",
            "color": "#E91E63", # Pink
            "points": ["Phoenix Airport", "Route 93", "Henderson", "Hoover Dam", "Las Vegas Strip"]
        })
    
    if show_all or day_selection == "Day 2":
        routes.append({
            "name": "Day 2: Vegas to Flagstaff",
            "color": "#9C27B0", # Purple
            "points": ["Las Vegas Strip", "Hoover Dam", "Grand Canyon West", "Grand Canyon South", "Flagstaff"]
        })
        
    if show_all or day_selection == "Day 3":
        routes.append({
            "name": "Day 3: Sedona Exploration",
            "color": "#FF9800", # Orange
            "points": ["Flagstaff", "Sedona", "Cathedral Rock", "Chapel of Holy Cross", "Bell Rock"]
        })

    if show_all or day_selection == "Day 4":
        routes.append({
            "name": "Day 4: Return to Phoenix",
            "color": "#4CAF50", # Green
            "points": ["Sedona", "Glendale", "St. Thomas Orthodox Church", "Phoenix Airport"]
        })

    # Draw Lines and Markers
    for route in routes:
        line_coords = []
        for point_name in route["points"]:
            loc_data = LOCATIONS[point_name]
            lat, lon = loc_data["coords"]
            line_coords.append([lat, lon])
            
            # Icons based on type
            icon_color = "gray"
            icon_icon = "info-sign"
            
            if loc_data["type"] == "start": icon_color, icon_icon = "green", "plane"
            elif loc_data["type"] == "stop": icon_color, icon_icon = "blue", "bed"
            elif loc_data["type"] == "highlight": icon_color, icon_icon = "red", "camera"
            
            folium.Marker(
                [lat, lon],
                popup=point_name,
                tooltip=point_name,
                icon=folium.Icon(color=icon_color, icon=icon_icon, prefix='fa', icon_color='white')
            ).add_to(m)
        
        folium.PolyLine(
            line_coords,
            color=route["color"],
            weight=4,
            opacity=0.8,
            tooltip=route["name"]
        ).add_to(m)

    return m

# ---------------------------------------------------------
# APP UI
# ---------------------------------------------------------

# Sidebar
with st.sidebar:
    st.title("🗺️ Trip Settings")
    
    start_date = st.date_input("Start Date", datetime.now())
    
    view_mode = st.radio(
        "View Mode",
        ["Overview", "Day 1", "Day 2", "Day 3", "Day 4"]
    )
    
    st.markdown("---")
    st.caption("Trip Stats")
    st.markdown("**Total Distance:** ~800 miles")
    st.markdown("**Driving Time:** ~16 hours")
    st.markdown("**States:** AZ, NV")

# Main Content
st.title("🌵 Southwest Road Trip Planner")
st.caption("Phoenix • Las Vegas • Grand Canyon • Sedona • Glendale")

# Dates for each day
day_1_date = start_date
day_2_date = start_date + timedelta(days=1)
day_3_date = start_date + timedelta(days=2)
day_4_date = start_date + timedelta(days=3)

# Map Section
st.markdown("### 📍 Interactive Route Map")
map_obj = create_map(view_mode, show_all=(view_mode == "Overview"))
st_folium(map_obj, width=1200, height=500)

# Itinerary Section
st.markdown("### 🗓️ Detailed Itinerary")

# Day 1
if view_mode in ["Overview", "Day 1"]:
    with st.expander(f"Day 1: Phoenix to Las Vegas ({day_1_date.strftime('%b %d')})", expanded=True):
        weather = get_weather(36.1147, -115.1728, day_1_date) # Weather for Vegas
        st.markdown(f"**Weather Forecast (Las Vegas):** `{weather}`")
        
        st.markdown("""
        <div class="itinerary-card">
            <h4>🛫 Morning: Arrival & Drive</h4>
            <ul>
                <li>Start at <b>Phoenix Sky Harbor (PHX)</b>.</li>
                <li>Take Route 93 North towards Las Vegas (The Joshua Tree Highway).</li>
            </ul>
        </div>
        
        <div class="itinerary-card">
            <h4>🚧 Mid-Day: Engineering Marvels</h4>
            <ul>
                <li>Stop at <b>Henderson</b> for lunch.</li>
                <li><b>Option A:</b> Visit <b>Hoover Dam</b> directly (Security check required).</li>
                <li><b>Option B:</b> Take the Bypass Bridge (Sunset/Mike O'Callaghan) for the view without stopping.</li>
            </ul>
        </div>
        
        <div class="itinerary-card">
            <h4>🎰 Evening: The Strip</h4>
            <ul>
                <li>Arrive in <b>Las Vegas</b>.</li>
                <li>Check into hotel on the Strip.</li>
                <li>Dinner and Bellagio Fountains.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

# Day 2
if view_mode in ["Overview", "Day 2"]:
    with st.expander(f"Day 2: The Grand Loop ({day_2_date.strftime('%b %d')})", expanded=True):
        weather = get_weather(36.0544, -112.1401, day_2_date) # Weather for GC South
        st.markdown(f"**Weather Forecast (Grand Canyon):** `{weather}`")
        
        st.markdown("""
        <div class="itinerary-card">
            <h4>🏜️ Morning: West Rim</h4>
            <ul>
                <li>Depart Las Vegas early (7:00 AM).</li>
                <li>Drive to <b>Grand Canyon West</b> (Skywalk).</li>
                <li><i>Note: This is Hualapai tribal land, requires separate entry fee.</i></li>
            </ul>
        </div>
        
        <div class="itinerary-card">
            <h4>🌲 Afternoon: South Rim</h4>
            <ul>
                <li>Long drive East to <b>Grand Canyon South Rim</b> (National Park).</li>
                <li>Visit Mather Point and Yavapai Geology Museum.</li>
                <li>Sunset at Hopi Point.</li>
            </ul>
        </div>
        
        <div class="itinerary-card">
            <h4>🛌 Evening: Flagstaff</h4>
            <ul>
                <li>Drive South to <b>Flagstaff, AZ</b>.</li>
                <li>Dinner in historic downtown Flagstaff (Route 66).</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

# Day 3
if view_mode in ["Overview", "Day 3"]:
    with st.expander(f"Day 3: Red Rock Country ({day_3_date.strftime('%b %d')})", expanded=True):
        weather = get_weather(34.8697, -111.7610, day_3_date) # Weather for Sedona
        st.markdown(f"**Weather Forecast (Sedona):** `{weather}`")
        
        st.markdown("""
        <div class="itinerary-card">
            <h4>⛰️ Morning: The Vortexes</h4>
            <ul>
                <li>Drive Hwy 89A (Scenic Switchbacks) from Flagstaff to <b>Sedona</b>.</li>
                <li>Hike or view <b>Cathedral Rock</b>.</li>
                <li>Visit <b>Bell Rock</b>.</li>
            </ul>
        </div>
        
        <div class="itinerary-card">
            <h4>⛪ Afternoon: Architecture & Views</h4>
            <ul>
                <li>Visit <b>Chapel of the Holy Cross</b> (built into the red rocks).</li>
                <li>Lunch at Tlaquepaque Arts & Shopping Village.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

# Day 4
if view_mode in ["Overview", "Day 4"]:
    with st.expander(f"Day 4: Glendale & Departure ({day_4_date.strftime('%b %d')})", expanded=True):
        weather = get_weather(33.5387, -112.1860, day_4_date) # Weather for Glendale
        st.markdown(f"**Weather Forecast (Phoenix/Glendale):** `{weather}`")
        
        st.markdown("""
        <div class="itinerary-card">
            <h4>🏈 Morning: Glendale</h4>
            <ul>
                <li>Drive South on I-17 from Sedona to <b>Glendale</b>.</li>
                <li>Visit Historic Downtown Glendale or Westgate Entertainment District.</li>
            </ul>
        </div>
        
        <div class="itinerary-card">
            <h4>⛪ Afternoon: St. Thomas Orthodox Church</h4>
            <ul>
                <li>Head to <b>2317 E Yale St, Phoenix, AZ 85006</b>.</li>
                <li>Visit St. Thomas Orthodox Church.</li>
            </ul>
        </div>

        <div class="itinerary-card">
            <h4>🛫 Late Afternoon: Departure</h4>
            <ul>
                <li>Short drive to <b>Phoenix Sky Harbor (PHX)</b>.</li>
                <li>Return Rental Car & Fly Out.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

# ---------------------------------------------------------
# EXPORT
# ---------------------------------------------------------
st.markdown("---")
col1, col2 = st.columns([3, 1])
with col1:
    st.caption("Trip Planner v1.1 | Data by OpenStreetMap & Open-Meteo")
with col2:
    if st.button("Download Itinerary PDF"):
        st.toast("Feature coming soon!", icon="📄")
