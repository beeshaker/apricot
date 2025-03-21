import streamlit as st
import hashlib
from conn import MySQLDatabase
from menu import menu


st.set_page_config(page_title="Create User", page_icon="🆕")


if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.switch_page("pages/login.py")  # ✅ Redirect to login
    st.stop()    
else:
    menu()

db = MySQLDatabase()

# Check if user is logged in
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.error("You must be logged in to access this page.")
    st.stop()

# Function to hash password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()



st.title("Create a New User")

# Form for new user creation
new_username = st.text_input("New Username")
new_password = st.text_input("New Password", type="password")
confirm_password = st.text_input("Confirm Password", type="password")
create_button = st.button("Create User")

if create_button:
    if new_password != confirm_password:
        st.error("Passwords do not match!")
    elif len(new_password) < 6:
        st.error("Password must be at least 6 characters long!")
    else:
        hashed_password = hash_password(new_password)
        insert_query = "INSERT INTO users (username, password_hash) VALUES (%s, %s)"
        try:
            db.execute_query(insert_query, (new_username, hashed_password))
            st.success(f"User '{new_username}' created successfully!")
        except Exception as e:
            st.error(f"Error: {e}")
