import streamlit as st
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta

from conn import MySQLDatabase
from menu import menu

db = MySQLDatabase()

# Auth
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.switch_page("pages/login.py")
    st.stop()

st.set_page_config(page_title="Lease Management Dashboard", page_icon="🏠", layout="wide")
st.title("Lease Management Dashboard")

if st.session_state["authenticated"]:
    menu()

# -----------------------------
# Helpers
# -----------------------------
def to_dt(s):
    return pd.to_datetime(s, errors="coerce")

def norm_bool(x):
    if pd.isna(x):
        return False
    if isinstance(x, bool):
        return x
    return str(x).strip().lower() in ("1", "true", "yes", "y")

# -----------------------------
# Fetch all leases once
# -----------------------------
leases = db.fetch_all_leases()  # <-- you will add this in conn.py (section 2)

if leases.empty:
    st.info("No leases found.")
    st.stop()

# Expected columns (adjust names here if your DB uses different ones)
# property_name, lease_end_date, created_at, lease_type, increment_due_date, increment_percent
leases["lease_end_date"] = to_dt(leases.get("lease_end_date"))
leases["created_at"] = to_dt(leases.get("created_at"))
leases["increment_due_date"] = to_dt(leases.get("increment_due_date"))
leases["increment_percent"] = pd.to_numeric(leases.get("increment_percent"), errors="coerce")

# -----------------------------
# Sidebar filters
# -----------------------------
st.sidebar.header("Filters")

# Year filter (by lease_end_date OR created_at; we’ll filter on lease_end_date by default)
years = sorted(
    {d.year for d in leases["lease_end_date"].dropna().dt.to_pydatetime()},
    reverse=True
)
selected_year = st.sidebar.selectbox("Year (by Lease End Date)", ["All"] + years)

lease_type_vals = sorted([x for x in leases["lease_type"].dropna().unique().tolist()])
selected_types = st.sidebar.multiselect(
    "Lease Type",
    options=lease_type_vals,
    default=lease_type_vals
)

# Increment due (based on increment_due_date being within X days)
inc_due_only = st.sidebar.checkbox("Show only Increment Due (next 90 days)", value=False)

# Increment % range
min_p = float(leases["increment_percent"].min()) if leases["increment_percent"].notna().any() else 0.0
max_p = float(leases["increment_percent"].max()) if leases["increment_percent"].notna().any() else 100.0
inc_range = st.sidebar.slider(
    "Increment % range",
    min_value=float(min_p),
    max_value=float(max_p),
    value=(float(min_p), float(max_p))
)

# Optional: property search
prop_search = st.sidebar.text_input("Search Property", value="").strip().lower()

# -----------------------------
# Apply filters
# -----------------------------
df = leases.copy()

if selected_year != "All":
    df = df[df["lease_end_date"].dt.year == int(selected_year)]

if selected_types:
    df = df[df["lease_type"].isin(selected_types)]

df = df[df["increment_percent"].fillna(-1).between(inc_range[0], inc_range[1])]

today = pd.Timestamp(date.today())
in_90_days = today + pd.Timedelta(days=90)

if inc_due_only:
    # increment_due_date within next 90 days
    df = df[(df["increment_due_date"].notna()) & (df["increment_due_date"] <= in_90_days) & (df["increment_due_date"] >= today)]

if prop_search:
    df = df[df["property_name"].fillna("").str.lower().str.contains(prop_search)]

# -----------------------------
# Define the 3 windows
# -----------------------------
three_months_ahead = today + relativedelta(months=3)
three_months_ago = today - relativedelta(months=3)

expired_df = df[df["lease_end_date"].notna() & (df["lease_end_date"] < today)].copy()
expiring_3m_df = df[df["lease_end_date"].notna() & (df["lease_end_date"] >= today) & (df["lease_end_date"] <= three_months_ahead)].copy()
uploaded_3m_df = df[df["created_at"].notna() & (df["created_at"] >= three_months_ago)].copy()

# -----------------------------
# Property-first UI
# -----------------------------
st.subheader("Properties")

# Build per-property views so leases don’t mix
properties = sorted([p for p in df["property_name"].dropna().unique().tolist()])

if not properties:
    st.warning("No properties match your filters.")
    st.stop()

# Summary counts
c1, c2, c3 = st.columns(3)
c1.metric("Expired (filtered)", len(expired_df))
c2.metric("Expiring in 3 months (filtered)", len(expiring_3m_df))
c3.metric("Uploaded in last 3 months (filtered)", len(uploaded_3m_df))

st.divider()

for prop in properties:
    prop_all = df[df["property_name"] == prop].copy()
    prop_expired = expired_df[expired_df["property_name"] == prop].copy()
    prop_expiring = expiring_3m_df[expiring_3m_df["property_name"] == prop].copy()
    prop_uploaded = uploaded_3m_df[uploaded_3m_df["property_name"] == prop].copy()

    # Skip properties with nothing after filters (optional)
    if prop_expired.empty and prop_expiring.empty and prop_uploaded.empty:
        continue

    with st.expander(f"🏠 {prop}  |  Expired: {len(prop_expired)}  •  3m Expiring: {len(prop_expiring)}  •  Uploaded 3m: {len(prop_uploaded)}", expanded=False):
        tab1, tab2, tab3 = st.tabs(["Expired", "3 Months to Expire", "Uploaded (Last 3 Months)"])

        with tab1:
            if prop_expired.empty:
                st.info("No expired leases for this property (under current filters).")
            else:
                st.dataframe(
                    prop_expired.sort_values("lease_end_date"),
                    use_container_width=True
                )

        with tab2:
            if prop_expiring.empty:
                st.info("No leases expiring within 3 months for this property (under current filters).")
            else:
                st.dataframe(
                    prop_expiring.sort_values("lease_end_date"),
                    use_container_width=True
                )

        with tab3:
            if prop_uploaded.empty:
                st.info("No leases uploaded in the last 3 months for this property (under current filters).")
            else:
                st.dataframe(
                    prop_uploaded.sort_values("created_at", ascending=False),
                    use_container_width=True
                )
