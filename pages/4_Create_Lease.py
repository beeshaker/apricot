import streamlit as st
import os
from conn import MySQLDatabase
from menu import menu


if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.switch_page("pages/login.py")  # ✅ Redirect to login
    st.stop()    
else:
    menu()


# Initialize database connection
db = MySQLDatabase()
username = st.session_state["username"]  # Get the logged-in user

# Lease Creation Page
st.title("Lease Creation")

# Fetch Clients and Properties for dropdowns
clients = db.fetch_all_clients_names()
properties = db.fetch_all_properties_names()

# Create dropdown options
client_options = {client['Tenant Name']: client['client_id'] for client in clients}
property_options = {property['Property Name']: property['property_id'] for property in properties}

# Lease Creation Form
with st.form("lease_form"):
    client_name = st.selectbox("Client", options=list(client_options.keys()))
    property_name = st.selectbox("Property", options=list(property_options.keys()))
    unit_name = st.text_input("Unit Name")
    start_date = st.date_input("Start Date")
    end_date = st.date_input("End Date")
    increment_period = st.number_input("Increment Period (Months)", min_value=1, step=1)
    original_rental_amount = st.number_input("Original Rental Amount", min_value=0.0, step=0.01)
    lease_deposit = st.number_input("Lease Deposit", min_value=0.0, step=0.01)
    increment_percentage = st.number_input("Increment Percentage", min_value=0.0, step=0.01)
    lease_pdf = st.file_uploader("Upload Lease PDF", type=["pdf"])
    signed = st.checkbox("Lease Signed?")
    submitted = st.form_submit_button("Create Lease")

    if submitted:
        # Check if there's an open lease for the same unit
        check_query = """
            SELECT COUNT(*) AS count
            FROM lease
            WHERE unit_name = %s AND lease_status = 'Open'
        """
        existing_leases = db.fetch_one(check_query, (unit_name,))
        if existing_leases['count'] > 0:
            st.error("An open lease already exists for this unit. Please close the existing lease before creating a new one.")
        else:
            # Save the uploaded PDF to a directory
            pdf_data = None
            if lease_pdf is not None:
                pdf_data = lease_pdf.getvalue()  # Read the PDF as bytes

            # Get selected client_id and property_id
            client_id = client_options[client_name]
            property_id = property_options[property_name]

            # ✅ Calculate increment amount based on percentage
            increment_amount = original_rental_amount * (increment_percentage / 100) if increment_percentage > 0 else 0.0

            # ✅ Insert the new lease into the database
            lease_id = db.insert_lease(
                client_id=client_id,
                property_id=property_id,
                unit_name=unit_name,
                start_date=start_date,
                end_date=end_date,
                rental_amount=original_rental_amount,
                lease_deposit=lease_deposit,
                lease_pdf=pdf_data,
                signed=signed,
                increment_period=increment_period if increment_period > 0 else None,
                increment_percentage=increment_percentage if increment_percentage > 0 else None,
                increment_amount=increment_amount if increment_amount > 0 else None
            )
            db.insert_audit_log(username, "Upload Lease", lease_id, "Lease")

            st.success("Lease created successfully!")
