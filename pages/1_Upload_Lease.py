import streamlit as st
from dotenv import load_dotenv
from conn import MySQLDatabase
from PyPDF2 import PdfReader
from menu import menu
import re
from pdf2image import convert_from_bytes
import json
from langchain_openai import ChatOpenAI
import pytesseract

if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.switch_page("pages/login.py")  # ✅ Redirect to login
    st.stop()    
else:
    menu()
    
    

username = st.session_state["username"]  # Get the logged-in user
load_dotenv()
#model = ChatGroq(model="llama-guard-3-8b", temperature=0)
model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def extract_text(file):
    text = ""
    try:
        if file.name.endswith(".pdf"):
            reader = PdfReader(file)
            for page in reader.pages:
                text += page.extract_text()

            if not text.strip():
                st.warning("No readable text found. Attempting OCR...")
                pdf_images = convert_from_bytes(file.read())
                for i, image in enumerate(pdf_images):
                    ocr_text = pytesseract.image_to_string(image)
                    text += f"\n\n[Page {i + 1}]\n{ocr_text}"
        else:
            st.warning("Only PDF files are supported for now.")
    except Exception as e:
        st.error(f"Error during text extraction: {e}")
    return text

def fetch_clients_and_properties():
    """Fetch clients and properties from the database."""
    db = MySQLDatabase()
    clients_df = db.fetch_all_clients()
    properties_list = db.fetch_all_properties()
    
    clients = {row['Tenant Name']: row.name for _, row in clients_df.iterrows()} if not clients_df.empty else {}
    properties = {prop[1]: prop[0] for prop in properties_list} if properties_list else {}
    
    return clients, properties





def Leasesummary():
    st.title("Upload Documents")

    # Initialize session state for Lease data and response
    if "Lease_text" not in st.session_state:
        st.session_state["Lease_text"] = ""
    if "parsed_data" not in st.session_state:
        st.session_state["parsed_data"] = {}
    if "editable_data" not in st.session_state:
        st.session_state["editable_data"] = {}

    # Fetch clients and properties from the database
    clients, properties = fetch_clients_and_properties()

    # File upload
    Lease_file = st.file_uploader("Upload Lease", type=["pdf"])

    if Lease_file and st.button("Upload Lease"):
        Lease_text = extract_text(Lease_file)
        if not Lease_text.strip():
            st.error("Could not extract text from the uploaded file. Please ensure it contains readable content.")
            return

        st.session_state["Lease_text"] = Lease_text

        st.info("Generating structured summary...")
        raw_data = summarize_lease(Lease_text)
        parsed_data = parse_lease_response(raw_data)

        # Ensure parsed_data is a dictionary
        if isinstance(parsed_data, dict):
            st.session_state["parsed_data"] = parsed_data
            st.session_state["editable_data"] = parsed_data.copy()  # Initialize editable data
            st.success("Lease uploaded and processed successfully!")
        else:
            st.error("Failed to generate structured summary. Please check the LLM response.")

    # Show parsed data and allow editing
    if st.session_state["parsed_data"]:
        st.write("**Review and Edit the Parsed Data:**")

        property_options = ["Select One"] + list(properties.keys())
        client_options = ["Select One"] + list(clients.keys())

        property_name = st.selectbox("Select Property", property_options, index=0)
        client_name = st.selectbox("Select Client", client_options, index=0)
        unit_name = st.text_input("Unit Name")
        lease_signed = st.checkbox("Lease Signed?")

        # Editable form for parsed data
        for key, value in st.session_state["editable_data"].items():
            if isinstance(value, (str, int, float)):
                st.session_state["editable_data"][key] = st.text_input(
                    key.capitalize().replace("_", " "), value=str(value)
                )

        # Button to submit the edited data to the database
        if st.button("Submit to Database"):
            # **Check if user has selected valid options**
            if property_name == "Select One" or client_name == "Select One":
                st.error("Please select a valid Property and Client before submitting.")
            else:
                db = MySQLDatabase()

                # Ensure client and property exist
                client_id = clients.get(client_name)  # Get client ID if exists
                property_id = properties.get(property_name)  # Get property ID if exists

                # If client does not exist, insert into database
                if not client_id:
                    client_insert_query = "INSERT INTO clients (name) VALUES (%s)"
                    db.execute_query(client_insert_query, (client_name,))
                    client_id = db.get_last_insert_id()

                # If property does not exist, insert into database
                if not property_id:
                    property_insert_query = "INSERT INTO Properties (name) VALUES (%s)"
                    db.execute_query(property_insert_query, (property_name,))
                    property_id = db.get_last_insert_id()

                # Check if there's an open lease for the same unit
                check_query = "SELECT COUNT(*) AS count FROM lease WHERE unit_name = %s AND Property_id = %s AND lease_status = 'Open'"
                existing_leases = db.fetch_one(check_query, (unit_name,property_id,))

                if existing_leases and existing_leases['count'] > 0:
                    st.error("An open lease already exists for this unit. Please close the existing lease before creating a new one.")
                else:
                    # Extract lease details from parsed data
                    lease_data = st.session_state["editable_data"]
                    start_date = lease_data.get("start_date")
                    end_date = lease_data.get("end_date")
                    increment_period = lease_data.get("increment_period")
                    rental_amount = lease_data.get("rental_amount", 0.0)
                    lease_deposit = lease_data.get("lease_deposit", 0.0)
                    signed = lease_signed
                    lease_pdf = Lease_file.read() if Lease_file else None
                    increment_percentage = lease_data.get("increment_percentage")
                    increment_amount = lease_data.get("increment_amount")
                    
                    if lease_deposit == None:
                        lease_deposit = 0   

                    # Insert the lease using insert_lease
                    if increment_period == None:
                        lease_id= db.insert_lease(client_id, property_id, unit_name, start_date, end_date, rental_amount, lease_deposit, lease_pdf, signed)
                        
                    else:
                        lease_id= db.insert_lease(client_id, property_id, unit_name, start_date, end_date, rental_amount, lease_deposit, lease_pdf, signed, increment_period,increment_percentage, increment_amount)

                    db.insert_audit_log(username, "Created Lease using upload", lease_id, "Lease")
                    st.success("Lease data inserted into the database successfully!")

            

def summarize_lease(lease_text):
    summary_prompt = """
        You are a senior property manager. Review this lease and extract the following:
        
        - Name of the lessor and the property name and LR number
        - Name of the tenant
        - Lease Start Date
        - Lease End Date
        - Lease Length
        - Lease Deposit
        - Lease Rent
        - Lease Increment Terms
        - Lease Termination Terms
        
        Lease:
        {lease_text}
    """
    try:
        load_dotenv()
        
        #model = ChatOpenAI(model="gpt-4-0125-preview", temperature=0)
        
        
        #
        
        formatted_prompt = summary_prompt.format(lease_text=lease_text)
        response = model.invoke(formatted_prompt)      
        

        if hasattr(response, "content"):
            st.write(response.content)
            return response.content
        else:
            return "No response content available."
    except Exception as e:
        st.error(f"Error during model invocation: {e}")
        return None




def parse_lease_response(response_text):
    """
    Parse the lease response text into a structured dictionary.
    """
    summary_prompt = """
        Review this lease summary and extract the following key information in JSON format.
        
        The JSON should have the following fields:
    
        - start_date: The start date of the lease in YYYY-MM-DD format.
        - end_date: The end date of the lease in YYYY-MM-DD format.
        - increment_period: The increment period in months (integer).
        - rental_amount: The monthly rental amount (float).
        - lease_deposit: The lease deposit amount (float).
        - increment_percentage: The increament percentage (integer).
        - increment_amount": The increament amount(float)

        Example JSON format:
        {{
            "start_date": "2024-12-01",
            "end_date": "2030-11-30",
            "increment_period": 24,
            "rental_amount": 50820.00,
            "lease_deposit": 165060.00
            "increment_percentage": 5
            "increment_amount": 2541.00
        }}

        Lease:
        {response_text}
    """
    try:
        # Load environment variables and initialize the model
        load_dotenv()
       

        # Format the prompt with the lease text
        formatted_prompt = summary_prompt.format(response_text=response_text)

        # Invoke the model
        
        response = model.invoke(formatted_prompt)
        

        # Extract JSON from the response using regex
        if hasattr(response, "content"):
            response_text = response.content.strip()
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)  # Extract JSON block
            if json_match:
                json_str = json_match.group(0)  # Get the matched JSON string
                return json.loads(json_str)  # Parse and return as dictionary
            else:
                st.error("No JSON object found in the response.")
                return None
        else:
            return None
    except json.JSONDecodeError as e:
        st.error(f"Error decoding JSON response: {e}")
        return None
    except Exception as e:
        st.error(f"Error during model invocation: {e}")
        return None
    
    
    
Leasesummary()