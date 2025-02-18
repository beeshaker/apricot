import streamlit as st
from conn import MySQLDatabase
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

# Fetch all leases (including original and new rental amounts)
query_all = """
    SELECT l.lease_id AS 'Lease ID',
           l.unit_name AS 'Unit Name',
           c.tenant_name AS 'Client',
           p.property_name AS 'Property',
           l.start_date AS 'Start Date',
           l.end_date AS 'End Date',
           l.increment_period AS 'Increment Period',
           l.original_rental_amount AS 'Original Rental Amount',
           l.new_rental_amount AS 'New Rental Amount',
           l.lease_deposit AS 'Lease Deposit',
           l.signed AS 'Signed',
           l.lease_status AS 'Status',
           l.lease_pdf AS 'Lease PDF'
    FROM lease l
    JOIN client c ON l.client_id = c.client_id
    JOIN property p ON l.property_id = p.property_id
"""
leases = db.fetch_all(query_all)

# **Check if leases exist**
if leases:
    column_names = ["Lease ID", "Unit Name", "Client", "Property", "Start Date", "End Date",
                    "Increment Period", "Original Rental Amount", "New Rental Amount",
                    "Lease Deposit", "Signed", "Status", "Lease PDF"]

    lease_dicts = [dict(zip(column_names, lease)) for lease in leases]
    for lease in lease_dicts:
        lease["Signed"] = "Yes" if lease["Signed"] == 1 else "No"

    # **Table Data Without Lease PDF**
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

    # **Display leases below the dropdown**
    st.subheader("All Leases")
    st.dataframe(lease_table_data, use_container_width=True)

    # **Lease Details Below**
    if lease_id:
        lease = next((lease for lease in lease_dicts if lease["Lease ID"] == lease_id), None)

        if lease:
            st.subheader("Lease Details")

            # ✅ Display lease details
            st.write(f"**Unit Name**: {lease['Unit Name']}")
            st.write(f"**Client**: {lease['Client']}")
            st.write(f"**Property**: {lease['Property']}")
            st.write(f"**Start Date**: {lease['Start Date']}")
            st.write(f"**End Date**: {lease['End Date']}")
            st.write(f"**Increment Period**: {lease['Increment Period']} months")
            st.write(f"**Original Rental Amount**: KSH {lease['Original Rental Amount']}")

            # ✅ Handle NULL values for `new_rental_amount`
            new_rental_amount = lease["New Rental Amount"]
            new_rental_amount = new_rental_amount if new_rental_amount is not None else lease["Original Rental Amount"]

            # **Allow user to modify new rental amount**
            new_rental_amount_input = st.number_input(
                "New Rental Amount (after escalation)", 
                value=new_rental_amount, min_value=0.0
            )

            st.write(f"**Lease Deposit**: KSH {lease['Lease Deposit']}")

            # ✅ Get the Lease PDF safely
            lease_pdf = lease.get("Lease PDF")

            if isinstance(lease_pdf, bytearray):
                lease_pdf = bytes(lease_pdf)  # Convert to bytes if it's a bytearray

            if lease_pdf and len(lease_pdf) > 0:
                st.write("**Lease PDF Available**")

                if st.button("View Lease PDF"):
                    encoded_pdf = base64.b64encode(lease_pdf).decode("utf-8")
                    pdf_display = f'<iframe src="data:application/pdf;base64,{encoded_pdf}" width="100%" height="600"></iframe>'
                    st.markdown(pdf_display, unsafe_allow_html=True)
            else:
                st.warning("No lease PDF available for this lease.")

            # ✅ Lease Edit Form
            with st.form("edit_form"):
                signed = st.checkbox("Lease Signed?", value=lease["Signed"] == "Yes")
                status = st.selectbox("Lease Status", options=["Open", "Closed"], index=["Open", "Closed"].index(lease["Status"]))
                update_submitted = st.form_submit_button("Update Lease")

            if update_submitted:
                # ✅ Update lease details
                update_query = """
                    UPDATE Lease
                    SET signed = %s, lease_status = %s, new_rental_amount = %s
                    WHERE lease_id = %s
                """
                db.execute_query(update_query, (signed, status, new_rental_amount_input, lease_id))
                st.success("Lease updated successfully!")
                st.rerun()
else:
    st.warning("No leases found.")
