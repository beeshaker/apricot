
import streamlit as st
import hashlib
from conn import MySQLDatabase

# Initialize database connection
db = MySQLDatabase()

# Hashing function for passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Authenticate user
def authenticate_user(username, password):
    hashed_password = hash_password(password)
    query = "SELECT * FROM users WHERE username = %s AND password_hash = %s"
    result = db.fetch_one(query, (username, hashed_password))
    return result is not None

# Set page configuration
st.set_page_config(page_title="Login", page_icon="🔒")

col1, col2, col3 = st.columns([1, 2, 1])  # Create 3 columns with the center one being wider
with col2:
    st.image("logo.png", use_container_width =True)  # Adjust the path to your logo file



st.title("Lease Management - Login")

# Input fields
username = st.text_input("Username")
password = st.text_input("Password", type="password")
login_button = st.button("Login")

# Handle login logic
if login_button:
    if authenticate_user(username, password):
        st.session_state["authenticated"] = True
        st.session_state["username"] = username
        st.success("Login successful! Redirecting...")
        st.switch_page("main.py")  # Redirect to the main dashboard
    else:
        st.error("Invalid username or password")