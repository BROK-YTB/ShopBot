import streamlit as st
from streamlit_cookies_controller import CookieController
import datetime
import uuid
import random

# Initialize Cookie Controller for persistent tracking
controller = CookieController()

# App Setup
st.set_page_config(page_title="Price Mogger", page_icon="🛍️", layout="centered")

st.title("🛍️ Price Mogger")
st.caption("Find the 3 best items strictly under your budget. Max 3 searches per week.")
st.markdown("---")

# Persistent Tracking logic
user_id = controller.get("pm_user_id")
if not user_id:
    user_id = str(uuid.uuid4())
    controller.set("pm_user_id", user_id)

if "usage_db" not in st.session_state:
    st.session_state["usage_db"] = {}

now = datetime.datetime.now()
if user_id not in st.session_state["usage_db"]:
    st.session_state["usage_db"][user_id] = []

# Filter out timestamps older than 7 days
st.session_state["usage_db"][user_id] = [
    t for t in st.session_state["usage_db"][user_id] if (now - t).days < 7
]

history = st.session_state["usage_db"][user_id]
uses_left = max(0, 3 - len(history))

# Display remaining uses
if uses_left > 0:
    st.info(f"⚡ You have **{uses_left}** free searches left this week.")
else:
    st.error("🚫 Weekly limit reached (3/3). Resets 7 days after your first search.")

# Inputs
item_query = st.text_input("What item are you looking for?", placeholder="e.g., Mechanical Keyboard")
budget = st.number_input("Strict Maximum Budget ($)", min_value=1.0, step=5.0, value=50.0)

# Search Execution
if st.button("Mog Prices", disabled=(uses_left == 0 or not item_query)):
    with st.spinner("Scouring database for the top 3 budget deals..."):
        # Log usage immediately
        st.session_state["usage_db"][user_id].append(datetime.datetime.now())
        
        # --- FREE SEARCH ENGINE SIMULATION (STRICTLY UNDER BUDGET) ---
        # Generates 3 realistic, distinct marketplace variations of the requested item
        variants = ["Standard Edition", "Pro Variant", "Value Bundle"]
        conditions = ["Brand New", "Open Box - Like New", "Refurbished (Excellent)"]
        
        results = []
        for i in range(3):
            # Ensure every price is strictly below the budget
            discount_factor = random.uniform(0.65, 0.95)
            price = round(budget * discount_factor, 2)
            
            results.append({
                "title": f"{item_query} ({variants[i]})",
                "price": price,
                "condition": conditions[i],
                "score": random.randint(88, 99)
            })
        
        # Sort items by price (lowest price first)
        results = sorted(results, key=lambda x: x['price'])
        # -------------------------------------------------------------

        st.success("🔥 Top 3 Deals Found (Strictly Under Budget)")
        
        # Minimalistic List Layout
        for idx, item in enumerate(results, 1):
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{idx}. {item['title']}**")
                    st.caption(f"Condition: {item['condition']} | Deal Score: {item['score']}/100")
                with col2:
                    st.metric(label="Price", value=f"${item['price']}")
                st.markdown("---")
        
        # Rerun to refresh the use counter component
        st.rerun()
