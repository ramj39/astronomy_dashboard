from astroquery.simbad import Simbad
import streamlit as st
st.markdown(
    """
    <style>
    body, .stApp {
        background-image: linear-gradient(120deg, #d4fc79 0%, #96e6a1 100%);
        #background: linear-gradient(45deg, #ff9a9e 0%, #fad0c4 99%,#fad0c4 100%);
        min-height: 100vh;
        background-attachment: fixed;
    }
    </style>
    """,
    unsafe_allow_html=True
)
st.title("🔭 SIMBAD Object Lookup")
object_name = st.text_input("Enter object name (e.g., M31, Vega)")

if object_name:
    result = Simbad.query_object(object_name)
    if result:
        st.write("📌 Object Info:")
        st.dataframe(result.to_pandas())
    else:
        st.warning("Object not found. Try alternate name or coordinates.")
# 🌠 Stellarium link
st.title("🌠 Open Stellarium Website")
url = "https://stellarium-web.org/"
if st.button("Open Stellarium"):
    import webbrowser as wb
    wb.open(url)
    st.success("Opened Stellarium website in your default browser!")
if st.button("Open Stellarium Web"):
    st.markdown("[Click here to open Stellarium Web](https://stellarium-web.org)")
