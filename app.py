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
    col1, col2, col3 = st.columns(3)
    with col1:
        business_type = st.text_input("Business Type", "dentist")
    with col2:
        city = st.text_input("City", "London")
    with col3:
        country = st.text_input("Country", "Canada")
    
    submit_button = st.form_submit_button(label='Generate Live Map')

# --- Main Logic ---
if submit_button:
    if not business_type or not city or not country:
        st.warning("Please fill in all three fields.")
    else:
        try:
            full_search_query = f"{business_type} in {city}, {country}"
            
            with st.spinner(f"Scraping live data for '{full_search_query}'... This can take 1-2 minutes."):
                apify_client = ApifyClient(st.secrets["APIFY_TOKEN"])
                
                # *** MOST IMPORTANT CHANGE: Input now matches your n8n setup ***
                run_input = {
                    "searchStringsArray": [full_search_query],
                    "maxResults": 10, # Using the correct name for the limit
                }
                
                actor_run = apify_client.actor("compass~crawler-google-places").call(run_input=run_input)
                
                items = [item for item in apify_client.dataset(actor_run["defaultDatasetId"]).iterate_items()]
                
                if not items:
                    st.error(f"No results found for '{full_search_query}'. The actor ran but returned no businesses. Please try a more specific location (e.g., 'London, Ontario').")
                else:
                    df = pd.DataFrame(items)
                    st.success(f"Found {len(df)} businesses.")

                    with st.spinner("Processing data and building map..."):
                        # *** UPDATED COLUMN NAMES: Matching the output from your n8n screenshot ***
                        df = df[['title', 'address', 'totalScore', 'reviewsCount', 'location']].rename(columns={
                            'title': 'Business Name', 'address': 'Address', 'totalScore': 'Stars', 'reviewsCount': 'Reviews Count'
                        })

                        # Extract lat/lng from the 'location' column
                        df['Latitude'] = df['location'].apply(lambda loc: loc.get('lat'))
                        df['Longitude'] = df['location'].apply(lambda loc: loc.get('lng'))
                        
                        df.dropna(subset=['Latitude', 'Longitude'], inplace=True)
                        df['Stars'] = pd.to_numeric(df['Stars'], errors='coerce')
                        df['Reviews Count'] = pd.to_numeric(df['Reviews Count'], errors='coerce').fillna(0)

                        def get_color(stars):
                            if pd.isna(stars) or stars < 4.0: return 'red'
                            elif stars < 4.5: return 'orange'
                            else: return 'green'
                        df['Color'] = df['Stars'].apply(get_color)
                        df['Size'] = 2 + df['Reviews Count'].apply(lambda x: x**0.5)

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
                    st_folium(m, width=1200, height=700, returned_objects=[])

        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.error("There might be an issue with the Apify Actor or your token. Please ensure the actor input format is correct.")

else:
    st.header("Sample Market Analysis")
    st.image("sample.png", caption="A sample analysis map showing businesses in London, ON.")
