import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from astropy.io import fits
from astropy.visualization import make_lupton_rgb, ZScaleInterval
from astropy.utils.data import download_file, get_pkg_data_filename
from astroquery.mast import Observations
from astroquery.sdss import SDSS
from astropy import coordinates as coords
from astropy import units as u
import plotly.express as px
from io import BytesIO
import time

# Page configuration
st.set_page_config(
    page_title="Hubble Data Explorer",
    page_icon="🔭",
    layout="wide"
)

# Custom CSS
st.markdown(
    """
    <style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<h1 class="main-header">🔭 Hubble Data Explorer</h1>', unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["🔭 Hubble Viewer", "📈 Metrics", "🌌 SDSS Overlay", "🧪 Debug"])

# Sidebar Controls
st.sidebar.title("🔧 Controls")

# Object selection with popular examples
popular_objects = {
    "Messier 51 (Whirlpool Galaxy)": "M51",
    "Messier 101 (Pinwheel Galaxy)": "M101", 
    "Messier 81 (Bode's Galaxy)": "M81",
    "Messier 82 (Cigar Galaxy)": "M82",
    "Messier 104 (Sombrero Galaxy)": "M104",
    "Messier 16 (Eagle Nebula)": "M16",
    "Messier 42 (Orion Nebula)": "M42",
    "NGC 891": "NGC 891",
    "NGC 1300": "NGC 1300"
}

selected_object_name = st.sidebar.selectbox(
    "Choose a popular object:",
    list(popular_objects.keys())
)
object_name = st.sidebar.text_input("Or enter custom object name:", popular_objects[selected_object_name])

search_radius = st.sidebar.slider("Search Radius (deg)", 0.01, 1.0, 0.1, 0.01)

# Image processing controls
st.sidebar.subheader("Image Processing")
stretch = st.sidebar.slider("RGB Stretch", 0.1, 2.0, 0.5, 0.1)
Q = st.sidebar.slider("RGB Q Factor", 1, 20, 10)

# Cache configuration with better error handling
@st.cache_data(show_spinner="Searching for observations...", ttl=3600)
def get_hubble_fits_urls(object_name, radius="0.1 deg"):
    try:
        st.info(f"🔍 Querying MAST for: {object_name} (radius: {radius})")
        
        # Query by object name
        obs_table = Observations.query_object(object_name, radius=radius)
        
        if len(obs_table) == 0:
            st.warning(f"⚠ No observations found for '{object_name}'. Trying with coordinates...")
            
            # Try to resolve object name to coordinates
            try:
                from astropy.coordinates import SkyCoord
                coord = SkyCoord.from_name(object_name)
                obs_table = Observations.query_region(coord, radius=radius)
            except:
                st.error(f"❌ Could not resolve '{object_name}' to coordinates")
                return [], pd.DataFrame()
        
        if len(obs_table) == 0:
            st.error(f"❌ No Hubble observations found for '{object_name}' in MAST database.")
            return [], pd.DataFrame()
            
        st.success(f"✅ Found {len(obs_table)} observations")
        
        # Get products
        obs_ids = obs_table['obsid'][:10]  # Limit to first 10 to avoid timeout
        products = Observations.get_product_list(obs_ids)
        
        # Filter for science images
        filtered = Observations.filter_products(
            products, 
            productType="image", 
            extension="fits",
            productSubGroupDescription="FLT"  # Try to get calibrated data
        )
        
        # If no FLT files, try any FITS
        if len(filtered) == 0:
            filtered = Observations.filter_products(
                products, 
                productType="image", 
                extension="fits"
            )
        
        if len(filtered) > 0:
            urls = filtered['dataURI']
            df = filtered.to_pandas()
            st.success(f"✅ Found {len(urls)} FITS files")
            return urls[:6], df  # Return up to 6 URLs
        
        st.warning("⚠ No FITS files found in the observations")
        return [], pd.DataFrame()
        
    except Exception as e:
        st.error(f"❌ MAST query failed: {str(e)}")
        return [], pd.DataFrame()

# Load FITS with timeout and fallback
@st.cache_data(show_spinner="Downloading FITS data...")
def load_fits_from_url(url, max_retries=2):
    for attempt in range(max_retries):
        try:
            path = download_file(url, cache=True, timeout=30)
            with fits.open(path) as hdul:
                # Find the first extension with image data
                for ext in hdul:
                    if ext.data is not None and len(ext.data.shape) >= 2:
                        return ext.data, ext.header
            return None, None
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            st.warning(f"⚠ Failed to load {url.split('/')[-1]}: {str(e)}")
            return None, None

# Create demo data for testing
def create_demo_data():
    """Create synthetic astronomical data for demo purposes"""
    size = 512
    y, x = np.ogrid[-size//2:size//2, -size//2:size//2]
    r = np.sqrt(x*2 + y*2)
    
    # Create synthetic galaxy/nebula data
    r_data = np.exp(-r/100) * (1 + 0.5*np.sin(0.1*x) * np.sin(0.1*y))
    g_data = np.exp(-r/120) * (1 + 0.3*np.sin(0.08*x) * np.sin(0.12*y)) 
    b_data = np.exp(-r/80) * (1 + 0.4*np.sin(0.12*x) * np.sin(0.09*y))
    
    # Add some stars
    for _ in range(50):
        cx, cy = np.random.randint(-200, 200, 2)
        star_r = np.sqrt((x-cx)*2 + (y-cy)*2)
        brightness = np.random.exponential(100)
        r_data += brightness * np.exp(-star_r/2)
        g_data += brightness * 0.8 * np.exp(-star_r/2)
        b_data += brightness * 0.6 * np.exp(-star_r/2)
    
    return r_data, g_data, b_data

def create_rgb_image(r_data, g_data, b_data, stretch=0.5, Q=10):
    """Create RGB image with robust normalization"""
    try:
        def safe_normalize(data):
            if data is None:
                return None
            data = np.nan_to_num(data)
            # Use percentile-based normalization for robustness
            p_low, p_high = np.percentile(data, [1, 99])
            data = np.clip(data, p_low, p_high)
            return (data - p_low) / (p_high - p_low)
        
        r_norm = safe_normalize(r_data)
        g_norm = safe_normalize(g_data) 
        b_norm = safe_normalize(b_data)
        
        if any(x is None for x in [r_norm, g_norm, b_norm]):
            return None
            
        rgb = make_lupton_rgb(r_norm, g_norm, b_norm, stretch=stretch, Q=Q)
        return rgb
    except Exception as e:
        st.error(f"❌ RGB creation failed: {str(e)}")
        return None

def plot_rgb_matplotlib(rgb_data, title="Hubble RGB Image"):
    """Plot RGB image using matplotlib"""
    if rgb_data is None:
        return
    
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.imshow(rgb_data)
    ax.set_title(title, fontsize=16, pad=20)
    ax.axis('off')
    plt.tight_layout()
    st.pyplot(fig)

# Main app logic
urls, products_df = get_hubble_fits_urls(object_name, f"{search_radius} deg")

# Tab 1: Hubble Viewer
with tab1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🔭 Hubble Image Viewer")
        
        if len(urls) >= 3:
            st.success(f"✅ Found {len(urls)} FITS files. Using first 3 for RGB composite.")
            
            # Load FITS data
            bands_data = {}
            with st.spinner("Loading FITS data..."):
                progress_bar = st.progress(0)
                for i, (url, band) in enumerate(zip(urls[:3], ['Red', 'Green', 'Blue'])):
                    data, header = load_fits_from_url(url)
                    bands_data[band] = data
                    progress_bar.progress((i + 1) / 3)
            
            # Create and display RGB
            if all(bands_data.values()):
                rgb_image = create_rgb_image(
                    bands_data['Red'],
                    bands_data['Green'], 
                    bands_data['Blue'],
                    stretch=stretch,
                    Q=Q
                )
                
                if rgb_image is not None:
                    plot_rgb_matplotlib(rgb_image, f"{object_name} - Hubble RGB")
                    
                    # Download option
                    buf = BytesIO()
                    plt.imsave(buf, rgb_image, format='png')
                    buf.seek(0)
                    
                    st.download_button(
                        label="📥 Download RGB Image",
                        data=buf,
                        file_name=f"{object_name}_hubble_rgb.png",
                        mime="image/png"
                    )
            else:
                st.error("❌ Failed to load one or more FITS files")
                
        elif len(urls) > 0:
            st.warning(f"⚠ Found only {len(urls)} FITS files. Need at least 3 for RGB composite.")
            
        else:
            st.warning("""
            *No Hubble data found.* This could be because:
            - The object isn't in the Hubble archive
            - The object name needs different formatting
            - Network issues with MAST service
            
            *Try these solutions:*
            - Use the popular objects from the dropdown
            - Increase the search radius
            - Check the object name spelling
            """)
            
            # Demo mode
            if st.checkbox("🎮 Show demo with synthetic data"):
                st.info("Displaying synthetic astronomical data for demonstration")
                r_demo,
