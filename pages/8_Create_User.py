import streamlit as st
import hashlib
from conn import MySQLDatabase

st.set_page_config(page_title="Create User", page_icon="🆕")


if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.switch_page("pages\login.py")  # ✅ Redirect to login
    st.stop()    
else:
    st.sidebar.page_link("main.py", label="Dashboard")
    st.sidebar.page_link("pages/1_Upload_Lease.py", label="Upload Lease")
    st.sidebar.page_link("pages/2_Create_Client.py", label="Create Client")
    st.sidebar.page_link("pages/3_Create_Property.py", label="Create Property")
    st.sidebar.page_link("pages/4_Create_Lease.py", label="Create Lease")
    st.sidebar.page_link("pages/5_Assistant.py", label="Assistant")
    st.sidebar.page_link("pages/6_Find_All_Leases.py", label="Find All Leases")
    st.sidebar.page_link("pages/7_Closed_Leases.py", label="Closed Leases")
    st.sidebar.page_link("pages/8_Create_User.py", label="Create User")
    
    # Logout button
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.success("Logged out successfully!")
        st.switch_page("pages/login.py")  # Redirect to login page

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
