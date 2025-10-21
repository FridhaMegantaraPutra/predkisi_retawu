"""
MINIMAL PREDICTION APP - Ultra Simple
======================================
Fokus: List hari + Total prediksi

Usage:
    streamlit run app_minimal.py
"""

import streamlit as st
import pandas as pd
import pickle
from datetime import datetime

st.set_page_config(page_title="Prediksi", page_icon="🔮", layout="centered")

# ============================================================================
# LOAD MODELS
# ============================================================================

@st.cache_resource
def load_models():
    try:
        with open('models_pkl/all_models.pkl', 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        st.error("❌ Error: File 'models_pkl/all_models.pkl' tidak ditemukan!")
        st.info("Pastikan folder models_pkl/ ada di direktori yang sama dengan app ini")
        st.stop()
    except Exception as e:
        st.error(f"❌ Error loading models: {str(e)}")
        st.stop()

try:
    models = load_models()
except Exception as e:
    st.error(f"❌ Error: {str(e)}")
    st.stop()

# ============================================================================
# HEADER
# ============================================================================

st.title("🔮 Prediksi Penjualan")
st.markdown("---")

# ============================================================================
# SIDEBAR - PRODUCT SELECTION
# ============================================================================

st.sidebar.header("📦 Pilih Produk")

# Search box
search = st.sidebar.text_input("🔍 Cari produk", "", key="search")

# Filter products
try:
    products = sorted(list(models.keys()))
    
    if search:
        products = [p for p in products if search.lower() in p.lower()]
        
        if not products:
            st.sidebar.warning(f"Tidak ada produk yang cocok dengan '{search}'")
            products = sorted(list(models.keys()))
    
    selected = st.sidebar.selectbox("Pilih produk:", products, key="product")
    
except Exception as e:
    st.error(f"❌ Error memuat daftar produk: {str(e)}")
    st.stop()

# Get model data
try:
    model_data = models[selected]
    model = model_data['model']
    df = model_data['original_data']
    metrics = model_data['metrics']
except KeyError as e:
    st.error(f"❌ Error: Data produk tidak lengkap. Missing key: {str(e)}")
    st.stop()
except Exception as e:
    st.error(f"❌ Error mengambil data produk: {str(e)}")
    st.stop()

# Model info in sidebar
quality = "🟢 Good" if metrics['MAPE'] < 20 else "🟡 Fair" if metrics['MAPE'] < 50 else "🔴 Poor"
st.sidebar.success(f"""
**Model Quality**
{quality} MAPE: {metrics['MAPE']:.1f}%

**Data**
Records: {len(df)}
""")

# ============================================================================
# MAIN CONTENT
# ============================================================================

st.subheader(f"📊 {selected}")

# Date inputs
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    start = st.date_input(
        "📅 Dari Tanggal",
        value=datetime(2025, 12, 1),
        key="start_date"
    )

with col2:
    end = st.date_input(
        "📅 Sampai Tanggal",
        value=datetime(2025, 12, 5),
        key="end_date"
    )

with col3:
    st.markdown("<br>", unsafe_allow_html=True)
    predict_btn = st.button("🚀 Prediksi", type="primary", use_container_width=True)

# ============================================================================
# VALIDATION
# ============================================================================

if start >= end:
    st.error("❌ **Error:** Tanggal akhir harus setelah tanggal awal!")
    st.stop()

days = (end - start).days + 1

if days > 365:
    st.warning(f"⚠️ **Warning:** Range terlalu besar ({days} hari). Prediksi mungkin kurang akurat. Maksimal 365 hari direkomendasikan.")

st.info(f"📊 **Total hari yang akan diprediksi: {days} hari**")

# ============================================================================
# GENERATE PREDICTION
# ============================================================================

if predict_btn:
    try:
        with st.spinner("🔮 Membuat prediksi..."):
            # Generate forecast
            dates = pd.date_range(start=start, end=end, freq='D')
            future = pd.DataFrame({'ds': dates})
            forecast = model.predict(future)
        
        st.success(f"✅ **Prediksi berhasil dibuat untuk {days} hari!**")
        
        st.markdown("---")
        
        # ====================================================================
        # SUMMARY METRICS
        # ====================================================================
        
        st.subheader("📊 Ringkasan Prediksi")
        
        total_prediksi = forecast['yhat'].sum()
        rata_rata = forecast['yhat'].mean()
        min_val = forecast['yhat'].min()
        max_val = forecast['yhat'].max()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("📈 **TOTAL PREDIKSI**", f"{total_prediksi:.2f} unit", 
                     help="Total prediksi untuk semua hari")
            st.metric("📊 **Rata-rata/hari**", f"{rata_rata:.2f} unit")
        
        with col2:
            st.metric("⬇️ **Minimum**", f"{min_val:.2f} unit")
            st.metric("⬆️ **Maximum**", f"{max_val:.2f} unit")
        
        st.markdown("---")
        
        # ====================================================================
        # LIST PREDIKSI PER HARI
        # ====================================================================
        
        st.subheader("📋 Prediksi Per Hari")
        
        # Prepare data
        result_df = pd.DataFrame({
            'Tanggal': forecast['ds'].dt.strftime('%Y-%m-%d'),
            'Hari': forecast['ds'].dt.strftime('%A'),
            'Prediksi': forecast['yhat'].round(2),
            'Range_Min': forecast['yhat_lower'].round(2),
            'Range_Max': forecast['yhat_upper'].round(2)
        })
        
        # Day emoji mapping
        day_emoji = {
            'Monday': '📘', 'Tuesday': '📗', 'Wednesday': '📙',
            'Thursday': '📕', 'Friday': '📔', 
            'Saturday': '🟦', 'Sunday': '🟥'
        }
        
        # Display all predictions
        st.markdown("### 📅 Detail Prediksi:")
        
        # Create container for better layout
        for idx, row in result_df.iterrows():
            emoji = day_emoji.get(row['Hari'], '📄')
            
            # Display in columns
            col1, col2, col3 = st.columns([3, 1, 3])
            
            with col1:
                st.write(f"{emoji} **{row['Tanggal']}** ({row['Hari']})")
            
            with col2:
                st.write("→")
            
            with col3:
                st.write(f"**{row['Prediksi']:.2f} unit** _(Range: {row['Range_Min']:.2f} - {row['Range_Max']:.2f})_")
            
            # Add separator every 7 days for better readability
            if (idx + 1) % 7 == 0 and idx < len(result_df) - 1:
                st.markdown("---")
        
        # Total at the end
        st.markdown("---")
        st.markdown(f"### 💰 **TOTAL: {total_prediksi:.2f} unit** untuk {days} hari")
        
        st.markdown("---")
        
        # ====================================================================
        # WEEKLY SUMMARY (if >= 7 days)
        # ====================================================================
        
        if days >= 7:
            st.subheader("📊 Ringkasan Per Minggu")
            
            temp_df = result_df.copy()
            temp_df['Tanggal'] = pd.to_datetime(temp_df['Tanggal'])
            temp_df['Week'] = temp_df['Tanggal'].dt.to_period('W')
            
            weekly = temp_df.groupby('Week').agg({
                'Prediksi': ['sum', 'mean', 'count']
            }).round(2)
            
            weekly.columns = ['Total', 'Rata-rata', 'Jumlah Hari']
            weekly = weekly.reset_index()
            weekly['Minggu'] = weekly['Week'].astype(str)
            weekly = weekly[['Minggu', 'Jumlah Hari', 'Total', 'Rata-rata']]
            
            st.dataframe(weekly, use_container_width=True, hide_index=True)
            
            st.markdown("---")
        
        # ====================================================================
        # DOWNLOAD BUTTON
        # ====================================================================
        
        st.subheader("📥 Download Hasil")
        
        # Prepare CSV
        csv_df = result_df.copy()
        csv_df.columns = ['Tanggal', 'Hari', 'Prediksi (unit)', 'Range Min', 'Range Max']
        
        # Add total row
        total_row = pd.DataFrame({
            'Tanggal': ['TOTAL'],
            'Hari': [''],
            'Prediksi (unit)': [total_prediksi],
            'Range Min': [''],
            'Range Max': ['']
        })
        csv_df = pd.concat([csv_df, total_row], ignore_index=True)
        
        csv = csv_df.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            label="📥 Download Prediksi (CSV)",
            data=csv,
            file_name=f"prediksi_{selected}_{start}_to_{end}.csv",
            mime="text/csv",
            type="primary",
            use_container_width=True
        )
        
    except ValueError as e:
        st.error(f"❌ **Error Validasi:** {str(e)}")
        st.info("Coba dengan range tanggal yang berbeda")
    
    except Exception as e:
        st.error(f"❌ **Error saat membuat prediksi:** {str(e)}")
        st.info("Silakan coba lagi atau pilih produk lain")

# ============================================================================
# FOOTER - HISTORICAL INFO
# ============================================================================

st.markdown("---")
st.subheader("📊 Informasi Data Historis")

col1, col2, col3 = st.columns(3)

try:
    with col1:
        st.info(f"""
        **📈 Statistik**
        
        Mean: {df['Qty Out'].mean():.2f}
        Total: {df['Qty Out'].sum():.2f}
        Records: {len(df)}
        """)
    
    with col2:
        st.info(f"""
        **📅 Periode**
        
        Dari: {df['Document Date'].min().strftime('%Y-%m-%d')}
        Sampai: {df['Document Date'].max().strftime('%Y-%m-%d')}
        """)
    
    with col3:
        st.info(f"""
        **🎯 Model**
        
        {quality}
        MAPE: {metrics['MAPE']:.1f}%
        MAE: {metrics['MAE']:.2f}
        """)

except Exception as e:
    st.warning(f"⚠️ Tidak dapat menampilkan info historis: {str(e)}")

# ============================================================================
# HELP SECTION
# ============================================================================

with st.expander("❓ Bantuan"):
    st.markdown("""
    ### Cara Menggunakan:
    
    1. **Pilih Produk** di sidebar (bisa pakai search)
    2. **Pilih Tanggal** mulai dan selesai
    3. **Klik Prediksi** untuk generate
    4. **Lihat Hasil** dalam bentuk list per hari
    5. **Download CSV** untuk export
    
    ### Quality Indicator:
    - 🟢 **Good** (MAPE < 20%): Sangat akurat
    - 🟡 **Fair** (MAPE 20-50%): Cukup akurat
    - 🔴 **Poor** (MAPE > 50%): Kurang akurat
    
    ### Tips:
    - Range 7-30 hari: Optimal
    - Range 30-90 hari: Cukup baik
    - Range > 90 hari: Kurang akurat
    """)