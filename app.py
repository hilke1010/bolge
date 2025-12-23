import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import io

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
            
            # Dil Hatasına Karşı Manuel Ay İsimleri
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

# --- YAPAY ZEKA RAPOR MOTORU ---
def create_detailed_ai_report(data, region_name, city_name):
    if data is None or data.empty:
        return ["Veri bulunamadı."]
    
    report_lines = []
    today = datetime.now()
    current_year = today.year
    
    total_count = len(data)
    unique_cities = data['İl'].nunique()
    
    # Rapor İçeriği
    report_lines.append(f"### 📢 {region_name} Bölgesi - {city_name} Analiz Raporu")
    report_lines.append(f"**Rapor Tarihi:** {today.strftime('%d.%m.%Y')}")
    report_lines.append("")
    report_lines.append(f"Bu rapor, seçilen filtreler doğrultusunda **{total_count}** adet bayi/sözleşme kaydı üzerinden oluşturulmuştur.")
    report_lines.append(f"Veri seti toplamda **{unique_cities}** farklı lokasyonu (İl) kapsamaktadır.")
    
    # Pareto
    top_cities = data['İl'].value_counts().head(3)
    if not top_cities.empty:
        top_city_names = ", ".join([f"{idx} ({val})" for idx, val in top_cities.items()])
        dominant_city = top_cities.index[0]
        dominant_ratio = int((top_cities.iloc[0] / total_count) * 100) if total_count > 0 else 0
        
        report_lines.append("#### 📍 Lokasyon ve Yoğunluk Analizi")
        report_lines.append(f"- Bölgedeki operasyonun ağırlık merkezi **{dominant_city}** ilidir.")
        report_lines.append(f"- Toplam hacmin **%{dominant_ratio}**'lik kısmı sadece bu ilde toplanmıştır.")
        report_lines.append(f"- En yoğun ilk 3 il: **{top_city_names}**.")
    
    # Zaman
    if 'Bitiş Yılı' in data.columns:
        this_year_count = data[data['Bitiş Yılı'] == current_year].shape[0]
        next_year_count = data[data['Bitiş Yılı'] == (current_year + 1)].shape[0]
        
        report_lines.append("#### 📅 Sözleşme Vade Yapısı")
        report_lines.append(f"- **{current_year} Yılı:** Yıl sonuna kadar **{this_year_count}** adet sözleşme sonlanacaktır.")
        
        if next_year_count > this_year_count:
            report_lines.append(f"- **📈 Trend:** {current_year + 1} yılında iş yükü artarak **{next_year_count}** adede yükselecektir.")
        else:
            report_lines.append(f"- **📉 Trend:** {current_year + 1} yılında yoğunluk azalarak **{next_year_count}** seviyesine inecektir.")

    # Risk
    if 'Kalan Gün' in data.columns:
        expired = data[data['Kalan Gün'] < 0].shape[0]
        urgent = data[(data['Kalan Gün'] >= 0) & (data['Kalan Gün'] < 90)].shape[0]

        report_lines.append("#### 🚨 Risk Matrisi")
        if expired > 0:
            report_lines.append(f"- 🔴 **KRİTİK:** Süresi dolmuş **{expired}** adet sözleşme mevcuttur.")
        if urgent > 0:
            report_lines.append(f"- 🟠 **ACİLİYET:** 90 gün içinde **{urgent}** bayi ile görüşülmelidir.")
        else:
            report_lines.append("- 🟢 Kısa vadede yüksek risk görünmemektedir.")

    report_lines.append("#### 💡 Sonuç")
    report_lines.append("Operasyonel süreklilik için 'Kritik' statüsündeki bayilere öncelik verilmelidir.")
    
    return report_lines


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

    # Excel İndirme
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
    st.subheader("📈 Özet Bilgiler")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Görüntülenen Bayi Sayısı", len(filtered_df))
    with col2:
        st.metric("Farklı İl Sayısı", filtered_df['İl'].nunique())
    
    st.markdown("---")

    # 4. SEKME YAPISI
    tab1, tab2, tab3 = st.tabs(["📍 Grafikler ve Analiz", "📅 Sözleşme Takip Listesi", "🧠 Yapay Zeka & Makina Analizi"])

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

    # --- TAB 2: INTERAKTİF SÖZLEŞME TABLOSU (DÜZELTİLDİ) ---
    with tab2:
        st.subheader("📅 Sözleşme Bitiş Takvimi")

        mevcut_yillar = sorted(filtered_df['Bitiş Yılı'].dropna().unique())
        
        if len(mevcut_yillar) > 0:
            selected_year = st.selectbox("Yıl Seçiniz:", options=mevcut_yillar, index=0)
            
            # Seçilen yıla göre filtrele
            year_df = filtered_df[filtered_df['Bitiş Yılı'] == selected_year].copy()
            
            # Aylık gruplama
            monthly_counts = year_df.groupby(['Bitiş Ayı No', 'Bitiş Ayı Adı']).size().reset_index(name='Sayi')
            monthly_counts = monthly_counts.sort_values('Bitiş Ayı No')

            st.info("💡 Tabloyu filtrelemek için grafikteki bir aya **tıklayınız**. Seçimi kaldırmak için boşluğa çift tıklayınız.")

            # Grafik
            fig_monthly = px.bar(monthly_counts, x='Bitiş Ayı Adı', y='Sayi', text='Sayi', title=f"{selected_year} Aylık Dağılım", color='Sayi')
            fig_monthly.update_traces(textposition='outside')
            fig_monthly.update_layout(clickmode='event+select')
            
            # Tıklama olayını yakala
            selected_event = st.plotly_chart(fig_monthly, use_container_width=True, on_select="rerun")
            
            # TABLO FİLTRELEME MANTIĞI
            table_data = year_df.copy() # Varsayılan: Hepsi
            
            if selected_event and selected_event['selection']['points']:
                # Seçilen ayı bul
                tiklanan_ay = selected_event['selection']['points'][0]['x']
                table_data = year_df[year_df['Bitiş Ayı Adı'] == tiklanan_ay]
                st.success(f"✅ Sadece **{tiklanan_ay}** ayı gösteriliyor.")
            
            # TABLO RENKLENDİRME VE GÖSTERİM
            table_data = table_data.sort_values(by='Kalan Gün')
            table_data['Bitiş Tarihi'] = table_data['Dağıtıcı ile Yapılan Sözleşme Bitiş Tarihi'].dt.strftime('%d/%m/%Y')
            
            display_cols = ['Unvan', 'İl', 'ADF', 'Bitiş Tarihi', 'Kalan Gün']
            final_cols = [c for c in display_cols if c in table_data.columns]
            
            # Renklendirme Fonksiyonu
            def highlight_urgent(val):
                if isinstance(val, int):
                    if val < 0:
                        return 'background-color: #ffcccc; color: black' # Kırmızı
                    elif val < 90:
                        return 'background-color: #ffffcc; color: black' # Sarı
                return ''

            st.dataframe(
                table_data[final_cols].style.map(highlight_urgent, subset=['Kalan Gün']),
                use_container_width=True,
                hide_index=True
            )
            
        else:
            st.warning("Veri yok.")

    # --- TAB 3: AI ANALİZİ ---
    with tab3:
        st.subheader("🧠 Akıllı Veri Analiz Raporu")
        st.info("Aşağıdaki rapor, soldaki menüden seçtiğiniz filtrelere (Bölge/İl) göre anlık olarak üretilmiştir.")
        
        analiz_sonucu = create_detailed_ai_report(filtered_df, selected_bolge, selected_il)
        
        with st.container():
            for line in analiz_sonucu:
                st.markdown(line)

else:
    st.info("Lütfen YENI.xlsx dosyasını yükleyiniz.")
