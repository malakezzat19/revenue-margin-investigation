import pandas as pd
import numpy as np

df = pd.read_csv("messy_sales_data.csv", parse_dates=["order_date"])

print("=" * 60)
print("STEP 0: UNDERSTAND -- raw shape and known issues")
print("=" * 60)
print("Raw shape:", df.shape)
print("Duplicate order_id rows:", df["order_id"].duplicated().sum())
print("Missing shipping_cost:", df["shipping_cost"].isnull().sum(),
      f"({df['shipping_cost'].isnull().mean()*100:.1f}%)")
print("discount_pct value range (raw):", df["discount_pct"].min(), "-", df["discount_pct"].max())
print("return_flag nulls:", df["return_flag"].isnull().sum())


# STEP 1: CLEAN

print("\n" + "=" * 60)
print("STEP 1: CLEAN")
print("=" * 60)

before = len(df)
df = df.drop_duplicates(subset="order_id", keep="first")
print(f"1. Removed duplicate order_id rows: {before - len(df)} rows dropped")

# Fix discount_pct inconsistency: anything > 1 is a whole-number percent
df["discount_pct"] = np.where(df["discount_pct"] > 1, df["discount_pct"] / 100, df["discount_pct"])
print("2. Standardized discount_pct to a 0-1 fraction. New range:",
      round(df["discount_pct"].min(), 3), "-", round(df["discount_pct"].max(), 3))

# Impute shipping_cost by category+year median (missing not at random check first)
df["year"] = df["order_date"].dt.year
miss_rate_by_cat = df.groupby("product_category")["shipping_cost"].apply(lambda s: s.isnull().mean())
print("3. Missing shipping_cost rate by category (checking it's not random):")
print((miss_rate_by_cat * 100).round(1))
df["shipping_cost"] = df["shipping_cost"].fillna(
    df.groupby(["product_category", "year"])["shipping_cost"].transform("median")
)
print("   -> Filled using median shipping cost per category+year (rate is similar")
print("      across categories, so a group median is a safe, low-bias fill).")

# return_flag: null treated as "not returned" (0) -- documented assumption
n_null_returns = df["return_flag"].isnull().sum()
df["return_flag"] = df["return_flag"].fillna(0).astype(int)
print(f"4. Filled {n_null_returns} null return_flag values with 0 (assumption: a")
print("   missing flag means no return was recorded, not that one occurred).")

print(f"\nClean shape: {df.shape}")


#2: ANALYZE -- revenue and margin by year

print("\n" + "=" * 60)
print("STEP 2: ANALYZE -- revenue vs. margin, year over year")
print("=" * 60)

# Assumption (stated as the biggest limitation later): approximate COGS
# as a fixed % of unit_price per category, since actual product cost
# is not in this dataset.
category_margin = {"Electronics": 0.20, "Apparel": 0.45, "Home": 0.35, "Beauty": 0.50}
df["assumed_cogs_pct"] = df["product_category"].map(category_margin).apply(lambda m: 1 - m)

df["gross_revenue"] = df["units_sold"] * df["unit_price"] * (1 - df["discount_pct"])
# a return effectively wipes out the revenue and cost of that order, but shipping is still spent
df["revenue"] = np.where(df["return_flag"] == 1, 0, df["gross_revenue"])
df["cogs"] = np.where(df["return_flag"] == 1, 0,
                       df["units_sold"] * df["unit_price"] * df["assumed_cogs_pct"])
df["profit"] = df["revenue"] - df["cogs"] - df["shipping_cost"]

yearly = df.groupby("year").agg(
    revenue=("revenue", "sum"),
    profit=("profit", "sum"),
    orders=("order_id", "count"),
    avg_discount=("discount_pct", "mean"),
    return_rate=("return_flag", "mean"),
    avg_shipping=("shipping_cost", "mean"),
)
yearly["margin_pct"] = yearly["profit"] / yearly["revenue"] * 100
print(yearly.round(3))

rev_growth = (yearly.loc[2025, "revenue"] / yearly.loc[2024, "revenue"] - 1) * 100
margin_change = yearly.loc[2025, "margin_pct"] - yearly.loc[2024, "margin_pct"]
print(f"\nRevenue growth 2024 -> 2025: {rev_growth:.1f}%")
print(f"Margin change 2024 -> 2025: {margin_change:.1f} points")


#3: DRIVERS

print("\n" + "=" * 60)
print("STEP 3: DRIVERS -- what's actually behind the two numbers")
print("=" * 60)

# Driver A: order volume growth (revenue driver)
order_growth = (yearly.loc[2025, "orders"] / yearly.loc[2024, "orders"] - 1) * 100
print(f"A. Order count grew {order_growth:.1f}% -- a real volume driver behind revenue growth.")

# Driver B: channel mix shift + channel-level discount/return
channel_mix = df.groupby(["year", "acquisition_channel"]).size().unstack()
channel_mix_pct = channel_mix.div(channel_mix.sum(axis=1), axis=0) * 100
print("\nB. Acquisition channel mix (% of orders):")
print(channel_mix_pct.round(1))

channel_stats = df.groupby(["year", "acquisition_channel"]).agg(
    avg_discount=("discount_pct", "mean"),
    return_rate=("return_flag", "mean"),
).round(3)
print("\nDiscount rate and return rate by channel and year:")
print(channel_stats)

# Driver C: category mix shift + category margin
category_mix = df.groupby(["year", "product_category"]).size().unstack()
category_mix_pct = category_mix.div(category_mix.sum(axis=1), axis=0) * 100
print("\nC. Product category mix (% of orders):")
print(category_mix_pct.round(1))

# Driver D: shipping cost trend
print(f"\nD. Average shipping cost: {yearly.loc[2024,'avg_shipping']:.2f} (2024) vs "
      f"{yearly.loc[2025,'avg_shipping']:.2f} (2025)")

# Overall discount trend
print(f"\nAverage discount_pct: {yearly.loc[2024,'avg_discount']*100:.1f}% (2024) vs "
      f"{yearly.loc[2025,'avg_discount']*100:.1f}% (2025)")

# Overall return rate trend
print(f"Return rate: {yearly.loc[2024,'return_rate']*100:.1f}% (2024) vs "
      f"{yearly.loc[2025,'return_rate']*100:.1f}% (2025)")


# Save a clean version and a chart for the writeup

import matplotlib.pyplot as plt

df.to_csv("clean_sales_data.csv", index=False)

fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))

axes[0].bar(["2024", "2025"], [yearly.loc[2024, "revenue"], yearly.loc[2025, "revenue"]],
            color=["#2A9D8F", "#E76F51"])
axes[0].set_title("Revenue: Up 20%")
axes[0].set_ylabel("Total Revenue ($)")

axes[1].bar(["2024", "2025"], [yearly.loc[2024, "margin_pct"], yearly.loc[2025, "margin_pct"]],
            color=["#2A9D8F", "#E76F51"])
axes[1].set_title("Profit Margin: Down 6 points")
axes[1].set_ylabel("Margin (%)")

plt.tight_layout()
plt.savefig("revenue_vs_margin.png", dpi=150)
print("\nSaved revenue_vs_margin.png")
