import streamlit as st
from conn import MySQLDatabase  # Assuming MySQLDatabase class is in conn.py
import pandas as pd
from menu import menu

# Initialize database connection
db = MySQLDatabase()

# Check authentication status
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.switch_page("pages/login.py")  # Redirect to login page
    st.stop()  # Stop further execution

# Set page configuration
st.set_page_config(page_title="Lease Management Dashboard", page_icon="🏠")
st.title("Lease Management Dashboard")

# Sidebar navigation links (visible only to authenticated users)
if st.session_state["authenticated"]:
    menu()
    

    # Logout button
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.success("Logged out successfully!")
        st.switch_page("pages/login.py")  # Redirect to login page

# Fetch data from the database
expired = db.fetch_all_expried()
expiring = db.fetch_all_expring()
new_add = db.fetch_all_recent_add()

# Display data
if not expired.empty:
    st.subheader("Expired Leases")
    st.dataframe(expired, use_container_width=True)

if not expiring.empty:
    st.subheader("Next 5 Leases to Expire")
    st.dataframe(expiring, use_container_width=True)

if not new_add.empty:
    st.subheader("Last 5 Leases Added")
    st.dataframe(new_add, use_container_width=True)