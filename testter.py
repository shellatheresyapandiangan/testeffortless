# ==============================================================================

# Dashboard Analisis Survei Restoran

# Analisis Data survei yang kompleks dan multi-respon

# ==============================================================================



# --- 1. Impor Library ---

import streamlit as st

import pandas as pd

import matplotlib.pyplot as plt



import seaborn as sns

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

def load_data(uploaded_file=None):

    if uploaded_file is not None:

        try:

            if uploaded_file.name.endswith('.csv'):

                df = pd.read_csv(uploaded_file)

            elif uploaded_file.name.endswith(('.xls', '.xlsx')):

                df = pd.read_excel(uploaded_file)

            else:

                st.error("Tipe file tidak didukung. Unggah file CSV atau Excel.")

                return pd.DataFrame()

            return df

        except Exception as e:

            st.error(f"Gagal memuat data dari file. Error: {e}")

            return pd.DataFrame()

    else:

        # Data demo jika tidak ada file yang diunggah

        cols = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9_1', 'S9_2', 'S9_3', 'S9_4', 'S9_5', 'S9_6', 'S10_1', 'S10_2', 'S10_3', 'S10_4', 'S10_5', 'S10_6', 'S11_1', 'S11_2', 'S11_3', 'S11_4', 'S11_5', 'S11_6', 'S11_7', 'S12_1', 'S12_2', 'S13', 'S14', 'S15_1', 'S15_2', 'S15_3', 'S15_4', 'Q1_1', 'Q2_1', 'Q2_2', 'Q2_3', 'Q2_4', 'Q2_5', 'Q3_1', 'Q3_2', 'Q3_3', 'Q3_4', 'Q3_5', 'Q3_6', 'Q3_7', 'Q3_8', 'Q3_9', 'Q4_1', 'Q4_2', 'Q4_3', 'Q4_4', 'Q4_5', 'Q4_6', 'Q4_7', 'Q4_8', 'Q4_9', 'Q5', 'Q6_1', 'Q6_2', 'Q6_3', 'Q7_1', 'Q7_2', 'Q7_3', 'Q7_4', 'Q7_5', 'Q7_6', 'Q7_7', 'Q7_8', 'Q7_9', 'Q7_10', 'Q7_11', 'Q7_12', 'Q7_13', 'Q7_14', 'Q7_15', 'Q8', 'Q9_1', 'Q9_2', 'Q9_3', 'Q9_4', 'Q9_5', 'Q9_6', 'Q9_7', 'Q9_8', 'Q9_9', 'Q9_10', 'Q9_11', 'Q9_12', 'Q9_13', 'Q9_14', 'Q9_15', 'Q9_16', 'Q10_1', 'Q10_2', 'Q10_3', 'Q10_4', 'Q10_5', 'Q10_6', 'Q10_7', 'Q10_8', 'Q10_9', 'Q10_10', 'Q10_11', 'Q10_12', 'Q10_13', 'Q10_14', 'Q10_15', 'Q10_16', 'Q11', 'Q12_1', 'Q12_2', 'Q12_3', 'Q13_1', 'Q13_2', 'Q13_3', 'Q13_4', 'Q13_5', 'Q13_6', 'Q13_7', 'Q13_8', 'Q13_9', 'Q13_10', 'Q13_11', 'Q13_12', 'Q13_13', 'Q13_14', 'Q13_15', 'Q14', 'Q15_1', 'Q15_2', 'Q15_3', 'Q15_4', 'Q15_5', 'Q15_6', 'Q15_7', 'Q15_8', 'Q16_1', 'Q16_2', 'Q16_3', 'Q16_4', 'Q17_1', 'Q17_2', 'Q17_3', 'Q18', 'Q19_1', 'Q19_2', 'Q19_3', 'Q19_4', 'Q19_5', 'Q20_1', 'Q20_2', 'Q20_3', 'Q20_4', 'Q21_1', 'Q21_2', 'Q21_3', 'Q23', 'Q24_1', 'Q24_2', 'Q24_3', 'Q24_4', 'Q24_5', 'Q25_1', 'Q25_2', 'Q26_1', 'Q26_2', 'Q26_3', 'Q26_4', 'Q27_1', 'Q27_2', 'Q27_3', 'Q28_1', 'Q28_2', 'Q29', 'Q30_1', 'Q30_2', 'Q30_3', 'Q30_4', 'Q30_5', 'Q30_6', 'Q30_7', 'Q30_8', 'Q30_9', 'Q30_10', 'Q31', 'Q32_1', 'Q32_2', 'Q32_3', 'Q32_4', 'Q32_5', 'Q32_6', 'Q32_7', 'Q32_8', 'Q32_9', 'Q32_10', 'Q33', 'Q34_1', 'Q34_2', 'Q34_3', 'Q34_4', 'Q34_5', 'Q34_6', 'Q34_7', 'Q34_8', 'Q34_9', 'Q34_10', 'Q34_11', 'Q34_12', 'Q34_13', 'Q34_14', 'Q34_15', 'Q34_16', 'Q35_1', 'Q35_2', 'Q35_3', 'Q35_4', 'Q35_5', 'Q35_6', 'Q36_1', 'Q36_2', 'Q36_3', 'Q36_4', 'Q36_5', 'Q36_6', 'Q37_1', 'Q37_2', 'Q37_3', 'Q37_4', 'Q37_5', 'Q37_6', 'Q37_7', 'Q37_8', 'Q37_9', 'Q37_10', 'Name', 'Company', 'Address', 'Address 2', 'City/Town', 'State/Province', 'ZIP/Postal Code', 'Country', 'Email Address', 'Phone Number']

        data = {

            'S1': ['Laki-laki', 'Perempuan'] * 50,

            'S2': ['45 - 49 tahun', '25 - 29 tahun', '30 - 34 tahun', '20 - 24 tahun', '40 - 44 tahun'] * 20,

            'S3': ['Menikah - punya anak', 'Belum menikah'] * 50,

            'Q1_1': ['KFC', 'McD', 'HokBen', 'KFC', 'Pizza Hut'] * 20,

            'Q2_1': ['Burger King', np.nan, 'Burger King', np.nan, 'Burger King'] * 20,

            'Q2_2': ['Solaria', 'Solaria', np.nan, 'Solaria', np.nan] * 20,

            'Q2_3': [np.nan, 'Sate Khas Senayan', 'Sate Khas Senayan', np.nan, 'Sate Khas Senayan'] * 20,

            'Q2_4': ['Yoshinoya', np.nan, 'Yoshinoya', np.nan, 'Yoshinoya'] * 20,

            'Q2_5': [np.nan] * 100,

            'Q3_1': ['KFC', 'KFC'] * 50,

            'Q3_2': ['McD', 'McD'] * 50,

            'Q3_3': ['Pizza Hut', 'Pizza Hut'] * 50,

            'Q3_4': ['HokBen', 'HokBen'] * 50,

            'Q3_5': ['Solaria', 'Solaria'] * 50,

            'Q3_6': [np.nan] * 100,

            'Q3_7': [np.nan] * 100,

            'Q3_8': [np.nan] * 100,

            'Q3_9': [np.nan] * 100,

            'Q15_1': ['Sangat Setuju', 'Setuju', 'Sangat Setuju', 'Netral', 'Setuju'] * 20,

            'Q15_2': ['Setuju', 'Sangat Tidak Setuju', 'Netral', 'Setuju', 'Tidak Setuju'] * 20,

            'Q15_3': ['Sangat Setuju', 'Sangat Setuju', 'Netral', 'Sangat Setuju', 'Netral'] * 20,

            'Q15_4': ['Setuju', 'Netral', 'Sangat Setuju', 'Setuju', 'Sangat Tidak Setuju'] * 20,

            'Q15_5': ['Setuju', 'Tidak Setuju', 'Netral', 'Setuju', 'Setuju'] * 20,

            'Q15_6': ['Sangat Setuju', 'Setuju', 'Sangat Tidak Setuju', 'Setuju', 'Netral'] * 20,

            'Q15_7': ['Setuju', 'Sangat Setuju', 'Setuju', 'Tidak Setuju', 'Sangat Setuju'] * 20,

            'Q15_8': ['Tidak Setuju', 'Netral', 'Sangat Setuju', 'Tidak Setuju', 'Netral'] * 20,

            'Q16_1': ['Sangat Penting', 'Penting', 'Sangat Penting', 'Netral', 'Penting'] * 20,

            'Q16_2': ['Penting', 'Sangat Tidak Penting', 'Netral', 'Penting', 'Tidak Penting'] * 20,

            'Q16_3': ['Sangat Penting', 'Sangat Penting', 'Netral', 'Sangat Penting', 'Netral'] * 20,

            'Q16_4': ['Penting', 'Netral', 'Sangat Penting', 'Penting', 'Sangat Tidak Penting'] * 20,

            'Q17_1': ['Sangat Penting', 'Tidak Penting', 'Netral', 'Sangat Penting', 'Penting'] * 20,

            'Q17_2': ['Penting', 'Sangat Penting', 'Penting', 'Tidak Penting', 'Sangat Penting'] * 20,

            'Q17_3': ['Sangat Tidak Penting', 'Netral', 'Sangat Penting', 'Tidak Penting', 'Netral'] * 20,

            'Q18': ['Sangat Penting', 'Penting', 'Netral', 'Tidak Penting', 'Sangat Tidak Penting'] * 20,

            'Q19_1': ['Sangat Penting', 'Penting', 'Sangat Penting', 'Netral', 'Penting'] * 20,

            'Q19_2': ['Penting', 'Sangat Tidak Penting', 'Netral', 'Penting', 'Tidak Penting'] * 20,

            'Q19_3': ['Sangat Penting', 'Sangat Penting', 'Netral', 'Sangat Penting', 'Netral'] * 20,

            'Q19_4': ['Penting', 'Netral', 'Sangat Penting', 'Penting', 'Sangat Tidak Penting'] * 20,

            'Q19_5': ['Sangat Penting', 'Tidak Penting', 'Netral', 'Sangat Penting', 'Penting'] * 20,

            'Q20_1': ['Sangat Puas', 'Puas', 'Netral', 'Puas', 'Sangat Tidak Puas'] * 20,

            'Q20_2': ['Puas', 'Tidak Puas', 'Sangat Puas', 'Puas', 'Netral'] * 20,

            'Q20_3': ['Sangat Puas', 'Netral', 'Tidak Puas', 'Sangat Puas', 'Netral'] * 20,

            'Q20_4': ['Tidak Puas', 'Netral', 'Sangat Puas', 'Tidak Puas', 'Netral'] * 20,

            'Q21_1': ['Puas', 'Sangat Puas', 'Puas', 'Tidak Puas', 'Sangat Puas'] * 20,

            'Q21_2': ['Sangat Tidak Puas', 'Tidak Puas', 'Sangat Puas', 'Tidak Puas', 'Netral'] * 20,

            'Q21_3': ['Sangat Puas', 'Puas', 'Netral', 'Sangat Puas', 'Puas'] * 20,

            'Q23': [1, 2, 3, 4, 5] * 20,

            'Q24_1': ['Sangat Puas', 'Puas', 'Netral', 'Tidak Puas', 'Sangat Tidak Puas'] * 20,

            'Q24_2': ['Sangat Puas', 'Netral', 'Sangat Tidak Puas', 'Puas', 'Netral'] * 20,

            'Q24_3': ['Puas', 'Sangat Puas', 'Puas', 'Sangat Tidak Puas', 'Tidak Puas'] * 20,

            'Q24_4': ['Netral', 'Tidak Puas', 'Sangat Puas', 'Netral', 'Sangat Puas'] * 20,

            'Q24_5': ['Puas', 'Netral', 'Puas', 'Tidak Puas', 'Sangat Tidak Puas'] * 20,

            'Q25_1': ['Sangat Setuju', 'Netral', 'Setuju', 'Sangat Setuju', 'Netral'] * 20,

            'Q25_2': ['Setuju', 'Sangat Setuju', 'Netral', 'Sangat Tidak Setuju', 'Setuju'] * 20,

            'Q26_1': ['Sangat Setuju', 'Netral', 'Tidak Setuju', 'Setuju', 'Sangat Tidak Setuju'] * 20,

            'Q26_2': ['Setuju', 'Sangat Setuju', 'Netral', 'Tidak Setuju', 'Setuju'] * 20,

            'Q26_3': ['Sangat Setuju', 'Netral', 'Setuju', 'Sangat Setuju', 'Netral'] * 20,

            'Q26_4': ['Setuju', 'Setuju', 'Sangat Setuju', 'Netral', 'Setuju'] * 20,

            'Q27_1': ['Sangat Setuju', 'Netral', 'Tidak Setuju', 'Setuju', 'Sangat Tidak Setuju'] * 20,

            'Q27_2': ['Sangat Setuju', 'Netral', 'Setuju', 'Sangat Setuju', 'Netral'] * 20,

            'Q27_3': ['Setuju', 'Sangat Setuju', 'Netral', 'Sangat Tidak Setuju', 'Setuju'] * 20,

            'Q28_1': ['Sangat Setuju', 'Netral', 'Tidak Setuju', 'Setuju', 'Sangat Tidak Setuju'] * 20,

            'Q28_2': ['Setuju', 'Sangat Setuju', 'Netral', 'Tidak Setuju', 'Setuju'] * 20,

        }

        missing_cols = [col for col in cols if col not in data]

        for col in missing_cols:

            data[col] = np.nan

        

        df = pd.DataFrame(data)

        return df[cols]



def process_multi_response(df, prefix_list):

    responses = pd.Series(dtype='object')

    for col_prefix in prefix_list:

        cols_to_combine = [col for col in df.columns if col.startswith(col_prefix) and '_' in col]

        if not cols_to_combine: continue

        combined_series = df[cols_to_combine].stack().dropna().reset_index(drop=True)

        responses = pd.concat([responses, combined_series], ignore_index=True)

    return responses



def calculate_likert_average(df, col_list):

    mapping = {

        'Sangat Tidak Setuju': 1, 'Tidak Setuju': 2, 'Netral': 3, 'Setuju': 4, 'Sangat Setuju': 5,

        'Sangat Tidak Penting': 1, 'Tidak Penting': 2, 'Netral': 3, 'Penting': 4, 'Sangat Penting': 5,

        'Sangat Tidak Puas': 1, 'Tidak Puas': 2, 'Netral': 3, 'Puas': 4, 'Sangat Puas': 5

    }

    averages = {}

    existing_cols = [col for col in col_list if col in df.columns]

    

    for col in existing_cols:

        series = df[col].map(mapping)

        if not series.isnull().all():

            averages[col] = series.mean()

    return pd.DataFrame.from_dict(averages, orient='index', columns=['Rata-rata']).sort_index()



# --- 4. Logika Utama Aplikasi ---

st.sidebar.title("Opsi Data")

uploaded_file = st.sidebar.file_uploader("Unggah file survei Anda (CSV atau XLSX)", type=['csv', 'xlsx'])



df = load_data(uploaded_file)



if not df.empty:

    st.markdown("<div class='main-column'>", unsafe_allow_html=True)

    st.markdown("<div class='header-title'>Dashboard Analisis Survei Restoran</div>", unsafe_allow_html=True)

    st.markdown("<div class='header-subtitle'>Analisis Mendalam dari Respon Konsumen</div>", unsafe_allow_html=True)

    

    # --- Analisis Top of Mind & Unaided Awareness ---

    with st.expander("📊 Frekuensi & Persentase (Top of Mind & Unaided)", expanded=True):

        col1, col2 = st.columns(2)

        with col1:

            st.subheader("Frekuensi Top of Mind (Q1_1)")

            if 'Q1_1' in df.columns:

                q1_freq = df['Q1_1'].value_counts().reset_index()

                q1_freq.columns = ['Restoran', 'Frekuensi']

                q1_freq['Persentase'] = (q1_freq['Frekuensi'] / len(df) * 100).round(2)

                st.dataframe(q1_freq, use_container_width=True)



                fig, ax = plt.subplots(figsize=(10, 6))

                sns.barplot(x='Frekuensi', y='Restoran', data=q1_freq, palette='viridis', ax=ax)

                ax.set_title('Top of Mind Frequency', fontsize=16)

                ax.set_xlabel('Frekuensi', fontsize=12)

                ax.set_ylabel('Restoran', fontsize=12)

                st.pyplot(fig)

            else:

                st.info("Kolom Q1_1 tidak ditemukan.")

        

        with col2:

            st.subheader("Frekuensi Unaided Awareness (Q1_1, Q2_1 - Q2_5)")

            if any(col in df.columns for col in ['Q1_1', 'Q2_1', 'Q2_2', 'Q2_3', 'Q2_4', 'Q2_5']):

                unaided_combined = pd.concat([df['Q1_1'].dropna() if 'Q1_1' in df.columns else pd.Series(), process_multi_response(df, ['Q2'])], ignore_index=True)

                unaided_freq = unaided_combined.value_counts().reset_index()

                unaided_freq.columns = ['Restoran', 'Frekuensi']

                st.dataframe(unaided_freq, use_container_width=True)

                

                fig, ax = plt.subplots(figsize=(10, 6))

                sns.barplot(x='Frekuensi', y='Restoran', data=unaided_freq, palette='magma', ax=ax)

                ax.set_title('Unaided Awareness Frequency', fontsize=16)

                ax.set_xlabel('Frekuensi', fontsize=12)

                ax.set_ylabel('Restoran', fontsize=12)

                st.pyplot(fig)

            else:

                st.info("Kolom untuk unaided awareness tidak ditemukan.")



    # --- Analisis Total Awareness ---

    with st.expander("📈 Total Awareness"):

        st.subheader("Frekuensi Total Awareness (Q3_1 - Q3_9)")

        if any(col in df.columns for col in ['Q3_1', 'Q3_2', 'Q3_3', 'Q3_4', 'Q3_5']):

            total_awareness_combined = process_multi_response(df, ['Q3'])

            total_awareness_freq = total_awareness_combined.value_counts().reset_index()

            total_awareness_freq.columns = ['Restoran', 'Frekuensi']

            

            col1, col2 = st.columns(2)

            with col1:

                st.dataframe(total_awareness_freq, use_container_width=True)

            with col2:

                fig, ax = plt.subplots(figsize=(10, 6))

                sns.barplot(x='Frekuensi', y='Restoran', data=total_awareness_freq, palette='plasma', ax=ax)

                ax.set_title('Total Awareness Frequency', fontsize=16)

                ax.set_xlabel('Frekuensi', fontsize=12)

                ax.set_ylabel('Restoran', fontsize=12)

                st.pyplot(fig)

        else:

            st.info("Kolom untuk total awareness tidak ditemukan.")



    # --- Analisis Brand Image ---

    with st.expander("🖼️ Brand Image"):

        st.subheader("Frekuensi Brand Image (Q15_1 - Q15_8)")

        brand_image_cols = [f'Q15_{i}' for i in range(1, 9)]

        

        for col in brand_image_cols:

            if col in df.columns and not df[col].isnull().all():

                st.markdown(f"**{col}:**")

                

                # --- Perbaikan: Pastikan nama kolom 'Respons' dan 'Frekuensi' sudah benar ---

                freq_data = df[col].value_counts().reset_index().rename(columns={'index': 'Respons', 'count': 'Frekuensi'})

                

                col1, col2 = st.columns(2)

                with col1:

                    st.dataframe(freq_data, use_container_width=True)

                with col2:

                    fig, ax = plt.subplots(figsize=(8, 5))

                    sns.barplot(x='Frekuensi', y='Respons', data=freq_data, palette='coolwarm', ax=ax)

                    ax.set_title(f'Frekuensi {col}', fontsize=14)

                    st.pyplot(fig)

            else:

                st.info(f"Tidak ada data untuk kolom {col}.")

    

    # --- Analisis Skala Likert (Rata-rata) ---

    with st.expander("📊 Rata-rata Skala Likert"):

        col1, col2, col3 = st.columns(3)

        

        # Tingkat Kepentingan (Q16_1 - Q19_5)

        with col1:

            st.subheader("1. Tingkat Kepentingan")

            importance_cols = [f'Q{i}_{j}' for i in range(16, 20) for j in range(1, 6)]

            importance_avg = calculate_likert_average(df, importance_cols)

            st.dataframe(importance_avg.style.background_gradient(cmap='YlGnBu').format(precision=2), use_container_width=True)



        # Tingkat Kepuasan (Q20_1 - Q24_5)

        with col2:

            st.subheader("2. Tingkat Kepuasan")

            satisfaction_cols = [f'Q{i}_{j}' for i in range(20, 25) for j in range(1, 6)]

            satisfaction_avg = calculate_likert_average(df, satisfaction_cols)

            st.dataframe(satisfaction_avg.style.background_gradient(cmap='YlOrRd').format(precision=2), use_container_width=True)



        # Tingkat Persesuaian (Q25_1 - Q28_2)

        with col3:

            st.subheader("3. Tingkat Persesuaian")

            agreement_cols = [f'Q{i}_{j}' for i in range(25, 29) for j in range(1, 5)]

            agreement_avg = calculate_likert_average(df, agreement_cols)

            st.dataframe(agreement_avg.style.background_gradient(cmap='PuBu').format(precision=2), use_container_width=True)



        st.subheader("Visualisasi Rata-rata Likert")

        likert_avgs = pd.concat([importance_avg.T, satisfaction_avg.T, agreement_avg.T])

        

        fig, ax = plt.subplots(figsize=(15, 8))

        likert_avgs.T.plot(kind='bar', ax=ax, rot=45, cmap='cividis')

        ax.set_title('Rata-rata Skala Likert Berdasarkan Kategori', fontsize=16)

        ax.set_ylabel('Rata-rata Skor', fontsize=12)

        ax.set_xlabel('Pertanyaan', fontsize=12)

        plt.tight_layout()

        st.pyplot(fig)

    

    # --- Conceptual Mapping (Crosstab) ---

    with st.expander("🗺️ Pemetaan Konseptual (Tabel Silang)"):

        st.subheader("Tabel Silang (Crosstab)")

        st.write("Pilih 2 parameter untuk membuat tabel silang. Data yang akan digunakan adalah dari Skala Likert.")

        

        all_likert_cols = [

            col for col in df.columns if re.match(r'Q(1[5-9]|2[0-8])_\d+', col)

        ]

        

        likert_df = df[['S1', 'S2'] + all_likert_cols].copy()

        

        likert_mapping = {

            'Sangat Tidak Setuju': 1, 'Tidak Setuju': 2, 'Netral': 3, 'Setuju': 4, 'Sangat Setuju': 5,

            'Sangat Tidak Penting': 1, 'Tidak Penting': 2, 'Netral': 3, 'Penting': 4, 'Sangat Penting': 5,

            'Sangat Tidak Puas': 1, 'Tidak Puas': 2, 'Netral': 3, 'Puas': 4, 'Sangat Puas': 5

        }

        

        for col in all_likert_cols:

            likert_df[col] = likert_df[col].map(likert_mapping)

        

        likert_options = ["Tingkat Kepentingan", "Tingkat Kepuasan", "Tingkat Persesuaian"]

        pivot_options = ["Jenis Kelamin (S1)", "Usia (S2)"]

        

        selected_likert = st.selectbox("Pilih Tipe Analisis:", options=likert_options)

        selected_pivot = st.selectbox("Pilih Parameter Pivot:", options=pivot_options)

        

        if selected_likert == "Tingkat Kepentingan":

            cols_to_pivot = [col for col in all_likert_cols if re.match(r'Q(1[6-9])_\d+', col)]

        elif selected_likert == "Tingkat Kepuasan":

            cols_to_pivot = [col for col in all_likert_cols if re.match(r'Q(2[0-4])_\d+', col)]

        else:

            cols_to_pivot = [col for col in all_likert_cols if re.match(r'Q(2[5-8])_\d+', col)]

        

        if selected_pivot == "Jenis Kelamin (S1)":

            pivot_col = 'S1'

        else:

            pivot_col = 'S2'

        

        if pivot_col in likert_df.columns and cols_to_pivot:

            pivot_table = likert_df.groupby(pivot_col)[cols_to_pivot].mean().T

            pivot_table.columns = pivot_table.columns.astype(str)

            

            st.dataframe(pivot_table.style.background_gradient(cmap='viridis', axis=None).format(precision=2), use_container_width=True)

            

            fig, ax = plt.subplots(figsize=(15, 8))

            pivot_table.plot(kind='bar', ax=ax, rot=45)

            ax.set_title(f'Tabel Silang {selected_likert} berdasarkan {selected_pivot}', fontsize=16)

            ax.set_ylabel('Rata-rata Skor', fontsize=12)

            plt.tight_layout()

            st.pyplot(fig)

        else:

            st.info("Kolom yang dipilih tidak ditemukan dalam data.")



    st.markdown("</div>", unsafe_allow_html=True)

else:

    st.info("Silakan unggah file data atau gunakan data demo yang telah disediakan.")
