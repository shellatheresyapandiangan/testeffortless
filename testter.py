# ==============================================================================
# Dashboard Analisis Survei Restoran
# Analisis Data survei yang kompleks dan multi-respon
# Versi: 2.4 (Perbaikan error dan data yang tercampur)
# ==============================================================================

# --- 1. Impor Library ---
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import re
import numpy as np
import io
import plotly.express as px

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
            try:
                df = pd.read_excel(uploaded_file)
            except ImportError:
                st.error("Gagal membaca file Excel. Harap instal pustaka 'openpyxl' dengan menjalankan perintah ini:")
                st.code("pip install openpyxl")
                return pd.DataFrame()
        else:
            st.error("Format file tidak didukung. Unggah file CSV atau Excel.")
            return pd.DataFrame()
        return df
    except Exception as e:
        st.error(f"Gagal memuat data. Periksa format file Anda. Error: {e}")
        return pd.DataFrame()

def process_multi_response(df, col_list):
    """Menggabungkan kolom multi-respon menjadi satu Series."""
    responses = pd.Series(dtype='object')
    
    # Filter kolom yang benar-benar ada di DataFrame
    valid_cols = [col for col in col_list if col in df.columns]
    
    if valid_cols:
        combined_series = df[valid_cols].stack().dropna().reset_index(drop=True)
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

def calculate_frequency_average(df, col_list):
    """Menghitung rata-rata frekuensi mingguan dari kolom teks."""
    # Konversi frekuensi ke nilai numerik rata-rata per minggu
    mapping = {
        'Setiap hari': 7.0,
        'Hampir setiap hari': 6.0,
        '4~6 kali dalam satu minggu': 5.0,
        '2~3 kali dalam satu minggu': 2.5,
        '1~2 kali dalam satu minggu': 1.5,
        'Kurang dari 1 kali dalam satu minggu': 0.5,
        'Tidak pernah': 0.0,
        # Konversi bulanan ke mingguan (asumsi 1 bulan = 4.33 minggu)
        '1x dalam sebulan': 1/4.33,
        '2x dalam sebulan': 2/4.33,
        '3x dalam sebulan': 3/4.33,
        '4x dalam sebulan': 4/4.33,
        '5x dalam sebulan': 5/4.33,
        '6x dalam sebulan': 6/4.33,
        '5-6x dalam sebulan': 5.5/4.33,
        '1-2 x dalam seminggu': 1.5,
        '3-4 x dalam seminggu': 3.5,
        '1-2x dalam seminggu': 1.5,
        '2-3x dalam seminggu': 2.5,
        '2x dalam sebulan': 2/4.33,
        '4-6x dalam seminggu': 5.0,
        '7x dalam seminggu': 7.0,
        'Lebih dari 10 kali': 10.0, # Asumsi, bisa disesuaikan
        'Tidak pernah': 0.0,
        'Kurang dari 1 kali': 0.5, # Asumsi, bisa disesuaikan
    }
    averages = {}
    for col in col_list:
        if col in df.columns:
            series = df[col].astype(str).str.strip().str.lower().map(
                {k.lower(): v for k, v in mapping.items()}
            )
            if not series.isnull().all():
                averages[col] = series.mean()
    return pd.DataFrame.from_dict(averages, orient='index', columns=['Rata-rata (Mingguan)']).sort_index()

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
            unaided_cols = [f'Q2_{i}' for i in range(1, 6)]
            unaided_combined = pd.concat([df.get('Q1_1', pd.Series()).dropna(), process_multi_response(df, unaided_cols)], ignore_index=True)
            if not unaided_combined.empty:
                unaided_freq = unaided_combined.value_counts().reset_index()
                unaided_freq.columns = ['Restoran', 'Frekuensi']
                st.dataframe(unaided_freq, use_container_width=True)
            else:
                st.info("Tidak ada data unaided awareness untuk dianalisis.")

        # --- Analisis Total Awareness ---
        with st.expander("📈 Total Awareness"):
            st.subheader("Frekuensi Total Awareness (Q3_1 - Q3_9)")
            total_awareness_cols = [f'Q3_{i}' for i in range(1, 10)]
            total_awareness_combined = process_multi_response(df, total_awareness_cols)
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

        # --- Analisis Frekuensi ---
        with st.expander("📈 Rata-rata Frekuensi Kunjungan"):
            st.subheader("Rata-rata Frekuensi (Mingguan)")
            frequency_cols = [f'S{i}_{j}' for i in range(9, 13) for j in range(1, 8)] + ['S13', 'S14']
            frequency_avg = calculate_frequency_average(df, frequency_cols)
            if not frequency_avg.empty:
                st.dataframe(frequency_avg, use_container_width=True)
            else:
                st.info("Tidak ada data frekuensi untuk dianalisis.")

        # --- Conceptual Mapping (Crosstab) ---
        with st.expander("🗺️ Pemetaan Konseptual (Tabel Silang)"):
            st.subheader("Tabel Silang (Crosstab) & Visualisasi")
            st.write("Pilih 2 parameter untuk membuat tabel silang. Data yang akan digunakan adalah dari Skala Likert dan Frekuensi.")
            
            # Gabungkan semua data numerik ke dalam satu DataFrame untuk kemudahan pivot
            importance_cols = [f'Q{i}_{j}' for i in range(16, 20) for j in range(1, 6) if f'Q{i}_{j}' in df.columns]
            satisfaction_cols = [f'Q{i}_{j}' for i in range(20, 25) for j in range(1, 6) if f'Q{i}_{j}' in df.columns]
            agreement_cols = [f'Q{i}_{j}' for i in range(25, 29) for j in range(1, 5) if f'Q{i}_{j}' in df.columns]
            all_likert_cols = importance_cols + satisfaction_cols + agreement_cols
            frequency_cols = [f'S{i}_{j}' for i in range(9, 13) for j in range(1, 8)] + ['S13', 'S14']
            
            all_numeric_cols = [col for col in all_likert_cols + frequency_cols if col in df.columns]
            
            likert_df = df.copy()
            
            # Pemetaan nilai string untuk kolom skala Likert
            likert_mapping = {
                'Sangat Tidak Setuju': 1, 'Tidak Setuju': 2, 'Netral': 3, 'Setuju': 4, 'Sangat Setuju': 5,
                'Sangat Tidak Penting': 1, 'Tidak Penting': 2, 'Netral': 3, 'Penting': 4, 'Sangat Penting': 5,
                'Sangat Tidak Puas': 1, 'Tidak Puas': 2, 'Netral': 3, 'Puas': 4, 'Sangat Puas': 5
            }
            # Perbaikan: Menggunakan .map() yang lebih aman daripada .replace()
            for col in all_likert_cols:
                likert_df[col] = likert_df[col].astype(str).str.strip().map(likert_mapping)

            # Pemetaan nilai string untuk kolom frekuensi
            freq_mapping = {
                'Setiap hari': 7.0, 'Hampir setiap hari': 6.0, '4~6 kali dalam satu minggu': 5.0,
                '2~3 kali dalam satu minggu': 2.5, '1~2 kali dalam satu minggu': 1.5,
                'Kurang dari 1 kali dalam satu minggu': 0.5, 'Tidak pernah': 0.0,
                '1x dalam sebulan': 1/4.33, '2x dalam sebulan': 2/4.33,
                '3x dalam sebulan': 3/4.33, '4x dalam sebulan': 4/4.33,
                '5x dalam sebulan': 5/4.33, '6x dalam sebulan': 6/4.33,
                '5-6x dalam sebulan': 5.5/4.33, '1-2 x dalam seminggu': 1.5,
                '3-4 x dalam seminggu': 3.5, '1-2x dalam seminggu': 1.5,
                '2-3x dalam seminggu': 2.5, '2x dalam sebulan': 2/4.33,
                '4-6x dalam seminggu': 5.0, '7x dalam seminggu': 7.0,
                'Lebih dari 10 kali': 10.0, 'Kurang dari 1 kali': 0.5,
            }
            for col in frequency_cols:
                likert_df[col] = likert_df[col].astype(str).str.strip().str.lower().map(
                    {k.lower(): v for k, v in freq_mapping.items()})
            
            # Pemetaan nilai string ke numerik untuk kolom pivot 'S1' dan 'S2'
            s1_mapping = {'Laki-laki': 'Laki-laki', 'Perempuan': 'Perempuan'}
            s2_mapping = {
                '15 - 19 tahun': '15-19', '20 - 24 tahun': '20-24', '25 - 29 tahun': '25-29', 
                '30 - 34 tahun': '30-34', '35 - 39 tahun': '35-39', '40 - 44 tahun': '40-44', 
                '45 - 49 tahun': '45-49', '50 - 54 tahun': '50-54', '>55 tahun': '>55'
            }
            if 'S1' in likert_df.columns:
                likert_df['S1'] = likert_df['S1'].astype(str).str.strip().map(s1_mapping)
            if 'S2' in likert_df.columns:
                likert_df['S2'] = likert_df['S2'].astype(str).str.strip().map(s2_mapping)
            
            pivot_options = ["Jenis Kelamin (S1)", "Usia (S2)"]
            selected_pivot = st.selectbox("Pilih Parameter Pivot:", options=pivot_options)
            
            if selected_pivot == "Jenis Kelamin (S1)":
                pivot_col = 'S1'
            else:
                pivot_col = 'S2'
            
            if pivot_col in likert_df.columns and not likert_df[pivot_col].isnull().all() and all_numeric_cols:
                pivot_table = likert_df.groupby(pivot_col)[all_numeric_cols].mean()
                
                # Ubah DataFrame menjadi format yang lebih cocok untuk heatmap Plotly
                df_heatmap = pivot_table.stack().reset_index()
                df_heatmap.columns = [pivot_col, 'Variabel', 'Rata-rata']
                
                # Buat heatmap interaktif
                fig = px.imshow(
                    df_heatmap.pivot(index=pivot_col, columns='Variabel', values='Rata-rata'),
                    color_continuous_scale='YlGnBu',
                    aspect="auto",
                    labels={'x': 'Variabel', 'y': selected_pivot, 'color': 'Rata-rata'}
                )
                
                # Atur tata letak
                fig.update_layout(
                    title='Pemetaan Rata-rata Berdasarkan Parameter Pivot',
                    xaxis_title='Variabel',
                    yaxis_title=selected_pivot,
                    xaxis_side="top"
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(f"Kolom pivot '{pivot_col}' tidak ditemukan atau tidak ada data numerik untuk dianalisis.")

st.markdown("</div>", unsafe_allow_html=True)
