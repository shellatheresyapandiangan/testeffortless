# ==============================================================================
# Dashboard Analisis Survei Restoran
# Analisis Data survei yang kompleks dan multi-respon
# Versi: 3.1 (Perbaikan Error 'ValueError')
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
            series = df[col].astype(str).str.strip().map(mapping)
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
        'Lebih dari 10 kali': 10.0, 'Kurang dari 1 kali': 0.5,
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

# Placeholder untuk API key
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
                
                fig_q1 = px.bar(q1_freq, x='Restoran', y='Frekuensi', 
                                title='Top of Mind Awareness',
                                labels={'Frekuensi': 'Jumlah Responden'},
                                color='Frekuensi',
                                color_continuous_scale=px.colors.sequential.YlGnBu)
                st.plotly_chart(fig_q1, use_container_width=True)
            else:
                st.info("Kolom 'Q1_1' tidak ditemukan dalam data.")
            
            st.subheader("2. Frekuensi Unaided Awareness (Q1_1, Q2_1 - Q2_5)")
            unaided_cols = [f'Q2_{i}' for i in range(1, 6)]
            unaided_combined = pd.concat([df.get('Q1_1', pd.Series()).dropna(), process_multi_response(df, unaided_cols)], ignore_index=True)
            if not unaided_combined.empty:
                unaided_freq = unaided_combined.value_counts().reset_index()
                unaided_freq.columns = ['Restoran', 'Frekuensi']
                st.dataframe(unaided_freq, use_container_width=True)
                
                fig_unaided = px.bar(unaided_freq, x='Restoran', y='Frekuensi', 
                                    title='Unaided Awareness',
                                    labels={'Frekuensi': 'Jumlah Responden'},
                                    color='Frekuensi',
                                    color_continuous_scale=px.colors.sequential.YlGnBu)
                st.plotly_chart(fig_unaided, use_container_width=True)
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
                
                fig_total = px.bar(total_awareness_freq, x='Restoran', y='Frekuensi',
                                    title='Total Awareness',
                                    labels={'Frekuensi': 'Jumlah Responden'},
                                    color='Frekuensi',
                                    color_continuous_scale=px.colors.sequential.YlGnBu)
                st.plotly_chart(fig_total, use_container_width=True)
            else:
                st.info("Tidak ada data total awareness untuk dianalisis.")

        # --- Analisis Brand Image ---
        with st.expander("🖼️ Brand Image"):
            st.subheader("Frekuensi Brand Image (Q15_1 - Q15_8)")
            brand_image_cols = [f'Q15_{i}' for i in range(1, 9)]
            for col in brand_image_cols:
                if col in df.columns and not df[col].isnull().all():
                    st.markdown(f"**Kolom: {col}**")
                    freq_df = df[col].value_counts().reset_index()
                    freq_df.columns = ['Respons', 'Frekuensi']
                    st.dataframe(freq_df, use_container_width=True)
                    fig_brand = px.bar(freq_df, x='Respons', y='Frekuensi',
                                       title=f'Frekuensi {col}',
                                       labels={'Respons': 'Pilihan', 'Frekuensi': 'Jumlah Responden'},
                                       color='Frekuensi',
                                       color_continuous_scale=px.colors.sequential.YlGnBu)
                    st.plotly_chart(fig_brand, use_container_width=True)
                else:
                    st.info(f"Tidak ada data untuk kolom {col}.")

        # --- Analisis Skala Likert (Rata-rata) ---
        with st.expander("📊 Rata-rata Skala Likert"):
            # Tingkat Kepentingan (Q16_1 - Q19_5)
            st.subheader("1. Rata-rata Tingkat Kepentingan (Q16 - Q19)")
            importance_cols = [f'Q{i}_{j}' for i in range(16, 20) for j in range(1, 6)]
            importance_avg = calculate_likert_average(df, importance_cols)
            if not importance_avg.empty:
                st.dataframe(importance_avg, use_container_width=True)
                fig_imp = px.bar(importance_avg, y=importance_avg.index, x='Rata-rata', 
                                title='Rata-rata Tingkat Kepentingan',
                                labels={'y': 'Parameter'}, orientation='h',
                                color='Rata-rata',
                                color_continuous_scale=px.colors.sequential.YlGnBu)
                fig_imp.update_yaxes(autorange="reversed")
                st.plotly_chart(fig_imp, use_container_width=True)
            else:
                st.info("Tidak ada data tingkat kepentingan.")
            
            # Tingkat Kepuasan (Q20_1 - Q24_5)
            st.subheader("2. Rata-rata Tingkat Kepuasan (Q20 - Q24)")
            satisfaction_cols = [f'Q{i}_{j}' for i in range(20, 25) for j in range(1, 6)]
            satisfaction_avg = calculate_likert_average(df, satisfaction_cols)
            if not satisfaction_avg.empty:
                st.dataframe(satisfaction_avg, use_container_width=True)
                fig_sat = px.bar(satisfaction_avg, y=satisfaction_avg.index, x='Rata-rata',
                                title='Rata-rata Tingkat Kepuasan',
                                labels={'y': 'Parameter'}, orientation='h',
                                color='Rata-rata',
                                color_continuous_scale=px.colors.sequential.YlGnBu)
                fig_sat.update_yaxes(autorange="reversed")
                st.plotly_chart(fig_sat, use_container_width=True)
            else:
                st.info("Tidak ada data tingkat kepuasan.")
            
            # Tingkat Persesuaian (Q25_1 - Q28_2)
            st.subheader("3. Rata-rata Tingkat Persesuaian (Q25 - Q28)")
            agreement_cols = [f'Q{i}_{j}' for i in range(25, 29) for j in range(1, 5)]
            agreement_avg = calculate_likert_average(df, agreement_cols)
            if not agreement_avg.empty:
                st.dataframe(agreement_avg, use_container_width=True)
                fig_agree = px.bar(agreement_avg, y=agreement_avg.index, x='Rata-rata',
                                title='Rata-rata Tingkat Persesuaian',
                                labels={'y': 'Parameter'}, orientation='h',
                                color='Rata-rata',
                                color_continuous_scale=px.colors.sequential.YlGnBu)
                fig_agree.update_yaxes(autorange="reversed")
                st.plotly_chart(fig_agree, use_container_width=True)
            else:
                st.info("Tidak ada data tingkat persesuaian.")

        # --- Analisis Frekuensi ---
        with st.expander("📈 Rata-rata Frekuensi Kunjungan"):
            st.subheader("Rata-rata Frekuensi (Mingguan)")
            frequency_cols = [f'S{i}_{j}' for i in range(9, 13) for j in range(1, 8)] + ['S13', 'S14']
            frequency_avg = calculate_frequency_average(df, frequency_cols)
            if not frequency_avg.empty:
                st.dataframe(frequency_avg, use_container_width=True)
                fig_freq = px.bar(frequency_avg, y=frequency_avg.index, x='Rata-rata (Mingguan)',
                                title='Rata-rata Frekuensi Kunjungan Mingguan',
                                labels={'y': 'Parameter'}, orientation='h',
                                color='Rata-rata (Mingguan)',
                                color_continuous_scale=px.colors.sequential.YlGnBu)
                fig_freq.update_yaxes(autorange="reversed")
                st.plotly_chart(fig_freq, use_container_width=True)
            else:
                st.info("Tidak ada data frekuensi untuk dianalisis.")

        # --- Conceptual Mapping (Crosstab) ---
        with st.expander("🗺️ Pemetaan Konseptual (Tabel Silang)"):
            st.subheader("Tabel Silang (Crosstab) & Visualisasi")
            st.write("Pilih 2 parameter untuk membuat tabel silang. Data yang akan digunakan adalah dari Skala Likert dan Frekuensi.")
            
            # Daftar semua kolom yang relevan
            importance_cols = [f'Q{i}_{j}' for i in range(16, 20) for j in range(1, 6)]
            satisfaction_cols = [f'Q{i}_{j}' for i in range(20, 25) for j in range(1, 6)]
            agreement_cols = [f'Q{i}_{j}' for i in range(25, 29) for j in range(1, 5)]
            all_likert_cols = importance_cols + satisfaction_cols + agreement_cols
            frequency_cols = [f'S{i}_{j}' for i in range(9, 13) for j in range(1, 8)] + ['S13', 'S14']
            all_numeric_cols = [col for col in all_likert_cols + frequency_cols if col in df.columns]

            # Membuat DataFrame yang dapat diubah
            likert_df = df.copy()

            # Mapping untuk skala Likert
            likert_mapping = {
                'Sangat Tidak Setuju': 1, 'Tidak Setuju': 2, 'Netral': 3, 'Setuju': 4, 'Sangat Setuju': 5,
                'Sangat Tidak Penting': 1, 'Tidak Penting': 2, 'Netral': 3, 'Penting': 4, 'Sangat Penting': 5,
                'Sangat Tidak Puas': 1, 'Tidak Puas': 2, 'Netral': 3, 'Puas': 4, 'Sangat Puas': 5
            }
            # Mengkonversi kolom Likert
            for col in all_likert_cols:
                if col in likert_df.columns:
                    likert_df[col] = likert_df[col].astype(str).str.strip().str.title().map(likert_mapping)

            # Mapping untuk frekuensi
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
            # Mengkonversi kolom frekuensi
            for col in frequency_cols:
                if col in likert_df.columns:
                    likert_df[col] = likert_df[col].astype(str).str.strip().str.lower().map(
                        {k.lower(): v for k, v in freq_mapping.items()})

            # Mapping untuk kolom pivot S1 dan S2
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
            
            # Pengecekan baru untuk memastikan kolom pivot ada dan tidak kosong
            if pivot_col in likert_df.columns and not likert_df[pivot_col].isnull().all() and all_numeric_cols:
                # Perbaikan utama: Menggunakan pd.to_numeric untuk konversi yang lebih aman
                for col in all_numeric_cols:
                    likert_df[col] = pd.to_numeric(likert_df[col], errors='coerce')

                # Filter baris yang relevan untuk pivot
                likert_df_clean = likert_df.dropna(subset=[pivot_col] + all_numeric_cols)

                if not likert_df_clean.empty:
                    pivot_table = likert_df_clean.groupby(pivot_col)[all_numeric_cols].mean()
                    
                    df_heatmap = pivot_table.stack().reset_index()
                    df_heatmap.columns = [pivot_col, 'Variabel', 'Rata-rata']
                    
                    fig = px.imshow(
                        df_heatmap.pivot(index=pivot_col, columns='Variabel', values='Rata-rata'),
                        color_continuous_scale='YlGnBu',
                        aspect="auto",
                        labels={'x': 'Variabel', 'y': selected_pivot, 'color': 'Rata-rata'},
                        title='Pemetaan Rata-rata Berdasarkan Parameter Pivot'
                    )
                    
                    fig.update_layout(
                        xaxis_title='Variabel',
                        yaxis_title=selected_pivot,
                        xaxis_side="top"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info(f"Setelah pembersihan, tidak ada data yang valid untuk membuat tabel silang dengan kolom '{pivot_col}'.")
            else:
                st.info(f"Kolom pivot '{pivot_col}' tidak ditemukan atau tidak memiliki data yang relevan.")


        # --- Analisis Open-Ended (Word Cloud) ---
        with st.expander("☁️ Analisis Teks Terbuka (Word Cloud)"):
            open_ended_cols = [f'Q{i}' for i in range(14, 15)] + [f'Q{i}_1' for i in range(10, 14)] + ['S11_8']
            open_ended_valid_cols = [col for col in open_ended_cols if col in df.columns]

            if open_ended_valid_cols:
                st.subheader("Word Cloud dari Jawaban Terbuka")
                selected_text_col = st.selectbox("Pilih kolom teks:", options=open_ended_valid_cols)
                
                if selected_text_col and not df[selected_text_col].isnull().all():
                    all_text = ' '.join(df[selected_text_col].astype(str).str.lower().dropna())
                    
                    # Bersihkan teks dari kata-kata umum (stopwords) dan karakter khusus
                    stopwords = set(['dan', 'atau', 'di', 'dari', 'yang', 'untuk', 'dengan', 'sangat'])
                    cleaned_text = " ".join([word for word in all_text.split() if word not in stopwords and len(word) > 2])

                    if cleaned_text:
                        wordcloud = WordCloud(
                            width=800, height=400, 
                            background_color='white', 
                            colormap='Blues',
                            max_words=100
                        ).generate(cleaned_text)
                        
                        fig, ax = plt.subplots()
                        ax.imshow(wordcloud, interpolation='bilinear')
                        ax.axis("off")
                        st.pyplot(fig)
                    else:
                        st.warning("Tidak ada teks yang cukup untuk membuat Word Cloud.")
                else:
                    st.info("Kolom yang dipilih tidak memiliki data teks.")
            else:
                st.info("Tidak ada kolom teks untuk dianalisis.")

st.markdown("</div>", unsafe_allow_html=True)
