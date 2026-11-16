import os
import sys
import django
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'greenleaf.settings')
django.setup()

from inventory.models import Product, Supplier
from billing.models import Sale, SaleItem

out_dir = Path("outputs")
out_dir.mkdir(exist_ok=True)

sns.set_theme(style="whitegrid", font="sans-serif")
plt.rcParams['font.size'] = 9
plt.rcParams['axes.titlesize'] = 11
plt.rcParams['axes.titleweight'] = 'bold'

# ── Query Data ──────────────────────────────────────────────────────────────
sales_df = pd.DataFrame(list(Sale.objects.all().values('id', 'sale_date', 'sale_time', 'total_amount', 'discount', 'final_amount', 'cashier_id')))
sales_df['sale_date'] = pd.to_datetime(sales_df['sale_date'])
sales_df['final_amount'] = sales_df['final_amount'].astype(float)
sales_df['total_amount'] = sales_df['total_amount'].astype(float)
sales_df['discount'] = sales_df['discount'].astype(float)

items_df = pd.DataFrame(list(SaleItem.objects.all().values('sale_id', 'product_id', 'quantity', 'unit_price', 'subtotal')))
items_df['quantity'] = items_df['quantity'].astype(int)
items_df['unit_price'] = items_df['unit_price'].astype(float)
items_df['subtotal'] = items_df['subtotal'].astype(float)

prods_df = pd.DataFrame(list(Product.objects.all().values('id', 'name', 'category', 'unit_price', 'stock_qty', 'reorder_level', 'expiry_date')))
prods_df['unit_price'] = prods_df['unit_price'].astype(float)
prods_df['stock_qty'] = prods_df['stock_qty'].astype(int)
prods_df['reorder_level'] = prods_df['reorder_level'].astype(int)
prods_df['expiry_date'] = pd.to_datetime(prods_df['expiry_date'])

merged_items = items_df.merge(prods_df[['id', 'name', 'category']], left_on='product_id', right_on='id', how='left')
merged_items = merged_items.merge(sales_df[['id', 'sale_date']], left_on='sale_id', right_on='id', how='left')

total_rev = sales_df['final_amount'].sum()
total_tx = len(sales_df)
avg_basket = sales_df['final_amount'].mean()
low_stock_n = len(prods_df[prods_df['stock_qty'] <= prods_df['reorder_level']])

print(f"EMPIRICAL DATA SUMMARY:")
print(f"Total Sales: {total_tx}")
print(f"Total Revenue: ₹{total_rev:,.2f}")
print(f"Average Basket Value: ₹{avg_basket:.2f}")
print(f"Low Stock Products: {low_stock_n}")
print(f"Date Span: {sales_df['sale_date'].min().strftime('%Y-%m-%d')} to {sales_df['sale_date'].max().strftime('%Y-%m-%d')}")

# ── 1. Daily Sales Trend ───────────────────────────────────────────────────
daily = sales_df.groupby('sale_date').agg(revenue=('final_amount', 'sum'), transactions=('id', 'count')).reset_index()
fig, ax1 = plt.subplots(figsize=(10, 4.5), dpi=300)
ax2 = ax1.twinx()
ax1.fill_between(daily['sale_date'], daily['revenue'], color='#2d6a4f', alpha=0.35, label='Daily Revenue (₹)')
ax1.plot(daily['sale_date'], daily['revenue'], color='#1b4332', lw=1.5)
ax2.plot(daily['sale_date'], daily['transactions'], color='#e76f51', lw=1.2, ls='--', label='Daily Bills')
ax1.set_title('Figure 1: Daily Revenue & Transaction Volume (151-Day Window)')
ax1.set_ylabel('Revenue (₹)', color='#1b4332')
ax2.set_ylabel('Number of Transactions', color='#e76f51')
ax1.tick_params(axis='x', rotation=30)
plt.tight_layout()
plt.savefig(out_dir / '01_daily_sales_trend.png')
plt.close()

# ── 2. Monthly Revenue Performance ──────────────────────────────────────────
sales_df['month'] = sales_df['sale_date'].dt.to_period('M').astype(str)
monthly = sales_df.groupby('month').agg(revenue=('final_amount', 'sum'), bills=('id', 'count')).reset_index()
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=300)
bars = ax.bar(monthly['month'], monthly['revenue'], color='#52b788', edgecolor='#1b4332', width=0.55)
ax.set_title('Figure 2: Monthly Sales Revenue Trajectory')
ax.set_ylabel('Total Revenue (₹)')
ax.set_xlabel('Month')
for bar in bars:
    yval = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2.0, yval + 1500, f"₹{yval:,.0f}", ha='center', va='bottom', fontsize=8, fontweight='bold')
plt.tight_layout()
plt.savefig(out_dir / '02_monthly_sales_performance.png')
plt.close()

# ── 3. Top 10 Best-Selling Products ─────────────────────────────────────────
top10 = merged_items.groupby('name').agg(revenue=('subtotal', 'sum'), qty=('quantity', 'sum')).sort_values('revenue', ascending=True).tail(10)
fig, ax = plt.subplots(figsize=(9, 5), dpi=300)
ax.barh(top10.index, top10['revenue'], color='#2d6a4f', edgecolor='#1b4332', height=0.6)
ax.set_title('Figure 3: Top 10 Revenue-Generating Grocery Items')
ax.set_xlabel('Gross Sales (₹)')
for i, v in enumerate(top10['revenue']):
    ax.text(v + 500, i, f" ₹{v:,.0f} ({top10['qty'].iloc[i]} units)", va='center', fontsize=8)
plt.tight_layout()
plt.savefig(out_dir / '03_top10_best_selling_products.png')
plt.close()

# ── 4. Category-Wise Sales Share ────────────────────────────────────────────
cat_rev = merged_items.groupby('category')['subtotal'].sum().sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
colors_palette = sns.color_palette("mako", len(cat_rev))
wedges, texts, autotexts = ax.pie(cat_rev, labels=cat_rev.index, autopct='%1.1f%%', startangle=140, colors=colors_palette, textprops={'fontsize': 8})
for at in autotexts:
    at.set_color('white')
    at.set_fontsize(7)
ax.set_title('Figure 4: Category Sales Distribution (%)')
plt.tight_layout()
plt.savefig(out_dir / '04_category_sales_distribution.png')
plt.close()

# ── 5. Inventory Stock vs Reorder Level ─────────────────────────────────────
sample_p = prods_df.sort_values('stock_qty').head(15)
fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
x = np.arange(len(sample_p))
width = 0.38
ax.bar(x - width/2, sample_p['stock_qty'], width, label='Available Stock (Units)', color='#52b788')
ax.bar(x + width/2, sample_p['reorder_level'], width, label='Reorder Threshold', color='#e76f51')
ax.set_xticks(x)
ax.set_xticklabels(sample_p['name'], rotation=45, ha='right', fontsize=8)
ax.set_title('Figure 5: Stock Levels vs. Reorder Thresholds (Vulnerable Inventory)')
ax.set_ylabel('Units')
ax.legend()
plt.tight_layout()
plt.savefig(out_dir / '05_inventory_stock_vs_reorder.png')
plt.close()

# ── 6. Expiry Timeline Distribution ─────────────────────────────────────────
today_ts = pd.Timestamp(date.today())
prods_df['days_to_expiry'] = (prods_df['expiry_date'] - today_ts).dt.days
valid_exp = prods_df.dropna(subset=['days_to_expiry'])
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=300)
sns.histplot(valid_exp['days_to_expiry'], bins=20, kde=True, color='#2d6a4f', ax=ax)
ax.axvline(15, color='#e76f51', ls='--', lw=2, label='15-Day Near Expiry Cutoff')
ax.set_title('Figure 6: Distribution of Inventory Shelf Life (Days to Expiry)')
ax.set_xlabel('Days Remaining Until Expiration')
ax.set_ylabel('Product Count')
ax.legend()
plt.tight_layout()
plt.savefig(out_dir / '06_expiry_timeline_distribution.png')
plt.close()

# ── 7. Discount Impact on Basket Size ────────────────────────────────────────
basket_size = items_df.groupby('sale_id')['quantity'].sum().reset_index()
sales_basket = sales_df.merge(basket_size, left_on='id', right_on='sale_id')
fig, ax = plt.subplots(figsize=(7, 4.5), dpi=300)
sns.boxplot(x='discount', y='quantity', data=sales_basket, palette='Greens', ax=ax)
ax.set_title('Figure 7: Impact of Promotional Discount (%) on Transaction Basket Size')
ax.set_xlabel('Promotional Discount Rate (%)')
ax.set_ylabel('Total Items Purchased per Bill')
plt.tight_layout()
plt.savefig(out_dir / '07_discount_vs_basket_size.png')
plt.close()

# ── 8. Executive Dashboard Summary ──────────────────────────────────────────
fig, axs = plt.subplots(2, 2, figsize=(11, 7), dpi=300)
# A: Revenue over time
axs[0, 0].plot(daily['sale_date'], daily['revenue'], color='#2d6a4f', lw=1.2)
axs[0, 0].set_title('A. Daily Gross Sales Trajectory')
axs[0, 0].tick_params(axis='x', rotation=30)
# B: Category revenue
axs[0, 1].barh(cat_rev.index[:6], cat_rev.values[:6], color='#52b788')
axs[0, 1].set_title('B. Top 6 Category Revenue (₹)')
# C: Discount distribution
sns.countplot(x='discount', data=sales_df, palette='viridis', ax=axs[1, 0])
axs[1, 0].set_title('C. Frequency of Applied Promotional Discounts')
# D: Basket value distribution
sns.histplot(sales_df['final_amount'], kde=True, color='#e76f51', ax=axs[1, 1], bins=25)
axs[1, 1].set_title('D. Distribution of Customer Bill Values (₹)')
plt.suptitle('Figure 8: GreenLeaf Grocers Executive Retail Intelligence Dashboard', fontsize=13, fontweight='bold', y=0.99)
plt.tight_layout()
plt.savefig(out_dir / '08_executive_dashboard_summary.png')
plt.close()

print("ALL 8 OUTPUT CHARTS GENERATED SUCCESSFULLY IN outputs/!")
