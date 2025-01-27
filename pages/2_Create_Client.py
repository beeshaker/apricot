import streamlit as st
from conn import MySQLDatabase

# Client Creation Page
st.title("Client Creation")
db = MySQLDatabase()

# Client Creation Form
with st.form("client_form"):
    tenant_name = st.text_input("Tenant Name")
    phone_number = st.text_input("Phone Number")
    email = st.text_input("Email")
    contact_person = st.text_input("Contact Person")
    address = st.text_area("Address")
    submitted = st.form_submit_button("Create Client")

    if submitted:
        db.insert_client(tenant_name, phone_number, email, contact_person, address)
        st.success("Client created successfully!")

# Sidebar Filters
st.sidebar.header("Search Filters")
search_name = st.sidebar.text_input("Search by Tenant Name")
search_phone = st.sidebar.text_input("Search by Phone Number")

# All Clients Section
st.subheader("All Clients")

# Fetch clients from the database
clients = db.fetch_all_clients()

# Apply filters
if not clients.empty:  # Check if DataFrame is not empty
    # Filter by name if a search term is entered
    if search_name:
        clients = clients[clients["Tenant Name"].str.contains(search_name, case=False, na=False)]

    # Filter by phone number if a search term is entered
    if search_phone:
        clients = clients[clients["Phone Number"].str.contains(search_phone, case=False, na=False)]


    # Display the filtered table
    if not clients.empty:
        st.dataframe(clients, use_container_width=True)
    else:
        st.write("No clients match the search criteria.")
else:
    st.write("No clients available.")
