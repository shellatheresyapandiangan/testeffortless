# ==============================================================================
# Dashboard Analisis Survei Restoran
# Analisis Data survei yang kompleks dan multi-respon
# Versi: 4.0 (Disesuaikan untuk struktur data yang lebih lengkap)
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
import plotly.graph_objects as go

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
    .stButton>button {
        border-radius: 10px;
        border: none;
        background-color: #4A90E2;
        color: white;
        padding: 10px 20px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. Fungsi-fungsi Bantuan ---
@st.cache_data
def load_data(uploaded_file):
    """Memuat data dari file yang diunggah dan membersihkan baris kosong/tidak relevan."""
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
        
        # Membersihkan data dengan menghapus baris yang memiliki NaN di sebagian besar kolom
        df.dropna(how='all', inplace=True)
        # Menghapus baris yang berisi string panjang, kemungkinan teks pertanyaan
        df = df[df.apply(lambda row: row.astype(str).str.len().sum() < 250, axis=1)]
        
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

def calculate_likert_average(df, col_list, mapping):
    """Menghitung rata-rata untuk skala Likert dengan konversi numerik."""
    averages = {}
    for col in col_list:
        if col in df.columns:
            series = df[col].astype(str).str.strip().str.title().map(mapping)
            if not series.isnull().all():
                valid_values = series.dropna()
                if not valid_values.empty:
                    averages[col] = valid_values.mean()
    if averages:
        return pd.DataFrame.from_dict(averages, orient='index', columns=['Rata-rata']).sort_index()
    return pd.DataFrame()

def calculate_frequency_average(df, col_list):
    """Menghitung rata-rata frekuensi mingguan dari kolom teks."""
    mapping = {
        'Setiap hari': 7.0, 'Hampir setiap hari': 6.0, '4~6 kali dalam satu minggu': 5.0,
        '2~3 kali dalam satu minggu': 2.5, '1~2 kali dalam satu minggu': 1.5,
        'Kurang dari 1 kali dalam satu minggu': 0.5, 'Tidak pernah': 0.0,
        '1x dalam sebulan': 1/4.33, '2x dalam sebulan': 2/4.33, '3x dalam sebulan': 3/4.33,
        '4x dalam sebulan': 4/4.33, '5x dalam sebulan': 5/4.33, '6x dalam sebulan': 6/4.33,
        '5-6x dalam sebulan': 5.5/4.33, '1-2 x dalam seminggu': 1.5, '3-4 x dalam seminggu': 3.5,
        '1-2x dalam seminggu': 1.5, '2-3x dalam seminggu': 2.5, '2x dalam sebulan': 2/4.33,
        '4-6x dalam seminggu': 5.0, '7x dalam seminggu': 7.0, 'Lebih dari 10 kali': 10.0, 'Kurang dari 1 kali': 0.5,
    }
    averages = {}
    for col in col_list:
        if col in df.columns:
            series = df[col].astype(str).str.strip().str.lower().map(
                {k.lower(): v for k, v in mapping.items()}
            )
            if not series.isnull().all():
                averages[col] = series.mean()
    if averages:
        return pd.DataFrame.from_dict(averages, orient='index', columns=['Rata-rata (Mingguan)']).sort_index()
    return pd.DataFrame()

def calculate_multiselect_counts(df, col_list):
    """Menghitung frekuensi pilihan dari kolom multi-respon."""
    responses = process_multi_response(df, col_list)
    if not responses.empty:
        responses = responses.str.strip().replace('', np.nan).dropna()
        return responses.value_counts().reset_index().rename(columns={'index': 'Respons', 0: 'Frekuensi'})
    return pd.DataFrame()

# --- 4. Logika Utama Aplikasi ---
st.markdown("<div class='main-column'>", unsafe_allow_html=True)
st.markdown("<div class='header-title'>Dashboard Analisis Survei Restoran</div>", unsafe_allow_html=True)
st.markdown("<div class='header-subtitle'>Analisis Mendalam dari Respon Konsumen</div>", unsafe_allow_html=True)

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

        # --- Analisis Demografi ---
        with st.expander("👥 Analisis Demografi", expanded=False):
            st.subheader("Distribusi Demografi Responden")
            
            # Pie Chart untuk Jenis Kelamin (S1)
            if 'S1' in df.columns and not df['S1'].isnull().all():
                gender_counts = df['S1'].value_counts()
                fig_gender = px.pie(gender_counts, values=gender_counts.values, names=gender_counts.index,
                                    title='Distribusi Jenis Kelamin', hole=0.3,
                                    color_discrete_sequence=px.colors.sequential.YlGnBu_r)
                st.plotly_chart(fig_gender, use_container_width=True)
            else:
                st.info("Kolom 'S1' (Jenis Kelamin) tidak ditemukan atau tidak memiliki data.")

            # Bar Chart untuk Kelompok Usia (S2)
            if 'S2' in df.columns and not df['S2'].isnull().all():
                age_counts = df['S2'].value_counts().sort_index()
                fig_age = px.bar(age_counts, x=age_counts.index, y=age_counts.values,
                                 title='Distribusi Kelompok Usia',
                                 labels={'x': 'Kelompok Usia', 'y': 'Jumlah Responden'},
                                 color=age_counts.values, color_continuous_scale=px.colors.sequential.YlGnBu)
                st.plotly_chart(fig_age, use_container_width=True)
            else:
                st.info("Kolom 'S2' (Kelompok Usia) tidak ditemukan atau tidak memiliki data.")
        
        # --- Analisis Multi-respon ---
        with st.expander("📊 Analisis Multi-respon & Frekuensi", expanded=False):
            st.subheader("Frekuensi Pilihan dari Berbagai Pertanyaan")

            # Frekuensi Unaided Awareness (Q1_1, Q2_1-Q2_5)
            st.markdown("#### Un-aided Awareness")
            unaided_cols = ['Q1_1'] + [f'Q2_{i}' for i in range(1, 6)]
            unaided_df = calculate_multiselect_counts(df, unaided_cols)
            if not unaided_df.empty:
                st.dataframe(unaided_df, use_container_width=True)
                fig_unaided = px.bar(unaided_df, x='Respons', y='Frekuensi', title='Frekuensi Un-aided Awareness', color='Frekuensi', color_continuous_scale=px.colors.sequential.YlGnBu)
                st.plotly_chart(fig_unaided, use_container_width=True)
            else: st.info("Tidak ada data yang lengkap untuk Un-aided Awareness.")

            # Frekuensi Total Awareness (Q3_1-Q3_9)
            st.markdown("#### Total Awareness")
            total_awareness_cols = [f'Q3_{i}' for i in range(1, 10)]
            total_awareness_df = calculate_multiselect_counts(df, total_awareness_cols)
            if not total_awareness_df.empty:
                st.dataframe(total_awareness_df, use_container_width=True)
                fig_total = px.bar(total_awareness_df, x='Respons', y='Frekuensi', title='Frekuensi Total Awareness', color='Frekuensi', color_continuous_scale=px.colors.sequential.YlGnBu)
                st.plotly_chart(fig_total, use_container_width=True)
            else: st.info("Tidak ada data yang lengkap untuk Total Awareness.")

            # Frekuensi Kunjungan Restoran Umum (Q4_1-Q4_9)
            st.markdown("#### Restoran yang Dikunjungi (6 Bulan Terakhir)")
            visited_rest_cols = [f'Q4_{i}' for i in range(1, 10)]
            visited_rest_df = calculate_multiselect_counts(df, visited_rest_cols)
            if not visited_rest_df.empty:
                st.dataframe(visited_rest_df, use_container_width=True)
            else: st.info("Tidak ada data yang lengkap untuk Restoran yang Dikunjungi.")

            # Frekuensi Pilihan Restoran Chinese Food (Q9_1-Q9_16) & Kunjungan (Q10_1-Q10_16)
            st.markdown("#### Restoran Chinese Food yang Dikunjungi")
            chinese_food_cols = [f'Q9_{i}' for i in range(1, 17)] + [f'Q10_{i}' for i in range(1, 17)]
            chinese_food_df = calculate_multiselect_counts(df, chinese_food_cols)
            if not chinese_food_df.empty:
                st.dataframe(chinese_food_df, use_container_width=True)
            else: st.info("Tidak ada data yang lengkap untuk Restoran Chinese Food.")

            # Frekuensi Penggunaan Internet (Q32_1-Q32_10)
            st.markdown("#### Penggunaan Internet")
            internet_cols = [f'Q32_{i}' for i in range(1, 11)]
            internet_df = calculate_multiselect_counts(df, internet_cols)
            if not internet_df.empty:
                st.dataframe(internet_df, use_container_width=True)
            else: st.info("Tidak ada data yang lengkap untuk Penggunaan Internet.")
            
        # --- Analisis Skala Likert & Frekuensi Kunjungan ---
        with st.expander("📝 Analisis Skala Likert & Frekuensi", expanded=False):
            
            # Analisis Frekuensi Kunjungan (S13, S14)
            st.markdown("#### Frekuensi Kunjungan Mingguan/Bulanan")
            freq_cols = ['S13', 'S14']
            freq_avg_df = calculate_frequency_average(df, freq_cols)
            if not freq_avg_df.empty:
                st.dataframe(freq_avg_df)
                fig_freq = px.bar(freq_avg_df, x=freq_avg_df.index, y='Rata-rata (Mingguan)',
                                  title='Rata-rata Frekuensi Kunjungan (Mingguan)',
                                  color='Rata-rata (Mingguan)',
                                  color_continuous_scale=px.colors.sequential.YlGnBu)
                st.plotly_chart(fig_freq, use_container_width=True)
            else:
                st.info("Tidak ada data yang lengkap untuk analisis frekuensi kunjungan.")

            # Mapping Skala Likert
            likert_mapping = {
                'Sangat Tidak Setuju': 1, 'Tidak Setuju': 2, 'Netral': 3, 'Setuju': 4, 'Sangat Setuju': 5,
                'Sangat Tidak Puas': 1, 'Tidak Puas': 2, 'Netral': 3, 'Puas': 4, 'Sangat Puas': 5,
                'Sangat Tidak Penting': 1, 'Tidak Penting': 2, 'Netral': 3, 'Penting': 4, 'Sangat Penting': 5
            }
            
            # Analisis Likert Kepuasan (Q16-Q17, Q20-Q21)
            st.markdown("#### Rata-rata Skor Kepuasan (Q16-Q17, Q20-Q21)")
            likert_cols_1 = [f'Q{i}_{j}' for i in [16,17,20,21] for j in range(1, 4)]
            likert_avg_df_1 = calculate_likert_average(df, likert_cols_1, likert_mapping)
            if not likert_avg_df_1.empty:
                st.dataframe(likert_avg_df_1)
                fig_likert_1 = px.bar(likert_avg_df_1, x='Rata-rata', y=likert_avg_df_1.index,
                                    title='Rata-rata Skor Kepuasan', orientation='h', color='Rata-rata', color_continuous_scale=px.colors.sequential.YlGnBu)
                fig_likert_1.update_yaxes(autorange="reversed")
                st.plotly_chart(fig_likert_1, use_container_width=True)
            else: st.info("Tidak ada data yang lengkap untuk analisis Kepuasan.")

            # Analisis Likert Penilaian (Q24_1-Q24_5, Q25_1-Q25_2, Q26_1-Q26_4)
            st.markdown("#### Rata-rata Skor Penilaian (Q24-Q26)")
            likert_cols_2 = [f'Q24_{i}' for i in range(1, 6)] + [f'Q25_{i}' for i in range(1, 3)] + [f'Q26_{i}' for i in range(1, 5)]
            likert_avg_df_2 = calculate_likert_average(df, likert_cols_2, likert_mapping)
            if not likert_avg_df_2.empty:
                st.dataframe(likert_avg_df_2)
                fig_likert_2 = px.bar(likert_avg_df_2, x='Rata-rata', y=likert_avg_df_2.index,
                                    title='Rata-rata Skor Penilaian', orientation='h', color='Rata-rata', color_continuous_scale=px.colors.sequential.YlGnBu)
                fig_likert_2.update_yaxes(autorange="reversed")
                st.plotly_chart(fig_likert_2, use_container_width=True)
            else: st.info("Tidak ada data yang lengkap untuk analisis Penilaian.")

            # Analisis Likert Persetujuan (Q27-Q28)
            st.markdown("#### Rata-rata Skor Persetujuan (Q27-Q28)")
            likert_cols_3 = [f'Q27_{i}' for i in range(1, 4)] + [f'Q28_{i}' for i in range(1, 3)]
            likert_avg_df_3 = calculate_likert_average(df, likert_cols_3, likert_mapping)
            if not likert_avg_df_3.empty:
                st.dataframe(likert_avg_df_3)
                fig_likert_3 = px.bar(likert_avg_df_3, x='Rata-rata', y=likert_avg_df_3.index,
                                    title='Rata-rata Skor Persetujuan', orientation='h', color='Rata-rata', color_continuous_scale=px.colors.sequential.YlGnBu)
                fig_likert_3.update_yaxes(autorange="reversed")
                st.plotly_chart(fig_likert_3, use_container_width=True)
            else: st.info("Tidak ada data yang lengkap untuk analisis Persetujuan.")
            
        # --- Conceptual Mapping (Crosstab) ---
        with st.expander("🗺️ Pemetaan Konseptual (Tabel Silang)"):
            st.subheader("Tabel Silang (Crosstab) & Visualisasi")
            st.write("Pilih 2 parameter untuk membuat tabel silang. Data yang akan digunakan adalah dari Skala Likert dan Frekuensi.")
            
            # Mendefinisikan semua kolom Likert dan Frekuensi yang relevan
            likert_cols = [f'Q{i}_{j}' for i in [16,17,20,21] for j in range(1, 4)] + [f'Q24_{i}' for i in range(1, 6)] + [f'Q25_{i}' for i in range(1, 3)] + [f'Q26_{i}' for i in range(1, 5)] + [f'Q27_{i}' for i in range(1, 4)] + [f'Q28_{i}' for i in range(1, 3)] + ['Q30_1', 'Q30_2'] + [f'Q30_{i}' for i in range(1, 11)] + ['Q33'] + [f'Q34_{i}' for i in range(1, 17)] + [f'Q35_{i}' for i in range(1, 7)] + [f'Q36_{i}' for i in range(1, 7)] + [f'Q37_{i}' for i in range(1, 11)]
            
            frequency_cols = ['S13', 'S14']
            all_cols_for_crosstab = [col for col in df.columns if col in likert_cols or col in frequency_cols]

            df_cleaned = df.copy()
            
            # Mapping untuk Likert
            likert_mapping = {
                'Sangat Tidak Setuju': 1, 'Tidak Setuju': 2, 'Netral': 3, 'Setuju': 4, 'Sangat Setuju': 5,
                'Sangat Tidak Puas': 1, 'Tidak Puas': 2, 'Netral': 3, 'Puas': 4, 'Sangat Puas': 5,
                'Sangat Tidak Penting': 1, 'Tidak Penting': 2, 'Netral': 3, 'Penting': 4, 'Sangat Penting': 5
            }
            for col in likert_cols:
                if col in df_cleaned.columns:
                    df_cleaned[col] = df_cleaned[col].astype(str).str.strip().str.title().map(likert_mapping)
            
            # Mapping untuk Frekuensi
            freq_mapping = {
                'Setiap hari': 7.0, 'Hampir setiap hari': 6.0, '4~6 kali dalam satu minggu': 5.0,
                '2~3 kali dalam satu minggu': 2.5, '1~2 kali dalam satu minggu': 1.5,
                'Kurang dari 1 kali dalam satu minggu': 0.5, 'Tidak pernah': 0.0,
                '1x dalam sebulan': 1/4.33, '2x dalam sebulan': 2/4.33, '3x dalam sebulan': 3/4.33,
                '4x dalam sebulan': 4/4.33, '5x dalam sebulan': 5/4.33, '6x dalam sebulan': 6/4.33,
                '5-6x dalam sebulan': 5.5/4.33, '1-2 x dalam seminggu': 1.5, '3-4 x dalam seminggu': 3.5,
                '1-2x dalam seminggu': 1.5, '2-3x dalam seminggu': 2.5, '2x dalam sebulan': 2/4.33,
                '4-6x dalam seminggu': 5.0, '7x dalam seminggu': 7.0, 'Lebih dari 10 kali': 10.0, 'Kurang dari 1 kali': 0.5,
            }
            for col in frequency_cols:
                if col in df_cleaned.columns:
                    df_cleaned[col] = df_cleaned[col].astype(str).str.strip().str.lower().map({k.lower(): v for k, v in freq_mapping.items()})

            # Mapping untuk kolom pivot S1 dan S2
            s1_mapping = {'Laki-laki': 'Laki-laki', 'Perempuan': 'Perempuan'}
            s2_mapping = {
                '15 - 19 tahun': '15-19', '20 - 24 tahun': '20-24', '25 - 29 tahun': '25-29', 
                '30 - 34 tahun': '30-34', '35 - 39 tahun': '35-39', '40 - 44 tahun': '40-44', 
                '45 - 49 tahun': '45-49', '50 - 54 tahun': '50-54', '>55 tahun': '>55'
            }
            if 'S1' in df_cleaned.columns: df_cleaned['S1'] = df_cleaned['S1'].astype(str).str.strip().map(s1_mapping)
            if 'S2' in df_cleaned.columns: df_cleaned['S2'] = df_cleaned['S2'].astype(str).str.strip().map(s2_mapping)

            pivot_options = ["Jenis Kelamin (S1)", "Usia (S2)"]
            selected_pivot = st.selectbox("Pilih Parameter Pivot:", options=pivot_options)
            pivot_col = 'S1' if selected_pivot == "Jenis Kelamin (S1)" else 'S2'

            if pivot_col in df_cleaned.columns and not df_cleaned[pivot_col].isnull().all():
                numeric_cols_for_crosstab = [col for col in df_cleaned.columns if col in all_cols_for_crosstab]
                if numeric_cols_for_crosstab:
                    df_clean_for_crosstab = df_cleaned.dropna(subset=[pivot_col] + numeric_cols_for_crosstab)
                    if not df_clean_for_crosstab.empty:
                        pivot_table = df_clean_for_crosstab.groupby(pivot_col)[numeric_cols_for_crosstab].mean().round(2)
                        st.write("Tabel Silang (Crosstab):")
                        st.dataframe(pivot_table, use_container_width=True)
                        
                        df_heatmap = pivot_table.stack().reset_index()
                        df_heatmap.columns = [pivot_col, 'Variabel', 'Rata-rata']
                        
                        fig = px.imshow(
                            df_heatmap.pivot(index=pivot_col, columns='Variabel', values='Rata-rata'),
                            color_continuous_scale='YlGnBu',
                            aspect="auto", labels={'x': 'Variabel', 'y': selected_pivot, 'color': 'Rata-rata'},
                            title='Pemetaan Rata-rata Berdasarkan Parameter Pivot'
                        )
                        fig.update_layout(xaxis_title='Variabel', yaxis_title=selected_pivot, xaxis_side="top")
                        st.plotly_chart(fig, use_container_width=True)
                    else: st.info(f"Tidak ada data yang valid untuk membuat tabel silang dengan kolom '{pivot_col}'.")
                else: st.info("Tidak ada kolom numerik yang tersedia untuk analisis tabel silang.")
            else: st.info(f"Kolom pivot '{pivot_col}' tidak ditemukan atau tidak memiliki data yang relevan.")
        
        # --- Analisis Open-Ended (Word Cloud) ---
        with st.expander("☁️ Analisis Teks Terbuka (Word Cloud)"):
            st.subheader("Word Cloud dari Jawaban Terbuka")
            open_ended_col_list = ['Q1_1', 'Q5', 'Q8', 'Q29', 'S15_1', 'S15_2', 'S15_3', 'S15_4']
            
            # Filter kolom yang benar-benar ada
            valid_open_ended_cols = [col for col in open_ended_col_list if col in df.columns]

            if not valid_open_ended_cols:
                st.info("Tidak ada kolom jawaban terbuka yang terdeteksi.")
            else:
                selected_col = st.selectbox("Pilih kolom jawaban terbuka:", options=valid_open_ended_cols)
            
                if selected_col and not df[selected_col].isnull().all():
                    text_data = df[selected_col].dropna().astype(str)
                    if not text_data.empty:
                        all_text = " ".join(text_data).lower()
                        all_text = re.sub(r'[^a-zA-Z0-9\s]', '', all_text)
                        
                        wordcloud = WordCloud(
                            width=800, height=400, background_color='white',
                            colormap='viridis', random_state=42
                        ).generate(all_text)
                        
                        fig, ax = plt.subplots(figsize=(10, 5))
                        ax.imshow(wordcloud, interpolation='bilinear')
                        ax.axis("off")
                        fig.patch.set_facecolor('#F8FAFC')
                        st.pyplot(fig)
                    else:
                        st.info(f"Kolom '{selected_col}' tidak berisi data teks yang dapat dianalisis.")
                else:
                    st.info(f"Kolom '{selected_col}' tidak ditemukan atau tidak memiliki data. Harap periksa nama kolomnya.")
        
st.markdown("</div>", unsafe_allow_html=True)
