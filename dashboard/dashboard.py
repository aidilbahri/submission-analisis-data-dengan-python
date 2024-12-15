import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.cm as cm
import numpy as np

st.set_page_config(layout="wide")

geojson_url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
geojson_data = requests.get(geojson_url).json()

# Load datasets
@st.cache
def load_data():
    customers_dataset_df = pd.read_csv('../data/customers_dataset.csv')
    orders_dataset_df = pd.read_csv('../data/orders_dataset.csv')
    order_items_dataset_df = pd.read_csv('../data/order_items_dataset.csv')
    return customers_dataset_df, orders_dataset_df, order_items_dataset_df

customers_dataset_df, orders_dataset_df, order_items_dataset_df = load_data()

# Gabungkan dataframe
all_df = pd.read_csv('../data/all_df.csv')

all_df.to_clipboard()

# Konversi kolom tanggal ke format datetime
all_df['order_purchase_timestamp'] = pd.to_datetime(all_df['order_purchase_timestamp'])

# Layout tab di dashboard
tab1, tab2 = st.tabs(["Peta Penjualan per State", "Bar Chart Kota dengan Penjualan Tertinggi"])

# --- Tab 1: Peta Penjualan per State ---
with tab1:
    st.header("Peta Penjualan per State")
    
    # Membuat daftar opsi untuk selectbox (2016-09 hingga 2018-07)
    date_range = pd.date_range(start='2016-09', end='2018-08', freq='M').strftime('%Y-%m').tolist()

# Membuat dropdown untuk memilih periode waktu
    selected_date = st.sidebar.selectbox("Pilih Periode (YYYY-MM)", date_range)

# Memisahkan tahun dan bulan dari selected_date
    selected_year, selected_month = map(int, selected_date.split('-'))

    # Filter data berdasarkan bulan dan tahun yang dipilih
    filtered_df = all_df[
        (all_df['order_purchase_timestamp'].dt.year == selected_year) &
        (all_df['order_purchase_timestamp'].dt.month == selected_month)
    ]

    # Mengelompokkan data penjualan berdasarkan state
    state_sales = filtered_df.groupby('customer_state')['price_x'].sum().reset_index()
    state_sales.rename(columns={'customer_state': 'state', 'price_x': 'sales'}, inplace=True)


    # Membuat peta Folium
    map_center = [-14.2350, -51.9253]  # Koordinat Brasil
    m = folium.Map(location=map_center, zoom_start=4)

    folium.Choropleth(
        geo_data=geojson_data,
        name='choropleth',
        data=state_sales,
        columns=['state', 'sales'],
        key_on='feature.properties.sigla',
        fill_color='YlGn',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name=f'Total Sales for {selected_month}/{selected_year}'
    ).add_to(m)


    st_folium(m, width=800, height=500)

# --- Tab 2: Bar Chart Kota dengan Penjualan Tertinggi ---
with tab2:
    st.header("Bar Chart Kota dengan Penjualan Tertinggi")
    
    
    city_sales = filtered_df.groupby('customer_city')['price_x'].sum().reset_index()
    city_sales.rename(columns={'customer_city': 'city', 'price_x': 'sales'}, inplace=True)
    
    top_7_cities = city_sales.sort_values('sales', ascending=False).head(7)
    
    # Normalisasi data 'sales' untuk membuat intensitas warna
    norm = plt.Normalize(top_7_cities['sales'].min(), top_7_cities['sales'].max())
    colors = cm.Blues(norm(top_7_cities['sales'])) 
    
    # Membuat bar chart
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(
        x='city',
        y='sales',
        data=top_7_cities,
        palette=colors  
    )
    ax.set_title(f"Top 7 Cities by Sales in {selected_month}/{selected_year}")
    ax.set_xlabel("City")
    ax.set_ylabel("Total Sales")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
    st.pyplot(fig)
