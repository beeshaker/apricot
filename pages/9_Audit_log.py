import streamlit as st
import pandas as pd
from conn import MySQLDatabase

db = MySQLDatabase()

if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.switch_page("login")
    st.stop()

st.title("Audit Log")

query = "SELECT username, action_type, target_type, target_id, timestamp FROM audit_log ORDER BY timestamp DESC"
log_data = db.fetch_all(query)

if log_data:
    df = pd.DataFrame(log_data, columns=["User", "Action", "Target Type", "Target ID", "Timestamp"])
    st.dataframe(df, use_container_width=True)
else:
    st.info("No user activity recorded yet.")
