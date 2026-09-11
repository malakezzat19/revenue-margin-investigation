import numpy as np
import pandas as pd

np.random.seed(42)

categories = ["Electronics", "Apparel", "Home", "Beauty"]
category_margin = {"Electronics": 0.20, "Apparel": 0.45, "Home": 0.35, "Beauty": 0.50}
category_price = {"Electronics": 220, "Apparel": 45, "Home": 80, "Beauty": 35}

channels = ["Organic", "Paid Ads", "Referral", "Email"]
channel_discount = {"Organic": 0.08, "Paid Ads": 0.25, "Referral": 0.10, "Email": 0.15}
channel_return_rate = {"Organic": 0.05, "Paid Ads": 0.12, "Referral": 0.06, "Email": 0.07}

def build_year(year, n_orders, category_weights, channel_weights, shipping_mean):
    dates = pd.to_datetime(f"{year}-01-01") + pd.to_timedelta(
        np.random.randint(0, 365, n_orders), unit="D"
    )
    category = np.random.choice(categories, n_orders, p=category_weights)
    channel = np.random.choice(channels, n_orders, p=channel_weights)
    units_sold = np.random.randint(1, 5, n_orders)

    unit_price = np.array([category_price[c] for c in category]) * np.random.uniform(0.9, 1.1, n_orders)

    # discount depends on channel, plus noise
    base_discount = np.array([channel_discount[ch] for ch in channel])
    discount_pct = np.clip(base_discount + np.random.normal(0, 0.03, n_orders), 0.02, 0.5)

    shipping_cost = np.random.normal(shipping_mean, 2, n_orders).clip(2, None)

    return_prob = np.array([channel_return_rate[ch] for ch in channel])
    return_flag = (np.random.rand(n_orders) < return_prob).astype(int)

    df = pd.DataFrame({
        "order_id": np.arange(1, n_orders + 1) + (0 if year == 2024 else 100000),
        "order_date": dates,
        "product_category": category,
        "units_sold": units_sold,
        "unit_price": np.round(unit_price, 2),
        "discount_pct": discount_pct,
        "shipping_cost": np.round(shipping_cost, 2),
        "return_flag": return_flag,
        "acquisition_channel": channel,
    })
    return df

# Year 1 (2024): baseline
df_2024 = build_year(
    2024, n_orders=9000,
    category_weights=[0.30, 0.30, 0.25, 0.15],
    channel_weights=[0.45, 0.20, 0.20, 0.15],
    shipping_mean=8.0,
)

# Year 2 (2025): more orders (revenue up), but margin-eroding shifts:
# - more Electronics (low margin), more Paid Ads (high discount + high return), higher shipping
df_2025 = build_year(
    2025, n_orders=9900,
    category_weights=[0.40, 0.25, 0.22, 0.13],
    channel_weights=[0.30, 0.38, 0.18, 0.14],
    shipping_mean=11.0,
)

df = pd.concat([df_2024, df_2025], ignore_index=True)


# Now inject the "known data issues" from the brief
-

# ~4000 duplicate order_id rows from a March 2025 system migration
march_2025_mask = (df["order_date"].dt.year == 2025) & (df["order_date"].dt.month == 3)
march_rows = df[march_2025_mask]
dup_rows = march_rows.sample(n=4000, random_state=1, replace=True)
df = pd.concat([df, dup_rows], ignore_index=True)

# shipping_cost missing for ~15% of rows
missing_idx = df.sample(frac=0.15, random_state=2).index
df.loc[missing_idx, "shipping_cost"] = np.nan

#  discount_pct inconsistent: some rows stored as whole percent (20) instead of 0.20
whole_pct_idx = df.sample(frac=0.35, random_state=3).index
df.loc[whole_pct_idx, "discount_pct"] = (df.loc[whole_pct_idx, "discount_pct"] * 100).round(1)

#  return_flag sometimes null instead of 0/1
null_return_idx = df.sample(frac=0.10, random_state=4).index
df.loc[null_return_idx, "return_flag"] = np.nan

df = df.sample(frac=1, random_state=5).reset_index(drop=True)  # shuffle rows
df.to_csv("messy_sales_data.csv", index=False)

print("Dataset created:", df.shape)
print(df.head())
