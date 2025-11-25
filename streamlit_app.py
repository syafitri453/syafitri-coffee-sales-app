import streamlit as st
import pandas as pd
import plotly.express as px
import io
import locale

# --- Konfigurasi Halaman ---
st.set_page_config(
    page_title="Dashboard Penjualan Kopi",
    page_icon="☕",
    layout="wide"
)

# --- Judul Aplikasi ---
st.title("☕ Analisis Penjualan Kopi")
st.markdown("Unggah data Coffee Sales Anda (CSV atau Excel) untuk visualisasi otomatis.")

# --- Fungsi Konversi Angka (Menangani Koma sebagai Desimal) ---
def convert_to_float(df, column_name):
    """Mengubah kolom string dengan koma desimal menjadi float."""
    # Ubah koma (,) menjadi titik (.) dan konversi ke numerik
    df[column_name] = df[column_name].astype(str).str.replace(',', '.', regex=False)
    df[column_name] = pd.to_numeric(df[column_name], errors='coerce')
    return df

# --- File Uploader ---
uploaded_file = st.file_uploader(
    "📂 Unggah file data Coffee Sales (CSV atau XLSX)",
    type=["csv", "xlsx"]
)

# --- Logika Utama ---
if uploaded_file is not None:
    # --- 1. Membaca Data Sesuai Tipe File ---
    try:
        if uploaded_file.name.endswith('.csv'):
            # Coba baca CSV dengan pemisah semicolon (;) karena data yang diunggah menggunakan ini
            df = pd.read_csv(uploaded_file, sep=';')
        elif uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file)
        
        # --- 2. Pembersihan & Persiapan Data ---
        
        # Kolom 'money' adalah total penjualan, kita perlu mengubahnya menjadi float
        df = convert_to_float(df, 'money')
        
        # Hapus baris di mana 'money' adalah NaN setelah konversi (data kotor)
        df.dropna(subset=['money'], inplace=True)
        
        # Pastikan kolom 'Date' ada dan diubah ke format datetime
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce', dayfirst=True)
            df.dropna(subset=['Date'], inplace=True) # Hapus baris dengan Date invalid
        
        # --- 3. Tampilan Dashboard ---
        
        st.header("Ringkasan Data")
        total_penjualan = df['money'].sum()
        
        col1, col2, col3 = st.columns(3)
        col1.metric("☕ Total Penjualan", f"Rp {total_penjualan:,.2f}")
        col2.metric("📦 Jumlah Transaksi", f"{len(df):,}")
        col3.metric("🔝 Produk Terlaris", df['coffee_name'].mode()[0])
        
        st.markdown("---")
        
        col4, col5 = st.columns(2)
        
        # Visualisasi 1: Penjualan Berdasarkan Produk
        with col4:
            st.subheader("Penjualan Berdasarkan Jenis Kopi")
            sales_by_coffee = df.groupby('coffee_name')['money'].sum().sort_values(ascending=False).reset_index()
            fig_coffee = px.bar(
                sales_by_coffee.head(10), # Ambil 10 produk teratas
                x='money',
                y='coffee_name',
                orientation='h',
                title='Top 10 Produk Terlaris',
                labels={'money': 'Total Penjualan (Rp)', 'coffee_name': 'Jenis Kopi'},
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_coffee.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_coffee, use_container_width=True)

        # Visualisasi 2: Tren Penjualan Harian (Jika kolom Date tersedia)
        with col5:
            if 'Date' in df.columns:
                st.subheader("Tren Penjualan Harian")
                daily_sales = df.groupby(df['Date'].dt.date)['money'].sum().reset_index()
                fig_trend = px.line(
                    daily_sales,
                    x='Date',
                    y='money',
                    title='Total Penjualan dari Waktu ke Waktu',
                    labels={'money': 'Total Penjualan (Rp)', 'Date': 'Tanggal'},
                    color_discrete_sequence=['#4CAF50']
                )
                st.plotly_chart(fig_trend, use_container_width=True)
            else:
                st.subheader("Distribusi Penjualan Berdasarkan Waktu")
                # Gunakan Time_of_Day jika Date tidak ada
                sales_by_time = df.groupby('Time_of_Day')['money'].sum().reset_index()
                fig_time = px.pie(
                    sales_by_time,
                    values='money',
                    names='Time_of_Day',
                    title='Proporsi Penjualan Berdasarkan Waktu',
                    color_discrete_sequence=px.colors.sequential.Agsunset
                )
                st.plotly_chart(fig_time, use_container_width=True)

        # Tampilkan Dataframe
        st.markdown("---")
        st.subheader("Pratinjau Data Mentah")
        st.dataframe(df)

    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses file: {e}")
        st.info("Pastikan file Anda adalah CSV yang dipisahkan semicolon (;) atau file Excel yang valid, dan kolom 'money' sudah benar.")

else:
    # Tampilan saat belum ada file yang diunggah
    st.info("Silakan unggah data 'Coffee Sales' Anda di atas untuk memulai analisis. Data Anda akan aman dan tidak disimpan.")
    
# Tambahkan bagian untuk Groq AI Commentary jika Anda ingin mengintegrasikannya nanti
# Saat ini, kita fokus pada fungsionalitas visualisasi dasar.
