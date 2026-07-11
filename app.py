import streamlit as st
import pycountry
from google import genai
from google.genai import types

# Currency conversion map
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

# Mobile configuration
st.set_page_config(page_title="ShopperBot", page_icon="🤖", layout="centered")

# --- 🔐 SEARCH LIMITER LOGIC ---
if "search_count" not in st.session_state:
    st.session_state.search_count = 0

MAX_SEARCHES = 3
searches_left = MAX_SEARCHES - st.session_state.search_count

# --- MAIN UI ---
st.title("🤖 ShopperBot")
st.caption("Your personal budget shopping assistant.")
st.divider()

# Show the user their remaining search allowance
if searches_left > 0:
    st.info(f"⏳ You have **{searches_left}** free searches remaining for this session.")
else:
    st.error("🚨 You have reached your limit of 3 free searches! Upgrade to Premium to unlock unlimited searches.")

# Inputs
item = st.text_input("What are you looking for?", placeholder="e.g., mechanical keyboard")

countries = sorted([c.name for c in pycountry.countries])
default_index = countries.index("United States") if "United States" in countries else 0
selected_country_name = st.selectbox("Your Country:", countries, index=default_index)

country_obj = pycountry.countries.get(name=selected_country_name)
country_code = country_obj.alpha_2 if country_obj else "US"
currency_info = COUNTRY_CURRENCY_MAP.get(country_code, {"code": "USD", "symbol": "$"})

currency_code = currency_info["code"]
currency_symbol = currency_info["symbol"]

budget = st.number_input(f"Maximum Budget ({currency_symbol}):", min_value=1, value=50, step=5)

st.divider()

# --- TRIGGER SEARCH ---
if st.button("Search Deals 🔎", use_container_width=True, disabled=(searches_left <= 0)):
    if not item:
        st.warning("Please type what you want to buy first!")
    else:
        # Deduct a search count instantly
        st.session_state.search_count += 1
        
        with st.spinner(f"Searching stores shipping to {selected_country_name}..."):
            try:
                client = genai.Client()

                prompt = f"""
                You are ShopperBot, an expert personal shopping assistant. 
                The user wants to buy: "{item}".
                They are located in: {selected_country_name}.
                Their strict maximum budget is: {budget} {currency_code} ({currency_symbol}).

                Search the internet for options currently available for sale that ship to or are sold in {selected_country_name}.
                Filter out anything that exceeds the budget of {budget} {currency_code}.
                Make sure all prices you quote are in {currency_code}.
                
                Provide a breakdown of the top 2-3 best recommendations. For each item, include:
                1. Product Name
                2. Current Price (In {currency_code} and under the budget)
                3. Retailer / Store Name
                4. Why it's a great choice for this budget
                5. The direct markdown link to buy it.
                
                If nothing fits the budget, suggest the closest alternative or explain why.
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
                
                # Rerun to instantly update the countdown counter banner
                st.rerun()

            except Exception as e:
                st.error("Something went wrong. Please check your API key setup.")
                st.info(f"Details: {e}")
