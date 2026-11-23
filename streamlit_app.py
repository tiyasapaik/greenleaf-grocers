import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime

st.set_page_config(
    page_title="GreenLeaf Grocers — Retail Analytics Dashboard",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1b4332;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #52b788;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
        font-weight: 600;
    }
    .metric-box {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.2rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        text-align: center;
    }
    .metric-value {
        font-size: 1.9rem;
        font-weight: 800;
        color: #2d6a4f;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #64748b;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ── Database Connection ──────────────────────────────────────────────────────
@st.cache_data
def load_data():
    conn = sqlite3.connect('db.sqlite3')
    
    prods = pd.read_sql("""
        SELECT p.id, p.name, p.category, p.unit_price, p.stock_qty, p.reorder_level, 
               p.expiry_date, p.barcode, s.name as supplier_name
        FROM inventory_product p
        LEFT JOIN inventory_supplier s ON p.supplier_id = s.id
    """, conn)
    
    sales = pd.read_sql("""
        SELECT s.id, s.sale_date, s.sale_time, s.total_amount, s.discount, s.final_amount,
               u.username as cashier
        FROM billing_sale s
        LEFT JOIN auth_user u ON s.cashier_id = u.id
    """, conn)
    
    items = pd.read_sql("""
        SELECT si.id, si.sale_id, si.product_id, si.quantity, si.unit_price, si.subtotal,
               p.name as product_name, p.category
        FROM billing_saleitem si
        JOIN inventory_product p ON si.product_id = p.id
    """, conn)
    
    conn.close()
    
    sales['sale_date'] = pd.to_datetime(sales['sale_date'])
    prods['expiry_date'] = pd.to_datetime(prods['expiry_date'])
    today = pd.Timestamp(date.today())
    prods['days_to_expiry'] = (prods['expiry_date'] - today).dt.days
    prods['is_low_stock'] = prods['stock_qty'] <= prods['reorder_level']
    prods['is_near_expiry'] = prods['days_to_expiry'].between(0, 15)
    prods['is_expired'] = prods['days_to_expiry'] < 0
    
    return prods, sales, items

prods, sales, items = load_data()

# ── Sidebar Filters ──────────────────────────────────────────────────────────
st.sidebar.markdown("### 🌿 GreenLeaf Grocers")
st.sidebar.markdown("**Store Operations & Analytics**")
st.sidebar.markdown("---")

min_date = sales['sale_date'].min().date()
max_date = sales['sale_date'].max().date()

date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)

if len(date_range) == 2:
    start_d, end_d = date_range
    filtered_sales = sales[(sales['sale_date'].dt.date >= start_d) & (sales['sale_date'].dt.date <= end_d)]
    filtered_items = items[items['sale_id'].isin(filtered_sales['id'])]
else:
    filtered_sales = sales
    filtered_items = items

st.sidebar.markdown("---")
st.sidebar.markdown("**Internship Submission:**")
st.sidebar.markdown("- **Developer:** Tiyasa Paik")
st.sidebar.markdown("- **Institution:** Unified Mentor Private Limited")
st.sidebar.markdown("- **Stack:** Python, Django, SQLite/MySQL, Pandas, Plotly, Streamlit")

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown('<div class="main-header">🌿 GreenLeaf Grocers — Management & Analytics System</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Centralized Retail Inventory, Point-of-Sale (POS) Automation & Executive Business Intelligence</div>', unsafe_allow_html=True)

# ── Top KPIs ─────────────────────────────────────────────────────────────────
total_rev = filtered_sales['final_amount'].sum()
total_tx = len(filtered_sales)
avg_basket = total_rev / total_tx if total_tx > 0 else 0
low_stock_count = prods['is_low_stock'].sum()
near_expiry_count = prods['is_near_expiry'].sum()

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.markdown(f'<div class="metric-box"><div class="metric-value">₹{total_rev:,.0f}</div><div class="metric-label">Total Revenue</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-box"><div class="metric-value">{total_tx}</div><div class="metric-label">Completed Transactions</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="metric-box"><div class="metric-value">₹{avg_basket:.2f}</div><div class="metric-label">Average Basket Size</div></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="metric-box"><div class="metric-value" style="color:#e76f51;">{low_stock_count}</div><div class="metric-label">Low Stock Alerts</div></div>', unsafe_allow_html=True)
with col5:
    st.markdown(f'<div class="metric-box"><div class="metric-value" style="color:#d90429;">{near_expiry_count}</div><div class="metric-label">Near Expiry (&le;15 Days)</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Sales Analytics", 
    "🏆 Top Products", 
    "📦 Inventory & Stock Alerts", 
    "📅 Expiry Surveillance", 
    "🧾 POS Billing Records"
])

# ── Tab 1: Sales Analytics ───────────────────────────────────────────────────
with tab1:
    c1, c2 = st.columns([7, 5])
    
    with c1:
        daily = filtered_sales.groupby(filtered_sales['sale_date'].dt.date)['final_amount'].sum().reset_index()
        fig_daily = px.area(
            daily, x='sale_date', y='final_amount',
            title="Daily Sales Revenue Trajectory (₹)",
            labels={'sale_date': 'Date', 'final_amount': 'Gross Sales (₹)'},
            color_discrete_sequence=['#2d6a4f']
        )
        fig_daily.update_layout(height=380, plot_bgcolor='white')
        st.plotly_chart(fig_daily, use_container_width=True)
        
    with c2:
        filtered_sales['month'] = filtered_sales['sale_date'].dt.to_period('M').astype(str)
        monthly = filtered_sales.groupby('month')['final_amount'].sum().reset_index()
        fig_monthly = px.bar(
            monthly, x='month', y='final_amount',
            title="Monthly Sales Progression (₹)",
            labels={'month': 'Month', 'final_amount': 'Revenue (₹)'},
            color_discrete_sequence=['#52b788'],
            text_auto='.2s'
        )
        fig_monthly.update_layout(height=380, plot_bgcolor='white')
        st.plotly_chart(fig_monthly, use_container_width=True)

    c3, c4 = st.columns([6, 6])
    with c3:
        cat_sales = filtered_items.groupby('category')['subtotal'].sum().reset_index().sort_values('subtotal', ascending=False)
        fig_cat = px.pie(
            cat_sales, names='category', values='subtotal',
            title="Category Revenue Distribution (%)",
            color_discrete_sequence=px.colors.sequential.Greens_r,
            hole=0.4
        )
        fig_cat.update_layout(height=380)
        st.plotly_chart(fig_cat, use_container_width=True)
        
    with c4:
        disc_sales = filtered_sales.groupby('discount').agg(
            revenue=('final_amount', 'sum'),
            bills=('id', 'count')
        ).reset_index()
        fig_disc = px.bar(
            disc_sales, x='discount', y='bills',
            title="Promotional Discount Frequency (Number of Bills)",
            labels={'discount': 'Discount Rate (%)', 'bills': 'Transactions'},
            color_discrete_sequence=['#f4a261'],
            text_auto=True
        )
        fig_disc.update_layout(height=380, plot_bgcolor='white')
        st.plotly_chart(fig_disc, use_container_width=True)

# ── Tab 2: Top Products ──────────────────────────────────────────────────────
with tab2:
    view_metric = st.radio("Rank Products By:", ["Gross Revenue (₹)", "Total Units Sold"], horizontal=True)
    metric_col = 'total_rev' if view_metric == "Gross Revenue (₹)" else 'total_qty'
    
    top_p = filtered_items.groupby(['product_name', 'category']).agg(
        total_rev=('subtotal', 'sum'),
        total_qty=('quantity', 'sum')
    ).reset_index().sort_values(metric_col, ascending=True).tail(12)
    
    fig_top = px.bar(
        top_p, x=metric_col, y='product_name', color='category',
        orientation='h',
        title=f"Top Best-Selling Products by {view_metric}",
        labels={'product_name': 'Product', metric_col: view_metric},
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig_top.update_layout(height=480, plot_bgcolor='white')
    st.plotly_chart(fig_top, use_container_width=True)
    
    st.markdown("#### 📋 Top Products Data Table")
    st.dataframe(
        top_p.sort_values(metric_col, ascending=False).rename(columns={
            'product_name': 'Product Name',
            'category': 'Category',
            'total_rev': 'Gross Revenue (₹)',
            'total_qty': 'Units Sold'
        }),
        use_container_width=True
    )

# ── Tab 3: Inventory & Stock Alerts ──────────────────────────────────────────
with tab3:
    st.markdown("### ⚠️ Low-Stock Reorder Watchlist")
    st.markdown("Products where physical available stock is less than or equal to the designated safety reorder threshold.")
    
    low_p = prods[prods['is_low_stock']][['name', 'category', 'unit_price', 'stock_qty', 'reorder_level', 'supplier_name']]
    if len(low_p) > 0:
        st.dataframe(low_p.rename(columns={
            'name': 'Product Name', 'category': 'Category', 'unit_price': 'Unit Price (₹)',
            'stock_qty': 'Current Stock', 'reorder_level': 'Reorder Level', 'supplier_name': 'Assigned Supplier'
        }), use_container_width=True)
    else:
        st.success("All inventory is currently above reorder levels!")
        
    st.markdown("---")
    st.markdown("### 📦 Complete Product Catalog")
    cat_filter = st.selectbox("Filter by Category", ["All Categories"] + sorted(prods['category'].unique().tolist()))
    if cat_filter != "All Categories":
        display_prods = prods[prods['category'] == cat_filter]
    else:
        display_prods = prods
        
    st.dataframe(display_prods[['name', 'category', 'unit_price', 'stock_qty', 'reorder_level', 'expiry_date', 'supplier_name']].rename(columns={
        'name': 'Product', 'category': 'Category', 'unit_price': 'Price (₹)',
        'stock_qty': 'Stock', 'reorder_level': 'Reorder Pt', 'expiry_date': 'Expiry Date', 'supplier_name': 'Supplier'
    }), use_container_width=True)

# ── Tab 4: Expiry Surveillance ───────────────────────────────────────────────
with tab4:
    st.markdown("### 📅 Perishable Shelf-Life Surveillance")
    st.markdown("Identifies items with immediate expiry risk (&le;15 days) to trigger dynamic First-Expired, First-Out (FEFO) markdown bundling.")
    
    expiry_p = prods[prods['is_near_expiry'] | prods['is_expired']][['name', 'category', 'stock_qty', 'expiry_date', 'days_to_expiry']]
    
    col_a, col_b = st.columns([5, 7])
    with col_a:
        st.dataframe(expiry_p.rename(columns={
            'name': 'Product', 'category': 'Category', 'stock_qty': 'Units at Risk',
            'expiry_date': 'Expiry Date', 'days_to_expiry': 'Days Left'
        }), use_container_width=True)
        
    with col_b:
        fig_exp = px.histogram(
            prods.dropna(subset=['days_to_expiry']), x='days_to_expiry', nbins=25,
            title="Distribution of Catalog Days-to-Expiry",
            labels={'days_to_expiry': 'Days Remaining Until Expiry'},
            color_discrete_sequence=['#2d6a4f']
        )
        fig_exp.add_vline(x=15, line_dash="dash", line_color="#e76f51", annotation_text="15-Day Alert Horizon")
        fig_exp.update_layout(height=350, plot_bgcolor='white')
        st.plotly_chart(fig_exp, use_container_width=True)

# ── Tab 5: POS Billing Records ───────────────────────────────────────────────
with tab5:
    st.markdown("### 🧾 Historical Point-of-Sale Transactions")
    st.dataframe(
        filtered_sales[['id', 'sale_date', 'sale_time', 'cashier', 'total_amount', 'discount', 'final_amount']].rename(columns={
            'id': 'Sale #', 'sale_date': 'Date', 'sale_time': 'Time', 'cashier': 'Cashier',
            'total_amount': 'Subtotal (₹)', 'discount': 'Discount (%)', 'final_amount': 'Amount Paid (₹)'
        }).sort_values('Sale #', ascending=False),
        use_container_width=True
    )
