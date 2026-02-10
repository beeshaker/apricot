import streamlit as st
import pandas as pd
from datetime import date
from typing import Optional

from conn import MySQLDatabase
from menu import menu

db = MySQLDatabase()

# Auth
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.switch_page("pages/login.py")
    st.stop()

st.set_page_config(page_title="Lease Management Dashboard", page_icon="🏠", layout="wide")
st.title("🏠 Lease Management Dashboard")

if st.session_state["authenticated"]:
    menu()

# -----------------------------
# Session defaults (filters)
# -----------------------------
def _init_filters():
    st.session_state.setdefault("lease_filter_property", "All")
    st.session_state.setdefault("lease_filter_unit", "")
    st.session_state.setdefault("lease_filter_year", "All")
    st.session_state.setdefault("lease_filter_inc_due", False)
    st.session_state.setdefault("lease_filter_inc_min", None)
    st.session_state.setdefault("lease_filter_inc_max", None)

_init_filters()

def clear_filters():
    st.session_state["lease_filter_property"] = "All"
    st.session_state["lease_filter_unit"] = ""
    st.session_state["lease_filter_year"] = "All"
    st.session_state["lease_filter_inc_due"] = False
    # keep % range as-is (optional) or reset:
    # st.session_state["lease_filter_inc_min"] = None
    # st.session_state["lease_filter_inc_max"] = None

# -----------------------------
# Helpers
# -----------------------------
def to_dt(s):
    return pd.to_datetime(s, errors="coerce")

def next_increment_due(
    start_date: pd.Timestamp,
    period_months: float,
    today: pd.Timestamp
) -> Optional[pd.Timestamp]:
    """Assumes increment_period is MONTHS (12 = yearly). Returns Timestamp or None."""
    if pd.isna(start_date) or pd.isna(period_months) or period_months <= 0:
        return None
    period_months = int(period_months)

    months_diff = (today.year - start_date.year) * 12 + (today.month - start_date.month)
    if today.day < start_date.day:
        months_diff -= 1
    k = max(0, (months_diff // period_months) + 1)
    return start_date + pd.DateOffset(months=k * period_months)

# -----------------------------
# Load data
# -----------------------------
leases_df_all = db.fetch_all_leases_dashboard()
props_df = db.fetch_properties()

if leases_df_all is None or leases_df_all.empty:
    st.info("✅ No leases found.")
    st.stop()

leases_df_all["start_date"] = to_dt(leases_df_all["start_date"])
leases_df_all["end_date"] = to_dt(leases_df_all["end_date"])
leases_df_all["created_at"] = to_dt(leases_df_all["created_at"])
leases_df_all["increment_percentage"] = pd.to_numeric(leases_df_all["increment_percentage"], errors="coerce")
leases_df_all["increment_period"] = pd.to_numeric(leases_df_all["increment_period"], errors="coerce")

today = pd.Timestamp(date.today())
three_months_ahead = today + pd.DateOffset(months=3)
three_months_ago = today - pd.DateOffset(months=3)

leases_df_all["next_increment_due"] = leases_df_all.apply(
    lambda r: next_increment_due(r["start_date"], r["increment_period"], today),
    axis=1
)
leases_df_all["next_increment_due"] = pd.to_datetime(leases_df_all["next_increment_due"], errors="coerce")

# -----------------------------
# Buckets (expiry)
# -----------------------------
leases_df_all["_end_date_only"] = leases_df_all["end_date"].dt.date
today_date = today.date()

leases_df_all["days_to_end"] = leases_df_all["_end_date_only"].apply(
    lambda d: (d - today_date).days if pd.notna(d) else None
)

leases_df_all["_expiry_bucket"] = "No end date"
leases_df_all.loc[leases_df_all["days_to_end"] < 0, "_expiry_bucket"] = "Expired"
leases_df_all.loc[leases_df_all["days_to_end"] == 0, "_expiry_bucket"] = "Ends today"
leases_df_all.loc[leases_df_all["days_to_end"].between(1, 90), "_expiry_bucket"] = "Expiring (≤ 3 months)"
leases_df_all.loc[leases_df_all["days_to_end"] > 90, "_expiry_bucket"] = "Active"

EXP_ICON = {
    "Expired": "🔴",
    "Ends today": "🟡",
    "Expiring (≤ 3 months)": "🟠",
    "Active": "🟢",
    "No end date": "⚪",
}

EXP_COLORS = {
    "Expired": "background-color: rgba(244, 67, 54, 0.12);",
    "Ends today": "background-color: rgba(255, 193, 7, 0.14);",
    "Expiring (≤ 3 months)": "background-color: rgba(255, 152, 0, 0.12);",
    "Active": "background-color: rgba(76, 175, 80, 0.10);",
    "No end date": "background-color: rgba(158, 158, 158, 0.10);",
}

def style_expiry_rows(row):
    bucket = row.get("_expiry_bucket", "No end date")
    return [EXP_COLORS.get(bucket, "")] * len(row)

# -----------------------------
# Stats (full df)
# -----------------------------
expired_count = int((leases_df_all["_expiry_bucket"] == "Expired").sum())
expiring_count = int((leases_df_all["_expiry_bucket"] == "Expiring (≤ 3 months)").sum())
uploaded_3m_count = int((leases_df_all["created_at"].notna() & (leases_df_all["created_at"] >= three_months_ago)).sum())

inc_due_90 = int(
    (leases_df_all["next_increment_due"].notna()
     & (leases_df_all["next_increment_due"] >= today)
     & (leases_df_all["next_increment_due"] <= (today + pd.Timedelta(days=90)))).sum()
)

# -----------------------------
# Simple stats cards (reuse your existing CSS if you want)
# -----------------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Expired", expired_count)
c2.metric("Expiring ≤ 3 months", expiring_count)
c3.metric("Uploaded last 3 months", uploaded_3m_count)
c4.metric("Increment due ≤ 90 days", inc_due_90)

st.divider()

# -----------------------------
# Filters row (ticket-like)
# -----------------------------
f1, f2, f3, f4, f5 = st.columns([1.2, 1, 0.9, 1.2, 0.7])

with f1:
    prop_vals = sorted(props_df["property_name"].dropna().unique().tolist()) if props_df is not None and not props_df.empty else []
    prop_options = ["All"] + prop_vals
    st.selectbox(
        "Property",
        options=prop_options,
        index=prop_options.index(st.session_state.lease_filter_property)
        if st.session_state.lease_filter_property in prop_options else 0,
        key="lease_filter_property",
    )

with f2:
    st.text_input(
        "Unit",
        value=st.session_state.lease_filter_unit,
        key="lease_filter_unit",
        placeholder="e.g. A1 / 445",
    )

with f3:
    end_years = sorted(leases_df_all["end_date"].dropna().dt.year.unique().tolist(), reverse=True)
    year_options = ["All"] + end_years
    st.selectbox(
        "Year (end date)",
        options=year_options,
        index=year_options.index(st.session_state.lease_filter_year)
        if st.session_state.lease_filter_year in year_options else 0,
        key="lease_filter_year",
    )

with f4:
    st.checkbox(
        "Increment due ≤ 90 days",
        value=bool(st.session_state.lease_filter_inc_due),
        key="lease_filter_inc_due",
    )

with f5:
    st.button("Clear", use_container_width=True, on_click=clear_filters)

# Increment % range filter (below filters row, like a "secondary filter")
inc_min = float(leases_df_all["increment_percentage"].min()) if leases_df_all["increment_percentage"].notna().any() else 0.0
inc_max = float(leases_df_all["increment_percentage"].max()) if leases_df_all["increment_percentage"].notna().any() else 100.0

# keep stable defaults
if st.session_state.lease_filter_inc_min is None:
    st.session_state.lease_filter_inc_min = inc_min
if st.session_state.lease_filter_inc_max is None:
    st.session_state.lease_filter_inc_max = inc_max

inc_range = st.slider(
    "Increment % range",
    min_value=float(inc_min),
    max_value=float(inc_max),
    value=(float(st.session_state.lease_filter_inc_min), float(st.session_state.lease_filter_inc_max)),
)

st.session_state.lease_filter_inc_min, st.session_state.lease_filter_inc_max = inc_range

# -----------------------------
# Apply filters
# -----------------------------
leases_df = leases_df_all.copy()

sel_prop = st.session_state.lease_filter_property
if sel_prop != "All":
    leases_df = leases_df[leases_df["property_name"] == sel_prop]

unit_q = st.session_state.lease_filter_unit.strip().lower()
if unit_q:
    leases_df = leases_df[leases_df["unit_name"].astype(str).str.lower().str.contains(unit_q, na=False)]

sel_year = st.session_state.lease_filter_year
if sel_year != "All":
    leases_df = leases_df[leases_df["end_date"].dt.year == int(sel_year)]

# Increment % range
leases_df = leases_df[
    leases_df["increment_percentage"].fillna(-1).between(st.session_state.lease_filter_inc_min, st.session_state.lease_filter_inc_max)
]

# Increment due ≤ 90 days
if st.session_state.lease_filter_inc_due:
    in_90 = today + pd.Timedelta(days=90)
    leases_df = leases_df[
        leases_df["next_increment_due"].notna()
        & (leases_df["next_increment_due"] >= today)
        & (leases_df["next_increment_due"] <= in_90)
    ]

if leases_df.empty:
    st.warning("No leases match your filters.")
    st.stop()

# -----------------------------
# Tabs (like tickets dashboard)
# -----------------------------
tab_expired, tab_expiring, tab_uploaded = st.tabs(["🔴 Expired", "🟠 Expiring (≤ 3 months)", "🆕 Uploaded (last 3 months)"])

def prep_display(df_in: pd.DataFrame) -> pd.DataFrame:
    df_out = df_in.copy()
    df_out.insert(0, "Status", df_out["_expiry_bucket"].map(EXP_ICON).fillna("⚪"))
    # hide helper cols
    drop_cols = ["_end_date_only"]
    df_out = df_out.drop(columns=[c for c in drop_cols if c in df_out.columns], errors="ignore")
    # reorder a bit
    preferred = [
        "Status","property_name","unit_name","lease_id","lease_status","signed",
        "start_date","end_date","created_at",
        "increment_percentage","increment_period","increment_amount","next_increment_due",
        "client_id"
    ]
    keep = [c for c in preferred if c in df_out.columns] + [c for c in df_out.columns if c not in preferred]
    return df_out[keep]

with tab_expired:
    df1 = leases_df[leases_df["_expiry_bucket"] == "Expired"]
    if df1.empty:
        st.info("No expired leases under current filters.")
    else:
        styled = prep_display(df1).style.apply(style_expiry_rows, axis=1)
        st.dataframe(styled, use_container_width=True, hide_index=True)

with tab_expiring:
    df2 = leases_df[leases_df["_expiry_bucket"] == "Expiring (≤ 3 months)"]
    if df2.empty:
        st.info("No leases expiring within 3 months under current filters.")
    else:
        styled = prep_display(df2).style.apply(style_expiry_rows, axis=1)
        st.dataframe(styled, use_container_width=True, hide_index=True)

with tab_uploaded:
    df3 = leases_df[leases_df["created_at"].notna() & (leases_df["created_at"] >= three_months_ago)]
    if df3.empty:
        st.info("No leases uploaded in last 3 months under current filters.")
    else:
        # uploaded is not an expiry bucket; still keep colors based on expiry if you want
        styled = prep_display(df3).style.apply(style_expiry_rows, axis=1)
        st.dataframe(styled, use_container_width=True, hide_index=True)
