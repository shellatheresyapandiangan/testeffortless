# ==============================================================================
# Dashboard Analisis Survei Restoran
# Analisis Data survei yang kompleks dan multi-respon
# Versi: 4.1 (Perbaikan koneksi API)
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
import json
import requests

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

def calculate_multiselect_counts(df, col_list):
    """Menghitung frekuensi pilihan dari kolom multi-respon."""
    responses = process_multi_response(df, col_list)
    if not responses.empty:
        responses = responses.str.strip().replace('', np.nan).dropna()
        return responses.value_counts().reset_index().rename(columns={'index': 'Respons', 0: 'Frekuensi'})
    return pd.DataFrame()

def call_gemini_api_for_summary(data_str, api_key):
    """
    Memanggil API Gemini untuk menghasilkan ringkasan naratif dari data.
    """
    if not api_key:
        return "Masukkan kunci API Gemini Anda untuk membuat ringkasan."

    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={api_key}"

    system_prompt = "Act as a professional data analyst. Provide a concise, single-paragraph summary of the key findings from the provided survey data. Focus on top-level insights about awareness, satisfaction, and key demographic trends. Write the summary in a professional but easy-to-understand tone. The summary must be in Indonesian."
    user_query = f"Berikut adalah ringkasan poin-poin data utama dari survei restoran. Tolong tulis ringkasan profesional dari temuan-temuan ini:\n\n{data_str}"

    payload = {
        "contents": [{"parts": [{"text": user_query}]}],
        "systemInstruction": {"parts": [{"text": system_prompt}]},
    }

    try:
        response = requests.post(api_url, headers={'Content-Type': 'application/json'}, json=payload)
        response.raise_for_status() # Tangani error HTTP

        result = response.json()
        
        if result and 'candidates' in result and len(result['candidates']) > 0:
            text = result['candidates'][0]['content']['parts'][0]['text']
            return text
        else:
            st.error("AI tidak dapat menghasilkan ringkasan. Respons dari API tidak valid.")
            return None
    except requests.exceptions.HTTPError as http_err:
        if http_err.response.status_code == 400:
            st.error("Terjadi kesalahan pada API: Permintaan tidak valid. Mohon periksa kembali data atau formatnya.")
        elif http_err.response.status_code == 401:
            st.error("Terjadi kesalahan pada API: Kunci API tidak valid. Mohon periksa kembali kunci yang Anda masukkan.")
        else:
            st.error(f"Terjadi kesalahan HTTP: {http_err}")
        return None
    except Exception as e:
        st.error(f"Terjadi kesalahan saat memanggil AI: {e}")
        return None

# --- 4. Logika Utama Aplikasi ---
st.markdown("<div class='main-column'>", unsafe_allow_html=True)
st.markdown("<div class='header-title'>Dashboard Analisis Survei Restoran</div>", unsafe_allow_html=True)
st.markdown("<div class='header-subtitle'>Analisis Mendalam dari Respon Konsumen</div>", unsafe_allow_html=True)

# --- Bagian Unggah File ---
st.subheader("Unggah Data Survei Anda")
uploaded_file = st.file_uploader("Pilih file CSV atau Excel Anda", type=['csv', 'xlsx', 'xls'])

# Bagian input Kunci API
st.markdown("---")
api_key = st.text_input("Masukkan Kunci API Gemini Anda di sini", type="password")

if uploaded_file:
    df = load_data(uploaded_file)
    
    if not df.empty:
        st.success("File berhasil diunggah!")
        
        # --- Bagian Ringkasan AI ---
        st.markdown("---")
        st.subheader("Ringkasan Analisis oleh AI")
        if not api_key:
            st.warning("Masukkan kunci API Anda di atas untuk melihat ringkasan AI.")
        else:
            with st.spinner("Harap tunggu sebentar, AI sedang menganalisis dan membuat ringkasan..."):
                # Kumpulkan ringkasan data untuk AI
                top_of_mind_summary = df['Q1_1'].value_counts().to_string()
                unaided_summary = calculate_multiselect_counts(df, [f'Q2_{i}' for i in range(1, 6)]).to_string()
                total_awareness_summary = calculate_multiselect_counts(df, [f'Q3_{i}' for i in range(1, 10)]).to_string()
                
                likert_mapping_satisfaction = {'Sangat Puas': 5, 'Puas': 4, 'Cukup Puas': 3, 'Kurang Puas': 2, 'Sangat Tidak Puas': 1}
                satisfaction_cols = [f'Q{i}_{j}' for i in range(20, 25) for j in range(1, 6) if f'Q{i}_{j}' in df.columns]
                satisfaction_summary = calculate_likert_average(df, satisfaction_cols, likert_mapping_satisfaction).to_string()
                
                full_summary_data = f"""
                Top of Mind Awareness (Q1_1):
                {top_of_mind_summary}
                
                Unaided Awareness (Q2_1-Q2_5):
                {unaided_summary}
                
                Total Awareness (Q3_1-Q3_9):
                {total_awareness_summary}
                
                Rata-rata Tingkat Kepuasan (Q20-Q24):
                {satisfaction_summary}
                """

                summary_text = call_gemini_api_for_summary(full_summary_data, api_key)
                if summary_text:
                    st.markdown(summary_text)

        st.markdown("<hr style='margin-top: 2rem; margin-bottom: 1.5rem; border: 1px solid #E2E8F0;'>", unsafe_allow_html=True)

        # --- Bagian Analisis Visual dan Detail ---
        with st.expander("📊 Analisis Visual & Detail"):
            st.subheader("Frekuensi Pilihan dari Berbagai Pertanyaan")

            # Frekuensi Top of Mind (Q1_1)
            st.markdown("#### Frekuensi Top of Mind (Q1_1)")
            q1_counts = df['Q1_1'].value_counts().reset_index()
            q1_counts.columns = ['Respons', 'Frekuensi']
            fig_q1 = px.pie(q1_counts, values='Frekuensi', names='Respons',
                             title='Top of Mind Awareness', hole=0.3,
                             color_discrete_sequence=px.colors.sequential.YlGnBu_r)
            st.plotly_chart(fig_q1, use_container_width=True)

            # Frekuensi UNAIDED AWARENESS
            st.markdown("#### Frekuensi Un-aided Awareness (Q2_1-Q2_5)")
            unaided_df = calculate_multiselect_counts(df, [f'Q2_{i}' for i in range(1, 6)])
            if not unaided_df.empty:
                fig_unaided = px.bar(unaided_df, x='Respons', y='Frekuensi', title='Frekuensi Un-aided Awareness', color='Frekuensi', color_continuous_scale=px.colors.sequential.YlGnBu)
                st.plotly_chart(fig_unaided, use_container_width=True)
            else: st.info("Tidak ada data yang lengkap untuk Un-aided Awareness.")

            # Frekuensi TOTAL AWARENESS
            st.markdown("#### Frekuensi Total Awareness (Q3_1-Q3_9)")
            total_awareness_df = calculate_multiselect_counts(df, [f'Q3_{i}' for i in range(1, 10)])
            if not total_awareness_df.empty:
                fig_total = px.bar(total_awareness_df, x='Respons', y='Frekuensi', title='Frekuensi Total Awareness', color='Frekuensi', color_continuous_scale=px.colors.sequential.YlGnBu)
                st.plotly_chart(fig_total, use_container_width=True)
            else: st.info("Tidak ada data yang lengkap untuk Total Awareness.")

            # Analisis Brand Image
            st.markdown("#### Brand Image (Q15_1-Q15_8)")
            brand_image_cols = [f'Q15_{i}' for i in range(1, 9)]
            brand_image_df = calculate_multiselect_counts(df, brand_image_cols)
            if not brand_image_df.empty:
                st.dataframe(brand_image_df)
                fig_brand = px.bar(brand_image_df, x='Respons', y='Frekuensi', title='Frekuensi Brand Image', color='Frekuensi', color_continuous_scale=px.colors.sequential.YlGnBu)
                st.plotly_chart(fig_brand, use_container_width=True)
            else: st.info("Tidak ada data yang lengkap untuk Brand Image.")

            # Mapping Skala Likert
            likert_mapping = {
                'Sangat Tidak Setuju': 1, 'Tidak Setuju': 2, 'Netral': 3, 'Setuju': 4, 'Sangat Setuju': 5,
                'Sangat Tidak Puas': 1, 'Tidak Puas': 2, 'Netral': 3, 'Puas': 4, 'Sangat Puas': 5,
                'Sangat Tidak Penting': 1, 'Tidak Penting': 2, 'Netral': 3, 'Penting': 4, 'Sangat Penting': 5
            }
            
            # Rata-rata Likert - Important Level
            st.markdown("#### Rata-rata Skor Important Level (Q16-Q19)")
            importance_cols = [f'Q{i}_{j}' for i in range(16, 20) for j in range(1, 6)]
            importance_avg_df = calculate_likert_average(df, importance_cols, likert_mapping)
            if not importance_avg_df.empty:
                fig_importance = px.bar(importance_avg_df, x='Rata-rata', y=importance_avg_df.index,
                                      title='Rata-rata Skor Important Level', orientation='h', color='Rata-rata', color_continuous_scale=px.colors.sequential.YlGnBu)
                fig_importance.update_yaxes(autorange="reversed")
                st.plotly_chart(fig_importance, use_container_width=True)
            else: st.info("Tidak ada data yang lengkap untuk analisis Important Level.")

            # Rata-rata Likert - Kepuasan
            st.markdown("#### Rata-rata Skor Kepuasan (Q20-Q24)")
            satisfaction_cols = [f'Q{i}_{j}' for i in range(20, 25) for j in range(1, 6)]
            satisfaction_avg_df = calculate_likert_average(df, satisfaction_cols, likert_mapping)
            if not satisfaction_avg_df.empty:
                fig_satisfaction = px.bar(satisfaction_avg_df, x='Rata-rata', y=satisfaction_avg_df.index,
                                      title='Rata-rata Skor Kepuasan', orientation='h', color='Rata-rata', color_continuous_scale=px.colors.sequential.YlGnBu)
                fig_satisfaction.update_yaxes(autorange="reversed")
                st.plotly_chart(fig_satisfaction, use_container_width=True)
            else: st.info("Tidak ada data yang lengkap untuk analisis Kepuasan.")

            # Rata-rata Likert - Agreement
            st.markdown("#### Rata-rata Skor Agreement (Q25-Q28)")
            agreement_cols = [f'Q{i}_{j}' for i in range(25, 29) for j in range(1, 3)]
            agreement_avg_df = calculate_likert_average(df, agreement_cols, likert_mapping)
            if not agreement_avg_df.empty:
                fig_agreement = px.bar(agreement_avg_df, x='Rata-rata', y=agreement_avg_df.index,
                                      title='Rata-rata Skor Agreement', orientation='h', color='Rata-rata', color_continuous_scale=px.colors.sequential.YlGnBu)
                fig_agreement.update_yaxes(autorange="reversed")
                st.plotly_chart(fig_agreement, use_container_width=True)
            else: st.info("Tidak ada data yang lengkap untuk analisis Agreement.")

        # --- Conceptual Mapping (Crosstab) ---
        with st.expander("🗺️ Pemetaan Konseptual (Tabel Silang)"):
            st.subheader("Tabel Silang (Crosstab) & Visualisasi")
            st.write("Pilih 2 parameter untuk membuat tabel silang.")
            
            # Tentukan semua kolom yang relevan
            likert_cols = [f'Q{i}_{j}' for i in range(16, 20) for j in range(1, 6)] + [f'Q{i}_{j}' for i in range(20, 25) for j in range(1, 6)] + [f'Q{i}_{j}' for i in range(25, 29) for j in range(1, 3)]
            demographic_cols = [col for col in df.columns if col.startswith('S')]
            all_cols_for_crosstab = [col for col in df.columns if col in likert_cols or col in demographic_cols]
            
            df_cleaned = df.copy()
            
            # Mapping untuk Likert
            likert_mapping_numeric = {
                'Sangat Tidak Setuju': 1, 'Tidak Setuju': 2, 'Netral': 3, 'Setuju': 4, 'Sangat Setuju': 5,
                'Sangat Tidak Puas': 1, 'Tidak Puas': 2, 'Netral': 3, 'Puas': 4, 'Sangat Puas': 5,
                'Sangat Tidak Penting': 1, 'Tidak Penting': 2, 'Netral': 3, 'Penting': 4, 'Sangat Penting': 5
            }
            for col in likert_cols:
                if col in df_cleaned.columns:
                    df_cleaned[col] = df_cleaned[col].astype(str).str.strip().str.title().map(likert_mapping_numeric)
            
            selected_pivot = st.selectbox("Pilih Kolom Pivot (Baris):", options=demographic_cols)
            selected_variable = st.selectbox("Pilih Kolom Variabel (Kolom):", options=likert_cols)

            if selected_pivot in df_cleaned.columns and selected_variable in df_cleaned.columns:
                pivot_table = pd.crosstab(df_cleaned[selected_pivot], df_cleaned[selected_variable], margins=True, normalize='index') * 100
                st.write("Tabel Silang (Crosstab):")
                st.dataframe(pivot_table.round(2), use_container_width=True)
                
                # Visualisasi Heatmap
                fig_heatmap = go.Figure(data=go.Heatmap(
                    z=pivot_table.drop('All', axis=1).values,
                    x=pivot_table.drop('All', axis=1).columns.tolist(),
                    y=pivot_table.index.tolist(),
                    colorscale='YlGnBu'
                ))
                fig_heatmap.update_layout(
                    title='Pemetaan Frekuensi Berdasarkan Kategori',
                    xaxis_title=selected_variable,
                    yaxis_title=selected_pivot
                )
                st.plotly_chart(fig_heatmap, use_container_width=True)
            else:
                st.info("Pilih kolom yang valid untuk analisis tabel silang.")

st.markdown("</div>", unsafe_allow_html=True)
