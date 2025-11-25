import streamlit as st
import pandas as pd
import plotly.express as px
import io

# --- Konfigurasi Halaman ---
st.set_page_config(
    page_title="Dashboard Penjualan Kopi Interaktif",
    page_icon="☕",
    layout="wide"
)

# --- Judul & Deskripsi Aplikasi ---
st.title("☕ Dashboard Analisis Penjualan Kopi")
st.markdown("Dashboard interaktif ini menyajikan ringkasan, tren, dan detail produk berdasarkan data *Coffee Sales* yang Anda unggah.")
st.markdown("---")

# --- Fungsi Konversi Angka (Wajib untuk data Anda) ---
def convert_to_float(df, column_name):
    """Mengubah kolom string dengan koma desimal (seperti '1,6') menjadi float."""
    # Ubah koma (,) menjadi titik (.) dan konversi ke numerik
    df[column_name] = df[column_name].astype(str).str.replace(',', '.', regex=False)
    # Gunakan 'coerce' untuk mengubah nilai yang tidak bisa dikonversi menjadi NaN
    df[column_name] = pd.to_numeric(df[column_name], errors='coerce')
    return df

# --- File Uploader ---
uploaded_file = st.file_uploader(
    "📂 Unggah file data Coffee Sales (CSV atau XLSX)",
    type=["csv", "xlsx"]
)

# --- Logika Pemrosesan Data ---
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            # Membaca CSV dengan pemisah semicolon (;) karena data Anda menggunakannya
            df = pd.read_csv(uploaded_file, sep=';')
        elif uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file)
        
        # --- 2. Pembersihan & Persiapan Data ---
        
        if 'money' not in df.columns or 'coffee_name' not in df.columns:
            st.error("⚠️ File yang diunggah harus memiliki kolom 'money' (penjualan) dan 'coffee_name' (produk).")
            st.stop()
            
        # Konversi kolom 'money' (penjualan)
        df = convert_to_float(df, 'money')
        df.dropna(subset=['money'], inplace=True)
        
        # Konversi kolom 'Date' jika ada
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce', dayfirst=True)
            df.dropna(subset=['Date'], inplace=True) 

        # --- 3. Tampilan Dashboard dengan Tabs ---
        
        # Tentukan tab
        tab_ringkasan, tab_produk, tab_waktu_pembayaran, tab_data_mentah = st.tabs([
            "📊 Ringkasan Kunci", 
            "☕ Analisis Produk", 
            "⏰ Tren Waktu & Pembayaran", 
            "📋 Data Mentah"
        ])

        # --- TAB 1: RINGKASAN KUNCI ---
        with tab_ringkasan:
            st.header("Ringkasan Kinerja Penjualan")
            
            # Perhitungan Metrik Kunci
            total_penjualan = df['money'].sum()
            jumlah_transaksi = len(df)
            produk_terlaris = df['coffee_name'].mode()[0] if not df['coffee_name'].empty else "N/A"
            
            # Tampilkan Metrik
            col1, col2, col3 = st.columns(3)
            col1.metric("💰 Total Penjualan", f"Rp {total_penjualan:,.2f}")
            col2.metric("📦 Jumlah Transaksi", f"{jumlah_transaksi:,}")
            col3.metric("🔝 Produk Terlaris", produk_terlaris)
            
            st.markdown("---")
            
            # Tren Penjualan Harian (Jika kolom Date tersedia)
            if 'Date' in df.columns and not df.empty:
                st.subheader("📈 Tren Penjualan Harian")
                daily_sales = df.groupby(df['Date'].dt.date)['money'].sum().reset_index()
                daily_sales.columns = ['Date', 'money'] 
                
                fig_trend = px.line(
                    daily_sales,
                    x='Date',
                    y='money',
                    title='Total Penjualan dari Waktu ke Waktu',
                    labels={'money': 'Total Penjualan (Rp)', 'Date': 'Tanggal'},
                    color_discrete_sequence=['#4CAF50'] # Hijau untuk pertumbuhan
                )
                st.plotly_chart(fig_trend, use_container_width=True)
            else:
                st.info("Kolom 'Date' tidak ditemukan atau tidak valid untuk visualisasi tren harian.")

        # --- TAB 2: ANALISIS PRODUK ---
        with tab_produk:
            st.header("Analisis Penjualan Berdasarkan Produk")
            
            if not df.empty:
                sales_by_coffee = df.groupby('coffee_name')['money'].sum().sort_values(ascending=False).reset_index()
                sales_by_coffee['persentase'] = (sales_by_coffee['money'] / total_penjualan) * 100
                
                col_bar, col_pie = st.columns(2)

                with col_bar:
                    st.subheader("🏆 Top 10 Produk Terlaris (Berdasarkan Nilai Penjualan)")
                    fig_coffee = px.bar(
                        sales_by_coffee.head(10), 
                        x='money',
                        y='coffee_name',
                        orientation='h',
                        labels={'money': 'Total Penjualan (Rp)', 'coffee_name': 'Jenis Kopi'},
                        color='money',
                        color_continuous_scale=px.colors.sequential.Agsunset # Skema warna emas/kopi
                    )
                    fig_coffee.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_coffee, use_container_width=True)
                
                with col_pie:
                    st.subheader("Distribution of Top 5 Products")
                    top_5_products = sales_by_coffee.head(5)
                    fig_pie = px.pie(
                        top_5_products,
                        values='money',
                        names='coffee_name',
                        title='Proporsi Penjualan 5 Produk Teratas',
                        color_discrete_sequence=px.colors.qualitative.Pastel1
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("Data tidak cukup untuk analisis produk.")


        # --- TAB 3: ANALISIS WAKTU & PEMBAYARAN ---
        with tab_waktu_pembayaran:
            st.header("Tren Penjualan & Distribusi Pembayaran")
            
            col_hour, col_month = st.columns(2)

            # Penjualan per Jam (hour_of_day)
            with col_hour:
                if 'hour_of_day' in df.columns and not df.empty:
                    st.subheader("🔔 Penjualan Berdasarkan Jam (Hour of Day)")
                    sales_by_hour = df.groupby('hour_of_day')['money'].sum().reset_index()
                    fig_hour = px.line(
                        sales_by_hour,
                        x='hour_of_day',
                        y='money',
                        title='Jam Puncak Penjualan',
                        labels={'money': 'Total Penjualan (Rp)', 'hour_of_day': 'Jam (0-23)'},
                        markers=True,
                        color_discrete_sequence=['#A0522D'] # Warna cokelat/kopi
                    )
                    st.plotly_chart(fig_hour, use_container_width=True)
                
                if 'cash_type' in df.columns and not df.empty:
                    st.subheader("💳 Distribusi Metode Pembayaran")
                    sales_by_payment = df.groupby('cash_type')['money'].sum().reset_index()
                    fig_payment = px.bar(
                        sales_by_payment,
                        x='cash_type',
                        y='money',
                        title='Penjualan Berdasarkan Tipe Pembayaran',
                        labels={'money': 'Total Penjualan (Rp)', 'cash_type': 'Tipe Pembayaran'},
                        color='cash_type',
                        color_discrete_sequence=px.colors.qualitative.Set2
                    )
                    st.plotly_chart(fig_payment, use_container_width=True)

            # Penjualan per Bulan (Month_name)
            with col_month:
                if 'Month_name' in df.columns and not df.empty:
                    st.subheader("🗓️ Penjualan Berdasarkan Bulan")
                    # Tentukan urutan bulan secara manual agar urutan di chart benar
                    month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                    df['Month_name'] = pd.Categorical(df['Month_name'], categories=month_order, ordered=True)
                    
                    sales_by_month = df.groupby('Month_name')['money'].sum().reset_index()
                    
                    fig_month = px.bar(
                        sales_by_month,
                        x='Month_name',
                        y='money',
                        title='Tren Penjualan Bulanan',
                        labels={'money': 'Total Penjualan (Rp)', 'Month_name': 'Bulan'},
                        color='money',
                        color_continuous_scale=px.colors.sequential.Teal
                    )
                    st.plotly_chart(fig_month, use_container_width=True)
                else:
                    st.info("Data tidak cukup untuk analisis waktu dan pembayaran.")
            

        # --- TAB 4: DATA MENTAH ---
        with tab_data_mentah:
            st.header("Pratinjau Data Mentah")
            st.dataframe(df)

    except Exception as e:
        # Menampilkan error jika proses pembacaan file gagal
        st.error("Terjadi kesalahan fatal saat memproses data.")
        st.exception(e) 
        st.info("Pastikan file Anda adalah CSV yang valid dengan pemisah titik koma (;) atau file Excel, dan kolom 'money' sudah benar.")

else:
    # Tampilan saat belum ada file yang diunggah
    st.info("⬆️ Silakan unggah file data 'Coffee Sales' Anda di atas untuk memulai analisis.")
