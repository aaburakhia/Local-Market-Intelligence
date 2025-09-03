import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from io import StringIO
from apify_client import ApifyClient
import numpy as np

# --- App Configuration ---
st.set_page_config(page_title="Local Market Intelligence", layout="wide")

# *** THIS IS THE FIX ***
# Inject custom CSS to force the map container to be full-width
st.markdown(
    """
    <style>
    /* This is to remove the padding and margin around the main block */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }
    /* This is to make the map take the full width */
    iframe {
        width: 100%;
    }
    </style>
    """,
    unsafe_allow_html=True
)


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

# (The rest of the code is exactly the same as Version 6)
if submit_button:
    if not business_type or not city or not country:
        st.warning("Please fill in all three fields.")
    else:
        try:
            full_search_query = f"{business_type} in {city}, {country}"
            
            with st.spinner(f"Scraping live data for '{full_search_query}'... This can take 1-2 minutes."):
                apify_client = ApifyClient(st.secrets["APIFY_TOKEN"])
                run_input = { "searchStringsArray": [full_search_query], "max_results": 150, }
                actor_run = apify_client.actor("compass~crawler-google-places").call(run_input=run_input)
                items = [item for item in apify_client.dataset(actor_run["defaultDatasetId"]).iterate_items()]
                
                if not items:
                    st.error(f"No results found for '{full_search_query}'. The actor ran but returned no businesses. Please try a more specific location (e.g., 'London, Ontario').")
                else:
                    df = pd.DataFrame(items)
                    st.success(f"Successfully found and processed {len(df)} businesses.")

                    with st.spinner("Building map..."):
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

                        center_lat = df['Latitude'].mean()
                        center_lon = df['Longitude'].mean()
                        m = folium.Map(location=[center_lat, center_lon], zoom_start=12, tiles="CartoDB positron")
                        for index, row in df.iterrows():
                            folium.CircleMarker(location=[row['Latitude'], row['Longitude']], radius=row['Size'], popup=f"<b>{row['Business Name']}</b><br>Stars: {row['Stars']}<br>Reviews: {row['Reviews Count']}", tooltip=row['Business Name'], color=row['Color'], fill=True, fill_color=row['Color'], fill_opacity=0.7).add_to(m)
                    
                    st.header("Interactive Market Map")
                    st_folium(m, height=700, returned_objects=[])

                    st.header("Legend")
                    st.markdown("""<style>.legend-item { display: flex; align-items: center; margin-bottom: 5px; }.legend-color { width: 20px; height: 20px; border-radius: 50%; margin-right: 10px; border: 1px solid #ddd;}</style><div class="legend-item"><div class="legend-color" style="background-color: green;"></div>Excellent Reputation (4.5+ Stars)</div><div class="legend-item"><div class="legend-color" style="background-color: orange;"></div>Average Reputation (4.0 - 4.4 Stars)</div><div class="legend-item"><div class="legend-color" style="background-color: red;"></div>Poor Reputation (< 4.0 Stars)</div><br>&#8226; <b>Circle Size</b> corresponds to the number of online reviews (a proxy for visibility and traffic).""", unsafe_allow_html=True)

        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.error("There might be an issue with the Apify Actor or your token. Please check the actor input format and your Streamlit Cloud secrets.")

else:
    st.header("Sample Market Analysis")
    st.image("sample.png", caption="A sample analysis map showing businesses in London, ON.")
