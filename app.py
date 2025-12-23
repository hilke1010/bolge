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
            df['Bitiş Ayı'] = df['Dağıtıcı ile Yapılan Sözleşme Bitiş Tarihi'].dt.month_name(locale='tr_TR') 
            # Not: Locale hatası alırsan burayı .dt.month_name() olarak bırakabilirsin.
            
        return df
    except Exception as e:
        st.error(f"Veri okunurken hata oluştu: {e}")
        return None

df = load_data()

# --- YENİ: DETAYLI RAPOR OLUŞTURMA MOTORU ---
def create_detailed_ai_report(data, region_name, city_name):
    if data.empty:
        return ["Veri bulunamadı."]
    
    report_lines = []
    today = datetime.now()
    current_year = today.year
    
    # İstatistikler
    total_count = len(data)
    unique_cities = data['İl'].nunique()
    avg_days = data['Kalan Gün'].mean()
    
    # 1. GİRİŞ VE GENEL DURUM
    report_lines.append(f"### 📢 {region_name} Bölgesi - {city_name} Analiz Raporu")
    report_lines.append(f"**Rapor Tarihi:** {today.strftime('%d.%m.%Y')}")
    report_lines.append("")
    report_lines.append(f"Bu rapor, seçilen filtreler doğrultusunda **{total_count}** adet bayi/sözleşme kaydı üzerinden oluşturulmuştur.")
    report_lines.append(f"Veri seti toplamda **{unique_cities}** farklı lokasyonu (İl) kapsamaktadır. Bu durum, operasyonel dağılımın genişliğini göstermektedir.")
    
    # 2. EN GÜÇLÜ OYUNCULAR (Pareto Analizi)
    top_cities = data['İl'].value_counts().head(3)
    top_city_names = ", ".join([f"{idx} ({val})" for idx, val in top_cities.items()])
    dominant_city = top_cities.index[0]
    dominant_ratio = int((top_cities.iloc[0] / total_count) * 100)
    
    report_lines.append("#### 📍 Lokasyon ve Yoğunluk Analizi")
    report_lines.append(f"- Bölgedeki operasyonun ağırlık merkezi **{dominant_city}** ilidir.")
    report_lines.append(f"- Toplam hacmin **%{dominant_ratio}**'lik kısmı sadece bu ilde toplanmıştır.")
    report_lines.append(f"- En yoğun ilk 3 il sıralaması şöyledir: **{top_city_names}**.")
    if dominant_ratio > 50:
        report_lines.append(f"- ⚠️ **Analiz Notu:** {dominant_city} iline olan bağımlılık %50'nin üzerindedir. Bu ilde yaşanacak pazar kaybı genel tabloyu ciddi etkiler.")

    # 3. ZAMAN VE GELECEK PROJEKSİYONU
    this_year_count = data[data['Bitiş Yılı'] == current_year].shape[0]
    next_year_count = data[data['Bitiş Yılı'] == (current_year + 1)].shape[0]
    next_year_2 = data[data['Bitiş Yılı'] == (current_year + 2)].shape[0]
    
    report_lines.append("#### 📅 Sözleşme Vade Yapısı ve Tahminler")
    report_lines.append(f"- **{current_year} Yılı Durumu:** İçinde bulunduğumuz yıl sonuna kadar **{this_year_count}** adet sözleşme sonlanacaktır.")
    
    trend = "sabit"
    if next_year_count > this_year_count:
        trend = "artış"
        fark = next_year_count - this_year_count
        report_lines.append(f"- **📈 Yükseliş Trendi:** {current_year + 1} yılında iş yükü artacaktır. Sözleşmesi bitecek bayi sayısı **{next_year_count}** adede yükselecektir (Artış: +{fark}).")
        report_lines.append(f"- **Stratejik Öneri:** Gelecek yılki yoğunluk için şimdiden yenileme görüşmelerine başlanması, churn (kayıp) oranını düşürecektir.")
    elif next_year_count < this_year_count:
        trend = "düşüş"
        report_lines.append(f"- **📉 Rahatlama Dönemi:** {current_year + 1} yılında sözleşme trafiği azalarak **{next_year_count}** seviyesine inecektir.")
    
    report_lines.append(f"- **Uzun Vade:** {current_year + 2} yılı için projeksiyon **{next_year_2}** adet sözleşmedir.")

    # 4. RİSK ANALİZİ
    expired = data[data['Kalan Gün'] < 0].shape[0]
    urgent = data[(data['Kalan Gün'] >= 0) & (data['Kalan Gün'] < 90)].shape[0]
    mid_term = data[(data['Kalan Gün'] >= 90) & (data['Kalan Gün'] < 180)].shape[0]

    report_lines.append("#### 🚨 Risk Matrisi ve Aksiyon Planı")
    if expired > 0:
        report_lines.append(f"- 🔴 **KRİTİK:** Şu an itibarıyla süresi dolmuş ve sistemde hala aktif görünen **{expired}** adet sözleşme tespit edilmiştir. Hukuki risk oluşturabilir.")
    
    if urgent > 0:
        report_lines.append(f"- 🟠 **ACİLİYET:** Önümüzdeki 90 gün (3 ay) içinde **{urgent}** bayi ile masaya oturulmalıdır.")
        report_lines.append(f"- Bu grup toplam portföyün **%{int(urgent/total_count*100)}**'sini oluşturmaktadır.")
    else:
        report_lines.append("- 🟢 Kısa vadede (3 ay) herhangi bir sözleşme riski bulunmamaktadır.")

    if mid_term > 0:
        report_lines.append(f"- 🟡 **Orta Vade:** 3-6 ay bandında **{mid_term}** adet sözleşme takibe alınmalıdır.")

    # 5. SONUÇ VE KAPANIŞ
    report_lines.append("#### 💡 Sonuç ve Yorum")
    report_lines.append("Veriler ışığında; bölgedeki operasyonel devamlılığı sağlamak adına öncelikli olarak 'Kritik' ve 'Acil' kategorisindeki bayilere ziyaret planlanmalıdır.")
    report_lines.append(f"{dominant_city} ilindeki pazar payının korunması, bölge hedeflerinin tutturulması için hayati önem taşımaktadır.")
    
    return report_lines


if df is not None:
    # 2. YAN MENÜ (FİLTRELER) - ESKİ HALİNE DÖNDÜ
    st.sidebar.info("🕒 Veriler her gün saat 10:00'da yenilenmektedir.")
    st.sidebar.markdown("---")
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

    # Excel İndirme (Yan Menüde)
    st.sidebar.markdown("---")
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        filtered_df.to_excel(writer, index=False, sheet_name='Rapor')
    st.sidebar.download_button(
        label="📥 Raporu Excel İndir",
        data=buffer.getvalue(),
        file_name=f"Rapor_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
        mime="application/vnd.ms-excel"
    )

    st.sidebar.markdown("---")
    st.sidebar.header("📧 İletişim")
    st.sidebar.info("kerim.aksu@milangaz.com.tr")


    # 3. KARTLAR (KPI) - ESKİ HALİNE DÖNDÜ
    st.subheader("📈 Özet Bilgiler")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Görüntülenen Bayi Sayısı", len(filtered_df))
    with col2:
        st.metric("Farklı İl Sayısı", filtered_df['İl'].nunique())
    
    st.markdown("---")

    # 4. SEKME YAPISI (YENİ SEKME EKLENDİ)
    tab1, tab2, tab3 = st.tabs(["📍 Grafikler ve Analiz", "📅 Sözleşme Takip Listesi", "🧠 Yapay Zeka & Makina Analizi"])

    # --- TAB 1: GRAFİKLER (ESKİSİ GİBİ) ---
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

    # --- TAB 2: SÖZLEŞME ANALİZİ (İNTERAKTİF ÖZELLİK KORUNDU) ---
    with tab2:
        st.subheader("📅 Sözleşme Bitiş Takvimi")

        filtered_df['Bitiş Yılı'] = filtered_df['Dağıtıcı ile Yapılan Sözleşme Bitiş Tarihi'].dt.year
        filtered_df['Bitiş Ayı No'] = filtered_df['Dağıtıcı ile Yapılan Sözleşme Bitiş Tarihi'].dt.month
        
        ay_map = {1: 'Ocak', 2: 'Şubat', 3: 'Mart', 4: 'Nisan', 5: 'Mayıs', 6: 'Haziran',
                  7: 'Temmuz', 8: 'Ağustos', 9: 'Eylül', 10: 'Ekim', 11: 'Kasım', 12: 'Aralık'}
        filtered_df['Bitiş Ayı Adı'] = filtered_df['Bitiş Ayı No'].map(ay_map)

        mevcut_yillar = sorted(filtered_df['Bitiş Yılı'].dropna().unique())
        
        if len(mevcut_yillar) > 0:
            selected_year = st.selectbox("Yıl Seçiniz:", options=mevcut_yillar, index=0)
            year_df = filtered_df[filtered_df['Bitiş Yılı'] == selected_year]
            
            monthly_counts = year_df.groupby(['Bitiş Ayı No', 'Bitiş Ayı Adı']).size().reset_index(name='Sayi')
            monthly_counts = monthly_counts.sort_values('Bitiş Ayı No')

            fig_monthly = px.bar(monthly_counts, x='Bitiş Ayı Adı', y='Sayi', text='Sayi', title=f"{selected_year} Aylık Dağılım")
            st.plotly_chart(fig_monthly, use_container_width=True)
            
            st.dataframe(year_df[['Unvan', 'İl', 'Bitiş Tarihi' if 'Bitiş Tarihi' in year_df.columns else 'Dağıtıcı ile Yapılan Sözleşme Bitiş Tarihi', 'Kalan Gün']], use_container_width=True)
        else:
            st.warning("Veri yok.")

    # --- TAB 3: YENİ EKLENEN DETAYLI AI ANALİZİ ---
    with tab3:
        st.subheader("🧠 Akıllı Veri Analiz Raporu")
        st.info("Aşağıdaki rapor, soldaki menüden seçtiğiniz filtrelere (Bölge/İl) göre anlık olarak üretilmiştir.")
        
        # Raporu Oluştur
        analiz_sonucu = create_detailed_ai_report(filtered_df, selected_bolge, selected_il)
        
        # Raporu Ekrana Bas (Satır Satır)
        report_container = st.container()
        with report_container:
            for line in analiz_sonucu:
                st.markdown(line)

else:
    st.info("Lütfen YENI.xlsx dosyasını yükleyiniz.")
