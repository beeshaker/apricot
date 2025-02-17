import streamlit as st
from conn import MySQLDatabase  # Assuming MySQLDatabase class is in conn.py
import pandas as pd
from datetime import datetime
from decimal import Decimal

# Initialize database connection
db = MySQLDatabase()

st.set_page_config(page_title="Lease Management Dashboard")

# Dashboard Title
st.title("Lease Management Dashboard")

# Fetch Expired Leases
expired = db.fetch_all_expried()
if not expired.empty:
    st.subheader("Expired Leases")
    st.dataframe(expired, use_container_width=True)

# Fetch Next 5 Leases to Expire
expiring = db.fetch_all_expring()
if not expiring.empty:
    st.subheader("Next 5 Leases to Expire")
    st.dataframe(expiring, use_container_width=True)

# Fetch Recently Added Leases
new_add = db.fetch_all_recent_add()
if not new_add.empty:
    st.subheader("Last 5 Leases Added")
    st.dataframe(new_add, use_container_width=True)

# Fetch All Leases with Rent Increments
query_upcoming_increments = """
    SELECT lease_id, unit_name, client_id, property_id, start_date, end_date, increment_period,
           original_rental_amount, new_rental_amount, lease_status, increment_percentage, increment_amount
    FROM lease
    WHERE increment_period IS NOT NULL
"""
all_leases = db.fetch_all(query_upcoming_increments)

if all_leases:
    leases_df = pd.DataFrame(all_leases, columns=[
        "Lease ID", "Unit Name", "Client ID", "Property ID", "Start Date", "End Date",
        "Increment Period (Months)", "Original Rent", "New Rent", "Lease Status", "Increment Percentage", "Increment Amount"
    ])

    # ✅ Convert datetime to date format (YYYY-MM-DD)
    leases_df["Start Date"] = pd.to_datetime(leases_df["Start Date"]).dt.date
    leases_df["End Date"] = pd.to_datetime(leases_df["End Date"]).dt.date

    # ✅ Calculate Next Increment Date and convert to date format
    leases_df["Next Increment Date"] = leases_df.apply(
        lambda row: (row["Start Date"] + pd.DateOffset(months=int(row["Increment Period (Months)"]))).date(), axis=1
    )

    # Filter leases where next increment is in the future
    today = datetime.today().date()
    upcoming_increments = leases_df[(leases_df["Next Increment Date"] > today)]

    # ✅ Ensure `increment_percentage` and `increment_amount` are properly handled
    upcoming_increments["Increment Percentage"] = upcoming_increments["Increment Percentage"].fillna(0).astype(float)

    # ✅ Calculate the increment amount dynamically if NULL
    upcoming_increments["Increment Amount"] = upcoming_increments.apply(
        lambda row: float(row["Increment Amount"]) if pd.notnull(row["Increment Amount"]) 
        else float(row["Original Rent"]) * (row["Increment Percentage"] / 100), axis=1
    )

    # ✅ Calculate the new expected rent amount
    upcoming_increments["Calculated New Rent"] = upcoming_increments.apply(
        lambda row: float(row["New Rent"]) if pd.notnull(row["New Rent"]) 
        else float(row["Original Rent"]) + row["Increment Amount"], axis=1
    )

    # Show Upcoming Rent Increments
    if not upcoming_increments.empty:
        st.subheader("Upcoming Rent Increments")
        st.dataframe(
            upcoming_increments[["Lease ID", "Unit Name", "Next Increment Date", "Original Rent", "Increment Percentage", "Increment Amount", "New Rent", "Calculated New Rent"]],
            use_container_width=True
        )

    # Fetch Recently Changed Rental Amounts
    query_recent_changes = """
        SELECT lease_id, unit_name, client_id, property_id, original_rental_amount, new_rental_amount, increment_amount, last_updated
        FROM lease
        WHERE new_rental_amount IS NOT NULL
        ORDER BY last_updated DESC
        LIMIT 5
    """
    recent_changes = db.fetch_all(query_recent_changes)

    if recent_changes:
        recent_changes_df = pd.DataFrame(recent_changes, columns=[
            "Lease ID", "Unit Name", "Client ID", "Property ID", "Original Rent", "New Rent", "Increment Amount", "Last Updated"
        ])

        # ✅ Convert `decimal.Decimal` to `float` before displaying
        recent_changes_df["Original Rent"] = recent_changes_df["Original Rent"].astype(float)
        recent_changes_df["New Rent"] = recent_changes_df["New Rent"].astype(float)
        recent_changes_df["Increment Amount"] = recent_changes_df["Increment Amount"].astype(float)

        # ✅ Convert `Last Updated` to date format
        recent_changes_df["Last Updated"] = pd.to_datetime(recent_changes_df["Last Updated"]).dt.date

        # Show Recent Changes in Rental Amounts
        st.subheader("Recently Changed Rental Amounts")
        st.dataframe(recent_changes_df, use_container_width=True)
