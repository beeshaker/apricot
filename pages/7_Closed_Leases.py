import streamlit as st
from conn import MySQLDatabase 
import pandas as pd
from menu import menu



if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.switch_page("pages\login.py")  # ✅ Redirect to login
    st.stop()    
else:
    menu()


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
