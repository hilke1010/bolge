import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import io

# Sayfa Ayarları
st.set_page_config(page_title="Bayi Analiz Paneli", layout="wide", page_icon="📊")

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
            
        return df
    except Exception as e:
        st.error(f"Veri okunurken hata oluştu: {e}")
        return None

df = load_data()

# --- YENİ EKLENEN FONKSİYON: BÖLGESEL DETAYLI YORUM ---
def generate_regional_commentary(region_df, region_name):
    comments = []
    
    # Veri Hazırlığı
    total_bayi = len(region_df)
    top_city = region_df['İl'].mode()[0] if not region_df.empty else "Bilinmiyor"
    top_city_count = region_df[region_df['İl'] == top_city].shape[0]
    
    # Yıl Analizi
    year_counts = region_df['Bitiş Yılı'].value_counts().sort_index()
    
    # 1. Giriş Yorumu
    comments.append(f"📌 **{region_name} Genel Görünüm:** Bölgede toplam **{total_bayi}** adet makina/bayi bulunmaktadır. "
                    f"Operasyonun kalbi **{top_city}** ilinde atmaktadır (Toplamın %{int(top_city_count/total_bayi*100)}'si).")
    
    # 2. Yıl Kıyaslaması (2025 vs 2026 vb.)
    current_year = datetime.now().year
    count_now = year_counts.get(current_year, 0)
    count_next = year_counts.get(current_year + 1, 0)
    count_next2 = year_counts.get(current_year + 2, 0)

    trend_msg = f"📉 **Sözleşme Takvimi:** {current_year} yılında **{count_now}** adet sözleşme sona erecektir. "
    
    if count_next > count_now:
        trend_msg += f"{current_year + 1} yılında ise bu sayı artarak **{count_next}** adede çıkacaktır. **Gelecek yıl operasyonel yük artacaktır.**"
    elif count_next < count_now and count_next > 0:
        trend_msg += f"{current_year + 1} yılında ise sayı düşerek **{count_next}** olacaktır. Daha rahat bir yıl öngörülmektedir."
    else:
        trend_msg += f"{current_year + 1} yılı için henüz yoğun bir bitiş görünmemektedir."
        
    comments.append(trend_msg)
    
    # 3. Risk Analizi
    riskli_sayi = region_df[region_df['Kalan Gün'] < 90].shape[0]
    if riskli_sayi > 0:
        comments.append(f"⚠️ **Kritik Uyarı:** Bölgede önümüzdeki 3 ay içerisinde yenilenmesi gereken **{riskli_sayi}** adet acil sözleşme bulunmaktadır. Ekiplerin bu noktalara odaklanması önerilir.")
    else:
        comments.append("✅ **Risk Durumu:** Kısa vadede (90 gün) acil müdahale gerektiren bir sözleşme bulunmamaktadır.")

    return comments

if df is not None:
    # --- YAN MENÜ TASARIMI ---
    st.sidebar.title("Menü")
    page = st.sidebar.radio("Gitmek İstediğiniz Sayfa:", ["🏠 Genel Özet (Dashboard)", "🔍 Bölge & Makina Analizi"])
    
    st.sidebar.markdown("---")
    st.sidebar.info("🕒 Veriler her gün 10:00'da güncellenir.")

    # --- EXCEL İNDİRME ---
    st.sidebar.header("📥 Veriyi İndir")
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Tüm_Veri')
    
    st.sidebar.download_button(
        label="📄 Tüm Listeyi Excel İndir",
        data=buffer.getvalue(),
        file_name=f"Tum_Bayi_Listesi_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
        mime="application/vnd.ms-excel"
    )

    # ==========================================
    # SAYFA 1: GENEL ÖZET (SADELEŞTİRİLMİŞ)
    # ==========================================
    if page == "🏠 Genel Özet (Dashboard)":
        st.title("🏢 Genel Yönetim Paneli")
        st.markdown("Türkiye geneli bayi ve sözleşme durumunun kuş bakışı görünümü.")
        st.markdown("---")

        # KPI Kartları
        col1, col2, col3 = st.columns(3)
        col1.metric("Toplam Bayi", len(df), delta_color="normal")
        col2.metric("Aktif İl Sayısı", df['İl'].nunique())
        col3.metric("Bu Yıl Bitecek Sözleşme", df[df['Bitiş Yılı'] == datetime.now().year].shape[0], delta="-Risk")

        st.markdown("---")
        
        # Sadece Pasta Grafik
        c1, c2 = st.columns([2, 1])
        with c1:
            st.subheader("Türkiye Geneli Bölgesel Dağılım")
            fig_pie = px.pie(df, names='BÖLGE', values='BÖLGE', title='Bölge Ağırlıkları', hole=0.4)
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with c2:
            st.info("💡 **Bilgi:** Detaylı analizler, iller bazında kırılımlar ve yıllık karşılaştırmalar için sol menüden **'Bölge & Makina Analizi'** sayfasına gidiniz.")

    # ==========================================
    # SAYFA 2: DETAYLI BÖLGE ANALİZİ (YENİ)
    # ==========================================
    elif page == "🔍 Bölge & Makina Analizi":
        st.title("🔍 Bölgesel Makina ve Sözleşme Analizi")
        st.markdown("Seçilen bölgeye özel stratejik raporlama ekranı.")
        
        # Bölge Seçimi
        bolgeler = sorted(df['BÖLGE'].unique().tolist())
        selected_region = st.selectbox("Analiz Edilecek Bölgeyi Seçiniz:", bolgeler)
        
        # Veriyi Filtrele
        region_df = df[df['BÖLGE'] == selected_region].copy()
        
        st.markdown("---")
        
        # --- YAPAY ZEKA YORUM KISMI ---
        st.subheader(f"🤖 {selected_region} Bölgesi Yapay Zeka Raporu")
        
        comments = generate_regional_commentary(region_df, selected_region)
        
        # Yorumları Güzel Kutular İçinde Göster
        col_text, col_stat = st.columns([3, 1])
        
        with col_text:
            for comment in comments:
                if "⚠️" in comment:
                    st.error(comment)
                elif "📉" in comment:
                    st.warning(comment)
                else:
                    st.success(comment)
        
        with col_stat:
            st.metric(f"{selected_region} Toplam", len(region_df))
            st.metric("En Yoğun İl", region_df['İl'].mode()[0])

        st.markdown("---")

        # --- GRAFİKLER ---
        tab1, tab2 = st.tabs(["📈 Yıllık Trend Analizi", "📋 Detaylı Liste"])
        
        with tab1:
            c1, c2 = st.columns(2)
            
            # Grafik 1: Yıllara Göre Bitiş
            with c1:
                st.subheader("Yıllara Göre Sözleşme Bitiş Takvimi")
                year_counts = region_df['Bitiş Yılı'].value_counts().reset_index()
                year_counts.columns = ['Yıl', 'Adet']
                year_counts = year_counts.sort_values('Yıl')
                
                fig_bar = px.bar(year_counts, x='Yıl', y='Adet', text='Adet', color='Adet', 
                                 title=f"{selected_region} - Yıllık Bitiş Dağılımı")
                st.plotly_chart(fig_bar, use_container_width=True)
                
            # Grafik 2: İllere Göre Dağılım
            with c2:
                st.subheader("Bölge İçi İl Dağılımı")
                city_counts = region_df['İl'].value_counts().reset_index()
                city_counts.columns = ['İl', 'Adet']
                
                fig_city = px.pie(city_counts, names='İl', values='Adet', title=f"{selected_region} İller")
                st.plotly_chart(fig_city, use_container_width=True)

        with tab2:
            st.subheader(f"{selected_region} Bölgesi Detaylı Bayi Listesi")
            
            # Tabloyu Düzenle
            region_df = region_df.sort_values(by='Kalan Gün')
            display_cols = ['Unvan', 'İl', 'ADF', 'Dağıtıcı ile Yapılan Sözleşme Başlangıç Tarihi', 'Dağıtıcı ile Yapılan Sözleşme Bitiş Tarihi', 'Kalan Gün']
            # Sütun varsa seç
            final_cols = [c for c in display_cols if c in region_df.columns]
            
            # Tarihleri string yap (görüntü bozulmasın)
            for col in ['Dağıtıcı ile Yapılan Sözleşme Başlangıç Tarihi', 'Dağıtıcı ile Yapılan Sözleşme Bitiş Tarihi']:
                if col in region_df.columns:
                    region_df[col] = region_df[col].dt.strftime('%d-%m-%Y')

            st.dataframe(region_df[final_cols], use_container_width=True, hide_index=True)

else:
    st.info("Lütfen YENI.xlsx dosyasını yükleyiniz.")
