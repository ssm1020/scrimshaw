import pandas as pd
from pathlib import Path

# ── CONFIG ───────────────────────────────────────────────────────────────────
DATA_DIR = Path("C:\\Users\\Sam\\Documents\\GitHub\\scrimshaw\\data")  # put all your CSVs in a /data folder

# ── LOADERS ──────────────────────────────────────────────────────────────────
def load_all():
    pos       = pd.read_csv(DATA_DIR / "pos_transactions.csv",    parse_dates=["date", "order_time"])
    labor     = pd.read_csv(DATA_DIR / "labor_scheduling.csv",    parse_dates=["date", "clock_in", "clock_out"])
    res       = pd.read_csv(DATA_DIR / "reservations.csv",        parse_dates=["date", "res_time"])
    inventory = pd.read_csv(DATA_DIR / "inventory_food_cost.csv", parse_dates=["date"])
    online    = pd.read_csv(DATA_DIR / "online_orders.csv",       parse_dates=["date"])
    employees = pd.read_csv(DATA_DIR / "employees.csv")
    menu      = pd.read_csv(DATA_DIR / "menu_items.csv")
    return pos, labor, res, inventory, online, employees, menu


# ── DAILY SUMMARY ─────────────────────────────────────────────────────────────
# One row per day — the backbone of your main dashboard view
def daily_summary(pos, labor):
    daily_rev = (
        pos.groupby("date")
        .agg(
            revenue      = ("net_revenue",  "sum"),
            orders       = ("order_id",     "nunique"),
            items_sold   = ("quantity",     "sum"),
        )
        .reset_index()
    )

    daily_labor = (
        labor.groupby("date")
        .agg(labor_cost = ("labor_cost", "sum"))
        .reset_index()
    )

    summary = daily_rev.merge(daily_labor, on="date", how="left")
    summary["labor_pct"]     = (summary["labor_cost"] / summary["revenue"]).round(1)
    summary["avg_order_val"] = (summary["revenue"] / summary["orders"]).round(2)
    summary["day_of_week"]   = summary["date"].dt.day_name()

    return summary


# ── REVENUE VIEWS ─────────────────────────────────────────────────────────────
def revenue_by_category(pos):
    return (
        pos.groupby("category")
        .agg(revenue=("net_revenue", "sum"), qty=("quantity", "sum"))
        .sort_values("revenue", ascending=False)
        .reset_index()
    )

def revenue_by_dow(pos):
    pos = pos.copy()
    pos["day_of_week"] = pos["date"].dt.day_name()
    order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    result = (
        pos.groupby("day_of_week")
        .agg(revenue=("net_revenue", "sum"), orders=("order_id", "nunique"))
        .reindex(order)
        .reset_index()
    )
    result["avg_revenue"] = (result["revenue"] / result["orders"]).round(2)
    return result

def top_items(pos, n=10):
    return (
        pos.groupby(["item_id", "item_name", "category"])
        .agg(qty_sold=("quantity", "sum"), revenue=("net_revenue", "sum"))
        .sort_values("revenue", ascending=False)
        .head(n)
        .reset_index()
    )


# ── LABOR VIEWS ───────────────────────────────────────────────────────────────
def labor_by_role(labor):
    return (
        labor.groupby("role")
        .agg(
            total_hours = ("actual_hrs",  "sum"),
            total_cost  = ("labor_cost",  "sum"),
            shifts      = ("emp_id",      "count"),
        )
        .sort_values("total_cost", ascending=False)
        .reset_index()
    )

def overtime_flags(labor, threshold=8.0):
    """Employees with shifts over threshold hours — useful flag for owners."""
    flagged = labor[labor["actual_hrs"] > threshold].copy()
    flagged["overtime_hrs"] = (flagged["actual_hrs"] - threshold).round(2)
    return flagged[["date","emp_name","role","actual_hrs","overtime_hrs","labor_cost"]]


# ── RESERVATION VIEWS ─────────────────────────────────────────────────────────
def reservation_summary(res):
    total     = len(res)
    no_shows  = (res["status"] == "No-show").sum()
    cancelled = (res["status"] == "Cancelled").sum()
    seated    = (res["status"] == "Seated").sum()
    return {
        "total_reservations": total,
        "seated":             int(seated),
        "no_shows":           int(no_shows),
        "cancellations":      int(cancelled),
        "no_show_rate":       round(no_shows / total * 100, 1),
    }

def covers_by_source(res):
    return (
        res[res["status"] == "Seated"]
        .groupby("source")
        .agg(covers=("covers", "sum"), reservations=("res_id", "count"))
        .reset_index()
    )


# ── ONLINE ORDER VIEWS ────────────────────────────────────────────────────────
def online_summary(online):
    return (
        online.groupby("platform")
        .agg(
            orders            = ("order_id",          "count"),
            gross_revenue     = ("gross_order_value",  "sum"),
            platform_fees     = ("platform_fee",       "sum"),
            net_revenue       = ("net_to_restaurant",  "sum"),
            avg_rating        = ("customer_rating",    "mean"),
            avg_delivery_mins = ("delivery_mins",      "mean"),
        )
        .round(2)
        .reset_index()
    )


# ── FOOD COST VIEWS ───────────────────────────────────────────────────────────
def food_cost_summary(inventory):
    total_food_cost = inventory["total_food_cost"].sum()
    total_waste     = inventory["waste_cost"].sum()
    return {
        "total_food_cost": round(total_food_cost, 2),
        "total_waste_cost": round(total_waste, 2),
        "waste_pct_of_food_cost": round(total_waste / total_food_cost * 100, 1),
    }

def waste_by_category(inventory):
    return (
        inventory.groupby("category")
        .agg(waste_cost=("waste_cost", "sum"), food_cost=("total_food_cost", "sum"))
        .sort_values("waste_cost", ascending=False)
        .reset_index()
    )


# ── QUICK TEST ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    pos, labor, res, inventory, online, employees, menu = load_all()

    summary = daily_summary(pos, labor)
    print("=== Daily Summary (first 5 rows) ===")
    print(summary.head())
    print(f"\nAvg daily revenue:    ${summary['revenue'].mean():,.2f}")
    print(f"Avg labor %:          {summary['labor_pct'].mean():.1f}%")

    print("\n=== Top 5 Items by Revenue ===")
    print(top_items(pos, n=5).to_string(index=False))

    print("\n=== Online Order Summary ===")
    print(online_summary(online).to_string(index=False))

    print("\n=== Reservation Summary ===")
    print(reservation_summary(res))

    print("\n=== Food Cost Summary ===")
    print(food_cost_summary(inventory))