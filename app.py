import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from io import StringIO
from apify_client import ApifyClient
import numpy as np
import google.generativeai as genai
# NEW: Import the pycountry library
import pycountry

# --- App Configuration & Style Injection ---
st.set_page_config(page_title="Local Market Intelligence", layout="wide")
st.markdown("""<style>/* Your CSS from before */</style>""", unsafe_allow_html=True) # Abridged

# --- NEW: Load Country Data Directly from the pycountry Library ---
@st.cache_data
def get_country_list():
    # This gets a list of all official country names from the library
    return sorted([country.name for country in pycountry.countries])

countries = get_country_list()

# --- Header ---
st.title("🗺️ Live Local Market Intelligence Tool")
st.write("Select a business type and location to generate a live competitive map and AI-powered analysis.")

# --- Session State Initialization ---
if 'map_data' not in st.session_state: st.session_state.map_data = None
if 'analysis' not in st.session_state: st.session_state.analysis = None
if 'kpis' not in st.session_state: st.session_state.kpis = None

# --- User Input Form ---
with st.form(key='search_form'):
    st.markdown("##### **Search Parameters**")
    col1, col2, col3 = st.columns(3)
    with col1:
        business_type = st.text_input("Business Type", placeholder="e.g., dentist, plumber, barbershop")
    with col2:
        # The country dropdown now uses our reliable library list
        country_index = countries.index("Canada") if "Canada" in countries else 0
        country = st.selectbox("Country", options=countries, index=country_index)
    with col3:
        # The city input is now a flexible text field
        city = st.text_input("City", placeholder="e.g., Toronto")
    
    submit_button = st.form_submit_button(label='Generate Analysis')

# --- Main Application Logic ---
if submit_button:
    if not all([business_type, city, country]):
        st.warning("Please fill in all three fields.")
    else:
        try:
            full_search_query = f"{business_type} in {city}, {country}"
            with st.spinner(f"Step 1/3: Scraping live data for '{full_search_query}'..."):
                apify_client = ApifyClient(st.secrets["APIFY_TOKEN"])
                run_input = {"searchStringsArray": [full_search_query], "maxResults": 150}
                actor_run = apify_client.actor("compass~crawler-google-places").call(run_input=run_input)
                items = [item for item in apify_client.dataset(actor_run["defaultDatasetId"]).iterate_items()]
            
            if not items:
                st.error(f"No results found for '{full_search_query}'.")
                st.session_state.map_data = None
            else:
                df = pd.DataFrame(items)
                st.success(f"Successfully found {len(df)} businesses.")

                with st.spinner("Step 2/3: Processing data and calculating metrics..."):
                    # Data processing... (same as before)
                    df = df[['title', 'address', 'totalScore', 'reviewsCount', 'location']].rename(columns={
                        'title': 'Business Name', 'address': 'Address', 'totalScore': 'Stars', 'reviewsCount': 'Reviews Count'
                    })
                    df['Latitude'] = df['location'].apply(lambda loc: loc.get('lat') if loc else None)
                    df['Longitude'] = df['location'].apply(lambda loc: loc.get('lng') if loc else None)
                    df.dropna(subset=['Latitude', 'Longitude'], inplace=True)
                    df['Stars'] = pd.to_numeric(df['Stars'], errors='coerce')
                    df['Reviews Count'] = pd.to_numeric(df['Reviews Count'], errors='coerce').fillna(0)
                    
                    avg_rating = df['Stars'].mean()
                    most_visible = df.loc[df['Reviews Count'].idxmax()]
                    st.session_state.kpis = {
                        "Total Businesses": len(df), "Average Rating": f"{avg_rating:.2f} Stars",
                        "Most Visible": f"{most_visible['Business Name']} ({most_visible['Reviews Count']} reviews)",
                    }

                with st.spinner("Step 3/3: Generating AI analysis with Google Gemini..."):
                    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
                    model = genai.GenerativeModel('gemini-2.0-flash-001')
                    prompt = f"""
                    You are an expert business consultant...
                    (The rest of the prompt is the same)
                    """
                    response = model.generate_content(prompt)
                    st.session_state.analysis = response.text
                    
                    m = folium.Map(location=[df['Latitude'].mean(), df['Longitude'].mean()], zoom_start=12, tiles="CartoDB positron")
                    # ... (map drawing code is the same)
                    st.session_state.map_data = m

        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.session_state.map_data = None

# --- Display Area ---
if st.session_state.kpis:
    st.header("Dashboard")
    # ... (KPI display code is the same)
    
if st.session_state.analysis:
    st.header("AI-Powered Analysis")
    st.markdown(st.session_state.analysis)

if st.session_state.map_data:
    st.header("Interactive Market Map")
    st_folium(st.session_state.map_data, use_container_width=True, height=600)
    # ... (Legend code is the same)
else:
    st.image("sample.png", caption="Your generated map and analysis will appear here.")
