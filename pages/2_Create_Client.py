import streamlit as st
from conn import MySQLDatabase
from menu import menu

# Client Creation Page
st.title("Client Creation")
db = MySQLDatabase()

if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.switch_page("pages/login.py")  # ✅ Redirect to login
    st.stop()    
else:
    menu()
    username = st.session_state["username"]  # Get the logged-in user

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

    # Reset the index to make the 'ID' column available
    clients.reset_index(inplace=True)

    # Display the filtered table with edit buttons
    if not clients.empty:
        st.dataframe(clients, use_container_width=True)
        if st.button("Refresh List"):
            st.rerun()

        # Allow editing of selected client
        selected_client_id = st.selectbox("Select Client to Edit", clients["ID"])
        selected_client = clients[clients["ID"] == selected_client_id].iloc[0]

        with st.form(f"edit_client_{selected_client_id}"):
            edit_phone = st.text_input("Edit Phone Number", value=selected_client["Phone Number"])
            edit_email = st.text_input("Edit Email", value=selected_client["Email"])
            edit_address = st.text_area("Edit Address", value=selected_client["Address"])
            update_submitted = st.form_submit_button("Update Client")

            if update_submitted:
                # Update client in the database
                update_result = db.update_client(selected_client_id, edit_phone, edit_email, edit_address)
                if update_result:
                    db.insert_audit_log(username, "Edit Client", selected_client_id, "Client")
                    st.success(f"Client ID {selected_client_id} updated successfully!")
                else:
                    st.error("Failed to update client data.")

    else:
        st.write("No clients match the search criteria.")
else:
    st.write("No clients available.")
