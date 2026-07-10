import streamlit as st
import pycountry
import time

# Complete global mapping of countries to their official currencies
COUNTRY_CURRENCY_MAP = {
    "US": {"code": "USD", "symbol": "$"},
    "GB": {"code": "GBP", "symbol": "£"},
    "CA": {"code": "CAD", "symbol": "CA$"},
    "AU": {"code": "AUD", "symbol": "A$"},
    "FR": {"code": "EUR", "symbol": "€"},
    "DE": {"code": "EUR", "symbol": "€"},
    "IT": {"code": "EUR", "symbol": "€"},
    "ES": {"code": "EUR", "symbol": "€"},
    "IN": {"code": "INR", "symbol": "₹"},
    "JP": {"code": "JPY", "symbol": "¥"},
    "CN": {"code": "CNY", "symbol": "¥"},
    "BR": {"code": "BRL", "symbol": "R$"},
}

st.set_page_config(page_title="ShopperBot", page_icon="🤖", layout="centered")

# --- 🍪 NATIVE BROWSER COOKIE TRACKING ---
# Read directly from the user's browser context
cookies = st.context.cookies

# Read current count or default to 0 if new user
cookie_count = cookies.get("shopperbot_count", "0")
current_searches = int(cookie_count)

# Read when their tracking timeline started
cookie_time = cookies.get("shopperbot_reset_time", "")
current_time = int(time.time())
ONE_WEEK_SECONDS = 7 * 24 * 60 * 60

# Logic to see if a week has passed to reset their usage
if cookie_time:
    time_passed = current_time - int(cookie_time)
    if time_passed >= ONE_WEEK_SECONDS:
        current_searches = 0
        cookie_time = str(current_time)
else:
    cookie_time = str(current_time)

MAX_SEARCHES = 3
searches_left = max(0, MAX_SEARCHES - current_searches)

# --- USER INTERFACE ---
st.title("🤖 ShopperBot")
st.caption("Your smart, persistent shopping buddy.")
st.divider()

if searches_left > 0:
    st.info(f"⏳ You have **{searches_left}** free searches remaining this week.")
else:
    st.error("🚨 You have used up your 3 free searches for this week! Upgrade to Premium to unlock unlimited hunting.")

# Item and budget inputs
item = st.text_input("What deal are we hunting today?", placeholder="e.g., mechanical keyboard")

countries = sorted([c.name for c in pycountry.countries])
default_index = countries.index("United States") if "United States" in countries else 0
selected_country_name = st.selectbox("Your Country:", countries, index=default_index)

# Resolve Currency Info dynamically
country_obj = pycountry.countries.get(name=selected_country_name)
country_code = country_obj.alpha_2 if country_obj else "US"
currency_info = COUNTRY_CURRENCY_MAP.get(country_code, {"code": "USD", "symbol": "$"})
currency_code = currency_info["code"]
currency_symbol = currency_info["symbol"]

budget = st.number_input(f"Maximum Budget ({currency_symbol}):", min_value=1, value=50, step=5)

st.divider()

# --- TRIGGER PROTECTED SEARCH ---
if st.button("Search Deals 🔎", use_container_width=True, disabled=(searches_left <= 0)):
    if not item:
        st.warning("Please type what you want to buy first!")
    else:
        # 1. Update counter numbers
        new_count = current_searches + 1
        
        # 2. Inject raw JavaScript via HTML to write the cookies securely right into their phone browser
        # Expire tracking set to roughly 30 days out so browser doesn't clear it instantly
        st.components.v1.html(f"""
            <script>
                document.cookie = "shopperbot_count={new_count}; max-age=2592000; path=/";
                document.cookie = "shopperbot_reset_time={cookie_time}; max-age=2592000; path=/";
                window.parent.location.reload();
            </script>
        """, height=0)
        
        with st.spinner(f"Searching stores shipping to {selected_country_name}..."):
            try:
                # Late imports to ensure component runs smoothly
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
