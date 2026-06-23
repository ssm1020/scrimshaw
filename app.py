import streamlit as st
import pandas as pd
import altair as alt
from datetime import timedelta
#Pull in data functions
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
#Pull in visual functions
from visuals import(
    crosshair_line_chart,
    crosshair_bar_chart,
    styled_table
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
if st.sidebar.button("All Time", width='stretch'):
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
#Pulling in line chart function from visuals.py
st.altair_chart(
    crosshair_line_chart(summary,"date","revenue","Date","Revenue","$,.0f"),
    width='stretch'
    )

st.markdown("---")

# ── REVENUE BREAKDOWN ─────────────────────────────────────────────────────────
st.subheader("Revenue Breakdown")
#Set side by side containers
col_a, col_b = st.columns(2)

#### COLUMN A - By category bar chart ####
with col_a:
    st.markdown("**By Category**")
    #Set data
    cat_df = revenue_by_category(pos_f)
    #Pulling in bar chart function rom visuals.py
    st.altair_chart(
        crosshair_bar_chart(cat_df, "category", "revenue", "Category", "Revenue", "$,.0f")
        )
#### COLUMN B - By day of the week bar chart ####
with col_b:
    st.markdown("**By Day of Week**")
    #Set data
    dow_df = revenue_by_dow(pos_f)
    #Pulling in bar chart function rom visuals.py
    st.altair_chart(
        crosshair_bar_chart(dow_df, "day_of_week", "revenue", "Day", "Revenue", "$,.0f",sort=["Mon","Tue","Wed","Thu","Fri","Sat","Sun"])
                    )

st.markdown("---")

# ── TOP ITEMS ─────────────────────────────────────────────────────────────────
st.subheader("Top 10 Items by Revenue")
items_df = top_items(pos_f, n=10)
#Call styled_table function from visuals.py
styled_table(items_df, {
            "item_name":  {"label": "Item"},
            "category":   {"label": "Category"},
            "qty_sold":   {"label": "Quantity Sold", "format": "%d"},
            "revenue":    {"label": "Revenue", "format": "$%.2f"},
        })

st.markdown("---")

# ── LABOR ─────────────────────────────────────────────────────────────────────
st.subheader("Labor")
col_c, col_d = st.columns(2)

with col_c:
    st.markdown("**Cost by Role**")
    #Set data
    labor_df = labor_by_role(labor_f)
    #Pulling in bar chart function rom visuals.py "role" "total_cost"
    st.altair_chart(
        crosshair_bar_chart(labor_df, "role", "total_cost", "Role", "Total Cost", "$,.0f")
        )

with col_d:
    st.markdown("**Labor % vs Revenue (Daily)**")
    #Pulling in line chart function
    # summary date labor_pct
    st.altair_chart(
    crosshair_line_chart(summary,"date","labor_pct","Date","Labor %",".1~%"),
    width='stretch'
    )

st.markdown("---")

# ── RESERVATIONS ──────────────────────────────────────────────────────────────
st.subheader("Reservations")
col_e, col_f = st.columns(2)

with col_e:
    st.markdown("**Status Breakdown**")
    status_df = res_f.groupby("status").size().reset_index(name="count")
    #Call styled_table function from visuals.py
    styled_table(status_df, {
            "status":  {"label": "Status"},
            "count":   {"label": "Count"}
            }
    )

with col_f:
    st.markdown("**Covers by Source**")
    source_df = covers_by_source(res_f)
    #Pulling in bar chart function rom visuals.py "source" "covers"
    st.altair_chart(
        crosshair_bar_chart(source_df, "source", "covers", "Source", "Covers", "d")
        )

st.markdown("---")

# ── ONLINE ORDERS ─────────────────────────────────────────────────────────────
st.subheader("Online Orders")
onl_df = online_summary(onl_f)
styled_table(onl_df, {
            "platform":  {"label": "Platform"},
            "orders":   {"label": "Orders"},
            "gross_revenue":  {"label": "Gross Revenue","format": "$%.2f"},
            "platform_fees":   {"label": "Platform Fees","format": "$%.2f"},
            "net_revenue":  {"label": "Net Revenue","format": "$%.2f"},
            "avg_rating":   {"label": "Avg Rating"},
            }
)

st.markdown("---")

# ── FOOD COST & WASTE ─────────────────────────────────────────────────────────
st.subheader("Food Cost & Waste")
col_g, col_h = st.columns(2)

with col_g:
    st.markdown("**Waste Cost by Category**")
    waste_df = waste_by_category(inv_f)
    #Pulling in bar chart function rom visuals.py "category" "waste_cost"
    st.altair_chart(
        crosshair_bar_chart(waste_df, "category", "waste_cost", "category", "Waste Cost", "$,.0f")
        )

with col_h:
    st.markdown("**Food Cost Summary**")
    st.metric("Total Food Cost",       f"${fc['total_food_cost']:,.2f}")
    st.metric("Total Waste Cost",      f"${fc['total_waste_cost']:,.2f}")
    st.metric("Waste % of Food Cost",  f"{fc['waste_pct_of_food_cost']}%")