# ==============================================================================
# Dashboard Analisis Survei Restoran
# ==============================================================================

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import re
import numpy as np

# --- 2. Konfigurasi Halaman ---
st.set_page_config(
    page_title="Dashboard Analisis Survei Restoran",
    page_icon="📊",
    layout="wide"
)

# --- CSS Kustom ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
    .stApp { background-color: #F0F4F8; font-family: 'Poppins', sans-serif; }
    .main-column { background-color: #FFFFFF; border-radius: 20px; padding: 2rem; box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.07); }
    .header-title { font-size: 2.5em; font-weight: 700; color: #1E293B; padding-bottom: 0.1rem; }
    .header-subtitle { font-size: 1.1em; color: #64748B; font-weight: 400; padding-bottom: 2rem; }
    h3 { color: #334155; font-weight: 600; margin-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)

# --- Fungsi-fungsi Bantuan ---
@st.cache_data
def load_data(uploaded_file=None):
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(uploaded_file)
            else:
                st.error("Tipe file tidak didukung.")
                return pd.DataFrame()
            return df
        except Exception as e:
            st.error(f"Gagal memuat data. Error: {e}")
            return pd.DataFrame()
    else:
        # Demo Data
        df = pd.DataFrame({
            'Q1_1': ['KFC','McD','HokBen','KFC','Pizza Hut']*20,
            'Q2_1': ['Burger King', np.nan, 'Burger King', np.nan, 'Burger King']*20,
            'Q3_1': ['KFC','KFC']*50,
            'Q15_1': ['Sangat Setuju','Setuju','Sangat Setuju','Netral','Setuju']*20,
            'Q16_1': ['Sangat Penting','Penting','Sangat Penting','Netral','Penting']*20,
            'Q20_1': ['Sangat Puas','Puas','Netral','Puas','Sangat Tidak Puas']*20,
            'Q25_1': ['Sangat Setuju','Netral','Setuju','Sangat Setuju','Netral']*20,
            'S1': ['Laki-laki','Perempuan']*50,
            'S2': ['25 - 29 tahun','30 - 34 tahun']*50
        })
        return df


def process_multi_response(df, prefix_list):
    responses = pd.Series([], dtype='object')
    for col_prefix in prefix_list:
        cols_to_combine = [c for c in df.columns if c.startswith(col_prefix) and '_' in c]
        if not cols_to_combine:
            continue
        combined = df[cols_to_combine].stack().dropna().reset_index(drop=True)
        responses = pd.concat([responses, combined], ignore_index=True)
    return responses


def calculate_likert_average(df, col_list):
    mapping = {
        'Sangat Tidak Setuju':1,'Tidak Setuju':2,'Netral':3,'Setuju':4,'Sangat Setuju':5,
        'Sangat Tidak Penting':1,'Tidak Penting':2,'Netral':3,'Penting':4,'Sangat Penting':5,
        'Sangat Tidak Puas':1,'Tidak Puas':2,'Netral':3,'Puas':4,'Sangat Puas':5
    }
    averages = {}
    for col in col_list:
        if col in df:
            series = df[col].map(mapping)
            if series.notna().any():
                averages[col] = series.mean()
    return pd.DataFrame.from_dict(averages, orient='index', columns=['Rata-rata']).sort_index()

# --- Sidebar Upload ---
st.sidebar.title("Opsi Data")
uploaded_file = st.sidebar.file_uploader("Unggah file survei Anda", type=['csv','xlsx'])

df = load_data(uploaded_file)

if not df.empty:
    st.markdown("<div class='main-column'>", unsafe_allow_html=True)
    st.markdown("<div class='header-title'>Dashboard Analisis Survei Restoran</div>", unsafe_allow_html=True)
    st.markdown("<div class='header-subtitle'>Analisis Mendalam dari Respon Konsumen</div>", unsafe_allow_html=True)

    # --- Top of Mind ---
    with st.expander("📊 Frekuensi & Persentase (Top of Mind & Unaided)", expanded=True):
        if 'Q1_1' in df:
            q1_freq = df['Q1_1'].value_counts().reset_index()
            q1_freq.columns = ['Restoran','Frekuensi']
            q1_freq['Persentase'] = (q1_freq['Frekuensi']/len(df)*100).round(2)
            st.dataframe(q1_freq)

        if any(col in df for col in ['Q1_1','Q2_1']):
            q1_series = df['Q1_1'].dropna() if 'Q1_1' in df else pd.Series([],dtype='object')
            unaided = pd.concat([q1_series, process_multi_response(df,['Q2'])], ignore_index=True)
            unaided_freq = unaided.value_counts().reset_index()
            unaided_freq.columns = ['Restoran','Frekuensi']
            st.dataframe(unaided_freq)

    # --- Brand Image ---
    with st.expander("🖼️ Brand Image"):
        for col in [c for c in df if c.startswith('Q15_')]:
            if not df[col].isna().all():
                freq_data = df[col].value_counts().reset_index()
                freq_data.columns = ['Respons','Frekuensi']
                st.write(f"**{col}**")
                st.dataframe(freq_data)

    # --- Likert ---
    with st.expander("📊 Rata-rata Skala Likert"):
        importance = calculate_likert_average(df,[c for c in df if c.startswith('Q16') or c.startswith('Q17') or c.startswith('Q18') or c.startswith('Q19')])
        satisfaction = calculate_likert_average(df,[c for c in df if c.startswith('Q20') or c.startswith('Q21') or c.startswith('Q22') or c.startswith('Q23') or c.startswith('Q24')])
        agreement = calculate_likert_average(df,[c for c in df if c.startswith('Q25') or c.startswith('Q26') or c.startswith('Q27') or c.startswith('Q28')])

        st.subheader("Visualisasi Rata-rata Likert")
        likert_avgs = pd.concat(
            [importance.T, satisfaction.T, agreement.T],
            keys=["Kepentingan","Kepuasan","Persesuaian"]
        )
        fig, ax = plt.subplots(figsize=(12,6))
        likert_avgs.T.plot(kind='bar', ax=ax, rot=45)
        st.pyplot(fig)
