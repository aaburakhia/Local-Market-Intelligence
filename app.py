import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from io import StringIO
from apify_client import ApifyClient
import numpy as np

# --- App Configuration & Style Injection ---
st.set_page_config(page_title="Local Market Intelligence", layout="wide")

# This is the CSS fix that forces the layout to be truly wide.
st.markdown("""
    <style>
    .main .block-container {
        padding-top: 2rem;
        padding-left: 5rem;
        padding-right: 5rem;
    }
    .stApp {
        background-color: #F0F2F6; /* A light grey background like many modern apps */
    }
    .st-emotion-cache-z5fcl4 {
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Header ---
st.title("🗺️ Live Local Market Intelligence Tool")
st.write("Enter a business type and a location to generate a live competitive map.")

# --- User Input Form ---
with st.form(key='search_form'):
    st.markdown("##### **Search Parameters**")
    col1, col2, col3 = st.columns(3)
    with col1:
        business_type = st.text_input("Business Type", "dentist", label_visibility="collapsed")
    with col2:
        city = st.text_input("City", "Toronto", label_visibility="collapsed")
    with col3:
        country = st.text_input("Country", "Canada", label_visibility="collapsed")
    
    submit_button = st.form_submit_button(label='Generate Live Map')

# --- Main Application Logic ---
if 'map' not in st.session_state:
    st.session_state.map = None

if submit_button:
    if not business_type or not city or not country:
        st.warning("Please fill in all three fields.")
    else:
        try:
            full_search_query = f"{business_type} in {city}, {country}"
            
            with st.spinner(f"Scraping live data for '{full_search_query}'... This can take 1-2 minutes."):
                apify_client = ApifyClient(st.secrets["APIFY_TOKEN"])
                
                # *** FIX #1: Using the correct 'maxResults' (camelCase) parameter ***
                run_input = {
                    "searchStringsArray": [full_search_query],
                    "maxResults": 10,
                }
                
                actor_run = apify_client.actor("compass~crawler-google-places").call(run_input=run_input)
                items = [item for item in apify_client.dataset(actor_run["defaultDatasetId"]).iterate_items()]
                
                if not items:
                    st.error(f"No results found for '{full_search_query}'. Please try a different search.")
                    st.session_state.map = None
                else:
                    df = pd.DataFrame(items)
                    st.success(f"Successfully found and processed {len(df)} businesses.")

                    with st.spinner("Building map..."):
                        # Data processing...
                        df = df[['title', 'address', 'totalScore', 'reviewsCount', 'location']].rename(columns={
                            'title': 'Business Name', 'address': 'Address', 'totalScore': 'Stars', 'reviewsCount': 'Reviews Count'
                        })
                        df['Latitude'] = df['location'].apply(lambda loc: loc.get('lat') if loc else None)
                        df['Longitude'] = df['location'].apply(lambda loc: loc.get('lng') if loc else None)
                        df.dropna(subset=['Latitude', 'Longitude'], inplace=True)
                        df['Stars'] = pd.to_numeric(df['Stars'], errors='coerce')
                        df['Reviews Count'] = pd.to_numeric(df['Reviews Count'], errors='coerce').fillna(0)

                        def get_color(stars):
                            if pd.isna(stars) or stars < 4.0: return 'red'
                            elif stars < 4.5: return 'orange'
                            else: return 'green'
                        df['Color'] = df['Stars'].apply(get_color)
                        df['Size'] = df['Reviews Count'].apply(lambda x: 4 + (x**0.5) * 0.3)

                        # Create the map object
                        center_lat = df['Latitude'].mean()
                        center_lon = df['Longitude'].mean()
                        m = folium.Map(location=[center_lat, center_lon], zoom_start=12, tiles="CartoDB positron")
                        for index, row in df.iterrows():
                            folium.CircleMarker(location=[row['Latitude'], row['Longitude']], radius=row['Size'], popup=f"<b>{row['Business Name']}</b><br>Stars: {row['Stars']}<br>Reviews: {row['Reviews Count']}", tooltip=row['Business Name'], color=row['Color'], fill=True, fill_color=row['Color'], fill_opacity=0.7).add_to(m)
                    
                    # Store the generated map in the session state
                    st.session_state.map = m

        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.session_state.map = None

# --- Display the Map and Legend ---
if st.session_state.map:
    st.header("Interactive Market Map")
    st_folium(st.session_state.map, use_container_width=True, height=600)

    st.header("Legend")
    col1, col2, col3, col4 = st.columns([1,4,1,4])
    with col1:
        st.markdown('<div style="width:20px; height:20px; border-radius:50%; background-color:green; border: 1px solid #ddd;"></div>', unsafe_allow_html=True)
    with col2:
        st.write("Excellent Reputation (4.5+ Stars)")
    with col3:
        st.markdown('<div style="width:20px; height:20px; border-radius:50%; background-color:orange; border: 1px solid #ddd;"></div>', unsafe_allow_html=True)
    with col4:
        st.write("Average Reputation (4.0-4.4 Stars)")
    
    col1, col2, col3, col4 = st.columns([1,4,1,4])
    with col1:
        st.markdown('<div style="width:20px; height:20px; border-radius:50%; background-color:red; border: 1px solid #ddd;"></div>', unsafe_allow_html=True)
    with col2:
        st.write("Poor Reputation (< 4.0 Stars)")
    with col3:
        st.markdown("&#9679;") # A circle character
    with col4:
        st.write("Circle size corresponds to the number of reviews.")
        
else:
    # Show the placeholder image if no map has been generated yet
    st.image("sample.png", caption="A sample analysis map showing businesses in London, ON.")
