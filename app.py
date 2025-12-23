import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import io

# Sayfa Ayarları
st.set_page_config(page_title="Bayi Strateji Paneli", layout="wide", page_icon="🤖")

# Başlık
st.title("🤖 Bayi Veri Analizi ve Gelecek Öngörü Sistemi")
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
            
            # Türkçe Ay İsimleri (Manuel Map - Garanti Çözüm)
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

# --- YENİ: GELİŞMİŞ ÖNGÖRÜ MOTORU (NOKTA ATIŞI TARİHLER) ---
def create_advanced_prediction_report(data):
    if data is None or data.empty:
        return

    today = datetime.now()
    current_year = today.year
    next_year = current_year + 1
    
    st.markdown(f"### 🔮 Gelecek Simülasyonu ve Stratejik Öngörüler ({current_year}-{next_year})")
    st.markdown("---")

    # 1. GELECEK YIL ANALİZİ (2026 vb.)
    next_year_data = data[data['Bitiş Yılı'] == next_year]
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown(f"#### 📅 {next_year} Yılı Kritik Tarihler")
        if not next_year_data.empty:
            # En yoğun ayı bul
            peak_month_idx = next_year_data['Bitiş Ayı No'].value_counts().idxmax()
            peak_count = next_year_data['Bitiş Ayı No'].value_counts().max()
            
            # Ay ismini bul
            ay_map_tr = {1: 'Ocak', 2: 'Şubat', 3: 'Mart', 4: 'Nisan', 5: 'Mayıs', 6: 'Haziran',
                         7: 'Temmuz', 8: 'Ağustos', 9: 'Eylül', 10: 'Ekim', 11: 'Kasım', 12: 'Aralık'}
            peak_month_name = ay_map_tr[peak_month_idx]
            
            total_next = len(next_year_data)
            
            st.error(f"🚨 **En Kritik Dönem:** {next_year} yılında operasyonel yük **{peak_month_name}** ayında zirve yapacak.")
            st.markdown(f"""
            - **{next_year} Toplam Bitiş:** {total_next} adet sözleşme.
            - **Zirve Noktası:** Sadece **{peak_month_name} {next_year}** döneminde **{peak_count}** adet sözleşme (Yıllık yükün %{int(peak_count/total_next*100)}'si) bitecek.
            - **Aksiyon:** {peak_month_name} ayından en az 3 ay önce saha ekibi planlaması yapılmalı.
            """)
        else:
            st.success(f"✅ {next_year} yılı için henüz sisteme girilmiş riskli bir sözleşme bitişi bulunmuyor.")

    with col2:
        st.markdown(f"#### 📍 {next_year} Yılında Hangi Şehirler Riskli?")
        if not next_year_data.empty:
            top_city = next_year_data['İl'].value_counts().head(1)
            city_name = top_city.index[0]
            city_count = top_city.values[0]
            
            st.warning(f"🎯 **Odak Şehir:** {next_year} yılında tüm dikkatinizi **{city_name}** iline vermelisiniz.")
            st.markdown(f"""
            - **{city_name}** ilinde tam **{city_count}** adet sözleşme sonlanacak.
            - Bu ili sırasıyla şu iller takip ediyor:
            """)
            
            # İlk 3 ili listele
            top3 = next_year_data['İl'].value_counts().head(3)
            for city, count in top3.items():
                st.markdown(f"*   **{city}:** {count} Sözleşme")
        else:
            st.info("Veri olmadığı için bölgesel risk haritası çıkarılamadı.")

    st.markdown("---")

    # 2. MEVSİMSEL ANALİZ (GENEL VERİ ÜZERİNDEN)
    st.markdown("#### 🌦️ Mevsimsel Yoğunluk Analizi")
    
    # Mevsimleri Grupla
    def get_season(month):
        if month in [12, 1, 2]: return "Kış"
        elif month in [3, 4, 5]: return "İlkbahar"
        elif month in [6, 7, 8]: return "Yaz"
        else: return "Sonbahar"
        
    data['Mevsim'] = data['Bitiş Ayı No'].apply(get_season)
    season_counts = data['Mevsim'].value_counts()
    dominant_season = season_counts.idxmax()
    
    st.info(f"💡 Yapay zeka analizine göre; işletmenizin sözleşme döngüsü genelde **{dominant_season}** mevsiminde yoğunlaşmaktadır.")
    st.markdown(f"Bu durum, sektördeki ticari döngülerin **{dominant_season}** aylarında (Örn: {dominant_season == 'Yaz' and 'Haziran-Ağustos' or 'ilgili aylar'}) hızlandığını işaret eder.")


if df is not None:
    # 2. YAN MENÜ
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
        
        st.sidebar.download_button(
            label="📥 Raporu Excel İndir",
            data=buffer.getvalue(),
            file_name=f"Rapor_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
            mime="application/vnd.ms-excel"
        )
    except:
        pass

    st.sidebar.markdown("---")
    st.sidebar.header("📧 İletişim")
    st.sidebar.info("kerim.aksu@milangaz.com.tr")

    # 3. KARTLAR
    st.subheader("📈 Genel Durum")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Toplam Bayi/Sözleşme", len(filtered_df))
    with col2:
        st.metric("Faaliyet Gösterilen İl", filtered_df['İl'].nunique())
    
    st.markdown("---")

    # 4. SEKME YAPISI
    tab1, tab2, tab3 = st.tabs(["📍 Grafikler", "📅 Sözleşme Takip", "🧠 Yapay Zeka & Öngörü"])

    # --- TAB 1 ---
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

    # --- TAB 2 ---
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

            monthly_counts = year_df.groupby(['Bitiş Ayı No', 'Bitiş Ayı Adı']).size().reset_index(name='Sayi')
            monthly_counts = monthly_counts.sort_values('Bitiş Ayı No')

            st.info("💡 Grafikteki aylara tıklayarak tabloyu filtreleyebilirsiniz.")

            fig_monthly = px.bar(monthly_counts, x='Bitiş Ayı Adı', y='Sayi', text='Sayi', title=f"{selected_year} Aylık Dağılım", color='Sayi')
            fig_monthly.update_traces(textposition='outside')
            fig_monthly.update_layout(clickmode='event+select')
            
            selected_event = st.plotly_chart(fig_monthly, use_container_width=True, on_select="rerun")
            
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

            st.dataframe(
                table_data[final_cols].style.map(highlight_urgent, subset=['Kalan Gün']),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning("Veri yok.")

    # --- TAB 3: YENİ GELİŞMİŞ AI RAPORU ---
    with tab3:
        st.subheader("🧠 Gelecek Stratejileri ve Öngörüler")
        create_advanced_prediction_report(filtered_df)

else:
    st.info("Lütfen YENI.xlsx dosyasını yükleyiniz.")
