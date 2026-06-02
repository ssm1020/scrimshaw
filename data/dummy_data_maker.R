library(tidyverse)
library(lubridate)

set.seed(42)

# ── CONFIG ──────────────────────────────────────────────────────────────────
START_DATE <- as.Date("2024-01-01")
END_DATE   <- as.Date("2024-03-31")
dates      <- seq(START_DATE, END_DATE, by = "day")
n_days     <- length(dates)

# ── LOOKUP TABLES ────────────────────────────────────────────────────────────

menu_items <- tribble(
  ~item_id, ~item_name,               ~category,    ~price, ~unit_cost,
  "M001",   "Cheeseburger",           "Entree",      14.00,   4.20,
  "M002",   "Veggie Burger",          "Entree",      13.00,   3.50,
  "M003",   "Grilled Salmon",         "Entree",      22.00,   8.00,
  "M004",   "Caesar Salad",           "Starter",      9.00,   2.10,
  "M005",   "French Onion Soup",      "Starter",      8.00,   1.80,
  "M006",   "Truffle Fries",          "Side",         7.00,   1.50,
  "M007",   "House Salad",            "Side",         6.00,   1.20,
  "M008",   "Craft Beer",             "Beverage",     7.00,   1.80,
  "M009",   "House Wine (glass)",     "Beverage",     9.00,   2.50,
  "M010",   "Soft Drink",             "Beverage",     3.50,   0.40,
  "M011",   "NY Cheesecake",          "Dessert",      8.00,   2.00,
  "M012",   "Chocolate Lava Cake",    "Dessert",      9.00,   2.20,
  "M013",   "Chicken Tacos",          "Entree",      13.00,   3.80,
  "M014",   "Fish & Chips",           "Entree",      16.00,   5.50,
  "M015",   "Kids Mac & Cheese",      "Kids",         7.00,   1.60
)

employees <- tribble(
  ~emp_id, ~name,              ~role,       ~hourly_rate,
  "E01",   "Marcus Webb",      "Manager",       22.00,
  "E02",   "Priya Nair",       "Server",        12.00,
  "E03",   "Jake Torres",      "Server",        12.00,
  "E04",   "Lily Chen",        "Server",        12.00,
  "E05",   "Darnell King",     "Server",        12.00,
  "E06",   "Rosa Gutierrez",   "Host",          11.00,
  "E07",   "Ahmed Hassan",     "Cook",          16.00,
  "E08",   "Tina Park",        "Cook",          16.00,
  "E09",   "Brian O'Neal",     "Cook",          15.00,
  "E10",   "Carmen Vega",      "Bartender",     13.00,
  "E11",   "Scott Miles",      "Busser",         9.50,
  "E12",   "Nia Johnson",      "Server",        12.00
)

# ── 1. POS TRANSACTIONS ──────────────────────────────────────────────────────
# One row per item ordered per transaction

server_ids <- employees %>% filter(role == "Server") %>% pull(emp_id)

pos_raw <- map_dfr(dates, function(d) {
  is_weekend  <- wday(d) %in% c(1, 7)
  is_friday   <- wday(d) == 6
  n_covers    <- if (is_weekend) sample(110:160, 1) else if (is_friday) sample(90:130, 1) else sample(50:100, 1)
  n_orders    <- round(n_covers / sample(c(1.5, 2, 2.5), 1))
  
  map_dfr(seq_len(n_orders), function(o) {
    order_id    <- paste0("ORD-", format(d, "%Y%m%d"), "-", str_pad(o, 4, pad = "0"))
    order_time  <- as.POSIXct(d) + hours(sample(11:21, 1)) + minutes(sample(0:59, 1))
    server      <- sample(server_ids, 1)
    table_num   <- sample(1:20, 1)
    n_items     <- sample(1:5, 1, prob = c(0.1, 0.25, 0.35, 0.2, 0.1))
    items       <- sample(menu_items$item_id, n_items, replace = TRUE,
                          prob = c(0.12,0.08,0.08,0.09,0.06,0.08,0.06,0.1,0.08,0.07,0.05,0.04,0.06,0.05,0.03))
    
    tibble(
      date         = d,
      order_id     = order_id,
      order_time   = order_time,
      server_id    = server,
      table_num    = table_num,
      item_id      = items,
      quantity     = sample(1:3, n_items, replace = TRUE, prob = c(0.7, 0.2, 0.1)),
      payment_type = sample(c("Card","Cash","DoorDash","UberEats"), 1,
                            prob = c(0.65, 0.10, 0.15, 0.10)),
      discount_pct = sample(c(0, 0, 0, 0.10, 0.15), 1)
    )
  })
})

pos_transactions <- pos_raw %>%
  left_join(menu_items %>% select(item_id, item_name, category, price), by = "item_id") %>%
  mutate(
    gross_revenue = price * quantity,
    discount_amt  = round(gross_revenue * discount_pct, 2),
    net_revenue   = round(gross_revenue - discount_amt, 2)
  ) %>%
  select(date, order_id, order_time, server_id, table_num,
         item_id, item_name, category, quantity,
         price, discount_pct, discount_amt, net_revenue, payment_type)

# ── 2. LABOR / SCHEDULING ────────────────────────────────────────────────────

labor <- map_dfr(dates, function(d) {
  is_weekend <- wday(d) %in% c(1, 7)
  scheduled_servers <- if (is_weekend) sample(server_ids, 5) else sample(server_ids, 3)
  cook_ids  <- employees %>% filter(role == "Cook") %>% pull(emp_id)
  other_ids <- employees %>% filter(role %in% c("Manager","Host","Bartender","Busser")) %>% pull(emp_id)
  scheduled <- c(scheduled_servers, cook_ids, other_ids)
  
  map_dfr(scheduled, function(eid) {
    role <- employees$role[employees$emp_id == eid]
    rate <- employees$hourly_rate[employees$emp_id == eid]
    
    # Pull server hours out of case_when to avoid type issues
    server_hrs <- if (is_weekend) runif(1, 6, 8) else runif(1, 4, 6)
    
    shift_hrs <- case_when(
      role == "Manager"   ~ runif(1, 8, 10),
      role == "Cook"      ~ runif(1, 7, 9),
      role == "Server"    ~ server_hrs,
      role == "Bartender" ~ runif(1, 6, 8),
      TRUE                ~ runif(1, 4, 6)
    )
    
    clock_in  <- as.POSIXct(d) + sample(10:12, 1) * 3600
    clock_out <- clock_in + shift_hrs * 3600
    actual_hrs <- as.numeric(difftime(clock_out, clock_in, units = "hours"))
    sched_hrs  <- round(shift_hrs + runif(1, -0.5, 0.5), 2)
    
    tibble(
      date          = d,
      emp_id        = eid,
      emp_name      = employees$name[employees$emp_id == eid],
      role          = role,
      clock_in      = clock_in,
      clock_out     = clock_out,
      scheduled_hrs = round(sched_hrs, 2),
      actual_hrs    = round(actual_hrs, 2),
      hourly_rate   = rate,
      labor_cost    = round(actual_hrs * rate, 2)
    )
  })
})

# ── 3. RESERVATIONS ─────────────────────────────────────────────────────────

reservations <- map_dfr(dates, function(d) {
  is_weekend <- wday(d) %in% c(1, 7)
  n_res      <- if (is_weekend) sample(20:35, 1) else sample(8:18, 1)
  
  map_dfr(seq_len(n_res), function(r) {
    party_size  <- sample(1:8, 1, prob = c(0.1, 0.25, 0.25, 0.2, 0.1, 0.05, 0.03, 0.02))
    res_time    <- as.POSIXct(d) + hours(sample(17:20, 1)) + minutes(sample(c(0,15,30,45), 1))
    status      <- sample(c("Seated","No-show","Cancelled"),1, prob = c(0.80, 0.10, 0.10))
    covers      <- if (status == "Seated") party_size else 0
    
    tibble(
      date         = d,
      res_id       = paste0("RES-", format(d, "%Y%m%d"), "-", str_pad(r, 3, pad="0")),
      res_time     = res_time,
      party_size   = party_size,
      covers       = covers,
      status       = status,
      source       = sample(c("OpenTable","Phone","Walk-in"), 1, prob = c(0.50, 0.30, 0.20))
    )
  })
})

# ── 4. INVENTORY / FOOD COST ─────────────────────────────────────────────────
# Daily usage derived from POS quantities sold

daily_item_qty <- pos_transactions %>%
  group_by(date, item_id) %>%
  summarise(qty_sold = sum(quantity), .groups = "drop")

inventory <- daily_item_qty %>%
  left_join(menu_items %>% select(item_id, item_name, category, unit_cost), by = "item_id") %>%
  mutate(
    waste_pct      = runif(n(), 0.02, 0.08),
    qty_used       = round(qty_sold * (1 + waste_pct)),
    total_food_cost = round(qty_used * unit_cost, 2),
    waste_cost     = round(qty_sold * waste_pct * unit_cost, 2)
  ) %>%
  select(date, item_id, item_name, category, qty_sold, qty_used,
         waste_pct, unit_cost, total_food_cost, waste_cost)

# ── 5. ONLINE ORDERS ─────────────────────────────────────────────────────────

online_orders <- pos_transactions %>%
  filter(payment_type %in% c("DoorDash","UberEats")) %>%
  group_by(date, order_id, payment_type) %>%
  summarise(
    gross_order_value = sum(net_revenue),
    .groups = "drop"
  ) %>%
  mutate(
    platform_fee_pct = if_else(payment_type == "DoorDash", 0.30, 0.27),
    platform_fee     = round(gross_order_value * platform_fee_pct, 2),
    net_to_restaurant = round(gross_order_value - platform_fee, 2),
    delivery_mins    = sample(25:55, n(), replace = TRUE),
    customer_rating  = round(runif(n(), 3.5, 5.0), 1)
  ) %>%
  select(date, order_id, platform = payment_type, gross_order_value,
         platform_fee_pct, platform_fee, net_to_restaurant,
         delivery_mins, customer_rating)

# ── EXPORT ───────────────────────────────────────────────────────────────────

write_csv(pos_transactions, "pos_transactions.csv")
write_csv(labor,            "labor_scheduling.csv")
write_csv(reservations,     "reservations.csv")
write_csv(inventory,        "inventory_food_cost.csv")
write_csv(online_orders,    "online_orders.csv")
write_csv(menu_items,       "menu_items.csv")       # handy lookup
write_csv(employees,        "employees.csv")         # handy lookup

cat("✅ All datasets written:\n")
cat("   pos_transactions.csv     —", nrow(pos_transactions), "rows\n")
cat("   labor_scheduling.csv     —", nrow(labor), "rows\n")
cat("   reservations.csv         —", nrow(reservations), "rows\n")
cat("   inventory_food_cost.csv  —", nrow(inventory), "rows\n")
cat("   online_orders.csv        —", nrow(online_orders), "rows\n")
cat("   menu_items.csv           — lookup table\n")
cat("   employees.csv            — lookup table\n")
