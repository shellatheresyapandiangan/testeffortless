# ==============================================================================
# Dashboard Analisis Survei Restoran
# Analisis Data survei yang kompleks dan multi-respon
# Versi: 2.0 (dengan fitur unggah file)
# ==============================================================================

# --- 1. Impor Library ---
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import re
import numpy as np
import io

# --- 2. Konfigurasi Halaman & Desain (CSS) ---
st.set_page_config(
    page_title="Dashboard Analisis Survei Restoran",
    page_icon="📊",
    layout="wide"
)

# --- Desain UI/UX Profesional dengan CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');

    .stApp {
        background-color: #F0F4F8;
        font-family: 'Poppins', sans-serif;
    }
    .main-column {
        background-color: #FFFFFF;
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.07);
    }
    .header-title {
        font-size: 2.5em;
        font-weight: 700;
        color: #1E293B;
        padding-bottom: 0.1rem;
    }
    .header-subtitle {
        font-size: 1.1em;
        color: #64748B;
        font-weight: 400;
        padding-bottom: 2rem;
    }
    h3 {
        color: #334155;
        font-weight: 600;
        margin-top: 1.5rem;
    }
    .stExpander {
        border: none;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        background-color: #F8FAFC;
        margin-top: 1.5rem;
    }
    .stExpander [data-testid="stExpanderHeader"] {
        font-size: 1.1em;
        font-weight: 600;
        color: #334155;
    }
    .stExpander [data-testid="stExpanderContent"] {
        padding-top: 1.5rem;
    }
    .dataframe-container {
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
    }
</style>
""", unsafe_allow_html=True)

# --- 3. Fungsi-fungsi Bantuan ---
@st.cache_data
def load_data(uploaded_file):
    """Memuat data dari file yang diunggah."""
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(uploaded_file)
        else:
            st.error("Format file tidak didukung. Unggah file CSV atau Excel.")
            return pd.DataFrame()
        return df
    except Exception as e:
        st.error(f"Gagal memuat data. Periksa format file Anda. Error: {e}")
        return pd.DataFrame()

def process_multi_response(df, prefix_list):
    """Menggabungkan kolom multi-respon menjadi satu Series."""
    responses = pd.Series(dtype='object')
    for col_prefix in prefix_list:
        cols_to_combine = [col for col in df.columns if col.startswith(col_prefix) and '_' in col]
        if not cols_to_combine: continue
        combined_series = df[cols_to_combine].stack().dropna().reset_index(drop=True)
        responses = pd.concat([responses, combined_series], ignore_index=True)
    return responses

def calculate_likert_average(df, col_list):
    """Menghitung rata-rata untuk skala Likert dengan konversi numerik."""
    mapping = {
        'Sangat Tidak Setuju': 1, 'Tidak Setuju': 2, 'Netral': 3, 'Setuju': 4, 'Sangat Setuju': 5,
        'Sangat Tidak Penting': 1, 'Tidak Penting': 2, 'Netral': 3, 'Penting': 4, 'Sangat Penting': 5,
        'Sangat Tidak Puas': 1, 'Tidak Puas': 2, 'Netral': 3, 'Puas': 4, 'Sangat Puas': 5
    }
    averages = {}
    for col in col_list:
        if col in df.columns:
            series = df[col].map(mapping)
            if not series.isnull().all():
                averages[col] = series.mean()
    return pd.DataFrame.from_dict(averages, orient='index', columns=['Rata-rata']).sort_index()

# --- 4. Logika Utama Aplikasi ---
st.markdown("<div class='main-column'>", unsafe_allow_html=True)
st.markdown("<div class='header-title'>Dashboard Analisis Survei Restoran</div>", unsafe_allow_html=True)
st.markdown("<div class='header-subtitle'>Analisis Mendalam dari Respon Konsumen</div>", unsafe_allow_html=True)

# Placeholder untuk API key, sesuai permintaan Anda
# Catatan: Kunci API Groq tidak diperlukan untuk analisis ini, tetapi saya sertakan sebagai contoh
groq_api_key = "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"

# --- Bagian Unggah File ---
st.subheader("Unggah Data Survei Anda")
uploaded_file = st.file_uploader("Pilih file CSV atau Excel Anda", type=['csv', 'xlsx', 'xls'])

if uploaded_file:
    df = load_data(uploaded_file)
    
    if not df.empty:
        st.success("File berhasil diunggah!")
        st.write("Pratinjau Data:")
        st.dataframe(df.head())
        
        st.markdown("<hr style='margin-top: 2rem; margin-bottom: 1.5rem; border: 1px solid #E2E8F0;'>", unsafe_allow_html=True)

        # --- Analisis Top of Mind & Unaided Awareness ---
        with st.expander("📊 Frekuensi & Persentase (Top of Mind & Unaided)", expanded=True):
            if 'Q1_1' in df.columns:
                st.subheader("1. Frekuensi Top of Mind (Q1_1)")
                q1_freq = df['Q1_1'].value_counts().reset_index()
                q1_freq.columns = ['Restoran', 'Frekuensi']
                q1_freq['Persentase'] = (q1_freq['Frekuensi'] / len(df) * 100).round(2)
                st.dataframe(q1_freq, use_container_width=True)
            else:
                st.info("Kolom 'Q1_1' tidak ditemukan dalam data.")
            
            st.subheader("2. Frekuensi Unaided Awareness (Q1_1, Q2_1 - Q2_5)")
            unaided_combined = pd.concat([df.get('Q1_1', pd.Series()).dropna(), process_multi_response(df, ['Q2'])], ignore_index=True)
            if not unaided_combined.empty:
                unaided_freq = unaided_combined.value_counts().reset_index()
                unaided_freq.columns = ['Restoran', 'Frekuensi']
                st.dataframe(unaided_freq, use_container_width=True)
            else:
                st.info("Tidak ada data unaided awareness untuk dianalisis.")

        # --- Analisis Total Awareness ---
        with st.expander("📈 Total Awareness"):
            st.subheader("Frekuensi Total Awareness (Q3_1 - Q3_9)")
            total_awareness_combined = process_multi_response(df, ['Q3'])
            if not total_awareness_combined.empty:
                total_awareness_freq = total_awareness_combined.value_counts().reset_index()
                total_awareness_freq.columns = ['Restoran', 'Frekuensi']
                st.dataframe(total_awareness_freq, use_container_width=True)
            else:
                st.info("Tidak ada data total awareness untuk dianalisis.")

        # --- Analisis Brand Image ---
        with st.expander("🖼️ Brand Image"):
            st.subheader("Frekuensi Brand Image (Q15_1 - Q15_8)")
            brand_image_cols = [f'Q15_{i}' for i in range(1, 9)]
            for col in brand_image_cols:
                if col in df.columns and not df[col].isnull().all():
                    st.markdown(f"**Kolom: {col}**")
                    st.dataframe(df[col].value_counts().reset_index().rename(columns={'index': 'Respons', col: 'Frekuensi'}), use_container_width=True)
                else:
                    st.info(f"Tidak ada data untuk kolom {col}.")

        # --- Analisis Skala Likert (Rata-rata) ---
        with st.expander("📊 Rata-rata Skala Likert"):
            # Tingkat Kepentingan (Q16_1 - Q19_5)
            st.subheader("1. Rata-rata Tingkat Kepentingan (Q16 - Q19)")
            importance_cols = [f'Q{i}_{j}' for i in range(16, 20) for j in range(1, 6) if f'Q{i}_{j}' in df.columns]
            importance_avg = calculate_likert_average(df, importance_cols)
            if not importance_avg.empty:
                st.dataframe(importance_avg, use_container_width=True)
            else:
                st.info("Tidak ada data tingkat kepentingan.")
            
            # Tingkat Kepuasan (Q20_1 - Q24_5)
            st.subheader("2. Rata-rata Tingkat Kepuasan (Q20 - Q24)")
            satisfaction_cols = [f'Q{i}_{j}' for i in range(20, 25) for j in range(1, 6) if f'Q{i}_{j}' in df.columns]
            satisfaction_avg = calculate_likert_average(df, satisfaction_cols)
            if not satisfaction_avg.empty:
                st.dataframe(satisfaction_avg, use_container_width=True)
            else:
                st.info("Tidak ada data tingkat kepuasan.")
            
            # Tingkat Persesuaian (Q25_1 - Q28_2)
            st.subheader("3. Rata-rata Tingkat Persesuaian (Q25 - Q28)")
            agreement_cols = [f'Q{i}_{j}' for i in range(25, 29) for j in range(1, 5) if f'Q{i}_{j}' in df.columns]
            agreement_avg = calculate_likert_average(df, agreement_cols)
            if not agreement_avg.empty:
                st.dataframe(agreement_avg, use_container_width=True)
            else:
                st.info("Tidak ada data tingkat persesuaian.")

        # --- Conceptual Mapping (Crosstab) ---
        with st.expander("🗺️ Pemetaan Konseptual (Tabel Silang)"):
            st.subheader("Tabel Silang (Crosstab)")
            st.write("Pilih 2 parameter untuk membuat tabel silang. Data yang akan digunakan adalah dari Skala Likert.")
            
            # Gabungkan semua data Likert ke dalam satu DataFrame untuk kemudahan pivot
            all_likert_cols = [col for col in importance_cols + satisfaction_cols + agreement_cols if col in df.columns]
            likert_df = df[['S1', 'S2'] + all_likert_cols].copy()
            mapping = {
                'Sangat Tidak Setuju': 1, 'Tidak Setuju': 2, 'Netral': 3, 'Setuju': 4, 'Sangat Setuju': 5,
                'Sangat Tidak Penting': 1, 'Tidak Penting': 2, 'Netral': 3, 'Penting': 4, 'Sangat Penting': 5,
                'Sangat Tidak Puas': 1, 'Tidak Puas': 2, 'Netral': 3, 'Puas': 4, 'Sangat Puas': 5
            }
            
            # Perbaikan: Menggunakan .replace() dan to_numeric untuk konversi yang lebih aman
            for col in all_likert_cols:
                likert_df[col] = likert_df[col].replace(mapping).astype(float)
                
            pivot_options = ["Jenis Kelamin (S1)", "Usia (S2)"]
            selected_pivot = st.selectbox("Pilih Parameter Pivot:", options=pivot_options)
            
            if selected_pivot == "Jenis Kelamin (S1)":
                pivot_col = 'S1'
            else:
                pivot_col = 'S2'
            
            if pivot_col in likert_df.columns and not likert_df[pivot_col].isnull().all():
                pivot_table = likert_df.groupby(pivot_col)[all_likert_cols].mean().T
                st.dataframe(pivot_table.style.background_gradient(cmap='viridis', axis=None).format(precision=2), use_container_width=True)
            else:
                st.info(f"Kolom pivot '{pivot_col}' tidak ditemukan atau kosong.")

st.markdown("</div>", unsafe_allow_html=True)
