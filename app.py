import streamlit as st

# Configure page settings
st.set_page_config(page_title="ShopperBot - Maintenance", page_icon="🤖", layout="centered")

# --- 🎨 CLEAN DARK THEME ---
st.html("""
<style>
    .stApp {
        background-color: #0e1117 !important;
    }
    .st-key-maintenance_panel {
        background-color: #161a25 !important;
        border: 1px solid #262730 !important;
        border-radius: 12px !important;
        padding: 40px !important;
        text-align: center;
        margin-top: 50px;
    }
    h1, p {
        color: #ffffff !important;
    }
</style>
""")

# --- MAINTENANCE PANEL ---
with st.container(key="maintenance_panel"):
    st.title("🚧 Under Maintenance")
    st.divider()
    st.markdown("### ShopperBot is temporarily offline.")
    st.write("We are currently updating our API connections and polishing the interface to bring you faster, more accurate deal hunting.")
    st.write(" Please check back shortly!")
