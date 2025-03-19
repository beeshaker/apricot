import streamlit as st
from conn import MySQLDatabase  # Assuming the `MySQLDatabase` class is defined in `conn.py`


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
    
# Initialize database connection
db = MySQLDatabase()


# Property Creation Page
st.title("Property Creation")

# Property Creation Form
with st.form("property_form"):
    property_name = st.text_input("Property Name")
    address = st.text_area("Address")
    owner = st.text_input("Owner")
    unit_count = st.number_input("Unit Count", min_value=1, step=1)
    submitted = st.form_submit_button("Create Property")

    if submitted:
        # Insert the new property into the database
        property_id = db.insert_property(property_name, address, owner, unit_count)
        
        if property_id:  # ✅ Ensure property was inserted before logging it
            db.insert_audit_log(username, "Create Property", property_id, "Property")
            st.success(f"Property created successfully! (ID: {property_id})")
        else:
            st.error("Error inserting property data.")

# Sidebar Filters
st.sidebar.header("Filter Properties")
search_property_name = st.sidebar.text_input("Search by Property Name")
search_owner = st.sidebar.text_input("Search by Owner")

# Fetch properties from the database
properties = db.fetch_all_properties()

# Apply filters from the sidebar
if properties:
    import pandas as pd

    # Convert fetched data to a DataFrame for easier handling
    column_names = ["ID","Property Name", "Address", "Owner", "Unit Count"]
    properties_df = pd.DataFrame(properties, columns=column_names)

    # Apply filters if search terms are provided
    if search_property_name:
        properties_df = properties_df[
            properties_df["Property Name"].str.contains(search_property_name, case=False, na=False)
        ]
    if search_owner:
        properties_df = properties_df[
            properties_df["Owner"].str.contains(search_owner, case=False, na=False)
        ]

    # Adjust the index to start from 1
    properties_df.index = properties_df.index + 1

    # Display the filtered or unfiltered table
    st.subheader("All Properties")
    if not properties_df.empty:
        st.dataframe(properties_df, use_container_width=True, hide_index=True)
    else:
        st.write("No properties match the search criteria.")
else:
    st.write("No properties available.")
