import streamlit as st
import pycountry
import time

# Supported major country/currency map
COUNTRY_CURRENCY_MAP = {
    "US": {"code": "USD", "symbol": "$"},
    "FR": {"code": "EUR", "symbol": "€"},
    "GB": {"code": "GBP", "symbol": "£"},
    "CA": {"code": "CAD", "symbol": "CA$"},
    "AU": {"code": "AUD", "symbol": "A$"},
    "DE": {"code": "EUR", "symbol": "€"},
    "IT": {"code": "EUR", "symbol": "€"},
    "ES": {"code": "EUR", "symbol": "€"},
    "IN": {"code": "INR", "symbol": "₹"},
    "JP": {"code": "JPY", "symbol": "¥"},
}

st.set_page_config(page_title="ShopperBot", page_icon="🤖", layout="centered")

# --- 🧪 LIQUID GLASS THEME ---
st.html("""
<style>
    .stApp {
        background: radial-gradient(circle at 50% 50%, #15162c 0%, #05060a 100%) !important;
    }
    .st-key-glass_card {
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(16px) saturate(180%) !important;
        -webkit-backdrop-filter: blur(16px) saturate(180%) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 16px !important;
        padding: 24px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37) !important;
    }
    input, select, div[data-baseweb="select"] {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border-radius: 12px !important;
    }
    button[kind="primary"] {
        background: linear-gradient(90deg, #4f46e5, #06b6d4) !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(6, 182, 212, 0.3) !important;
    }
</style>
""")

# --- 📍 AUTOMATIC COUNTRY DETECTION ---
# Grabs the browser's locale (e.g., "fr-FR", "en-US")
user_locale = st.context.locale
detected_cc = "US" # Fallback default
if user_locale and "-" in user_locale:
    detected_cc = user_locale.split("-")[1].upper()

# Find full country name matching the code
try:
    detected_country_name = pycountry.countries.get(alpha_2=detected_cc).name
except:
    detected_country_name = "United States"

# --- 🍪 WEEKLY LIMIT TRACKING ---
cookies = st.context.cookies
current_searches = int(cookies.get("sb_count", "0"))
reset_time = cookies.get("sb_reset", "")
current_time = int(time.time())

if reset_time and (current_time - int(reset_time) >= 7 * 24 * 60 * 60):
    current_searches = 0
    reset_time = str(current_time)
elif not reset_time:
    reset_time = str(current_time)

searches_left = max(0, 3 - current_searches)

# --- UI CONTENT CONTAINER ---
with st.container(key="glass_card"):
    st.title(" 🛒shopperbot🛍️")
    st.caption("Your premium, free, personal deal hunter.")
    st.divider()

    if searches_left > 0:
        st.info(f"⏳ You have **{searches_left}** free searches remaining this week.")
    else:
        st.error("🚨 You've reached your weekly limit of 3 free searches!")

    # Inputs
    item = st.text_input("What would you like?", placeholder="e.g., Sony WH-1000XM4")
    
    countries_list = sorted([c.name for c in pycountry.countries])
    default_idx = countries_list.index(detected_country_name) if detected_country_name in countries_list else 0
    selected_country = st.selectbox("Shipping Country:", countries_list, index=default_idx)

    # Resolve currency metrics
    c_obj = pycountry.countries.get(name=selected_country)
    cc = c_obj.alpha_2 if c_obj else "US"
    curr = COUNTRY_CURRENCY_MAP.get(cc, {"code": "USD", "symbol": "$"})

    budget = st.number_input(f"Your Budget ({curr['symbol']}):", min_value=1, value=100, step=10)
    st.divider()

    # Trigger Search Button
    if st.button("Find the Best Deals 🔎", type="primary", use_container_width=True, disabled=(searches_left <= 0)):
        if not item:
            st.warning("Please enter what you want to buy!")
        else:
            # Set cookies directly in browser using JavaScript injection
            st.components.v1.html(f"""
                <script>
                    document.cookie = "sb_count={current_searches + 1}; max-age=2592000; path=/";
                    document.cookie = "sb_reset={reset_time}; max-age=2592000; path=/";
                    window.parent.location.reload();
                </script>
            """, height=0)

            st.markdown(":shimmer[ShopperBot is digging through the web indexes for the lowest price...]")
            
            try:
                from google import genai
                from google.genai import types
                
                client = genai.Client()
                prompt = f"""
                You are ShopperBot. The user wants to buy: "{item}".
                Shipping location: {selected_country}. Strict maximum budget: {budget} {curr['code']} ({curr['symbol']}).
                Search the internet for options currently available for sale that ship to or are sold in {selected_country}.
                Filter out anything that exceeds the budget. Provide a breakdown of the top 2-3 choices with direct markdown links.
                """

                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        tools=[types.Tool(google_search=types.GoogleSearch())],
                        temperature=0.3,
                    )
                )
                st.subheader("🎉 Top Picks Found Within Budget:")
                st.markdown(response.text)

            except Exception as e:
                st.error("API link failure. Please verify your backend API Key settings.")
