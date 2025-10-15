import streamlit as st


st.set_page_config(
    page_title="CKN Analytics Dashboard",
    page_icon="👋",
    layout="wide"
)

col1, col2, col3 = st.columns(3)

with col2:
    st.image("docs/ckn-logo.png", width=150)

st.header("CKN Streaming Analytics Dashboard")

st.markdown(
    """
    Welcome to CKN Streaming Analytics Dashboard!
"""
)


