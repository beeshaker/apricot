import streamlit as st
from conn import MySQLDatabase 
import pandas as pd



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

st.subheader("Closed Lease History")

# Fetch closed leases with proper column names
query_closed = """
    SELECT l.lease_id AS 'Lease ID', 
           l.unit_name AS 'Unit Name', 
           c.tenant_name AS 'Client', 
           p.property_name AS 'Property', 
           cl.closed_by AS 'Closed By', 
           cl.close_reason AS 'Close Reason', 
           cl.close_date AS 'Close Date'
    FROM closed_leases cl
    JOIN lease l ON cl.lease_id = l.lease_id
    JOIN client c ON l.client_id = c.client_id
    JOIN property p ON l.property_id = p.property_id
"""
closed_leases = db.fetch_all(query_closed)

# Ensure the result is a DataFrame with correct headers

if closed_leases:
    column_names = ["Lease ID", "Unit Name", "Client", "Property", "Closed By", "Close Reason", "Close Date"]
    closed_leases_df = pd.DataFrame(closed_leases, columns=column_names)
    st.dataframe(closed_leases_df, use_container_width=True, hide_index= True)
else:
    st.info("No closed leases found.")
