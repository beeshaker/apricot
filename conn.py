import mysql.connector
from mysql.connector import Error
import pandas as pd
import streamlit as st

class MySQLDatabase:
    def __init__(self):
        
        '''
        self.host = "localhost"
        self.user = "root"
        self.password = "pass"
        self.database = "apricot"
        '''      
        
        self.host = st.secrets["DB_HOST"]
        self.user= st.secrets["DB_USER"]
        self.password= st.secrets["DB_PASSWORD"]
        self.database =st.secrets["DB_TABLE"]
        
       
        self.conn = None
        self.cursor = None
        self.connect()  # ✅ Keep connection open on startup

    def connect(self):
        """Establish a connection to the database."""
        try:
            if self.conn is None or not self.conn.is_connected():
                self.conn = mysql.connector.connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database=self.database
                )
                self.cursor = self.conn.cursor(buffered=True)
                print("✅ Connected to MySQL")
        except Exception as e:
            print(f"🚨 Connection Error: {e}")
            self.conn = None
            self.cursor = None

    def close(self):
        """Close the connection to the database."""
        if self.cursor is not None:
            self.cursor.close()
            self.cursor = None
        if self.conn is not None and self.conn.is_connected():
            self.conn.close()
            self.conn = None
        print("Connection closed")

    def insert_to_db(self, data):
        """
        Insert lease information into the database.
        :param data: A dictionary containing the lease data.
        """
        try:
            self.connect()
            query = """
                INSERT INTO lease (
                    tenant_name, start_date, end_date, increment_period, 
                    property_name, unit_name, rental_amount, lease_deposit
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                data["tenant_name"], data["start_date"], data["end_date"],
                data["increment_period"], data["property_name"], 
                data["unit_name"], data["rental_amount"], data["lease_deposit"]
            )
            self.cursor.execute(query, values)
            self.conn.commit()
            print("Data inserted successfully")
        except Error as e:
            print(f"Error while inserting data: {e}")
        finally:
            self.close()

    def fetch_all_leases(self):
        """
        Fetch all leases from the lease table and return as a Pandas DataFrame.
        :return: Pandas DataFrame containing lease details.
        """
        try:
            self.connect()
            query = """
            SELECT l.lease_id, c.tenant_name, p.property_name, l.unit_name, l.start_date, l.end_date, l.increment_period, l.rental_amount, l.lease_deposit, l.created_at, 
       l.last_updated From lease AS l JOIN property AS p ON l.property_id = p.property_id JOIN client AS c ON l.client_id = c.client_id LIMIT 5;"""
       
            self.cursor.execute(query)
            rows = self.cursor.fetchall()

            column_names = [
                "Lease ID", "Tenant Name", "Property Name", "Unit Name","Start Date", "End Date",
                "Increment Period", "Rental Amount", "Lease Deposit", "Created At", "Updated At"
            ]

            return pd.DataFrame(rows, columns=column_names)
        except Error as e:
            print(f"Error fetching leases: {e}")
            return pd.DataFrame()
        finally:
            self.close()

    
    
    def fetch_all_expring(self):
        try:
            self.connect()
            query = """
                SELECT l.lease_id, unit_name, tenant_name, property_name, end_date
                From lease l
                JOIN client c ON l.client_id = c.client_id
                JOIN property p ON l.property_id = p.property_id
                WHERE l.lease_status = 'Open' and end_date > CURDATE()
                ORDER BY l.end_date ASC
                LIMIT 5
            """
            self.cursor.execute(query)
            result = self.cursor.fetchall()
            
            # Define column names matching the query
            columns = ["Lease ID", "Unit Name", "Client", "Property", "End Date"]
            
            # Convert to pandas DataFrame
            df = pd.DataFrame(result, columns=columns)
            
            # Set the 'ID' column as the index
            df.set_index('Lease ID', inplace=True)
            
            return df
        except Error as e:
            print(f"Error fetching clients: {e}")
            return pd.DataFrame()  # Return an empty DataFrame on error
        
    
    def fetch_all_recent_add(self):
        try:
            self.connect()
            query = """
                SELECT l.lease_id, unit_name, tenant_name, property_name, start_date
                From lease l
                JOIN client c ON l.client_id = c.client_id
                JOIN property p ON l.property_id = p.property_id
                WHERE l.lease_status = 'Open'
                ORDER BY l.start_date DESC
                LIMIT 5
            """
            self.cursor.execute(query)
            result = self.cursor.fetchall()
            
            # Define column names matching the query
            columns = ["Lease ID", "Unit Name", "Client", "Property", "End Date"]
            
            # Convert to pandas DataFrame
            df = pd.DataFrame(result, columns=columns)
            
            # Set the 'ID' column as the index
            df.set_index('Lease ID', inplace=True)
            
            return df
        except Error as e:
            print(f"Error fetching clients: {e}")
            return pd.DataFrame()  # Return an empty DataFrame on error
        
        
    def fetch_all_expried(self):
        try:
            self.connect()
            query = """
                SELECT l.lease_id, unit_name, tenant_name, property_name, end_date
                From lease l
                JOIN client c ON l.client_id = c.client_id
                JOIN property p ON l.property_id = p.property_id
                WHERE l.end_date < CURDATE() AND l.lease_status = 'Open'
            """
            self.cursor.execute(query)
            result = self.cursor.fetchall()
            
            # Define column names matching the query
            columns = ["Lease ID", "Unit Name", "Client", "Property", "End Date"]
            
            # Convert to pandas DataFrame
            df = pd.DataFrame(result, columns=columns)
            
            # Set the 'ID' column as the index
            df.set_index('Lease ID', inplace=True)
            
            return df
        except Error as e:
            print(f"Error fetching clients: {e}")
            return pd.DataFrame()  # Return an empty DataFrame on error
    
    
    def insert_client(self, tenant_name, phone_number, email, contact_person, address):
        """
        Insert client information into the database and return the client_id.
        """
        try:
            self.connect()
            query = """
                INSERT INTO client (tenant_name, phone_number, email, contact_person, address)
                VALUES (%s, %s, %s, %s, %s)
            """
            values = (tenant_name, phone_number, email, contact_person, address)
            self.cursor.execute(query, values)
            self.conn.commit()

            # ✅ Get the last inserted client_id
            client_id = self.cursor.lastrowid  

            print(f"Client data inserted successfully with ID {client_id}")
            return client_id  # ✅ Return client_id for audit log

        except Error as e:
            print(f"Error while inserting client data: {e}")
            return None  # ✅ Return None if insertion fails

        finally:
            self.close()


    def fetch_all_clients(self):
        try:
            self.connect()
            query = """
                SELECT client_id as ID, tenant_name AS 'Tenant Name', 
                    phone_number AS 'Phone Number', 
                    email AS 'Email', 
                    contact_person AS 'Contact Person', 
                    address AS 'Address'
                from client 
            """
            self.cursor.execute(query)
            result = self.cursor.fetchall()
            
            # Define column names matching the query
            columns = ['ID', 'Tenant Name', 'Phone Number', 'Email', 'Contact Person', 'Address']
            
            # Convert to pandas DataFrame
            df = pd.DataFrame(result, columns=columns)
            
            # Set the 'ID' column as the index
            df.set_index('ID', inplace=True)
            
            return df
        except Error as e:
            print(f"Error fetching clients: {e}")
            return pd.DataFrame()  # Return an empty DataFrame on error
        


    def insert_property(self, property_name, address, owner, unit_count):
        """
        Insert property information into the database and return the property_id.
        """
        try:
            self.connect()
            query = """
                INSERT INTO property (property_name, address, owner, unit_count)
                VALUES (%s, %s, %s, %s)
            """
            self.cursor.execute(query, (property_name, address, owner, unit_count))
            self.conn.commit()

            # ✅ Get the last inserted property_id
            property_id = self.cursor.lastrowid  

            print(f"Property data inserted successfully with ID {property_id}")
            return property_id  # ✅ Return property_id for audit log

        except Error as e:
            print(f"Error while inserting property data: {e}")
            return None  # ✅ Return None if insertion fails

        finally:
            self.close()


    def fetch_all_properties(self):
        try:
            self.connect()
            query = """
                SELECT property_id as ID, property_name AS 'Property Name', 
                       address AS 'Address', 
                       owner AS 'Owner', 
                       unit_count AS 'Unit Count'
                from property
            """
            self.cursor.execute(query)
            result = self.cursor.fetchall()
            return result
        except Error as e:
            print(f"Error fetching properties: {e}")
            return []
        finally:
            self.close()
            

    def insert_lease(self, client_id, property_id, unit_name, start_date, end_date, rental_amount, lease_deposit, lease_pdf, signed, increment_period=None, increment_percentage=None, increment_amount=None):
        try:
            self.connect()

            # Determine which query to use based on optional parameters
            if increment_period is None:
                query = """
                    INSERT INTO lease (client_id, property_id, unit_name, start_date, end_date, original_rental_amount, lease_deposit, lease_pdf, signed)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                values = (client_id, property_id, unit_name, start_date, end_date, rental_amount, lease_deposit, lease_pdf, signed)
            else:
                query = """
                    INSERT INTO lease (client_id, property_id, unit_name, start_date, end_date, increment_period, original_rental_amount, lease_deposit, lease_pdf, signed, increment_percentage, increment_amount)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                values = (client_id, property_id, unit_name, start_date, end_date, increment_period, rental_amount, lease_deposit, lease_pdf, signed, increment_percentage, increment_amount)

            # Execute the query
            self.cursor.execute(query, values)
            self.conn.commit()

            # Get the last inserted lease_id
            lease_id = self.cursor.lastrowid  # ✅ This returns the inserted lease ID

            print(f"Lease data inserted successfully with ID {lease_id}")
            return lease_id  # ✅ Return lease_id for audit log

        except Error as e:
            print(f"Error while inserting lease data: {e}")
            return None  # ✅ Return None if insertion fails

        finally:
            self.close()



    def fetch_all_leases_detailed(self):
        try:
            self.connect()
            query = """
                SELECT l.unit_name AS 'Unit Name',
                       c.tenant_name AS 'Client',
                       p.property_name AS 'Property',
                       l.start_date AS 'Start Date',
                       l.end_date AS 'End Date',
                       l.increment_period AS 'Increment Period',
                       l.rental_amount AS 'Rental Amount',
                       l.lease_deposit AS 'Lease Deposit',
                       l.lease_pdf AS 'Lease PDF',
                       l.signed AS 'Signed',
                       l.lease_status AS 'Status'
                FROM lease l
                JOIN client c ON l.client_id = c.client_id
                JOIN property p ON l.property_id = p.property_id
            """
            self.cursor.execute(query)
            result = self.cursor.fetchall()
            return result
        except Error as e:
            print(f"Error fetching detailed leases: {e}")
            return []
        finally:
            self.close()

    def fetch_all(self, query, params=None):
        try:
            self.connect()  # Ensure the connection is established
            if self.cursor is None:
                raise Exception("Database cursor is not initialized.")
            self.cursor.execute(query, params)
            result = self.cursor.fetchall()
            return result
        except Exception as e:
            print(f"Error fetching data: {e}")
            return []
        finally:
            self.close()
            
            
    def fetch_all_expiring_leases(self):
        try:
            print("✅ Connecting to database...")
            self.connect()  # Ensure connection is open

            print("✅ Running SQL query...")
            query = """
                SELECT l.lease_id, unit_name, tenant_name, property_name, end_date
                FROM lease l
                JOIN client c ON l.client_id = c.client_id
                JOIN property p ON l.property_id = p.property_id
                WHERE l.lease_status = 'Open'
                ORDER BY l.end_date ASC
                LIMIT 5
            """
            self.cursor.execute(query)
            
            print("✅ Fetching results...")
            rows = self.cursor.fetchall()
            
            print(f"✅ Retrieved {len(rows)} rows")  # Print the number of rows
            
            columns = ["Lease ID", "Unit Name", "Tenant Name", "Property Name", "End Date"]
            df = pd.DataFrame(rows, columns=columns)

            print("✅ Returning DataFrame to Streamlit")
            return df

        except Exception as e:
            print(f"🚨 Error fetching leases: {e}")
            return pd.DataFrame(columns=["Lease ID", "Unit Name", "Tenant Name", "Property Name", "End Date"])

        

            
            

    def execute_query(self, query, params=None):
        try:
            self.connect()
            self.cursor.execute(query, params)
            self.conn.commit()
            print("Query executed successfully")
        except Error as e:
            print(f"Error executing query: {e}")
        finally:
            self.close()
            
            
            
    def fetch_one(self, query, params=None):
        """
        Fetches a single record from the database.

        :param query: SQL query to execute.
        :param params: Parameters for the SQL query.
        :return: Dictionary containing the fetched row or None if no result.
        """
        try:
            self.connect()  # Ensure connection is established
            
            # Initialize a local cursor instead of modifying self.cursor
            cursor = self.conn.cursor(dictionary=True)  
            cursor.execute(query, params)  # Execute the query with parameters
            row = cursor.fetchone()  # Fetch the first matching record
            
            return row if row else None  # Return the fetched row as a dictionary, or None if no result
        except Exception as e:
            print(f"Error fetching record: {e}")
            return None
        finally:
            if 'cursor' in locals():  # Ensure cursor is closed only if it was created
                cursor.close()
            self.close()  # Close the connection properly




    def fetch_all_clients_names(self):
        try:
            self.connect()
            query = """
                SELECT client_id, tenant_name AS 'Tenant Name'
                from client 
            """
            self.cursor.execute(query)
            rows = self.cursor.fetchall()

            # Convert tuples to dictionaries
            columns = ["client_id", "Tenant Name"]
            return [dict(zip(columns, row)) for row in rows]
        except Error as e:
            print(f"Error fetching clients: {e}")
            return []
        finally:
            self.close()
            
            
    def fetch_all_properties_names(self):
        try:
            self.connect()
            query = """
                SELECT property_id, property_name AS 'Property Name'
                from property
            """
            self.cursor.execute(query)
            rows = self.cursor.fetchall()

            # Convert tuples to dictionaries
            columns = ["property_id", "Property Name"]
            return [dict(zip(columns, row)) for row in rows]
        except Error as e:
            print(f"Error fetching properties: {e}")
            return []
        finally:
            self.close()
            
            
    def fetch_leases_for_reminder(self):
        query = """
        SELECT lease_id, end_date
        From lease
        WHERE lease_status = 'Open' 
        AND (
            end_date = CURDATE() + INTERVAL 3 MONTH OR
            end_date = CURDATE() + INTERVAL 1 MONTH OR
            end_date = CURDATE() + INTERVAL 1 WEEK OR
            end_date = CURDATE() + INTERVAL 1 DAY
        );
        """
        return self.fetch_all(query)
    
    
    def update_client(self, client_id, phone_number, email, address):
        try:
            self.connect()
            query = """
                UPDATE client
                SET phone_number = %s, email = %s, address = %s
                WHERE client_id = %s
            """
            self.cursor.execute(query, (phone_number, email, address, client_id))
            self.conn.commit()
            print(f"Client ID {client_id} updated successfully.")
            return True
        except Exception as e:
            print(f"Error updating client ID {client_id}: {e}")
            return False
        finally:
            self.close()



    def insert_audit_log(self, username, action_type, target_id, target_type):
        query = """
        INSERT INTO audit_log (username, action_type, target_id, target_type)
        VALUES (%s, %s, %s, %s)
        """
        self.execute_query(query, (username, action_type, target_id, target_type))