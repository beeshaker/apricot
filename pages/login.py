import streamlit as st
import hashlib
from conn import MySQLDatabase

st.set_page_config(page_title="Login", page_icon="🔒")

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def authenticate_user(username: str, password: str):
    username = (username or "").strip()
    password = password or ""

    if not username or not password:
        return None

    db = MySQLDatabase()  # ✅ create fresh per call (safe with your connect/close style)

    user = db.fetch_one(
        "SELECT id, username, password_hash, COALESCE(is_admin,0) AS is_admin FROM users WHERE username = %s",
        (username,)
    )

    if not user:
        return None

    entered_hash = hash_password(password)

    # ✅ compare in python
    if user["password_hash"] == entered_hash:
        return user

    return None


col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image("logo.png", use_container_width=True)

st.title("Lease Management - Login")

username = st.text_input("Username")
password = st.text_input("Password", type="password")

if st.button("Login"):
    user = authenticate_user(username, password)

    if user:
        st.session_state["authenticated"] = True
        st.session_state["username"] = user["username"]
        st.session_state["user_id"] = user["id"]
        st.session_state["is_admin"] = bool(user.get("is_admin", 0))
        st.success("Login successful! Redirecting...")
        st.switch_page("main.py")
    else:
        st.error("Invalid username or password")
