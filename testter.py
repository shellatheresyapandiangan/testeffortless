# ==============================================================================
# Dashboard Analisis Survei Restoran
# Analisis Data survei yang kompleks dan multi-respon
# Versi: 3.5 (Penambahan Analisis Likert & Multi-respon)
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
        'Sangat Tidak Puas': 1, 'Tidak Puas': 2, 'Netral': 3, 'Puas': 4, 'Sangat Puas': 5,
        'Sangat Tidak Penting': 1, 'Tidak Penting': 2, 'Netral': 3, 'Penting': 4, 'Sangat Penting': 5
    }
    averages = {}
    for col in col_list:
        if col in df.columns:
            series = df[col].astype(str).str.strip().str.title().map(mapping)
            if not series.isnull().all():
                # Handling cases where some values might not be in the mapping
                valid_values = series.dropna()
                if not valid_values.empty:
                    averages[col] = valid_values.mean()
    if averages:
        return pd.DataFrame.from_dict(averages, orient='index', columns=['Rata-rata']).sort_index()
    return pd.DataFrame()

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
            # Check if all values are NaN after mapping, if so, skip
            if not series.isnull().all():
                averages[col] = series.mean()
    if averages:
        return pd.DataFrame.from_dict(averages, orient='index', columns=['Rata-rata (Mingguan)']).sort_index()
    return pd.DataFrame()

def calculate_multiselect_counts(df, col_list):
    """Menghitung frekuensi pilihan dari kolom multi-respon."""
    responses = process_multi_response(df, col_list)
    if not responses.empty:
        # Menghapus spasi ekstra dan nilai kosong
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
        
        # --- Analisis Un-aided Awareness (Q1_1-Q2_5) ---
        with st.expander("2. Frekuensi Unaided Awareness (Q1_1, Q2_1 - Q2_5)", expanded=False):
            st.subheader("Frekuensi Un-aided Awareness")
            unaided_cols = ['Q1_1'] + [f'Q2_{i}' for i in range(1, 6)]
            unaided_df = calculate_multiselect_counts(df, unaided_cols)
            
            if not unaided_df.empty:
                st.dataframe(unaided_df, use_container_width=True)
                fig_unaided = px.bar(unaided_df, x='Respons', y='Frekuensi',
                                     title='Frekuensi Un-aided Awareness',
                                     labels={'Respons': 'Restoran', 'Frekuensi': 'Jumlah Responden'},
                                     color='Frekuensi',
                                     color_continuous_scale=px.colors.sequential.YlGnBu)
                st.plotly_chart(fig_unaided, use_container_width=True)
            else:
                st.info("Tidak ada data yang lengkap untuk Un-aided Awareness. Pastikan kolom 'Q1_1' dan 'Q2_1' sampai 'Q2_5' ada.")


        # --- Analisis Total Awareness (Q3_1-Q3_9) ---
        with st.expander("3. Frekuensi Total Awareness (Q3_1-Q3_9)", expanded=False):
            st.subheader("Frekuensi Total Awareness")
            total_awareness_cols = [f'Q3_{i}' for i in range(1, 10)]
            total_awareness_df = calculate_multiselect_counts(df, total_awareness_cols)

            if not total_awareness_df.empty:
                st.dataframe(total_awareness_df, use_container_width=True)
                fig_total = px.bar(total_awareness_df, x='Respons', y='Frekuensi',
                                   title='Frekuensi Total Awareness',
                                   labels={'Respons': 'Pilihan', 'Frekuensi': 'Jumlah Responden'},
                                   color='Frekuensi',
                                   color_continuous_scale=px.colors.sequential.YlGnBu)
                st.plotly_chart(fig_total, use_container_width=True)
            else:
                st.info("Tidak ada data yang lengkap untuk Total Awareness. Pastikan kolom 'Q3_1' sampai 'Q3_9' ada.")


        # --- Brand Image (Q15_1-Q15_8) ---
        with st.expander("6. Brand Image (Q15_1-Q15_8)", expanded=False):
            st.subheader("Frekuensi Brand Image")
            brand_image_cols = [f'Q15_{i}' for i in range(1, 9)]
            brand_image_df = calculate_multiselect_counts(df, brand_image_cols)

            if not brand_image_df.empty:
                st.dataframe(brand_image_df, use_container_width=True)
                fig_brand = px.bar(brand_image_df, x='Respons', y='Frekuensi',
                                   title='Frekuensi Brand Image',
                                   labels={'Respons': 'Pilihan', 'Frekuensi': 'Jumlah Responden'},
                                   color='Frekuensi',
                                   color_continuous_scale=px.colors.sequential.YlGnBu)
                st.plotly_chart(fig_brand, use_container_width=True)
            else:
                st.info("Tidak ada data yang lengkap untuk Brand Image. Pastikan kolom 'Q15_1' sampai 'Q15_8' ada.")

        # --- Analisis Skala Likert ---
        with st.expander("7. Analisis Skala Likert", expanded=False):
            st.subheader("Rata-rata Skor Skala Likert")
            
            # Likert Q16-Q19
            st.markdown("#### Kepuasan (Q16-Q19)")
            likert_cols_1 = [f'Q{i}_{j}' for i in range(16, 20) for j in range(1, 6)]
            likert_avg_df_1 = calculate_likert_average(df, likert_cols_1)
            
            if not likert_avg_df_1.empty:
                st.dataframe(likert_avg_df_1)
                fig_likert_1 = px.bar(likert_avg_df_1, x='Rata-rata', y=likert_avg_df_1.index,
                                    title='Rata-rata Skor Kepuasan (Q16-Q19)',
                                    labels={'x': 'Rata-rata Skor', 'y': 'Pernyataan Survei'},
                                    orientation='h',
                                    color='Rata-rata',
                                    color_continuous_scale=px.colors.sequential.YlGnBu)
                fig_likert_1.update_yaxes(autorange="reversed")
                st.plotly_chart(fig_likert_1, use_container_width=True)
            else:
                st.info("Tidak ada data yang lengkap untuk analisis Kepuasan (Q16-Q19).")

            # Likert Q20-Q24
            st.markdown("#### Penilaian (Q20-Q24)")
            likert_cols_2 = [f'Q{i}_{j}' for i in range(20, 25) for j in range(1, 6)]
            likert_avg_df_2 = calculate_likert_average(df, likert_cols_2)
            
            if not likert_avg_df_2.empty:
                st.dataframe(likert_avg_df_2)
                fig_likert_2 = px.bar(likert_avg_df_2, x='Rata-rata', y=likert_avg_df_2.index,
                                    title='Rata-rata Skor Penilaian (Q20-Q24)',
                                    labels={'x': 'Rata-rata Skor', 'y': 'Pernyataan Survei'},
                                    orientation='h',
                                    color='Rata-rata',
                                    color_continuous_scale=px.colors.sequential.YlGnBu)
                fig_likert_2.update_yaxes(autorange="reversed")
                st.plotly_chart(fig_likert_2, use_container_width=True)
            else:
                st.info("Tidak ada data yang lengkap untuk analisis Penilaian (Q20-Q24).")

            # Likert Q25-Q28
            st.markdown("#### Persetujuan (Q25-Q28)")
            likert_cols_3 = [f'Q{i}_{j}' for i in range(25, 29) for j in range(1, 3)]
            likert_avg_df_3 = calculate_likert_average(df, likert_cols_3)
            
            if not likert_avg_df_3.empty:
                st.dataframe(likert_avg_df_3)
                fig_likert_3 = px.bar(likert_avg_df_3, x='Rata-rata', y=likert_avg_df_3.index,
                                    title='Rata-rata Skor Persetujuan (Q25-Q28)',
                                    labels={'x': 'Rata-rata Skor', 'y': 'Pernyataan Survei'},
                                    orientation='h',
                                    color='Rata-rata',
                                    color_continuous_scale=px.colors.sequential.YlGnBu)
                fig_likert_3.update_yaxes(autorange="reversed")
                st.plotly_chart(fig_likert_3, use_container_width=True)
            else:
                st.info("Tidak ada data yang lengkap untuk analisis Persetujuan (Q25-Q28).")

        # --- Conceptual Mapping (Crosstab) ---
        with st.expander("🗺️ Pemetaan Konseptual (Tabel Silang)"):
            st.subheader("Tabel Silang (Crosstab) & Visualisasi")
            st.write("Pilih 2 parameter untuk membuat tabel silang.")
            
            # Contoh daftar kolom yang relevan untuk crosstab
            likert_cols = [f'Q{i}_{j}' for i in range(16, 29) for j in range(1, 6)]
            frequency_cols = [f'S{i}_{j}' for i in range(9, 13) for j in range(1, 8)] + ['S13', 'S14']
            all_cols = [col for col in df.columns if col in likert_cols or col in frequency_cols]

            # Mengkonversi kolom Likert ke numerik
            df_cleaned = df.copy()
            likert_mapping = {
                'Sangat Tidak Setuju': 1, 'Tidak Setuju': 2, 'Netral': 3, 'Setuju': 4, 'Sangat Setuju': 5,
                'Sangat Tidak Puas': 1, 'Tidak Puas': 2, 'Netral': 3, 'Puas': 4, 'Sangat Puas': 5,
                'Sangat Tidak Penting': 1, 'Tidak Penting': 2, 'Netral': 3, 'Penting': 4, 'Sangat Penting': 5
            }
            for col in likert_cols:
                if col in df_cleaned.columns:
                    df_cleaned[col] = df_cleaned[col].astype(str).str.strip().str.title().map(likert_mapping)
            
            # Mengkonversi kolom frekuensi ke numerik
            freq_mapping = {
                'Setiap hari': 7.0, 'Hampir setiap hari': 6.0, '4~6 kali dalam satu minggu': 5.0,
                '2~3 kali dalam satu minggu': 2.5, '1~2 kali dalam satu minggu': 1.5,
                'Kurang dari 1 kali dalam satu minggu': 0.5, 'Tidak pernah': 0.0,
            }
            for col in frequency_cols:
                if col in df_cleaned.columns:
                    df_cleaned[col] = df_cleaned[col].astype(str).str.strip().str.lower().map(
                        {k.lower(): v for k, v in freq_mapping.items()})

            # Mapping untuk kolom pivot S1 dan S2
            s1_mapping = {'Laki-laki': 'Laki-laki', 'Perempuan': 'Perempuan'}
            s2_mapping = {
                '15 - 19 tahun': '15-19', '20 - 24 tahun': '20-24', '25 - 29 tahun': '25-29', 
                '30 - 34 tahun': '30-34', '35 - 39 tahun': '35-39', '40 - 44 tahun': '40-44', 
                '45 - 49 tahun': '45-49', '50 - 54 tahun': '50-54', '>55 tahun': '>55'
            }
            if 'S1' in df_cleaned.columns:
                df_cleaned['S1'] = df_cleaned['S1'].astype(str).str.strip().map(s1_mapping)
            if 'S2' in df_cleaned.columns:
                df_cleaned['S2'] = df_cleaned['S2'].astype(str).str.strip().map(s2_mapping)

            # Pilihan kolom pivot
            pivot_options = ["Jenis Kelamin (S1)", "Usia (S2)"]
            selected_pivot = st.selectbox("Pilih Parameter Pivot:", options=pivot_options)
            
            if selected_pivot == "Jenis Kelamin (S1)":
                pivot_col = 'S1'
            else:
                pivot_col = 'S2'

            # Pengecekan baru untuk memastikan kolom pivot ada
            if pivot_col in df_cleaned.columns and not df_cleaned[pivot_col].isnull().all():
                numeric_cols_for_crosstab = [col for col in df_cleaned.columns if col in all_cols]
                
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
                        st.info(f"Tidak ada data yang valid untuk membuat tabel silang dengan kolom '{pivot_col}'.")
                else:
                    st.info("Tidak ada kolom numerik yang tersedia untuk analisis tabel silang.")
            else:
                st.info(f"Kolom pivot '{pivot_col}' tidak ditemukan atau tidak memiliki data yang relevan.")


        # --- Analisis Open-Ended (Word Cloud) ---
        with st.expander("☁️ Analisis Teks Terbuka (Word Cloud)"):
            st.subheader("Word Cloud dari Jawaban Terbuka")
            
            # User input for the column name
            open_ended_col = st.text_input(
                "Masukkan nama kolom yang berisi jawaban terbuka (misal: 'Kritik dan Saran'):",
                placeholder="nama_kolom_teks"
            )
        
            if open_ended_col:
                if open_ended_col in df.columns and not df[open_ended_col].isnull().all():
                    # Filter out empty/NaN values
                    text_data = df[open_ended_col].dropna().astype(str)
                    
                    if not text_data.empty:
                        # Combine all text into a single string
                        all_text = " ".join(text_data).lower()
                        
                        # Clean the text (remove non-alphanumeric, etc.) - simple version
                        all_text = re.sub(r'[^a-zA-Z0-9\s]', '', all_text)
                        
                        # Generate the word cloud
                        wordcloud = WordCloud(
                            width=800, height=400,
                            background_color='white',
                            colormap='viridis',
                            random_state=42
                        ).generate(all_text)
                        
                        # Display the word cloud using matplotlib
                        fig, ax = plt.subplots(figsize=(10, 5))
                        ax.imshow(wordcloud, interpolation='bilinear')
                        ax.axis("off")
                        fig.patch.set_facecolor('#F8FAFC')
                        
                        st.pyplot(fig)
                    else:
                        st.info(f"Kolom '{open_ended_col}' tidak berisi data teks yang dapat dianalisis.")
                else:
                    st.info(f"Kolom '{open_ended_col}' tidak ditemukan atau tidak memiliki data. Harap periksa nama kolomnya.")
            else:
                st.info("Masukkan nama kolom teks untuk membuat Word Cloud.")

st.markdown("</div>", unsafe_allow_html=True)
# ==============================================================================
# Dashboard Analisis Survei Restoran
# Analisis Data survei yang kompleks dan multi-respon
# Versi: 3.5 (Penambahan Analisis Likert & Multi-respon)
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
            series = df[col].astype(str).str.strip().str.title().map(mapping)
            if not series.isnull().all():
                averages[col] = series.mean()
    if averages:
        return pd.DataFrame.from_dict(averages, orient='index', columns=['Rata-rata']).sort_index()
    return pd.DataFrame()

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
    if averages:
        return pd.DataFrame.from_dict(averages, orient='index', columns=['Rata-rata (Mingguan)']).sort_index()
    return pd.DataFrame()

def calculate_multiselect_counts(df, col_name, separator=';'):
    """Menghitung frekuensi pilihan dari kolom multi-respon."""
    if col_name in df.columns:
        # Gabungkan semua string, pisahkan, dan hitung frekuensinya
        all_options = df[col_name].dropna().astype(str).str.split(separator).explode().str.strip()
        counts = all_options.value_counts()
        return counts
    return pd.Series(dtype='object')


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

        # --- Visualisasi Demografi ---
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

        # --- Analisis Skala Likert ---
        with st.expander("⭐ Analisis Skala Likert", expanded=False):
            st.subheader("Rata-rata Skor Skala Likert")
            st.info("Edit kode untuk menyesuaikan nama kolom Likert Anda. Contoh: 'S7_1', 'S8_2'.")
            
            # Contoh daftar kolom Likert. Sesuaikan dengan data Anda.
            likert_cols = [f'S7_{i}' for i in range(1, 10)] + [f'S8_{i}' for i in range(1, 8)]
            likert_avg_df = calculate_likert_average(df, likert_cols)

            if not likert_avg_df.empty:
                st.write("Skor Rata-rata:")
                st.dataframe(likert_avg_df)

                fig_likert = px.bar(likert_avg_df, x='Rata-rata', y=likert_avg_df.index,
                                    title='Rata-rata Skor Berdasarkan Skala Likert',
                                    labels={'x': 'Rata-rata Skor', 'y': 'Pernyataan Survei'},
                                    orientation='h',
                                    color='Rata-rata',
                                    color_continuous_scale=px.colors.sequential.YlGnBu)
                fig_likert.update_yaxes(autorange="reversed")
                st.plotly_chart(fig_likert, use_container_width=True)
            else:
                st.info("Tidak ada data yang lengkap untuk analisis skala Likert. Pastikan nama kolom Anda benar.")

        # --- Analisis Multi-respon (Multi-select) ---
        with st.expander("🔗 Analisis Multi-respon", expanded=False):
            st.subheader("Analisis Jawaban Multi-respon")
            
            multi_select_col = st.text_input(
                "Masukkan nama kolom multi-respon (misal: 'S5_multi' atau 'Jenis Promosi'):",
                placeholder="nama_kolom_multi"
            )

            if multi_select_col:
                if multi_select_col in df.columns:
                    counts = calculate_multiselect_counts(df, multi_select_col)
                    
                    if not counts.empty:
                        st.write("Frekuensi Pilihan:")
                        st.dataframe(counts)
                        
                        fig_multi = px.bar(counts, x=counts.index, y=counts.values,
                                          title=f'Frekuensi Pilihan di Kolom "{multi_select_col}"',
                                          labels={'x': 'Pilihan', 'y': 'Frekuensi'},
                                          color=counts.values,
                                          color_continuous_scale=px.colors.sequential.YlGnBu)
                        st.plotly_chart(fig_multi, use_container_width=True)
                    else:
                        st.info(f"Kolom '{multi_select_col}' tidak berisi data yang valid.")
                else:
                    st.error(f"Kolom '{multi_select_col}' tidak ditemukan dalam data Anda.")
            else:
                st.info("Masukkan nama kolom untuk memulai analisis multi-respon.")


        # --- Analisis Frekuensi Utama (S9_x, S10_x, S11_x, S12_x) ---
        with st.expander("📈 Rata-rata Frekuensi Kunjungan", expanded=False):
            st.subheader("Rata-rata Frekuensi (Mingguan)")
            
            # Perbandingan Frekuensi Sebelum vs. Saat Ini (S9 vs S10)
            st.markdown("#### Perbandingan Kebiasaan Makan Sebelum dan Setelah Pandemi")
            
            s9_cols = ['S9_1', 'S9_2', 'S9_3', 'S9_4', 'S9_5', 'S9_6']
            s10_cols = ['S10_1', 'S10_2', 'S10_3', 'S10_4', 'S10_5', 'S10_6']
            
            s9_found = all(col in df.columns for col in s9_cols)
            s10_found = all(col in df.columns for col in s10_cols)

            if s9_found and s10_found:
                s9_avg = calculate_frequency_average(df, s9_cols)
                s10_avg = calculate_frequency_average(df, s10_cols)

                combined_df = pd.DataFrame({
                    'Sebelum Pandemi': s9_avg['Rata-rata (Mingguan)'],
                    'Saat Ini': s10_avg['Rata-rata (Mingguan)']
                })
                combined_df.index = [
                    'Memasak di Rumah', 'Take Away Restoran', 'Take Away Warung', 
                    'Dining In Restoran', 'Dining In Warung', 'Pengantaran Online'
                ]
                
                fig_compare = px.bar(combined_df, x=combined_df.index, y=['Sebelum Pandemi', 'Saat Ini'],
                                     barmode='group',
                                     title='Perbandingan Kebiasaan Makan (Rata-rata Mingguan)',
                                     labels={'x': 'Kebiasaan', 'y': 'Rata-rata Frekuensi'},
                                     color_discrete_map={'Sebelum Pandemi': '#9AC2E9', 'Saat Ini': '#4A90E2'})
                st.plotly_chart(fig_compare, use_container_width=True)
            else:
                st.info("Tidak ada data yang lengkap untuk perbandingan S9 dan S10.")

            # Rata-rata Frekuensi Kunjungan ke Berbagai Jenis Restoran (S11)
            st.markdown("#### Rata-rata Frekuensi Kunjungan Berdasarkan Jenis Restoran")
            s11_cols = [f'S11_{j}' for j in range(1, 8)]
            if all(col in df.columns for col in s11_cols):
                s11_avg = calculate_frequency_average(df, s11_cols)
                s11_avg.index = ['Restoran Jepang', 'Restoran Western', 'Restoran India', 
                                 'Restoran Italia', 'Restoran Cina', 'Restoran Indonesia', 'Restoran Perancis']
                
                fig_s11 = px.bar(s11_avg, y=s11_avg.index, x='Rata-rata (Mingguan)',
                                 title='Rata-rata Frekuensi Kunjungan ke Jenis Restoran',
                                 labels={'y': 'Jenis Restoran', 'Rata-rata (Mingguan)': 'Rata-rata Frekuensi Mingguan'},
                                 orientation='h',
                                 color='Rata-rata (Mingguan)',
                                 color_continuous_scale=px.colors.sequential.YlGnBu)
                fig_s11.update_yaxes(autorange="reversed")
                st.plotly_chart(fig_s11, use_container_width=True)
            else:
                st.info("Tidak ada data yang lengkap untuk analisis jenis restoran (S11).")

        # --- Analisis Frekuensi S13 & S14 ---
        with st.expander("📊 Frekuensi S13 dan S14"):
            st.subheader("Frekuensi Kunjungan (S13, S14)")
            freq_s_cols = ['S13', 'S14']
            
            for col in freq_s_cols:
                if col in df.columns and not df[col].isnull().all():
                    st.markdown(f"**Kolom: {col}**")
                    freq_df = df[col].value_counts().reset_index()
                    freq_df.columns = ['Respons', 'Frekuensi']
                    st.dataframe(freq_df, use_container_width=True)
                    
                    fig_s_freq = px.bar(freq_df, x='Respons', y='Frekuensi',
                                       title=f'Frekuensi {col}',
                                       labels={'Respons': 'Pilihan', 'Frekuensi': 'Jumlah Responden'},
                                       color='Frekuensi',
                                       color_continuous_scale=px.colors.sequential.YlGnBu)
                    st.plotly_chart(fig_s_freq, use_container_width=True)
                else:
                    st.info(f"Tidak ada data untuk kolom {col}.")


        # --- Conceptual Mapping (Crosstab) ---
        with st.expander("🗺️ Pemetaan Konseptual (Tabel Silang)"):
            st.subheader("Tabel Silang (Crosstab) & Visualisasi")
            st.write("Pilih 2 parameter untuk membuat tabel silang.")
            
            # Daftar semua kolom yang relevan
            frequency_cols = [f'S{i}_{j}' for i in range(9, 13) for j in range(1, 8)] + ['S13', 'S14']
            all_numeric_cols = [col for col in frequency_cols if col in df.columns]

            # Membuat DataFrame yang dapat diubah
            data_df = df.copy()

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
                if col in data_df.columns:
                    data_df[col] = data_df[col].astype(str).str.strip().str.lower().map(
                        {k.lower(): v for k, v in freq_mapping.items()})

            # Mapping untuk kolom pivot S1 dan S2
            s1_mapping = {'Laki-laki': 'Laki-laki', 'Perempuan': 'Perempuan'}
            s2_mapping = {
                '15 - 19 tahun': '15-19', '20 - 24 tahun': '20-24', '25 - 29 tahun': '25-29', 
                '30 - 34 tahun': '30-34', '35 - 39 tahun': '35-39', '40 - 44 tahun': '40-44', 
                '45 - 49 tahun': '45-49', '50 - 54 tahun': '50-54', '>55 tahun': '>55'
            }
            if 'S1' in data_df.columns:
                data_df['S1'] = data_df['S1'].astype(str).str.strip().map(s1_mapping)
            if 'S2' in data_df.columns:
                data_df['S2'] = data_df['S2'].astype(str).str.strip().map(s2_mapping)

            pivot_options = ["Jenis Kelamin (S1)", "Usia (S2)"]
            selected_pivot = st.selectbox("Pilih Parameter Pivot:", options=pivot_options)
            
            if selected_pivot == "Jenis Kelamin (S1)":
                pivot_col = 'S1'
            else:
                pivot_col = 'S2'
            
            # Pengecekan baru untuk memastikan kolom pivot ada dan tidak kosong
            if pivot_col in data_df.columns and not data_df[pivot_col].isnull().all() and all_numeric_cols:
                # Perbaikan utama: Menggunakan pd.to_numeric untuk konversi yang lebih aman
                for col in all_numeric_cols:
                    data_df[col] = pd.to_numeric(data_df[col], errors='coerce')

                # Filter baris yang relevan untuk pivot
                data_df_clean = data_df.dropna(subset=[pivot_col] + all_numeric_cols)

                if not data_df_clean.empty:
                    pivot_table = data_df_clean.groupby(pivot_col)[all_numeric_cols].mean()
                    
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
            st.subheader("Word Cloud dari Jawaban Terbuka")
            
            # User input for the column name
            open_ended_col = st.text_input(
                "Masukkan nama kolom yang berisi jawaban terbuka (misal: 'Q15_text' atau 'Kritik dan Saran'):",
                placeholder="nama_kolom_teks"
            )
        
            if open_ended_col:
                if open_ended_col in df.columns and not df[open_ended_col].isnull().all():
                    # Filter out empty/NaN values
                    text_data = df[open_ended_col].dropna().astype(str)
                    
                    if not text_data.empty:
                        # Combine all text into a single string
                        all_text = " ".join(text_data).lower()
                        
                        # Clean the text (remove non-alphanumeric, etc.) - simple version
                        all_text = re.sub(r'[^a-zA-Z0-9\s]', '', all_text)
                        
                        # Generate the word cloud
                        wordcloud = WordCloud(
                            width=800, height=400,
                            background_color='white',
                            colormap='viridis',
                            random_state=42
                        ).generate(all_text)
                        
                        # Display the word cloud using matplotlib
                        fig, ax = plt.subplots(figsize=(10, 5))
                        ax.imshow(wordcloud, interpolation='bilinear')
                        ax.axis("off")
                        fig.patch.set_facecolor('#F8FAFC')
                        
                        st.pyplot(fig)
                    else:
                        st.info(f"Kolom '{open_ended_col}' tidak berisi data teks yang dapat dianalisis.")
                else:
                    st.info(f"Kolom '{open_ended_col}' tidak ditemukan atau tidak memiliki data. Harap periksa nama kolomnya.")
            else:
                st.info("Masukkan nama kolom teks untuk membuat Word Cloud.")

st.markdown("</div>", unsafe_allow_html=True)
