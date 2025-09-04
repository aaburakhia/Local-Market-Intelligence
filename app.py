import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from io import StringIO
from apify_client import ApifyClient
import numpy as np
import google.generativeai as genai
import pycountry
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

# --- App Configuration & Enhanced CSS ---
st.set_page_config(page_title="Market Intelligence Pro", layout="wide", page_icon="🎯")

st.markdown("""
<style>
/* Professional styling */
.main-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 2rem;
    border-radius: 15px;
    margin-bottom: 2rem;
    color: white;
    text-align: center;
    box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
}

.metric-container {
    background: white;
    padding: 1.5rem;
    border-radius: 12px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    border-left: 5px solid #667eea;
    margin: 1rem 0;
    transition: transform 0.2s ease;
}

.metric-container:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.15);
}

.analysis-container {
    background: #f8f9ff;
    border: 2px solid #e1e5f7;
    border-radius: 12px;
    padding: 2rem;
    margin: 1rem 0;
}

.legend-container {
    background: white;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 1rem;
    margin: 1rem 0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.insight-highlight {
    background: linear-gradient(90deg, #fff3cd 0%, #ffeaa7 100%);
    border-left: 4px solid #f39c12;
    padding: 1rem;
    border-radius: 8px;
    margin: 1rem 0;
}

.data-power-message {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1rem;
    border-radius: 10px;
    text-align: center;
    margin: 1rem 0;
    font-size: 1.1em;
}

/* Hide Streamlit elements for professional look */
.reportview-container .main footer {visibility: hidden;}
.stApp > header {visibility: hidden;}
#MainMenu {visibility: hidden;}
.stDeployButton {display:none;}

/* Enhanced form styling */
.stForm {
    background: white;
    padding: 2rem;
    border-radius: 12px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}
</style>
""", unsafe_allow_html=True)

# --- Enhanced Data Loading ---
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_country_list():
    return sorted([country.name for country in pycountry.countries])

# --- Professional Header Component ---
def render_header():
    st.markdown("""
    <div class="main-header">
        <h1>🎯 Market Intelligence Pro</h1>
        <p style="font-size: 1.2em; margin: 0;">Real-time competitive analysis powered by AI</p>
        <small>Transform data into competitive advantage</small>
    </div>
    """, unsafe_allow_html=True)

# --- Data Power Messages ---
def show_data_power_messages(current_step, total_steps=3):
    messages = [
        "🔥 Data is your competitive superpower - Collecting market intelligence...",
        "⚡ Transforming raw data into strategic insights...",
        "🧠 AI is analyzing patterns humans miss - Almost ready!"
    ]
    
    progress = current_step / total_steps
    st.progress(progress)
    
    if current_step < len(messages):
        st.markdown(f"""
        <div class="data-power-message">
            {messages[current_step]}
        </div>
        """, unsafe_allow_html=True)

# --- Enhanced KPI Dashboard ---
def render_kpi_dashboard(kpis, df):
    st.markdown("### 📊 Market Overview Dashboard")
    
    # Calculate additional metrics
    high_rated = len(df[df['Stars'] >= 4.0]) if len(df) > 0 else 0
    low_review = len(df[df['Reviews Count'] < 10]) if len(df) > 0 else 0
    opportunity_score = min(10, max(1, (low_review / len(df) * 10) if len(df) > 0 else 5))
    
    # Enhanced metrics with better formatting
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-container">
            <h3 style="color: #667eea; margin: 0;">🏪 Total Competitors</h3>
            <h2 style="margin: 0.5rem 0;">{kpis['Total Businesses']}</h2>
            <small style="color: #666;">Active in this market</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        avg_rating_num = float(kpis["Average Rating"].split()[0])
        rating_color = "#27ae60" if avg_rating_num >= 4.0 else "#f39c12" if avg_rating_num >= 3.5 else "#e74c3c"
        st.markdown(f"""
        <div class="metric-container">
            <h3 style="color: {rating_color}; margin: 0;">⭐ Avg Rating</h3>
            <h2 style="margin: 0.5rem 0; color: {rating_color};">{kpis["Average Rating"]}</h2>
            <small style="color: #666;">{high_rated} businesses rated 4.0+</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-container">
            <h3 style="color: #9b59b6; margin: 0;">🏆 Market Leader</h3>
            <h4 style="margin: 0.5rem 0; font-size: 1rem;">{kpis["Most Visible"].split('(')[0].strip()}</h4>
            <small style="color: #666;">{kpis["Most Visible"].split('(')[1]}</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        opp_color = "#27ae60" if opportunity_score >= 7 else "#f39c12" if opportunity_score >= 5 else "#e74c3c"
        st.markdown(f"""
        <div class="metric-container">
            <h3 style="color: {opp_color}; margin: 0;">💡 Market Opportunity</h3>
            <h2 style="margin: 0.5rem 0; color: {opp_color};">{opportunity_score:.1f}/10</h2>
            <small style="color: #666;">{opportunity_desc}</small>
        </div>
        """, unsafe_allow_html=True)

    # Enhanced visualizations
    st.markdown("### 📈 Market Analytics")
    col1, col2 = st.columns(2)
    
    with col1:
        # Rating distribution with better styling
        if len(df) > 0:
            rating_counts = df['Stars'].round().value_counts().sort_index()
            fig = px.bar(
                x=rating_counts.index, 
                y=rating_counts.values,
                title="📊 Rating Distribution",
                labels={'x': 'Star Rating', 'y': 'Number of Businesses'},
                color=rating_counts.values,
                color_continuous_scale='viridis'
            )
            fig.update_layout(
                height=350,
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                title_font_size=16,
                title_x=0.5
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Review volume analysis
        if len(df) > 0:
            # Create review volume categories
            df['Review_Category'] = pd.cut(
                df['Reviews Count'], 
                bins=[0, 10, 50, 200, float('inf')], 
                labels=['New (0-10)', 'Growing (11-50)', 'Established (51-200)', 'Dominant (200+)']
            )
            cat_counts = df['Review_Category'].value_counts()
            
            fig = px.pie(
                values=cat_counts.values,
                names=cat_counts.index,
                title="🎯 Market Maturity Distribution",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig.update_layout(
                height=350,
                title_font_size=16,
                title_x=0.5,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig, use_container_width=True)

# --- Geographic AI Analysis ---
def generate_geographic_analysis(df, business_type, city, country):
    try:
        # Analyze geographic distribution
        north_businesses = len(df[df['Latitude'] > df['Latitude'].median()])
        south_businesses = len(df[df['Latitude'] <= df['Latitude'].median()])
        east_businesses = len(df[df['Longitude'] > df['Longitude'].median()])
        west_businesses = len(df[df['Longitude'] <= df['Longitude'].median()])
        
        # Find concentration areas
        high_rated_north = len(df[(df['Latitude'] > df['Latitude'].median()) & (df['Stars'] >= 4.0)])
        high_rated_south = len(df[(df['Latitude'] <= df['Latitude'].median()) & (df['Stars'] >= 4.0)])
        
        geographic_prompt = f"""
You are analyzing the geographic distribution of {business_type} businesses in {city}, {country}.

GEOGRAPHIC DATA:
- Northern area: {north_businesses} businesses ({high_rated_north} highly rated 4.0+)
- Southern area: {south_businesses} businesses
- Eastern area: {east_businesses} businesses  
- Western area: {west_businesses} businesses
- Total businesses: {len(df)}

PROVIDE ONLY GEOGRAPHIC INSIGHTS:

## 🗺️ Geographic Market Analysis

Focus on:
- Where businesses are concentrated (north/south/east/west)
- Areas with fewer competitors (opportunities)  
- Quality distribution across different areas
- Geographic gaps in coverage

Keep it concise and map-focused. No general market analysis.
"""
        
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        model = genai.GenerativeModel('gemini-2.0-flash-001')
        
        response = model.generate_content(geographic_prompt)
        return response.text if response.text else "Geographic analysis could not be generated."
        
    except Exception as e:
        return f"""
## 🗺️ Geographic Distribution Overview

**Key Observations:**
- Northern area: {north_businesses} businesses
- Southern area: {south_businesses} businesses  
- Eastern area: {east_businesses} businesses
- Western area: {west_businesses} businesses

**Opportunities:** Areas with fewer competitors may present expansion opportunities.
"""

# --- Enhanced Map with Clean Tooltips ---
def create_enhanced_map(df):
    if len(df) == 0:
        return None
    
    # Calculate center point
    center_lat = df['Latitude'].mean()
    center_lng = df['Longitude'].mean()
    
    # Create map with better styling
    m = folium.Map(
        location=[center_lat, center_lng], 
        zoom_start=12, 
        tiles="CartoDB positron",
        control_scale=True
    )
    
    # Color and size mapping functions
    def get_color(rating):
        if rating >= 4.5: return '#27ae60'  # Dark green
        elif rating >= 4.0: return '#2ecc71'  # Green
        elif rating >= 3.5: return '#f1c40f'  # Yellow
        elif rating >= 3.0: return '#e67e22'  # Orange
        else: return '#e74c3c'  # Red
    
    def get_size(reviews):
        if reviews >= 200: return 15
        elif reviews >= 100: return 12
        elif reviews >= 50: return 9
        elif reviews >= 20: return 6
        else: return 4
    
    # Add markers with clean popups
    for idx, row in df.iterrows():
        rating = row['Stars'] if pd.notna(row['Stars']) else 0
        reviews = int(row['Reviews Count']) if pd.notna(row['Reviews Count']) else 0
        
        popup_html = f"""
        <div style="min-width: 180px; font-family: Arial; text-align: center;">
            <h4 style="margin: 0; color: #2c3e50; font-size: 14px;">{row['Business Name']}</h4>
            <hr style="margin: 8px 0;">
            <div style="font-size: 16px; color: {get_color(rating)};">
                <strong>{rating}⭐</strong>
            </div>
            <div style="font-size: 14px; color: #666; margin-top: 5px;">
                {reviews:,} reviews
            </div>
        </div>
        """
        
        folium.CircleMarker(
            location=[row['Latitude'], row['Longitude']],
            radius=get_size(reviews),
            popup=folium.Popup(popup_html, max_width=250),
            color='white',
            weight=2,
            fillColor=get_color(rating),
            fillOpacity=0.8,
            tooltip=f"{row['Business Name']} ({rating}⭐)"
        ).add_to(m)
    
    return m

# --- Clean Map Legend ---
def render_map_legend():
    st.markdown("### 🗺️ Map Legend")
    
    st.markdown("**Rating Colors:**")
    legend_html = """
    <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 15px;">
        <span style="color: #27ae60;">🟢 4.5+ Excellent</span>
        <span style="color: #2ecc71;">🟢 4.0+ Very Good</span>
        <span style="color: #f1c40f;">🟡 3.5+ Good</span>
        <span style="color: #e67e22;">🟠 3.0+ Fair</span>
        <span style="color: #e74c3c;">🔴 <3.0 Poor</span>
    </div>
    """
    st.markdown(legend_html, unsafe_allow_html=True)
    
    st.markdown("**Circle Sizes (Review Volume):**")
    size_html = """
    <div style="display: flex; flex-wrap: wrap; gap: 10px;">
        <span>⚫ 200+ Dominant</span>
        <span>🔵 100+ Established</span>
        <span>🟤 50+ Growing</span>
        <span>🟡 20+ Moderate</span>
        <span>⚪ <20 New</span>
    </div>
    """
    st.markdown(size_html, unsafe_allow_html=True)

# --- MAIN APPLICATION ---
countries = get_country_list()

render_header()

# --- Session State Initialization ---
if 'map_data' not in st.session_state:
    st.session_state.map_data = None
if 'geographic_analysis' not in st.session_state:
    st.session_state.geographic_analysis = None
if 'kpis' not in st.session_state:
    st.session_state.kpis = None
if 'df' not in st.session_state:
    st.session_state.df = None
if 'last_search' not in st.session_state:
    st.session_state.last_search = None
if 'show_detailed_analysis' not in st.session_state:
    st.session_state.show_detailed_analysis = False

# --- Enhanced User Input Form ---
st.markdown("### 🔍 Market Research Parameters")

with st.form(key='search_form'):
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        business_type = st.text_input(
            "Business Type", 
            placeholder="e.g., dentist, plumber, barbershop, restaurant",
            help="Enter the type of business you want to analyze"
        )
    
    with col2:
        country_index = countries.index("Canada") if "Canada" in countries else 0
        country = st.selectbox("Country", options=countries, index=country_index)
    
    with col3:
        city = st.text_input("City", placeholder="e.g., Toronto, Vancouver")
    
    submit_button = st.form_submit_button(
        label='🚀 Generate Market Intelligence',
        use_container_width=True,
        type="primary"
    )

# --- Main Application Logic ---
if submit_button:
    if not all([business_type, city, country]):
        st.warning("⚠️ Please fill in all required fields: Business Type, Country, and City.")
    else:
        # Clear previous results
        st.session_state.map_data = None
        st.session_state.geographic_analysis = None
        st.session_state.kpis = None
        st.session_state.df = None
        st.session_state.show_detailed_analysis = False
        
        search_query = f"{business_type} in {city}, {country}"
        st.session_state.last_search = search_query
        
        # Progress tracking with data power messages
        progress_container = st.container()
        
        try:
            with progress_container:
                show_data_power_messages(0)
                
            with st.spinner("🔍 Collecting market intelligence..."):
                apify_client = ApifyClient(st.secrets["APIFY_TOKEN"])
                run_input = {
                    "searchStringsArray": [search_query], 
                    "maxResults": 150,
                    "language": "en"
                }
                actor_run = apify_client.actor("compass~crawler-google-places").call(run_input=run_input)
                items = [item for item in apify_client.dataset(actor_run["defaultDatasetId"]).iterate_items()]
                
            progress_container.empty()
            show_data_power_messages(1)
            
            if not items:
                st.error(f"❌ No results found for '{search_query}'. Try a different business type or location.")
            else:
                with st.spinner("⚡ Processing competitive intelligence..."):
                    df = pd.DataFrame(items)
                    
                    # Enhanced data processing
                    df = df[['title', 'address', 'totalScore', 'reviewsCount', 'location']].rename(columns={
                        'title': 'Business Name', 
                        'address': 'Address', 
                        'totalScore': 'Stars', 
                        'reviewsCount': 'Reviews Count'
                    })
                    
                    # Better coordinate extraction
                    df['Latitude'] = df['location'].apply(lambda loc: loc.get('lat') if isinstance(loc, dict) else None)
                    df['Longitude'] = df['location'].apply(lambda loc: loc.get('lng') if isinstance(loc, dict) else None)
                    df = df.dropna(subset=['Latitude', 'Longitude'])
                    
                    # Enhanced data cleaning
                    df['Stars'] = pd.to_numeric(df['Stars'], errors='coerce').fillna(0)
                    df['Reviews Count'] = pd.to_numeric(df['Reviews Count'], errors='coerce').fillna(0)
                    
                    # Calculate comprehensive KPIs
                    avg_rating = df[df['Stars'] > 0]['Stars'].mean()
                    most_visible = df.loc[df['Reviews Count'].idxmax()]
                    
                    st.session_state.kpis = {
                        "Total Businesses": len(df),
                        "Average Rating": f"{avg_rating:.2f} Stars" if not pd.isna(avg_rating) else "N/A",
                        "Most Visible": f"{most_visible['Business Name']} ({int(most_visible['Reviews Count'])} reviews)"
                    }
                    st.session_state.df = df
                
                progress_container.empty()
                show_data_power_messages(2)
                
                with st.spinner("🧠 Generating geographic insights..."):
                    st.session_state.geographic_analysis = generate_geographic_analysis(
                        df, business_type, city, country
                    )
                    st.session_state.map_data = create_enhanced_map(df)
                
                progress_container.empty()
                st.success(f"✅ Intelligence gathered! Found {len(df)} businesses - Data is your superpower! 🔥")

        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")
            st.info("💡 This might be due to API limits or connectivity issues. Please try again in a few minutes.")

# --- Display Map First ---
if st.session_state.map_data:
    st.markdown("### 🗺️ Market Intelligence Map")
    
    # Map and legend in columns
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st_folium(st.session_state.map_data, use_container_width=True, height=600)
    
    with col2:
        render_map_legend()
    
    # Geographic Analysis
    if st.session_state.geographic_analysis:
        st.markdown(st.session_state.geographic_analysis)
    
    # Run Deeper Analysis Button
    st.markdown("---")
    if st.button("📊 Run Deeper Analysis", use_container_width=True, type="secondary"):
        st.session_state.show_detailed_analysis = True
        st.rerun()

# --- Detailed Analysis (Only shown after button click) ---
if st.session_state.show_detailed_analysis and st.session_state.kpis and st.session_state.df is not None:
    render_kpi_dashboard(st.session_state.kpis, st.session_state.df)

# --- Placeholder when no data ---
if not st.session_state.map_data:
    st.markdown("### 🎯 Market Intelligence Preview")
    placeholder_col1, placeholder_col2, placeholder_col3 = st.columns([1, 2, 1])
    with placeholder_col2:
        st.image("https://via.placeholder.com/600x400/f8f9ff/667eea?text=Your+Market+Map+Will+Appear+Here", 
                 caption="Enter your search parameters above to generate live market intelligence")
        st.markdown("""
        <div style="text-align: center; color: #666; margin-top: 1rem;">
            <p>🔥 Transform data into competitive advantage</p>
            <p>🗺️ Interactive geographic analysis</p>
            <p>⚡ AI-powered market insights</p>
        </div>
        """, unsafe_allow_html=True)
