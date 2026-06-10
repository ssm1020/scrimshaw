import streamlit as st
import pandas as pd
import altair as alt
from datetime import timedelta
from data import (
    load_all,
    daily_summary,
    revenue_by_category,
    revenue_by_dow,
    top_items,
    labor_by_role,
    reservation_summary,
    covers_by_source,
    online_summary,
    food_cost_summary,
    waste_by_category,
)

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Restaurant Dashboard",
    page_icon="🍽️",
    layout="wide"
)

# ── LOAD DATA ─────────────────────────────────────────────────────────────────
@st.cache_data
def get_data():
    return load_all()

pos, labor, res, inventory, online, employees, menu = get_data()

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
st.sidebar.title("🍽️ Restaurant Analytics")
st.sidebar.markdown("---")

# Preset buttons
st.sidebar.markdown("**Quick Select**")
col1, col2 = st.sidebar.columns(2)
if col1.button("Last 7 Days"):
    st.session_state["date_range"] = "7d"
if col2.button("Last 30 Days"):
    st.session_state["date_range"] = "30d"
if st.sidebar.button("All Time", use_container_width=True):
    st.session_state["date_range"] = "all"

st.sidebar.markdown("**Or pick a range**")

min_date = pos["date"].min().date()
max_date = pos["date"].max().date()

# Resolve preset into default dates
preset = st.session_state.get("date_range", "all")
if preset == "7d":
    default_start = max_date - timedelta(days=6)
elif preset == "30d":
    default_start = max_date - timedelta(days=29)
else:
    default_start = min_date

start_date = st.sidebar.date_input("Start date", value=default_start, min_value=min_date, max_value=max_date)
end_date   = st.sidebar.date_input("End date",   value=max_date,      min_value=min_date, max_value=max_date)

# ── FILTER DATA ───────────────────────────────────────────────────────────────
def filter_by_date(df, start, end, col="date"):
    mask = (df[col].dt.date >= start) & (df[col].dt.date <= end)
    return df[mask]

pos_f   = filter_by_date(pos,       start_date, end_date)
labor_f = filter_by_date(labor,     start_date, end_date)
res_f   = filter_by_date(res,       start_date, end_date)
inv_f   = filter_by_date(inventory, start_date, end_date)
onl_f   = filter_by_date(online,    start_date, end_date)

# ── HEADER ────────────────────────────────────────────────────────────────────
st.title("Restaurant Performance Dashboard")
st.caption(f"Showing {start_date.strftime('%b %d, %Y')} → {end_date.strftime('%b %d, %Y')}")
st.markdown("---")

# ── TOP METRICS ───────────────────────────────────────────────────────────────
summary = daily_summary(pos_f, labor_f)
fc      = food_cost_summary(inv_f)
rs      = reservation_summary(res_f)

total_revenue    = summary["revenue"].sum()
total_labor_cost = summary["labor_cost"].sum()
avg_labor_pct    = summary["labor_pct"].mean()
avg_order_val    = summary["avg_order_val"].mean()
total_food_cost  = fc["total_food_cost"]
no_show_rate     = rs["no_show_rate"]

m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("Total Revenue",    f"${total_revenue:,.0f}")
m2.metric("Labor Cost",       f"${total_labor_cost:,.0f}")
m3.metric("Avg Labor %",      f"{avg_labor_pct:.1f}%")
m4.metric("Avg Order Value",  f"${avg_order_val:.2f}")
m5.metric("Food Cost",        f"${total_food_cost:,.0f}")
m6.metric("No-Show Rate",     f"{no_show_rate:.1f}%")

st.markdown("---")

# ── REVENUE OVER TIME ─────────────────────────────────────────────────────────
# st.subheader("Revenue Over Time")
# st.line_chart(summary.set_index("date")["revenue"])

revenue_over_time_chart = alt.Chart(summary).mark_line().encode(
    x=alt.X("date:T", title="Date"),
    y=alt.Y("revenue:Q",title="Revenue",axis=alt.Axis(format="$,.0f")),
    tooltip=[
        alt.Tooltip("date:T",title="Date"),
        alt.Tooltip("revenue:Q",title="Revenue",format="$,.0f")
    ]
).properties(
    height=300
).interactive(bind_y=False)

st.altair_chart(revenue_over_time_chart, use_container_width=True)

st.markdown("---")

# ── REVENUE BREAKDOWN ─────────────────────────────────────────────────────────
st.subheader("Revenue Breakdown")
col_a, col_b = st.columns(2)

with col_a:
    st.markdown("**By Category**")
    cat_df = revenue_by_category(pos_f)
    st.bar_chart(cat_df.set_index("category")["revenue"])

with col_b:
    st.markdown("**By Day of Week**")
    dow_df = revenue_by_dow(pos_f)
    st.bar_chart(dow_df.set_index("day_of_week")["avg_revenue"])

st.markdown("---")

# ── TOP ITEMS ─────────────────────────────────────────────────────────────────
st.subheader("Top 10 Items by Revenue")
items_df = top_items(pos_f, n=10)
st.dataframe(
    items_df[["item_name", "category", "qty_sold", "revenue"]],
    use_container_width=True,
    hide_index=True
)

st.markdown("---")

# ── LABOR ─────────────────────────────────────────────────────────────────────
st.subheader("Labor")
col_c, col_d = st.columns(2)

with col_c:
    st.markdown("**Cost by Role**")
    labor_df = labor_by_role(labor_f)
    st.bar_chart(labor_df.set_index("role")["total_cost"])

with col_d:
    st.markdown("**Labor % vs Revenue (Daily)**")
    st.line_chart(summary.set_index("date")["labor_pct"])

st.markdown("---")

# ── RESERVATIONS ──────────────────────────────────────────────────────────────
st.subheader("Reservations")
col_e, col_f = st.columns(2)

with col_e:
    st.markdown("**Status Breakdown**")
    status_df = res_f.groupby("status").size().reset_index(name="count")
    st.dataframe(status_df, use_container_width=True, hide_index=True)

with col_f:
    st.markdown("**Covers by Source**")
    source_df = covers_by_source(res_f)
    st.bar_chart(source_df.set_index("source")["covers"])

st.markdown("---")

# ── ONLINE ORDERS ─────────────────────────────────────────────────────────────
st.subheader("Online Orders")
onl_df = online_summary(onl_f)
st.dataframe(
    onl_df[["platform","orders","gross_revenue","platform_fees","net_revenue","avg_rating"]],
    use_container_width=True,
    hide_index=True
)

st.markdown("---")

# ── FOOD COST & WASTE ─────────────────────────────────────────────────────────
st.subheader("Food Cost & Waste")
col_g, col_h = st.columns(2)

with col_g:
    st.markdown("**Waste Cost by Category**")
    waste_df = waste_by_category(inv_f)
    st.bar_chart(waste_df.set_index("category")["waste_cost"])

with col_h:
    st.markdown("**Food Cost Summary**")
    st.metric("Total Food Cost",       f"${fc['total_food_cost']:,.2f}")
    st.metric("Total Waste Cost",      f"${fc['total_waste_cost']:,.2f}")
    st.metric("Waste % of Food Cost",  f"{fc['waste_pct_of_food_cost']}%")