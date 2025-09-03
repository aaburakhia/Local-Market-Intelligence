import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from io import StringIO
from apify_client import ApifyClient
import numpy as np

# --- App Configuration ---
st.set_page_config(page_title="Local Market Intelligence", layout="wide")

# Custom CSS for better styling
st.markdown(
    """
    <style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }
    iframe {
        width: 100%;
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .legend-item { 
        display: flex; 
        align-items: center; 
        margin-bottom: 5px; 
    }
    .legend-color { 
        width: 20px; 
        height: 20px; 
        border-radius: 50%; 
        margin-right: 10px; 
        border: 1px solid #ddd;
    }
    .insight-box {
        background-color: #e8f4f8;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🗺️ Live Local Market Intelligence Tool")
st.write("Enter a business type and a location to generate a live competitive map with market insights.")

# --- User Input Fields ---
with st.form(key='search_form'):
    col1, col2, col3 = st.columns(3)
    with col1:
        business_type = st.text_input("Business Type", "dentist", help="e.g., restaurant, dentist, gym, coffee shop")
    with col2:
        city = st.text_input("City", "London", help="City name")
    with col3:
        country = st.text_input("Country", "Canada", help="Country name")
    
    # Advanced options
    with st.expander("Advanced Options"):
        max_results = st.slider("Maximum results to fetch", 50, 300, 150)
        min_reviews = st.number_input("Minimum reviews filter", 0, 100, 0)
    
    submit_button = st.form_submit_button(label='🔍 Generate Live Market Analysis')

if submit_button:
    if not business_type or not city or not country:
        st.warning("Please fill in all three fields.")
    else:
        try:
            full_search_query = f"{business_type} in {city}, {country}"
            
            with st.spinner(f"Scraping live data for '{full_search_query}'... This can take 1-2 minutes."):
                apify_client = ApifyClient(st.secrets["APIFY_TOKEN"])
                run_input = { 
                    "searchStringsArray": [full_search_query], 
                    "max_results": max_results,
                }
                actor_run = apify_client.actor("compass~crawler-google-places").call(run_input=run_input)
                items = [item for item in apify_client.dataset(actor_run["defaultDatasetId"]).iterate_items()]
                
                if not items:
                    st.error(f"No results found for '{full_search_query}'. Please try a more specific location.")
                else:
                    # Data processing
                    df = pd.DataFrame(items)
                    
                    # Select and rename columns
                    columns_to_keep = ['title', 'address', 'totalScore', 'reviewsCount', 'location']
                    if 'phone' in df.columns:
                        columns_to_keep.append('phone')
                    if 'website' in df.columns:
                        columns_to_keep.append('website')
                    
                    df = df[columns_to_keep].rename(columns={
                        'title': 'Business Name', 
                        'address': 'Address', 
                        'totalScore': 'Stars', 
                        'reviewsCount': 'Reviews Count'
                    })
                    
                    # Extract coordinates
                    df['Latitude'] = df['location'].apply(lambda loc: loc.get('lat') if loc else None)
                    df['Longitude'] = df['location'].apply(lambda loc: loc.get('lng') if loc else None)
                    df.dropna(subset=['Latitude', 'Longitude'], inplace=True)
                    
                    # Clean numeric data
                    df['Stars'] = pd.to_numeric(df['Stars'], errors='coerce')
                    df['Reviews Count'] = pd.to_numeric(df['Reviews Count'], errors='coerce').fillna(0)
                    
                    # Apply filters
                    df = df[df['Reviews Count'] >= min_reviews]
                    
                    st.success(f"Successfully found and processed {len(df)} businesses (after filtering).")

                    # Market Insights Dashboard
                    st.header("📊 Market Insights")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        avg_rating = df['Stars'].mean()
                        st.metric("Average Rating", f"{avg_rating:.2f}⭐" if not pd.isna(avg_rating) else "N/A")
                    
                    with col2:
                        total_businesses = len(df)
                        st.metric("Total Businesses", f"{total_businesses:,}")
                    
                    with col3:
                        high_rated = len(df[df['Stars'] >= 4.5])
                        st.metric("Highly Rated (4.5+)", f"{high_rated} ({high_rated/total_businesses*100:.1f}%)")
                    
                    with col4:
                        avg_reviews = df['Reviews Count'].mean()
                        st.metric("Avg Review Count", f"{avg_reviews:.0f}" if not pd.isna(avg_reviews) else "N/A")
                    
                    # Market Analysis Insights
                    st.subheader("🔍 Market Analysis")
                    
                    # Calculate insights
                    rating_categories = {
                        'Excellent (4.5+)': len(df[df['Stars'] >= 4.5]),
                        'Good (4.0-4.4)': len(df[(df['Stars'] >= 4.0) & (df['Stars'] < 4.5)]),
                        'Fair (3.5-3.9)': len(df[(df['Stars'] >= 3.5) & (df['Stars'] < 4.0)]),
                        'Poor (<3.5)': len(df[df['Stars'] < 3.5])
                    }
                    
                    col_insight1, col_insight2 = st.columns(2)
                    
                    with col_insight1:
                        st.markdown(f"""
                        <div class="insight-box">
                            <h4>🏆 Rating Distribution</h4>
                            <ul>
                                <li>Excellent (4.5+): {rating_categories['Excellent (4.5+)']} businesses</li>
                                <li>Good (4.0-4.4): {rating_categories['Good (4.0-4.4)']} businesses</li>
                                <li>Fair (3.5-3.9): {rating_categories['Fair (3.5-3.9)']} businesses</li>
                                <li>Poor (<3.5): {rating_categories['Poor (<3.5)']} businesses</li>
                            </ul>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col_insight2:
                        top_rated = df.nlargest(3, 'Stars')[['Business Name', 'Stars', 'Reviews Count']]
                        most_reviewed = df.nlargest(3, 'Reviews Count')[['Business Name', 'Stars', 'Reviews Count']]
                        
                        st.markdown(f"""
                        <div class="insight-box">
                            <h4>📈 Top Performers</h4>
                            <p><strong>Highest Rated:</strong></p>
                            <ul>
                        """, unsafe_allow_html=True)
                        
                        for idx, row in top_rated.iterrows():
                            st.markdown(f"<li>{row['Business Name']} ({row['Stars']}⭐, {int(row['Reviews Count'])} reviews)</li>", unsafe_allow_html=True)
                        
                        st.markdown("</ul></div>", unsafe_allow_html=True)
                    
                    # Map Generation
                    with st.spinner("Building interactive map..."):
                        def get_color(stars):
                            if pd.isna(stars) or stars < 4.0: return 'red'
                            elif stars < 4.5: return 'orange'
                            else: return 'green'
                        
                        df['Color'] = df['Stars'].apply(get_color)
                        df['Size'] = df['Reviews Count'].apply(lambda x: max(6, min(20, 4 + (x**0.5) * 0.3)))

                        center_lat = df['Latitude'].mean()
                        center_lon = df['Longitude'].mean()
                        
                        # Create map with better styling
                        m = folium.Map(location=[center_lat, center_lon], zoom_start=12, tiles="CartoDB positron")
                        
                        # Add markers
                        for index, row in df.iterrows():
                            popup_content = f"""
                            <div style="width: 200px;">
                                <b>{row['Business Name']}</b><br>
                                <i>{row['Address']}</i><br>
                                ⭐ Rating: {row['Stars'] if not pd.isna(row['Stars']) else 'N/A'}<br>
                                📝 Reviews: {int(row['Reviews Count'])}<br>
                            </div>
                            """
                            
                            folium.CircleMarker(
                                location=[row['Latitude'], row['Longitude']], 
                                radius=row['Size'], 
                                popup=folium.Popup(popup_content, max_width=250),
                                tooltip=row['Business Name'], 
                                color=row['Color'], 
                                fill=True, 
                                fill_color=row['Color'], 
                                fill_opacity=0.7,
                                weight=2
                            ).add_to(m)
                        
                        # Add a marker for the city center
                        folium.Marker(
                            [center_lat, center_lon],
                            popup=f"Center of {city}, {country}",
                            icon=folium.Icon(color='blue', icon='info-sign')
                        ).add_to(m)
                    
                    # Display map
                    st.header("🗺️ Interactive Market Map")
                    st_folium(m, height=700, returned_objects=[])

                    # Legend
                    st.header("📝 Legend")
                    st.markdown("""
                    <div class="legend-item"><div class="legend-color" style="background-color: green;"></div>Excellent Reputation (4.5+ Stars)</div>
                    <div class="legend-item"><div class="legend-color" style="background-color: orange;"></div>Average Reputation (4.0 - 4.4 Stars)</div>
                    <div class="legend-item"><div class="legend-color" style="background-color: red;"></div>Poor Reputation (< 4.0 Stars)</div>
                    <br>• <b>Circle Size</b> corresponds to the number of online reviews (larger = more reviews)
                    <br>• <b>Blue Marker</b> indicates the city center
                    """, unsafe_allow_html=True)
                    
                    # Data table
                    st.header("📋 Business Data Table")
                    display_df = df[['Business Name', 'Address', 'Stars', 'Reviews Count']].copy()
                    display_df = display_df.sort_values('Stars', ascending=False, na_position='last')
                    st.dataframe(display_df, use_container_width=True)
                    
                    # Download option
                    csv = display_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download data as CSV",
                        data=csv,
                        file_name=f"{business_type}_{city}_{country}_market_data.csv",
                        mime="text/csv"
                    )

        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.error("There might be an issue with the Apify Actor or your token. Please check the actor input format and your Streamlit Cloud secrets.")

else:
    st.header("📊 How This Tool Works")
    st.info("""
    This tool provides live competitive intelligence by:
    
    1. **Data Collection**: Scraping real-time business data from Google Places
    2. **Visual Mapping**: Plotting businesses on an interactive map
    3. **Competitive Analysis**: Color-coding by reputation and sizing by review volume
    4. **Market Insights**: Providing key metrics and distributions
    
    Perfect for market research, competitor analysis, and location planning!
    """)
    
    # Only show sample image if it exists
    try:
        st.header("Sample Market Analysis")
        st.image("sample.png", caption="A sample analysis map showing businesses in London, ON.")
    except:
        pass  # Image doesn't exist, continue without it
