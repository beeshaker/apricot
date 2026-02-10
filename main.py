import streamlit as st
import pandas as pd
from datetime import date
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

def add_months(dt: pd.Timestamp, months: int) -> pd.Timestamp:
    return dt + pd.DateOffset(months=months)

def next_increment_due(start_date: pd.Timestamp, period_months: float, today: pd.Timestamp) -> pd.Timestamp | pd.NaT:
    """
    Assumes increment_period is in MONTHS (12 = yearly).
    """
    if pd.isna(start_date) or pd.isna(period_months) or period_months <= 0:
        return pd.NaT

    period_months = int(period_months)

    months_diff = (today.year - start_date.year) * 12 + (today.month - start_date.month)
    if today.day < start_date.day:
        months_diff -= 1

    k = max(0, (months_diff // period_months) + 1)  # next period number
    return add_months(start_date, k * period_months)

# -----------------------------
# Load data
# -----------------------------
df = db.fetch_all_leases_dashboard()

if df.empty:
    st.info("No leases found.")
    st.stop()

df["start_date"] = to_dt(df["start_date"])
df["end_date"] = to_dt(df["end_date"])
df["created_at"] = to_dt(df["created_at"])
df["increment_percentage"] = pd.to_numeric(df["increment_percentage"], errors="coerce")
df["increment_period"] = pd.to_numeric(df["increment_period"], errors="coerce")

today = pd.Timestamp(date.today())
three_months_ahead = today + pd.DateOffset(months=3)
three_months_ago = today - pd.DateOffset(months=3)

# derived increment due date
df["next_increment_due"] = df.apply(
    lambda r: next_increment_due(r["start_date"], r["increment_period"], today),
    axis=1
)

# -----------------------------
# Sidebar filters
# -----------------------------
st.sidebar.header("Filters")

# Year filter (end_date year)
end_years = sorted(df["end_date"].dropna().dt.year.unique().tolist(), reverse=True)
selected_year = st.sidebar.selectbox("Year (by end_date)", ["All"] + end_years)

# Increment due in X days
inc_due_only = st.sidebar.checkbox("Show only increment due within 90 days", value=False)

# Increment % range
if df["increment_percentage"].notna().any():
    min_p = float(df["increment_percentage"].min())
    max_p = float(df["increment_percentage"].max())
else:
    min_p, max_p = 0.0, 100.0

inc_range = st.sidebar.slider(
    "Increment % range",
    min_value=float(min_p),
    max_value=float(max_p),
    value=(float(min_p), float(max_p))
)

# Search property/unit
search = st.sidebar.text_input("Search property / unit", value="").strip().lower()

# -----------------------------
# Apply filters
# -----------------------------
f = df.copy()

if selected_year != "All":
    f = f[f["end_date"].dt.year == int(selected_year)]

f = f[f["increment_percentage"].fillna(-1).between(inc_range[0], inc_range[1])]

if inc_due_only:
    in_90 = today + pd.Timedelta(days=90)
    f = f[(f["next_increment_due"].notna()) & (f["next_increment_due"] >= today) & (f["next_increment_due"] <= in_90)]

if search:
    f = f[
        f["property_name"].fillna("").str.lower().str.contains(search)
        | f["unit_name"].fillna("").str.lower().str.contains(search)
        | f["property_id"].astype(str).str.contains(search)
    ]

# -----------------------------
# Windows (global counts)
# -----------------------------
expired_df = f[f["end_date"].notna() & (f["end_date"] < today)].copy()
expiring_3m_df = f[f["end_date"].notna() & (f["end_date"] >= today) & (f["end_date"] <= three_months_ahead)].copy()
uploaded_3m_df = f[f["created_at"].notna() & (f["created_at"] >= three_months_ago)].copy()

# Summary
c1, c2, c3, c4 = st.columns(4)
c1.metric("Expired", len(expired_df))
c2.metric("Expiring (≤ 3 months)", len(expiring_3m_df))
c3.metric("Uploaded (last 3 months)", len(uploaded_3m_df))
c4.metric(
    "Increment due (≤ 90 days)",
    int(((f["next_increment_due"].notna())
         & (f["next_increment_due"] <= (today + pd.Timedelta(days=90)))
         & (f["next_increment_due"] >= today)).sum())
)

st.divider()

# -----------------------------
# Property/Unit windows (no mixing)
# -----------------------------
groups = (
    f[["property_id", "property_name", "unit_name"]]
    .dropna(subset=["property_id", "unit_name"])
    .drop_duplicates()
    .sort_values(["property_name", "unit_name"])
    .values.tolist()
)

if not groups:
    st.warning("No results match your filters.")
    st.stop()

cols_to_show = [
    "lease_id", "lease_status", "signed",
    "start_date", "end_date", "created_at",
    "increment_percentage", "increment_period", "increment_amount",
    "next_increment_due",
    "client_id"
]

for property_id, property_name, unit_name in groups:
    g_expired = expired_df[(expired_df["property_id"] == property_id) & (expired_df["unit_name"] == unit_name)]
    g_expiring = expiring_3m_df[(expiring_3m_df["property_id"] == property_id) & (expiring_3m_df["unit_name"] == unit_name)]
    g_uploaded = uploaded_3m_df[(uploaded_3m_df["property_id"] == property_id) & (uploaded_3m_df["unit_name"] == unit_name)]

    if g_expired.empty and g_expiring.empty and g_uploaded.empty:
        continue

    header = f"🏠 {property_name} — {unit_name} | Expired: {len(g_expired)} • 3m: {len(g_expiring)} • Uploaded 3m: {len(g_uploaded)}"
    with st.expander(header, expanded=False):
        tab1, tab2, tab3 = st.tabs(["Expired", "3 Months to Expire", "Uploaded (Last 3 Months)"])

        with tab1:
            if g_expired.empty:
                st.info("No expired leases here.")
            else:
                st.dataframe(g_expired[cols_to_show].sort_values("end_date"), use_container_width=True)

        with tab2:
            if g_expiring.empty:
                st.info("No leases expiring within 3 months here.")
            else:
                st.dataframe(g_expiring[cols_to_show].sort_values("end_date"), use_container_width=True)

        with tab3:
            if g_uploaded.empty:
                st.info("No leases uploaded in the last 3 months here.")
            else:
                st.dataframe(g_uploaded[cols_to_show].sort_values("created_at", ascending=False), use_container_width=True)
