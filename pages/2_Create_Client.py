import streamlit as st
from conn import MySQLDatabase

# Client Creation Page
st.title("Client Creation")
db = MySQLDatabase()

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
    
    username = st.session_state["username"]  # Get the logged-in user
    
    # Logout button
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.success("Logged out successfully!")
        st.switch_page("pages/login.py")  # Redirect to login page


# Client Creation Form
with st.form("client_form"):
    tenant_name = st.text_input("Tenant Name")
    phone_number = st.text_input("Phone Number")
    email = st.text_input("Email")
    contact_person = st.text_input("Contact Person")
    address = st.text_area("Address")
    submitted = st.form_submit_button("Create Client")

    if submitted:
        client_id = db.insert_client(tenant_name, phone_number, email, contact_person, address)
        if client_id:  # ✅ Ensure client was inserted before logging it
            db.insert_audit_log(username, "Create Client", client_id, "Client")
            st.success(f"Client created successfully! (ID: {client_id})")
        else:
            st.error("Error inserting client data.")

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
