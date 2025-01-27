import mysql.connector

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="pass",
        database="apricot"
    )
    cursor = conn.cursor()
    
    query = """
        SELECT l.lease_id, unit_name, tenant_name, property_name, end_date
        FROM Lease l
        JOIN Client c ON l.client_id = c.client_id
        JOIN Property p ON l.property_id = p.property_id
        WHERE l.lease_status = 'Open'
        ORDER BY l.end_date ASC
        LIMIT 5
    """

    print("Executing query...")
    cursor.execute(query)
    result = cursor.fetchall()
    print("Query executed successfully!")

    print("Result:", result)

except Exception as e:
    print(f"🚨 Error: {e}")

finally:
    if conn.is_connected():
        cursor.close()
        conn.close()
        print("✅ Connection closed")
