import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Sayfa Ayarları
st.set_page_config(page_title="Bayi Analiz Paneli", layout="wide", page_icon="📊")

# Başlık
st.title("📊 Bayi ve Sözleşme Veri Analizi")
st.markdown("---")

# 1. VERİ YÜKLEME
@st.cache_data
def load_data():
    try:
        df = pd.read_excel("YENI.xlsx")
        
        # Sütun isimlerindeki boşlukları temizle
        df.columns = df.columns.str.strip()
        
        # Tarih formatına çevirme
        date_cols = ['Dağıtıcı ile Yapılan Sözleşme Başlangıç Tarihi', 
                     'Dağıtıcı ile Yapılan Sözleşme Bitiş Tarihi']
        
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"Veri okunurken hata oluştu: {e}")
        return None

df = load_data()

if df is not None:
    # 2. YAN MENÜ (FİLTRELER, NOTLAR VE LİNKLER)
    
    # --- YENİ EKLENEN KISIM: BİLGİ NOTU ---
    st.sidebar.info("🕒 Not: Veriler her gün saat 10:00'da yenilenmektedir.")
    st.sidebar.markdown("---")
    # --------------------------------------

    st.sidebar.header("🔍 Filtreler")

    # Bölge Filtresi
    bolge_list = ["Tümü"] + list(df['BÖLGE'].unique())
    selected_bolge = st.sidebar.selectbox("Bölge Seçiniz", bolge_list)

    # İl Filtresi
    if selected_bolge != "Tümü":
        filtered_df = df[df['BÖLGE'] == selected_bolge]
        il_list = ["Tümü"] + list(filtered_df['İl'].unique())
    else:
        filtered_df = df
        il_list = ["Tümü"] + list(df['İl'].unique())

    selected_il = st.sidebar.selectbox("İl Seçiniz", il_list)

    # Filtreleri Uygula
    if selected_il != "Tümü":
        filtered_df = filtered_df[filtered_df['İl'] == selected_il]

    # --- LİNKLER VE İLETİŞİM ---
    st.sidebar.markdown("---") 
    st.sidebar.header("🔗 Rapor Bağlantıları")
    
    # Linkler
    st.sidebar.markdown("📊 [EPDK Sektör Raporu](https://pazarpayi.streamlit.app/)")
    st.sidebar.markdown("⛽ [Akaryakıt Lisans Raporu](https://akartakip.streamlit.app/)")
    st.sidebar.markdown("🔥 [LPG Lisans Raporu](https://lpgtakip.streamlit.app/)")
    
    st.sidebar.markdown("---") 
    
    # İletişim
    st.sidebar.header("📧 İletişim")
    st.sidebar.info("kerim.aksu@milangaz.com.tr")
    # -----------------------------------------------

    # 3. KARTLAR (KPI)
    st.subheader("📈 Özet Bilgiler")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Toplam Bayi/Kayıt", len(filtered_df))
    with col2:
        st.metric("Farklı İl Sayısı", filtered_df['İl'].nunique())
    with col3:
        unique_adf = filtered_df['ADF'].nunique() if 'ADF' in filtered_df.columns else 0
        st.metric("Farklı ADF Sayısı", unique_adf)

    st.markdown("---")

    # 4. SEKME YAPISI
    tab1, tab2 = st.tabs(["📍 Bölge, İl ve ADF Analizi", "📅 Sözleşme Takip Listesi"])

    # --- TAB 1: GRAFİKLER ---
    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Bölge Dağılımı")
            fig_bolge = px.pie(filtered_df, names='BÖLGE', title='Bölge Bazlı Oranlar', hole=0.4)
            st.plotly_chart(fig_bolge, use_container_width=True)
        
        with c2:
            st.subheader("ADF Dağılımı")
            if 'ADF' in filtered_df.columns:
                adf_counts = filtered_df['ADF'].value_counts().reset_index()
                adf_counts.columns = ['ADF', 'Sayı']
                fig_adf = px.bar(adf_counts, x='ADF', y='Sayı', color='Sayı', title='ADF Koduna Göre Dağılım')
                st.plotly_chart(fig_adf, use_container_width=True)
            else:
                st.warning("ADF sütunu bulunamadı.")

        st.subheader("Tüm İllerin Dağılımı")
        city_counts = filtered_df['İl'].value_counts().reset_index()
        city_counts.columns = ['İl', 'Sayı']
        fig_il = px.bar(city_counts, x='İl', y='Sayı', text='Sayı', color='Sayı', height=500, title='İl Bazlı Bayi Sayıları (Tam Liste)')
        fig_il.update_traces(textposition='outside')
        st.plotly_chart(fig_il, use_container_width=True)

    # --- TAB 2: SÖZLEŞME ANALİZİ ---
    with tab2:
        st.subheader("Sözleşme Bitiş Takvimi")

        filtered_df['Bitiş Yılı'] = filtered_df['Dağıtıcı ile Yapılan Sözleşme Bitiş Tarihi'].dt.year
        yearly_counts = filtered_df['Bitiş Yılı'].value_counts().sort_index().reset_index()
        yearly_counts.columns = ['Yıl', 'Bitecek Sözleşme Sayısı']
        fig_timeline = px.line(yearly_counts, x='Yıl', y='Bitecek Sözleşme Sayısı', markers=True)
        st.plotly_chart(fig_timeline, use_container_width=True)

        st.markdown("---")
        st.subheader("📄 Sözleşme Bitiş Listesi (Yakından Uzağa)")

        today = pd.to_datetime("today")
        contract_df = filtered_df[filtered_df['Dağıtıcı ile Yapılan Sözleşme Bitiş Tarihi'].notna()].copy()
        contract_df['Kalan Gün'] = (contract_df['Dağıtıcı ile Yapılan Sözleşme Bitiş Tarihi'] - today).dt.days
        contract_df = contract_df.sort_values(by='Kalan Gün', ascending=True)
        contract_df['Bitiş Tarihi'] = contract_df['Dağıtıcı ile Yapılan Sözleşme Bitiş Tarihi'].dt.strftime('%d/%m/%Y')

        display_cols = ['Unvan', 'BÖLGE', 'İl', 'ADF', 'Bitiş Tarihi', 'Kalan Gün']
        final_cols = [c for c in display_cols if c in contract_df.columns or c in ['Bitiş Tarihi', 'Kalan Gün']]

        def highlight_urgent(val):
            color = ''
            if val < 0:
                color = 'background-color: #ffcccc'
            elif val < 90:
                color = 'background-color: #ffffcc'
            return color

        st.dataframe(
            contract_df[final_cols].style.applymap(highlight_urgent, subset=['Kalan Gün']),
            use_container_width=True,
            hide_index=True
        )

else:
    st.info("Lütfen YENI.xlsx dosyasını program klasörüne ekleyiniz.")
