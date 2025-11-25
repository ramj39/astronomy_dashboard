import streamlit as st
import pandas as pd
from astroquery.simbad import Simbad
from astropy.table import Table
st.markdown(
    """
    <style>
    body, .stApp {
        background: linear-gradient(45deg, #ff9a9e 0%, #fad0c4 99%,#fad0c4 100%);
        min-height: 100vh;
        background-attachment: fixed;
    }
    </style>
    """,
    unsafe_allow_html=True
)
st.title("Astropy Table to Simbad & Stellarium Viewer")
st.markdown("Upload a CSV or manually enter an object name, query Simbad, display coordinates, and prepare for Stellarium import.")

# Step 1: User Input box
st.subheader("Quick Simbad Lookup")
user_object = st.text_input("Enter an object name or catalog ID (e.g., 'Vega', 'M42', 'NGC 7000')", "")
if user_object:
    custom_simbad = Simbad()
    custom_simbad.add_votable_fields('ra(d)', 'dec(d)')
    result = custom_simbad.query_object(user_object)

    if result is None:
        st.error(f"No object '{user_object}' found in Simbad.")
    else:
        sim_df = result.to_pandas()
        st.write("Simbad Query Result:")
        st.dataframe(sim_df)
        st.write("Available columns:", sim_df.columns.tolist())
        coords = f"{sim_df.iloc[0]['main_id']}: RA={sim_df.iloc[0]['ra']} Dec={sim_df.iloc[0]['dec']}"

        #coords = f"{sim_df.iloc[0]['MAIN_ID']}: RA={sim_df.iloc[0]['RA_d']} Dec={sim_df.iloc[0]['DEC_d']}"
        st.text(coords)
        st.download_button("Download Coordinate for Stellarium", coords, file_name="stellarium_coord.txt")

st.markdown("---")

# Step 2: CSV Upload
uploaded_file = st.file_uploader("Upload your CSV (object names or catalog IDs)", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("Uploaded data:")
    st.dataframe(df)

    object_names = df.iloc[:, 0].tolist()
    st.write(f"Querying Simbad for {len(object_names)} objects...")
    
    custom_simbad = Simbad()
    custom_simbad.add_votable_fields('ra(d)', 'dec(d)')
    result = custom_simbad.query_objects(object_names)

    if result is None:
        st.error("No objects found in Simbad. Check your object names!")
    else:
        sim_df = result.to_pandas()
        st.write("Simbad Query Results:")
        st.dataframe(sim_df)
        coords = []
        for idx, row in sim_df.iterrows():
            coords.append(f"{row['MAIN_ID']}: RA={row['RA_d']} Dec={row['DEC_d']}")
        st.subheader("Stellarium-Friendly Coordinates")
        st.text('\n'.join(coords))
        st.download_button("Download Coordinates for Stellarium", '\n'.join(coords), file_name="stellarium_coords.txt")

st.markdown("""
**Instructions:**
- Enter a single object name or upload a CSV for batch lookup.
- Download coordinates for Stellarium and use F3 search or Solar System Editor for import.
""")
