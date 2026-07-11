import streamlit as st
import pycountry
import time

# Complete global mapping of countries to their official currencies
COUNTRY_CURRENCY_MAP = {
    "US": {"code": "USD", "symbol": "$"}, "GB": {"code": "GBP", "symbol": "£"},
    "CA": {"code": "CAD", "symbol": "CA$"}, "AU": {"code": "AUD", "symbol": "A$"},
    "FR": {"code": "EUR", "symbol": "€"}, "DE": {"code": "EUR", "symbol": "€"},
    "IT": {"code": "EUR", "symbol": "€"}, "ES": {"code": "EUR", "symbol": "€"},
    "IN": {"code": "INR", "symbol": "₹"}, "JP": {"code": "JPY", "symbol": "¥"},
    "CN": {"code": "CNY", "symbol": "¥"}, "BR": {"code": "BRL", "symbol": "R$"},
}

st.set_page_config(page_title="ShopperBot", page_icon="🤖", layout="centered")

# --- 🧪 LIQUID GLASS UI CUSTOMIZATION (CSS Injection) ---
st.markdown("""
    <style>
    /* Dark glass layout styling */
    .stApp {
        background: radial-gradient(circle at 50% 50%, #1a1b35 0%, #0a0b10 100%);
    }
    
    /* Make standard containers look like blurred liquid glass */
    div[data-testid="stVerticalBlock"] > div {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(12px) saturate(180%);
        -webkit-backdrop-filter: blur(12px) saturate(180%);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        margin-bottom: 15px;
    }
    
    /* Custom input field style overrides */
    input, select, .stSelectbox div {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border-radius: 10px !important;
    }
    
    /* Animated glowing button */
    button[kind="primary"] {
        background: linear-gradient(90deg, #4f46e5, #06b6d4) !important;
        border: none !important;
        color: white !important;
        font-weight: bold !important;
        box-shadow: 0 4px 15px rgba(6, 182, 212, 0.4) !important;
        transition: all 0.3s ease !important;
    }
    button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(6, 182, 212, 0.6) !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 📍 AUTOMATIC COUNTRY GEOLOCATION LOGIC ---
cookies = st.context.cookies
detected_country = cookies.get("detected_country_name", "United States")

# Inject safe background script to auto-detect country if not already saved in browser
if "detected_country_name" not in cookies:
    st.components.v1.html("""
        <script>
            fetch('https://ipapi.co/json/')
                .then(res => res.json())
                .then(data => {
                    if(data.country_name) {
                        document.cookie = "detected_country_name=" + data.country_name + "; max-age=2592000; path=/";
                        window.parent.location.reload();
                    }
                });
        </script>
    """, height=0)

# --- 🍪 NATIVE BROWSER COOKIE TRACKING ---
cookie_count = cookies.get("shopperbot_count", "0")
current_searches = int(cookie_count)
cookie_time = cookies.get("shopperbot_reset_time", "")
current_time = int(time.time())
ONE_WEEK_SECONDS = 7 * 24 * 60 * 60

if cookie_time:
    time_passed = current_time - int(cookie_time)
    if time_passed >= ONE_WEEK_SECONDS:
        current_searches = 0
        cookie_time = str(current_time)
else:
    cookie_time = str(current_time)

MAX_SEARCHES = 3
searches_left = max(0, MAX_SEARCHES - current_searches)

# --- MAIN GLASS PANEL USER INTERFACE ---
st.title("🤖 ShopperBot")
st.caption("Your Free localized budget shopping assistant.")
st.divider()

if searches_left > 0:
    st.info(f"⏳ You have **{searches_left}** free searches remaining this week.")
else:
    st.error("🚨 Limit reached! 3 free searches utilized this week.")

item = st.text_input("What deal are we hunting today?", placeholder="e.g., mechanical keyboard")

# Dynamically set list and default to the auto-detected browser location
countries = sorted([c.name for c in pycountry.countries])
default_index = countries.index(detected_country) if detected_country in countries else countries.index("United States")
selected_country_name = st.selectbox("Shipping Destination:", countries, index=default_index)

# Resolve Currency Info dynamically
country_obj = pycountry.countries.get(name=selected_country_name)
country_code = country_obj.alpha_2 if country_obj else "US"
currency_info = COUNTRY_CURRENCY_MAP.get(country_code, {"code": "USD", "symbol": "$"})
currency_code = currency_info["code"]
currency_symbol = currency_info["symbol"]

budget = st.number_input(f"Maximum Budget ({currency_symbol}):", min_value=1, value=50, step=5)

st.divider()

# --- TRIGGER PROTECTED SEARCH ---
if st.button("Search Deals 🔎", type="primary", use_container_width=True, disabled=(searches_left <= 0)):
    if not item:
        st.warning("Please type what you want to buy first!")
    else:
        new_count = current_searches + 1
        st.components.v1.html(f"""
            <script>
                document.cookie = "shopperbot_count={new_count}; max-age=2592000; path=/";
                document.cookie = "shopperbot_reset_time={cookie_time}; max-age=2592000; path=/";
                window.parent.location.reload();
            </script>
        """, height=0)
        
        with st.spinner("Scouring live web indexes..."):
            try:
                from google import genai
                from google.genai import types
                
                client = genai.Client()
                prompt = f"""
                You are ShopperBot, an expert personal shopping assistant. 
                The user wants to buy: "{item}".
                They are located in: {selected_country_name}.
                Their strict maximum budget is: {budget} {currency_code} ({currency_symbol}).

                Search the internet for options currently available for sale that ship to or are sold in {selected_country_name}.
                Filter out anything that exceeds the budget. Quote prices in {currency_code}.
                
                Provide a breakdown of the top 2-3 best recommendations with store names and direct markdown links.
                """

                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        tools=[types.Tool(google_search=types.GoogleSearch())],
                        temperature=0.3,
                    )
                )
                
                st.subheader("🎉 Best Matches Found:")
                st.markdown(response.text)

            except Exception as e:
                st.error("Something went wrong with the API configuration.")
                st.info(f"Details: {e}")
