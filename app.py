import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import io

# Sayfa Ayarları
st.set_page_config(page_title="Bayi Makina Analizi", layout="wide", page_icon="🤖")

# Başlık
st.title("🤖 Bayi Veri ve Makina Analizi")
st.markdown("---")

# 1. VERİ YÜKLEME
@st.cache_data
def load_data():
    try:
        df = pd.read_excel("YENI.xlsx")
        df.columns = df.columns.str.strip()
        
        date_cols = ['Dağıtıcı ile Yapılan Sözleşme Başlangıç Tarihi', 
                     'Dağıtıcı ile Yapılan Sözleşme Bitiş Tarihi']
        
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Kalan Gün Hesaplama
        today = pd.to_datetime("today")
        if 'Dağıtıcı ile Yapılan Sözleşme Bitiş Tarihi' in df.columns:
            df['Kalan Gün'] = (df['Dağıtıcı ile Yapılan Sözleşme Bitiş Tarihi'] - today).dt.days
            df['Bitiş Yılı'] = df['Dağıtıcı ile Yapılan Sözleşme Bitiş Tarihi'].dt.year
            
            ay_map_tr = {
                1: 'Ocak', 2: 'Şubat', 3: 'Mart', 4: 'Nisan', 5: 'Mayıs', 6: 'Haziran',
                7: 'Temmuz', 8: 'Ağustos', 9: 'Eylül', 10: 'Ekim', 11: 'Kasım', 12: 'Aralık'
            }
            df['Bitiş Ayı No'] = df['Dağıtıcı ile Yapılan Sözleşme Bitiş Tarihi'].dt.month
            df['Bitiş Ayı Adı'] = df['Bitiş Ayı No'].map(ay_map_tr)
            
        return df
    except Exception as e:
        st.error(f"Veri okunurken hata oluştu: {e}")
        return None

df = load_data()

# --- MAKİNA ANALİZİ RAPORU ---
def create_machine_analysis_report(data):
    if data is None or data.empty:
        return

    today = datetime.now()
    current_year = today.year
    next_year = current_year + 1
    
    st.markdown(f"### 📊 Detaylı Makina Analiz Raporu ({current_year} - {next_year})")
    st.markdown("---")

    # 1. BÖLÜM: 2026 PROJEKSİYONU
    next_year_data = data[data['Bitiş Yılı'] == next_year]
    total_next = len(next_year_data)

    st.markdown(f"#### 1. {next_year} Yılı Sözleşme Bitiş Projeksiyonu")
    
    if not next_year_data.empty:
        peak_month_idx = next_year_data['Bitiş Ayı No'].value_counts().idxmax()
        peak_count = next_year_data['Bitiş Ayı No'].value_counts().max()
        ay_map_tr = {1: 'Ocak', 2: 'Şubat', 3: 'Mart', 4: 'Nisan', 5: 'Mayıs', 6: 'Haziran',
                     7: 'Temmuz', 8: 'Ağustos', 9: 'Eylül', 10: 'Ekim', 11: 'Kasım', 12: 'Aralık'}
        peak_month_name = ay_map_tr[peak_month_idx]

        st.info(f"📅 **Zaman Dağılımı:** {next_year} yılında toplam **{total_next}** adet sözleşme sona erecektir. "
                f"En yüksek hacim **{peak_month_name}** ayında (**{peak_count}** adet) gerçekleşmektedir.")

        st.markdown(f"**📍 {next_year} Yılı İl Bazlı Tam Dağılım Listesi:**")
        city_counts = next_year_data['İl'].value_counts().reset_index()
        city_counts.columns = ['İl Adı', 'Bitecek Sözleşme Sayısı']
        city_counts['Bölgesel Pay (%)'] = (city_counts['Bitecek Sözleşme Sayısı'] / total_next * 100).round(1)
        st.dataframe(city_counts, use_container_width=True, hide_index=True)
    else:
        st.write(f"{next_year} yılı için sistemde kayıtlı bir veri bulunmamaktadır.")

    st.markdown("---")

    # 2. BÖLÜM: ADF ANALİZİ
    st.markdown("#### 2. ADF Kodu Segmentasyon Analizi")
    if 'ADF' in data.columns:
        total_records = len(data)
        adf_counts = data['ADF'].value_counts()
        unique_adf = len(adf_counts)
        top_adf = adf_counts.index[0]
        top_adf_ratio = (adf_counts.iloc[0] / total_records) * 100

        col1, col2 = st.columns([2, 1])
        with col1:
            st.write(f"Veri setinde toplam **{unique_adf}** farklı ADF kodu bulunmaktadır.")
            st.write(f"En baskın segment **{top_adf}** kodudur ve portföyün **%{top_adf_ratio:.1f}**'ini oluşturmaktadır.")
            
            adf_df = adf_counts.reset_index()
            adf_df.columns = ['ADF Kodu', 'Sayı']
            adf_df['Oran (%)'] = (adf_df['Sayı'] / total_records * 100).round(1)
            st.dataframe(adf_df.head(10), use_container_width=True, hide_index=True)
        
        with col2:
            fig_adf = px.pie(adf_df, names='ADF Kodu', values='Sayı', title='ADF Genel Dağılımı', hole=0.4)
            st.plotly_chart(fig_adf, use_container_width=True)
    else:
        st.warning("ADF verisi bulunamadı.")


if df is not None:
    # YAN MENÜ
    st.sidebar.info("🕒 Veriler her gün saat 10:00'da yenilenmektedir.")
    st.sidebar.markdown("---")
    st.sidebar.header("🔍 Filtreler")

    bolge_list = ["Tümü"] + list(df['BÖLGE'].unique())
    selected_bolge = st.sidebar.selectbox("Bölge Seçiniz", bolge_list)

    if selected_bolge != "Tümü":
        filtered_df = df[df['BÖLGE'] == selected_bolge]
        il_list = ["Tümü"] + list(filtered_df['İl'].unique())
    else:
        filtered_df = df
        il_list = ["Tümü"] + list(df['İl'].unique())

    selected_il = st.sidebar.selectbox("İl Seçiniz", il_list)

    if selected_il != "Tümü":
        filtered_df = filtered_df[filtered_df['İl'] == selected_il]

    # Excel İndir
    st.sidebar.markdown("---")
    try:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            filtered_df.to_excel(writer, index=False, sheet_name='Rapor')
        st.sidebar.download_button(label="📥 Raporu Excel İndir", data=buffer.getvalue(), file_name=f"Rapor_{datetime.now().strftime('%Y-%m-%d')}.xlsx", mime="application/vnd.ms-excel")
    except:
        pass

    st.sidebar.markdown("---")
    st.sidebar.header("📧 İletişim")
    st.sidebar.info("kerim.aksu@milangaz.com.tr")

    # KARTLAR
    st.subheader("📈 Genel Durum")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Toplam Bayi/Sözleşme", len(filtered_df))
    with col2:
        st.metric("Faaliyet Gösterilen İl", filtered_df['İl'].nunique())
    
    st.markdown("---")

    # SEKME YAPISI
    tab1, tab2, tab3 = st.tabs(["📍 Grafikler", "📅 Sözleşme Takip", "🧠 Makina Analizi"])

    # --- TAB 1: GRAFİKLER (GENEL ADF EKLENDİ) ---
    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Bölge Dağılımı")
            fig_bolge = px.pie(filtered_df, names='BÖLGE', title='Bölge Bazlı Oranlar', hole=0.4)
            st.plotly_chart(fig_bolge, use_container_width=True)
        with c2:
            st.subheader("En Yoğun 10 İl")
            top_cities = filtered_df['İl'].value_counts().nlargest(10).reset_index()
            top_cities.columns = ['İl', 'Sayı']
            fig_top_cities = px.bar(top_cities, x='İl', y='Sayı', color='Sayı', title='En Çok Bayi Olan İller')
            st.plotly_chart(fig_top_cities, use_container_width=True)
        
        # --- YENİ EKLENEN KISIM: GENEL ADF GRAFİĞİ ---
        st.markdown("---")
        st.subheader("📊 Genel ADF (Segment) Analizi")
        if 'ADF' in filtered_df.columns:
            adf_genel = filtered_df['ADF'].value_counts().reset_index()
            adf_genel.columns = ['ADF', 'Sayı']
            fig_adf_genel = px.bar(adf_genel, x='ADF', y='Sayı', color='Sayı', text='Sayı', title="Tüm Portföyün ADF Dağılımı")
            st.plotly_chart(fig_adf_genel, use_container_width=True)
        else:
            st.warning("ADF Sütunu bulunamadı.")

    # --- TAB 2: SÖZLEŞME TAKİP (YILLIK ADF EKLENDİ) ---
    with tab2:
        st.subheader("📅 Yıllık ve Aylık Sözleşme Takibi")

        mevcut_yillar = sorted(filtered_df['Bitiş Yılı'].dropna().unique())
        
        if len(mevcut_yillar) > 0:
            c_sel, c_info = st.columns([1, 3])
            with c_sel:
                selected_year = st.selectbox("Yıl Seçiniz:", options=mevcut_yillar, index=0)
            
            year_df = filtered_df[filtered_df['Bitiş Yılı'] == selected_year].copy()
            total_in_year = len(year_df)
            
            with c_info:
                st.metric(f"{selected_year} Toplam Sözleşme", f"{total_in_year} Adet")
            
            # --- YENİ EKLENEN KISIM: SEÇİLEN YIL İÇİN ADF ANALİZİ ---
            st.markdown(f"#### 🔍 {selected_year} Yılı Özel ADF Analizi")
            col_g1, col_g2 = st.columns([2, 1])
            
            with col_g1:
                # Aylık Grafik
                monthly_counts = year_df.groupby(['Bitiş Ayı No', 'Bitiş Ayı Adı']).size().reset_index(name='Sayi')
                monthly_counts = monthly_counts.sort_values('Bitiş Ayı No')
                fig_monthly = px.bar(monthly_counts, x='Bitiş Ayı Adı', y='Sayi', text='Sayi', title=f"{selected_year} Aylık Sözleşme Bitişleri", color='Sayi')
                fig_monthly.update_traces(textposition='outside')
                fig_monthly.update_layout(clickmode='event+select')
                selected_event = st.plotly_chart(fig_monthly, use_container_width=True, on_select="rerun")
            
            with col_g2:
                # O yılın ADF Grafiği
                if 'ADF' in year_df.columns:
                    adf_year_counts = year_df['ADF'].value_counts().reset_index()
                    adf_year_counts.columns = ['ADF', 'Sayı']
                    fig_adf_year = px.pie(adf_year_counts, names='ADF', values='Sayı', title=f"{selected_year} Yılında Bitenlerin ADF Dağılımı", hole=0.3)
                    st.plotly_chart(fig_adf_year, use_container_width=True)
            # --------------------------------------------------------

            st.info("💡 Tabloyu filtrelemek için **Aylık Grafik (Sol)** üzerindeki çubuklara tıklayınız.")

            # Tablo Filtreleme
            table_data = year_df.copy()
            if selected_event and selected_event['selection']['points']:
                tiklanan_ay = selected_event['selection']['points'][0]['x']
                table_data = year_df[year_df['Bitiş Ayı Adı'] == tiklanan_ay]
                st.success(f"✅ **{tiklanan_ay}** ayı filtrelendi.")
            
            table_data = table_data.sort_values(by='Kalan Gün')
            table_data['Bitiş Tarihi'] = table_data['Dağıtıcı ile Yapılan Sözleşme Bitiş Tarihi'].dt.strftime('%d/%m/%Y')
            
            display_cols = ['Unvan', 'İl', 'ADF', 'Bitiş Tarihi', 'Kalan Gün']
            final_cols = [c for c in display_cols if c in table_data.columns]
            
            def highlight_urgent(val):
                if isinstance(val, int):
                    if val < 0: return 'background-color: #ffcccc; color: black'
                    elif val < 90: return 'background-color: #ffffcc; color: black'
                return ''

            st.dataframe(table_data[final_cols].style.map(highlight_urgent, subset=['Kalan Gün']), use_container_width=True, hide_index=True)
        else:
            st.warning("Veri yok.")

    # --- TAB 3: MAKİNA ANALİZİ ---
    with tab3:
        st.subheader("🧠 Detaylı Makina Analizi")
        create_machine_analysis_report(filtered_df)

else:
    st.info("Lütfen YENI.xlsx dosyasını yükleyiniz.")
