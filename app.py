# app.py
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from io import StringIO
from apify_client import ApifyClient

# --- App Configuration ---
st.set_page_config(page_title="Local Market Intelligence", layout="wide")
st.title("🗺️ Live Local Market Intelligence Tool")
st.write("Enter a business type and a location to generate a live competitive map.")

# --- User Input Fields ---
with st.form(key='search_form'):
    col1, col2 = st.columns(2)
    with col1:
        business_type = st.text_input("Business Type", "plumber")
    with col2:
        city = st.text_input("City, Province/State", "Calgary, AB")
    
    submit_button = st.form_submit_button(label='Generate Live Map')

# --- Main Logic ---
if submit_button:
    if not business_type or not city:
        st.warning("Please enter both a business type and a city.")
    else:
        try:
            # --- Step 1: Get Live Data from Apify ---
            with st.spinner(f"Scraping live data for '{business_type}' in '{city}'... This can take 1-2 minutes."):
                apify_client = ApifyClient(st.secrets["APIFY_TOKEN"])
                
                run_input = {
                    "searchStringsArray": [f"{business_type} in {city}"],
                    "maxCrawledPlacesPerSearch": 150, # Get up to 150 results
                }
                
                actor_run = apify_client.actor("apify/google-maps-scraper").call(run_input=run_input)
                
                items = [item for item in apify_client.dataset(actor_run["defaultDatasetId"]).iterate_items()]
                df = pd.DataFrame(items)

            st.success(f"Found {len(df)} businesses.")

            # --- Step 2: Prepare the Scraped Data ---
            with st.spinner("Processing data and building map..."):
                # Select and rename the columns we need
                df = df[['title', 'address', 'reviewsCount', 'stars', 'location.lat', 'location.lng']].rename(columns={
                    'title': 'Business Name', 'address': 'Address', 'reviewsCount': 'Reviews Count',
                    'stars': 'Stars', 'location.lat': 'Latitude', 'location.lng': 'Longitude'
                })
                
                df.dropna(subset=['Latitude', 'Longitude'], inplace=True)
                df['Stars'] = pd.to_numeric(df['Stars'], errors='coerce')
                df['Reviews Count'] = pd.to_numeric(df['Reviews Count'], errors='coerce').fillna(0)

                def get_color(stars):
                    if pd.isna(stars) or stars < 4.0: return 'red'
                    elif stars < 4.5: return 'orange'
                    else: return 'green'
                df['Color'] = df['Stars'].apply(get_color)
                df['Size'] = 2 + df['Reviews Count'].apply(lambda x: x**0.5)

                # --- Step 3: Create and Display the Map ---
                center_lat = df['Latitude'].mean()
                center_lon = df['Longitude'].mean()
                
                m = folium.Map(location=[center_lat, center_lon], zoom_start=12, tiles="CartoDB positron")
                
                for index, row in df.iterrows():
                    folium.CircleMarker(
                        location=[row['Latitude'], row['Longitude']], radius=row['Size'],
                        popup=f"<b>{row['Business Name']}</b><br>Stars: {row['Stars']}<br>Reviews: {row['Reviews Count']}",
                        tooltip=row['Business Name'], color=row['Color'], fill=True,
                        fill_color=row['Color'], fill_opacity=0.7
                    ).add_to(m)
            
            st.header("Interactive Market Map")
            st_folium(m, width=1200, height=700)

        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.error("This could be due to an invalid Apify Token or an issue with the data scraping. Please check your token in the Streamlit Cloud secrets.")
