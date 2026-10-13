import os
from datetime import datetime

import pandas as pd
import streamlit as st
from groq import Groq

st.set_page_config(
    page_title="BrewBuddy AI",
    page_icon="☕",
    layout="wide"
)

MENU = [
    {"name": "Espresso", "category": "Hot Coffee", "price": 350},
    {"name": "Cappuccino", "category": "Hot Coffee", "price": 480},
    {"name": "Cafe Latte", "category": "Hot Coffee", "price": 500},
    {"name": "Mocha", "category": "Hot Coffee", "price": 550},
    {"name": "Caramel Macchiato", "category": "Hot Coffee", "price": 590},
    {"name": "Iced Latte", "category": "Cold Coffee", "price": 520},
    {"name": "Iced Caramel Latte", "category": "Cold Coffee", "price": 600},
    {"name": "Chocolate Frappe", "category": "Cold Coffee", "price": 650},
    {"name": "Vanilla Frappe", "category": "Cold Coffee", "price": 630},
    {"name": "Peach Iced Tea", "category": "Tea & More", "price": 380},
    {"name": "Hot Chocolate", "category": "Tea & More", "price": 420},
    {"name": "Chocolate Croissant", "category": "Snacks", "price": 320},
    {"name": "Classic Brownie", "category": "Snacks", "price": 280},
]


def get_api_key():
    try:
        return st.secrets.get("GROQ_API_KEY", "")
    except Exception:
        return os.getenv("GROQ_API_KEY", "")


def ask_barista(question):
    key = get_api_key()

    if not key:
        return "Please configure GROQ_API_KEY in Streamlit Secrets."

    try:
        client = Groq(api_key=key)

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are BrewBuddy, a friendly AI barista. "
                        "Recommend drinks from the café menu. "
                        "All prices are in Pakistani rupees. "
                        + str(MENU)
                    )
                },
                {"role": "user", "content": question}
            ],
            temperature=0.7,
            max_tokens=400
        )

        return response.choices[0].message.content

    except Exception as error:
        return f"AI Barista error: {error}"


if "cart" not in st.session_state:
    st.session_state.cart = {}

if "chat" not in st.session_state:
    st.session_state.chat = []

st.markdown("""
<style>
.stApp {background-color: #fff8f0;}
.hero {
    background: linear-gradient(120deg, #382116, #98613f);
    padding: 25px;
    border-radius: 18px;
    color: white;
    text-align: center;
}
.hero h1 {color: white;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
<h1>☕ BrewBuddy AI</h1>
<p>Your cosy corner for coffee and creativity.</p>
</div>
""", unsafe_allow_html=True)

page = st.sidebar.radio(
    "Explore BrewBuddy",
    ["Home & Menu", "AI Barista", "Coffee Quiz", "Your Order"]
)

if page == "Home & Menu":
    st.header("Our Coffee Menu")

    category = st.selectbox(
        "Select category",
        ["All"] + sorted({item["category"] for item in MENU})
    )

    products = [
        item for item in MENU
        if category == "All" or item["category"] == category
    ]

    columns = st.columns(3)

    for index, item in enumerate(products):
        with columns[index % 3]:
            with st.container(border=True):
                st.subheader("☕ " + item["name"])
                st.write(f'Price: Rs {item["price"]}')

                quantity = st.number_input(
                    "Quantity",
                    min_value=1,
                    max_value=20,
                    value=1,
                    key="qty_" + item["name"]
                )

                if st.button(
                    "Add to order",
                    key="add_" + item["name"]
                ):
                    name = item["name"]
                    st.session_state.cart[name] = (
                        st.session_state.cart.get(name, 0)
                        + quantity
                    )
                    st.success("Added to your order!")

elif page == "AI Barista":
    st.header("🤖 Ask the AI Barista")

    for message in st.session_state.chat:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    question = st.chat_input(
        "Example: Recommend a sweet iced coffee"
    )

    if question:
        st.session_state.chat.append(
            {"role": "user", "content": question}
        )

        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Preparing your recommendation..."):
                answer = ask_barista(question)
                st.markdown(answer)

        st.session_state.chat.append(
            {"role": "assistant", "content": answer}
        )

elif page == "Coffee Quiz":
    st.header("✨ Find Your Coffee Match")

    sweetness = st.selectbox(
        "How sweet?",
        ["Not sweet", "A little sweet", "Very sweet"]
    )

    temperature = st.radio(
        "Temperature", ["Hot", "Iced", "Either"]
    )

    strength = st.radio(
        "Coffee strength", ["Mild", "Balanced", "Strong"]
    )

    if st.button("Find my match"):
        if temperature == "Iced":
            match = (
                "Iced Caramel Latte"
                if sweetness == "Very sweet"
                else "Iced Latte"
            )
        elif sweetness == "Very sweet":
            match = "Caramel Macchiato"
        elif strength == "Strong":
            match = "Espresso"
        else:
            match = "Cappuccino"

        st.success(f"Your coffee match is {match}!")

        if st.button("Add match to order"):
            st.session_state.cart[match] = (
                st.session_state.cart.get(match, 0) + 1
            )
            st.success("Added to your order!")

elif page == "Your Order":
    st.header("🛒 Your Order")

    if not st.session_state.cart:
        st.info("Your cart is empty. Add items from Home & Menu.")
    else:
        total = 0
        rows = []

        for name, quantity in st.session_state.cart.items():
            item = next(x for x in MENU if x["name"] == name)
            subtotal = item["price"] * quantity
            total += subtotal

            rows.append({
                "Item": name,
                "Quantity": quantity,
                "Unit price": item["price"],
                "Subtotal": subtotal
            })

        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True
        )

        st.subheader(f"Total bill: Rs {total:,}")

        with st.form("checkout_form"):
            customer = st.text_input("Customer name")
            order_type = st.radio(
                "Order type", ["Takeaway", "Dine-in"]
            )
            notes = st.text_area("Special instructions")
            submitted = st.form_submit_button("Confirm demo order")

        if submitted:
            if not customer.strip():
                st.error("Enter your name first.")
            else:
                ticket = "BB-" + datetime.now().strftime(
                    "%Y%m%d%H%M%S"
                )

                record = {
                    "ticket": ticket,
                    "date": datetime.now().isoformat(),
                    "customer": customer.strip(),
                    "order_type": order_type,
                    "items": str(st.session_state.cart),
                    "total_pkr": total,
                    "notes": notes
                }

                file_exists = os.path.exists("orders.csv")

                pd.DataFrame([record]).to_csv(
                    "orders.csv",
                    mode="a",
                    header=not file_exists,
                    index=False
                )

                st.success(f"Demo order saved! Ticket: {ticket}")
                st.session_state.cart = {}

        if st.button("Clear cart"):
            st.session_state.cart = {}
            st.rerun()

st.divider()
st.caption("BrewBuddy AI | Student project")
