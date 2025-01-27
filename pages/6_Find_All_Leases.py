import streamlit as st
from conn import MySQLDatabase  # Assuming `MySQLDatabase` is defined in `conn.py`
import base64

# Initialize database connection
db = MySQLDatabase()

# Set page configuration
st.set_page_config(page_title="Lease Management", layout="wide")

# Title
st.title("Search and Edit Lease")

# Sidebar Search
st.sidebar.header("Search Leases")
search_query = st.sidebar.text_input("Search by Unit Name or Client Name")

# Fetch all leases **without removing Lease PDF before selecting a lease**
query_all = """
    SELECT l.lease_id AS 'Lease ID',
           l.unit_name AS 'Unit Name',
           c.tenant_name AS 'Client',
           p.property_name AS 'Property',
           l.start_date AS 'Start Date',
           l.end_date AS 'End Date',
           l.increment_period AS 'Increment Period',
           l.rental_amount AS 'Rental Amount',
           l.lease_deposit AS 'Lease Deposit',
           l.signed AS 'Signed',
           l.lease_status AS 'Status',
           l.lease_pdf AS 'Lease PDF'  -- Keep this for later use
    FROM Lease l
    JOIN Client c ON l.client_id = c.client_id
    JOIN Property p ON l.property_id = p.property_id
"""
leases = db.fetch_all(query_all)

# **Check if leases exist**
if leases:
    column_names = ["Lease ID", "Unit Name", "Client", "Property", "Start Date", "End Date",
                    "Increment Period", "Rental Amount", "Lease Deposit", "Signed", "Status", "Lease PDF"]

    lease_dicts = [dict(zip(column_names, lease)) for lease in leases]
    for lease in lease_dicts:
        lease["Signed"] = "Yes" if lease["Signed"] == 1 else "No"


    # **Make a copy for the table WITHOUT removing Lease PDF from the original**
    lease_table_data = [{k: v for k, v in lease.items() if k != "Lease PDF"} for lease in lease_dicts]

else:
    lease_dicts = []
    lease_table_data = []

# **Search Filter**
if search_query.strip():
    lease_table_data = [lease for lease in lease_table_data if 
                        search_query.lower() in lease["Unit Name"].lower() or 
                        search_query.lower() in lease["Client"].lower()]

# **Dropdown Above Dataframe**
st.subheader("Select Lease to Edit")
if lease_table_data:
    lease_ids = [lease["Lease ID"] for lease in lease_table_data]
    lease_id = st.selectbox("Choose a Lease", lease_ids, format_func=lambda x: f"Lease {x}")

    # **Display leases below the dropdown (without Lease PDF column)**
    st.subheader("All Leases")
    st.dataframe(lease_table_data, use_container_width=True)

    # **Lease Details Below**
    if lease_id:
        # ✅ Fetch the full lease details using the original list (to include Lease PDF)
        lease = next((lease for lease in lease_dicts if lease["Lease ID"] == lease_id), None)

        if lease:
            st.subheader("Lease Details")

            # ✅ Display lease details properly
            st.write(f"**Unit Name**: {lease['Unit Name']}")
            st.write(f"**Client**: {lease['Client']}")
            st.write(f"**Property**: {lease['Property']}")
            st.write(f"**Start Date**: {lease['Start Date']}")
            st.write(f"**End Date**: {lease['End Date']}")
            st.write(f"**Increment Period**: {lease['Increment Period']} months")
            st.write(f"**Rental Amount**: KSH {lease['Rental Amount']}")
            st.write(f"**Lease Deposit**: KSH {lease['Lease Deposit']}")

            # ✅ Get the Lease PDF safely (from the original lease data)
            lease_pdf = lease.get("Lease PDF")

            # **Fix: Handle MySQL BLOB data correctly**
            if isinstance(lease_pdf, bytearray):
                lease_pdf = bytes(lease_pdf)  # Convert to bytes if it's a bytearray

            # **Lease PDF View**
            if lease_pdf and len(lease_pdf) > 0:  # Ensuring it's not NULL or empty
                st.write("**Lease PDF Available**")

                # **View Button**
                if st.button("View Lease PDF"):
                    # Convert BLOB data to Base64 for inline display
                    encoded_pdf = base64.b64encode(lease_pdf).decode("utf-8")
                    pdf_display = f'<iframe src="data:application/pdf;base64,{encoded_pdf}" width="100%" height="600"></iframe>'
                    st.markdown(pdf_display, unsafe_allow_html=True)
            else:
                st.warning("No lease PDF available for this lease.")

            # ✅ Lease Edit Form
            with st.form("edit_form"):
                signed_checkbox = lease["Signed"] == "Yes"
                signed = st.checkbox("Lease Signed?", value=lease["Signed"])
                status = st.selectbox("Lease Status", options=["Open", "Closed"], index=["Open", "Closed"].index(lease["Status"]))
                update_submitted = st.form_submit_button("Update Lease")

            if update_submitted:
                # ✅ Update lease details correctly
                update_query = """
                    UPDATE Lease
                    SET signed = %s, lease_status = %s
                    WHERE lease_id = %s
                """
                db.execute_query(update_query, (signed, status, lease_id))
                st.success("Lease updated successfully!")
                st.rerun()  # Refresh the page to show updated values
else:
    st.warning("No leases found.")
