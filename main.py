import streamlit as st
from conn import MySQLDatabase  # Assuming MySQLDatabase class is in conn.py

# Initialize database connection
db = MySQLDatabase()

st.set_page_config(page_title="Lease Management Dashboard")

# Dashboard Title
st.title("Lease Management Dashboard")

# Fetch Data
expired = db.fetch_all_expried()
if not expired.empty:
    st.subheader("Expired Leases")
    st.dataframe(expired, use_container_width=True)
    
exipring = db.fetch_all_expring()
if not exipring.empty:
    st.subheader("Next 5 Leases to Expire")
    st.dataframe(exipring, use_container_width=True)
    
new_add = db.fetch_all_recent_add()
if not new_add.empty:
    st.subheader("Last 5 Leases added")
    st.dataframe(new_add, use_container_width=True)