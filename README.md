# The Dataset That Told Two Stories

A full data analysis case study: leadership says revenue is up 20% year-over-year, finance says profit margin quietly dropped 6 points in the same period. This project cleans the data and finds out why both are true — and how they're connected.

## The scenario

A messy e-commerce sales dataset with known issues:
- ~4,000 duplicate `order_id` rows from a system migration
- `shipping_cost` missing for ~15% of rows
- `discount_pct` stored inconsistently (0.20 vs 20)
- `return_flag` sometimes null instead of 0/1

## What this project does

1. **Generates** a realistic messy two-year dataset with these exact issues baked in (`generate_data.py`)
2. **Cleans** the data step by step: removes duplicates, standardizes discount format, imputes missing shipping cost by category, handles null return flags
3. **Analyzes** revenue and profit margin year-over-year
4. **Identifies the real drivers**: order volume growth, a shift toward a higher-discount acquisition channel (Paid Ads), a shift toward a lower-margin product category (Electronics), and rising shipping costs
5. **Gives a specific recommendation**: rebalance acquisition spend away from over-reliance on Paid Ads, and revisit Electronics pricing/costs

## Key findings

- Revenue grew **20%**, profit margin dropped **6 points** — both stories are true
- Paid Ads share of orders grew from 20% to 38%, with a 25% average discount (3x the organic rate)
- Electronics share of orders grew from 30% to 40% — the lowest-margin category
- Average shipping cost per order rose from $8 to $11

## Files in this repo

- `generate_data.py` — builds the synthetic messy dataset
- `analysis.py` — the full cleaning and analysis pipeline
- `messy_sales_data.csv` — the raw dataset with all known issues
- `clean_sales_data.csv` — the cleaned dataset used for analysis
- `revenue_vs_margin.png` — chart showing both trends side by side

## Tech used

- Python, Pandas, NumPy, Matplotlib

## Biggest assumption / limitation

The dataset has no actual product cost (COGS) data, so profit margins were approximated using industry-typical margins per category. The exact numbers would shift with real cost data, but the direction of the story — margin eroding through channel and product mix shifts, not random noise — should hold either way.
