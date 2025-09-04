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

.legend-box {
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
        <small>Generate professional market insights in minutes</small>
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
            <h3 style="color: {opp_color}; margin: 0;">💡 Opportunity Score</h3>
            <h2 style="margin: 0.5rem 0; color: {opp_color};">{opportunity_score:.1f}/10</h2>
            <small style="color: #666;">{low_review} businesses with &lt;10 reviews</small>
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

# --- Enhanced AI Analysis with Better Prompting ---
def generate_enhanced_analysis(df, business_type, city, country, kpis):
    try:
        # Prepare more detailed data for AI
        top_performers = df.nlargest(5, 'Reviews Count')[['Business Name', 'Stars', 'Reviews Count']].to_dict('records')
        rating_distribution = df['Stars'].round().value_counts().to_dict()
        
        # Calculate market insights
        avg_reviews = df['Reviews Count'].mean()
        median_rating = df['Stars'].median()
        competition_density = len(df)
        
        enhanced_prompt = f"""
You are a senior business strategy consultant specializing in local market analysis. Analyze this {business_type} market in {city}, {country}.

MARKET DATA:
- Total Competitors: {kpis['Total Businesses']}
- Average Rating: {kpis['Average Rating']}
- Average Reviews: {avg_reviews:.1f}
- Median Rating: {median_rating}
- Market Leader: {kpis['Most Visible']}

TOP 5 COMPETITORS:
{chr(10).join([f"• {p['Business Name']}: {p['Stars']}⭐ ({p['Reviews Count']} reviews)" for p in top_performers])}

RATING BREAKDOWN:
{chr(10).join([f"• {rating}⭐: {count} businesses" for rating, count in sorted(rating_distribution.items())])}

PROVIDE A COMPREHENSIVE ANALYSIS WITH:

## 🎯 Executive Summary
[2-3 sentences summarizing the market opportunity]

## 📊 Market Landscape
- Competition density assessment
- Quality vs quantity analysis
- Market maturity level

## 💡 Key Opportunities
- Specific gaps in the market
- Underserved rating segments
- Low-competition areas

## ⚠️ Competitive Threats
- Dominant players to watch
- Market saturation indicators
- Barriers to entry

## 🚀 Strategic Recommendations
- Market entry strategies
- Differentiation opportunities
- Target customer segments

## 📈 Success Metrics to Track
- KPIs for market penetration
- Competitive benchmarks

Keep analysis professional, data-driven, and actionable. Use specific numbers from the data provided.
"""
        
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        model = genai.GenerativeModel('gemini-2.0-flash-001')
        
        # Add retry logic for robustness
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = model.generate_content(enhanced_prompt)
                if response.text:
                    return response.text
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                time.sleep(2)  # Wait before retry
        
    except Exception as e:
        return f"""
## ⚠️ Analysis Generation Error

We encountered an issue generating the detailed analysis: {str(e)}

### Quick Market Insights:
- **Total Competitors:** {kpis['Total Businesses']} businesses found
- **Market Leader:** {kpis['Most Visible']}
- **Average Quality:** {kpis['Average Rating']}

### Manual Analysis Recommendations:
1. **Market Size:** {'Large' if kpis['Total Businesses'] > 100 else 'Medium' if kpis['Total Businesses'] > 50 else 'Small'} market with {kpis['Total Businesses']} competitors
2. **Quality Level:** {'High' if float(kpis['Average Rating'].split()[0]) > 4.0 else 'Moderate'} average quality ({kpis['Average Rating']})
3. **Opportunity Assessment:** Review individual competitors for gaps in service or location coverage

*Please try refreshing the analysis or contact support if this persists.*
"""

# --- Enhanced Map with Professional Legend ---
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
    
    # Add markers with enhanced popups
    for idx, row in df.iterrows():
        rating = row['Stars'] if pd.notna(row['Stars']) else 0
        reviews = int(row['Reviews Count']) if pd.notna(row['Reviews Count']) else 0
        
        popup_html = f"""
        <div style="min-width: 200px; font-family: Arial;">
            <h4 style="margin: 0; color: #2c3e50;">{row['Business Name']}</h4>
            <hr style="margin: 8px 0;">
            <div style="display: flex; justify-content: space-between; margin: 5px 0;">
                <span><b>Rating:</b></span>
                <span style="color: {get_color(rating)};">{rating}⭐</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin: 5px 0;">
                <span><b>Reviews:</b></span>
                <span>{reviews:,}</span>
            </div>
            <div style="margin-top: 10px; font-size: 12px; color: #666;">
                <b>Address:</b><br>{row.get('Address', 'N/A')}
            </div>
        </div>
        """
        
        folium.CircleMarker(
            location=[row['Latitude'], row['Longitude']],
            radius=get_size(reviews),
            popup=folium.Popup(popup_html, max_width=300),
            color='white',
            weight=2,
            fillColor=get_color(rating),
            fillOpacity=0.8,
            tooltip=f"{row['Business Name']} ({rating}⭐)"
        ).add_to(m)
    
    return m

# --- Professional Legend Component ---
def render_map_legend():
    st.markdown("""
    <div class="legend-box">
        <h4 style="margin: 0 0 1rem 0; color: #2c3e50;">🗺️ Map Legend</h4>
        
        <div style="margin-bottom: 1rem;">
            <h5 style="margin: 0.5rem 0; color: #34495e;">Rating Colors:</h5>
            <div style="display: flex; flex-wrap: wrap; gap: 15px;">
                <span>🟢 4.5+ Excellent</span>
                <span style="color: #2ecc71;">🟢 4.0+ Very Good</span>
                <span style="color: #f1c40f;">🟡 3.5+ Good</span>
                <span style="color: #e67e22;">🟠 3.0+ Fair</span>
                <span style="color: #e74c3c;">🔴 <3.0 Poor</span>
            </div>
        </div>
        
        <div>
            <h5 style="margin: 0.5rem 0; color: #34495e;">Circle Sizes (Review Volume):</h5>
            <div style="display: flex; flex-wrap: wrap; gap: 15px;">
                <span>⚫ 200+ Dominant</span>
                <span>🔵 100+ Established</span>
                <span>🟤 50+ Growing</span>
                <span>🟡 20+ Moderate</span>
                <span>⚪ <20 New</span>
            </div>
        </div>
        
        <div style="margin-top: 1rem; padding: 0.5rem; background: #ecf0f1; border-radius: 5px;">
            <small><b>💡 Pro Tip:</b> Click on any circle to see detailed business information!</small>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- Progress Bar Component ---
def show_progress_steps(current_step, total_steps=3):
    steps = ["🔍 Data Collection", "📊 Processing", "🧠 AI Analysis"]
    progress = current_step / total_steps
    
    st.progress(progress)
    
    cols = st.columns(3)
    for i, (col, step) in enumerate(zip(cols, steps)):
        with col:
            if i < current_step:
                st.success(f"✅ {step}")
            elif i == current_step:
                st.info(f"⏳ {step}")
            else:
                st.write(f"⏸️ {step}")

# --- MAIN APPLICATION ---
countries = get_country_list()

render_header()

# --- Session State Initialization ---
if 'map_data' not in st.session_state:
    st.session_state.map_data = None
if 'analysis' not in st.session_state:
    st.session_state.analysis = None
if 'kpis' not in st.session_state:
    st.session_state.kpis = None
if 'df' not in st.session_state:
    st.session_state.df = None
if 'last_search' not in st.session_state:
    st.session_state.last_search = None

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
    
    # Quick search templates
    st.markdown("**Quick Templates:**")
    template_col1, template_col2, template_col3, template_col4 = st.columns(4)
    with template_col1:
        if st.form_submit_button("🦷 Dental Practice", use_container_width=True):
            business_type = "dentist"
    with template_col2:
        if st.form_submit_button("🔧 Home Services", use_container_width=True):
            business_type = "plumber"
    with template_col3:
        if st.form_submit_button("🍕 Restaurants", use_container_width=True):
            business_type = "restaurant"
    with template_col4:
        if st.form_submit_button("💄 Beauty Salon", use_container_width=True):
            business_type = "beauty salon"
    
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
        st.session_state.analysis = None
        st.session_state.kpis = None
        st.session_state.df = None
        
        search_query = f"{business_type} in {city}, {country}"
        st.session_state.last_search = search_query
        
        # Progress tracking
        progress_container = st.container()
        
        try:
            with progress_container:
                show_progress_steps(0)
                
            with st.spinner(f"🔍 Step 1/3: Collecting live data for '{search_query}'..."):
                apify_client = ApifyClient(st.secrets["APIFY_TOKEN"])
                run_input = {
                    "searchStringsArray": [search_query], 
                    "maxResults": 150,
                    "language": "en"
                }
                actor_run = apify_client.actor("compass~crawler-google-places").call(run_input=run_input)
                items = [item for item in apify_client.dataset(actor_run["defaultDatasetId"]).iterate_items()]
                
            progress_container.empty()
            show_progress_steps(1)
            
            if not items:
                st.error(f"❌ No results found for '{search_query}'. Try a different business type or location.")
            else:
                with st.spinner("📊 Step 2/3: Processing and analyzing data..."):
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
                show_progress_steps(2)
                
                with st.spinner("🧠 Step 3/3: Generating AI-powered market analysis..."):
                    st.session_state.analysis = generate_enhanced_analysis(
                        df, business_type, city, country, st.session_state.kpis
                    )
                    st.session_state.map_data = create_enhanced_map(df)
                
                progress_container.empty()
                show_progress_steps(3)
                st.success(f"✅ Analysis complete! Found {len(df)} businesses and generated comprehensive insights.")

        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")
            st.info("💡 This might be due to API limits or connectivity issues. Please try again in a few minutes.")

# --- Display Results ---
if st.session_state.kpis and st.session_state.df is not None:
    render_kpi_dashboard(st.session_state.kpis, st.session_state.df)

if st.session_state.analysis:
    st.markdown("""
    <div class="analysis-container">
    """, unsafe_allow_html=True)
    st.markdown("### 🧠 AI-Powered Market Analysis")
    st.markdown(st.session_state.analysis)
    
    # Add analysis metadata
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    with col2:
        st.caption(f"🔍 Query: {st.session_state.last_search}")
    with col3:
        if st.button("📥 Export Report", help="Feature coming soon!"):
            st.info("Export functionality will be available in the premium version!")
    
    st.markdown("</div>", unsafe_allow_html=True)

if st.session_state.map_data:
    st.markdown("### 🗺️ Interactive Market Map")
    
    # Map and legend in columns
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st_folium(st.session_state.map_data, use_container_width=True, height=600)
    
    with col2:
        render_map_legend()
    
    # Add map insights
    if st.session_state.df is not None:
        st.markdown("""
        <div class="insight-highlight">
            <h5>🎯 Quick Map Insights:</h5>
        </div>
        """, unsafe_allow_html=True)
        
        insight_col1, insight_col2 = st.columns(2)
        with insight_col1:
            high_rated = len(st.session_state.df[st.session_state.df['Stars'] >= 4.0])
            st.metric("High-Rated Locations", f"{high_rated}/{len(st.session_state.df)}")
        
        with insight_col2:
            established = len(st.session_state.df[st.session_state.df['Reviews Count'] >= 50])
            st.metric("Established Players", f"{established}/{len(st.session_state.df)}")

else:
    # Professional placeholder
    st.markdown("### 🎯 Market Intelligence Preview")
    placeholder_col1, placeholder_col2, placeholder_col3 = st.columns([1, 2, 1])
    with placeholder_col2:
        st.image("https://via.placeholder.com/600x400/f8f9ff/667eea?text=Your+Market+Map+Will+Appear+Here", 
                 caption="Enter your search parameters above to generate live market intelligence")
        st.markdown("""
        <div style="text-align: center; color: #666; margin-top: 1rem;">
            <p>🔍 Real-time competitor discovery</p>
            <p>📊 Interactive market visualization</p>
            <p>🧠 AI-powered strategic insights</p>
        </div>
        """, unsafe_allow_html=True)
