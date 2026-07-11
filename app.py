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

# --- 🎨 CLEAN MINIMALIST THEME ---
st.html("""
<style>
    .stApp { background-color: #0e1117 !important; }
    .st-key-main_panel {
        background-color: #161a25 !important;
        border: 1px solid #262730 !important;
        border-radius: 12px !important;
        padding: 24px !important;
    }
    h1, h2, h3, p, span, label { color: #ffffff !important; }
    input, select, div[data-baseweb="select"] {
        background-color: #0e1117 !important;
        border: 1px solid #4a5568 !important;
        color: #ffffff !important;
        border-radius: 8px !important;
    }
    button[kind="primary"] {
        background: #0066cc !important;
        border: none !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
    }
    button[kind="primary"]:hover { background: #0052a3 !important; }
</style>
""")

# --- 🍪 COOKIES & SEARCH LIMITS ---
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

# --- 📍 AUTOMATIC PHYSICAL IP DETECTION ---
# Check if we already have the country saved in a browser cookie
detected_country_name = cookies.get("ip_country_name", "")

# If we don't have it, run a quick client-side IP lookup and save it to a cookie
if not detected_country_name:
    st.components.v1.html("""
        <script>
            fetch('https://ipapi.co/json/')
                .then(res => res.json())
                .then(data => {
                    if (data.country_name) {
                        // Save country to cookie for 30 days
                        document.cookie = "ip_country_name=" + data.country_name + "; max-age=2592000; path=/";
                        // Instantly reload to apply the default choice
                        window.parent.location.reload();
                    }
                })
                .catch(err => console.log("IP lookup failed:", err));
        </script>
    """, height=0)
    # Temporary fallback while the script reloads
    detected_country_name = "United States"

# --- UI CONTENT PANEL ---
with st.container(key="main_panel"):
    st.title("🤖 ShopperBot")
    st.caption("Your minimal, clean personal deal hunter.")
    st.divider()

    if searches_left > 0:
        st.info(f"⏳ You have **{searches_left}** free searches remaining this week.")
    else:
        st.error("🚨 Limit reached! 3 free searches utilized this week.")

    # Inputs
    item = st.text_input("What would you like?", placeholder="e.g., Sony WH-1000XM4")
    
    countries_list = sorted([c.name for c in pycountry.countries])
    
    # Set dropdown default to the physically tracked IP country name
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
            st.components.v1.html(f"""
                <script>
                    document.cookie = "sb_count={current_searches + 1}; max-age=2592000; path=/";
                    document.cookie = "sb_reset={reset_time}; max-age=2592000; path=/";
                    window.parent.location.reload();
                </script>
            """, height=0)

            st.markdown(":shimmer[ShopperBot is scanning web indexes...]")
            
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
