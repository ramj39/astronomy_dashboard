import streamlit as st
from astroquery.simbad import Simbad
import pandas as pd
from io import BytesIO
import os
import matplotlib.pyplot as plt
from astropy.coordinates import SkyCoord
import astropy.units as u
st.markdown(
    """
    <style>
    body, .stApp {
        #background: linear-gradient(45deg, #ff9a9e 0%, #fad0c4 99%,#fad0c4 100%);
        #background-color: #f0f8ff;
        #background-color: #f0f8ff;
        background-color: #f0f8ff;
        min-height: 100vh;
        background-attachment: fixed;
    }
    </style>
    """,
    unsafe_allow_html=True
)
st.set_page_config(page_title="SIMBAD Object Query", layout="centered")
st.title("🔭 SIMBAD Astronomical Object Lookup")

# Create a Simbad instance
custom_simbad = Simbad()
custom_simbad.TIMEOUT = 10

# Get all available votable fields
available_fields = sorted(custom_simbad.get_votable_fields())

# Define preferred defaults and filter them safely
preferred_defaults = ["ra", "dec", "otype"]
safe_defaults = [field for field in preferred_defaults if field in available_fields]

# Multiselect for user-driven field selection
selected_fields = st.multiselect(
    "Select fields to include in the query:",
    available_fields,
    default=safe_defaults
)

# Input field for object name
object_name = st.text_input("Enter object name (e.g., M1, Betelgeuse, NGC 1976):", "M1")

# Export options
st.markdown("### 📤 Export Options")
export_choice = st.radio(
    "Choose export method:",
    ["Download Excel", "Append to Local Excel", "Upload to Google Drive"]
)

# Query SIMBAD
if st.button("Query SIMBAD"):
    with st.spinner("Querying SIMBAD..."):
        try:
            custom_simbad.reset_votable_fields()
            for field in selected_fields:
                custom_simbad.add_votable_fields(field)

            result_table = custom_simbad.query_object(object_name)

            if result_table is None:
                st.warning("No results found. Please check the object name.")
            else:
                st.success("Object found!")
                df = result_table.to_pandas()
                st.write("### Result Table")
                st.dataframe(df)

                # 🌌 Plot RA/Dec on sky map
                try:
                    st.write("### Sky Position Plot")
                    st.write("Available columns:", df.columns.tolist())

                    ra_col = next((col for col in df.columns if 'RA' in col.upper()), None)
                    dec_col = next((col for col in df.columns if 'DEC' in col.upper()), None)

                    if ra_col and dec_col:
                        ra = df.iloc[0][ra_col]
                        dec = df.iloc[0][dec_col]
                        coord = SkyCoord(ra, dec, unit=(u.hourangle, u.deg))

                        fig, ax = plt.subplots(figsize=(6, 4))
                        ax.scatter(coord.ra.deg, coord.dec.deg, color='cyan', s=100, edgecolors='black')
                        ax.set_xlabel("Right Ascension (deg)")
                        ax.set_ylabel("Declination (deg)")
                        ax.set_title(f"Sky Position: {object_name}")
                        ax.grid(True)
                        st.pyplot(fig)
                    else:
                        st.warning("RA/Dec columns not found. Try selecting 'ra' and 'dec' in the field list.")
                except Exception as e:
                    st.warning(f"Could not plot RA/Dec: {e}")

                # 📤 Export logic
                if export_choice == "Download Excel":
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df.to_excel(writer, index=False, sheet_name='SIMBAD_Result')
                    st.download_button(
                        label="📥 Download as Excel",
                        data=output.getvalue(),
                        file_name=f"{object_name}_SIMBAD.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

                elif export_choice == "Append to Local Excel":
                    filename = "simbad_results.xlsx"
                    if os.path.exists(filename):
                        try:
                            existing_df = pd.read_excel(filename)
                            combined_df = pd.concat([existing_df, df], ignore_index=True)
                        except Exception as e:
                            st.error(f"Error reading existing Excel file: {e}")
                            combined_df = df
                    else:
                        combined_df = df

                    try:
                        with pd.ExcelWriter(filename, engine='openpyxl', mode='w') as writer:
                            combined_df.to_excel(writer, index=False, sheet_name='SIMBAD_Results')
                        st.success(f"Appended results to `{filename}` successfully.")
                    except Exception as e:
                        st.error(f"Error writing to Excel file: {e}")

                elif export_choice == "Upload to Google Drive":
                    try:
                        from pydrive.auth import GoogleAuth
                        from pydrive.drive import GoogleDrive

                        gauth = GoogleAuth()
                        gauth.LocalWebserverAuth()
                        drive = GoogleDrive(gauth)

                        temp_file = f"{object_name}_SIMBAD.xlsx"
                        df.to_excel(temp_file, index=False)

                        file_drive = drive.CreateFile({'title': temp_file})
                        file_drive.SetContentFile(temp_file)
                        file_drive.Upload()
                        st.success("Uploaded to Google Drive!")
                    except Exception as e:
                        st.error(f"Google Drive upload failed: {e}")

        except Exception as e:
            st.error(f"Error querying SIMBAD: {e}")
# 🔭 Hubble Data Viewer
'''st.title("🔭 View Hubble Observations")

from astroquery.mast import Observations

if st.button("Query Hubble Data"):
    with st.spinner("Querying Hubble via MAST..."):
        try:
            obs_table = Observations.query_object(object_name, radius="0.05 deg")
            obs_ids = obs_table['obsid']
            products = Observations.get_product_list(obs_ids)
            filtered = Observations.filter_products(products, productType="image", extension="fits")
            df_hubble = filtered.to_pandas()

            if df_hubble.empty:
                st.warning("No Hubble FITS images found for this object.")
            else:
                st.success(f"Found {len(df_hubble)} Hubble image products.")
                st.dataframe(df_hubble[["obs_id", "productFilename", "dataURI"]].head())

                # Optional: show first FITS URL
                first_url = df_hubble.iloc[0]["dataURI"]
                st.markdown(f"🔗 [View First FITS File]({first_url})")
        except Exception as e:
            st.error(f"Error querying Hubble data: {e}")'''

# 🌠 Stellarium link
st.title("🌠 Open Stellarium Website")
url = "https://stellarium-web.org/"
if st.button("Open Stellarium"):
    import webbrowser as wb
    wb.open(url)
    st.success("Opened Stellarium website in your default browser!")
if st.button("Open Stellarium Web"):
    st.markdown("[Click here to open Stellarium Web](https://stellarium-web.org)")
