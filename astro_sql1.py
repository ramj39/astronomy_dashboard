import streamlit as st
from astroquery.gaia import Gaia
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
st.title("Interactive Gaia ADQL Query Runner")

# Default query example for guidance
default_query = """
SELECT TOP 10 source_id, ra, dec, parallax
FROM gaiadr2.gaia_source
WHERE parallax < 1 AND bp_rp BETWEEN -0.75 AND 2
"""

user_query = st.text_area("Enter your ADQL query:", value=default_query, height=200)

if st.button("Run Query"):
    st.write("Running query...")
    try:
        job = Gaia.launch_job_async(user_query)
        results = job.get_results()
        st.success("Query finished! Top results below:")
        st.dataframe(results.to_pandas())
    except Exception as e:
        st.error(f"Error running query: {e}")
