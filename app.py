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
        # Dosya adının YENI.xlsx olduğundan emin olun
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
    st.sidebar.info("🕒 Not: Veriler her gün saat 10:00'da yenilenmektedir.")
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

    # --- LİNKLER VE İLETİŞİM ---
    st.sidebar.markdown("---") 
    st.sidebar.header("🔗 Rapor Bağlantıları")
    st.sidebar.markdown("📊 [EPDK Sektör Raporu](https://pazarpayi.streamlit.app/)")
    st.sidebar.markdown("⛽ [Akaryakıt Lisans Raporu](https://akartakip.streamlit.app/)")
    st.sidebar.markdown("🔥 [LPG Lisans Raporu](https://lpgtakip.streamlit.app/)")
    
    st.sidebar.markdown("---") 
    st.sidebar.header("📧 İletişim")
    st.sidebar.info("kerim.aksu@milangaz.com.tr")

    # 3. KARTLAR (KPI) - ADF KISMI KALDIRILDI
    st.subheader("📈 Özet Bilgiler")
    
    # 3 Sütun yerine 2 Sütun yapıyoruz
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Toplam Bayi/Kayıt", len(filtered_df))
    with col2:
        st.metric("Farklı İl Sayısı", filtered_df['İl'].nunique())
    
    st.markdown("---")

    # 4. SEKME YAPISI
    tab1, tab2 = st.tabs(["📍 Bölge ve İl Analizi", "📅 Sözleşme Takip Listesi"])

    # --- TAB 1: GRAFİKLER ---
    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Bölge Dağılımı")
            fig_bolge = px.pie(filtered_df, names='BÖLGE', title='Bölge Bazlı Oranlar', hole=0.4)
            st.plotly_chart(fig_bolge, use_container_width=True)
        
        with c2:
            st.subheader("İl Bazlı En Yoğun 10 İl")
            top_cities = filtered_df['İl'].value_counts().nlargest(10).reset_index()
            top_cities.columns = ['İl', 'Sayı']
            fig_top_cities = px.bar(top_cities, x='İl', y='Sayı', color='Sayı', title='En Çok Bayi Olan 10 İl')
            st.plotly_chart(fig_top_cities, use_container_width=True)

        st.subheader("Tüm İllerin Dağılımı")
        city_counts = filtered_df['İl'].value_counts().reset_index()
        city_counts.columns = ['İl', 'Sayı']
        fig_il = px.bar(city_counts, x='İl', y='Sayı', text='Sayı', color='Sayı', height=500, title='İl Bazlı Bayi Sayıları (Tam Liste)')
        fig_il.update_traces(textposition='outside')
        st.plotly_chart(fig_il, use_container_width=True)

    # --- TAB 2: SÖZLEŞME ANALİZİ (YENİLENMİŞ) ---
    with tab2:
        st.subheader("📅 Sözleşme Bitiş Takvimi ve Analizi")

        # Veriyi Hazırlama
        contract_df = filtered_df[filtered_df['Dağıtıcı ile Yapılan Sözleşme Bitiş Tarihi'].notna()].copy()
        
        # Yıl ve Ay Bilgilerini Çıkarma
        contract_df['Bitiş Yılı'] = contract_df['Dağıtıcı ile Yapılan Sözleşme Bitiş Tarihi'].dt.year
        contract_df['Bitiş Ayı No'] = contract_df['Dağıtıcı ile Yapılan Sözleşme Bitiş Tarihi'].dt.month
        
        # Türkçe Ay İsimleri Haritası
        ay_map = {
            1: 'Ocak', 2: 'Şubat', 3: 'Mart', 4: 'Nisan', 5: 'Mayıs', 6: 'Haziran',
            7: 'Temmuz', 8: 'Ağustos', 9: 'Eylül', 10: 'Ekim', 11: 'Kasım', 12: 'Aralık'
        }
        contract_df['Bitiş Ayı Adı'] = contract_df['Bitiş Ayı No'].map(ay_map)

        # 1. ADIM: YIL SEÇİMİ
        mevcut_yillar = sorted(contract_df['Bitiş Yılı'].unique())
        if len(mevcut_yillar) > 0:
            selected_year = st.selectbox("Analiz Etmek İstediğiniz Yılı Seçiniz:", options=mevcut_yillar, index=0)
            
            # Seçilen yıla göre filtrele
            year_filtered_df = contract_df[contract_df['Bitiş Yılı'] == selected_year]
            
            # 2. ADIM: AYLIK GRAFİK OLUŞTURMA
            monthly_counts = year_filtered_df.groupby(['Bitiş Ayı No', 'Bitiş Ayı Adı']).size().reset_index(name='Sözleşme Sayısı')
            monthly_counts = monthly_counts.sort_values('Bitiş Ayı No') # Ayları sıraya diz

            st.markdown(f"### 📊 {selected_year} Yılı Aylık Sözleşme Bitiş Dağılımı")
            st.info("💡 Tabloyu filtrelemek için aşağıdaki grafikten bir aya **tıklayınız**. Seçimi kaldırmak için grafiğin boş bir yerine çift tıklayınız.")

            fig_monthly = px.bar(
                monthly_counts, 
                x='Bitiş Ayı Adı', 
                y='Sözleşme Sayısı',
                text='Sözleşme Sayısı',
                color='Sözleşme Sayısı',
                title=f"{selected_year} Yılı Aylık Dağılım",
                labels={'Bitiş Ayı Adı': 'Ay', 'Sözleşme Sayısı': 'Bitecek Sözleşme'}
            )
            fig_monthly.update_traces(textposition='outside')
            fig_monthly.update_layout(clickmode='event+select') # Tıklama özelliği

            # Grafiği çiz ve tıklama olayını yakala
            # on_select="rerun" Streamlit'in yeni sürümlerinde (1.35+) çalışır.
            selected_event = st.plotly_chart(fig_monthly, use_container_width=True, on_select="rerun")
            
            # 3. ADIM: GRAFİKTEN GELEN SEÇİME GÖRE TABLOYU FİLTRELEME
            final_table_df = year_filtered_df.copy() # Varsayılan olarak o yılın tamamı
            secilen_ay = None

            # Eğer bir seçim yapıldıysa (Streamlit 1.35+ on_select dönüşü)
            if selected_event and selected_event['selection']['points']:
                point = selected_event['selection']['points'][0]
                if 'x' in point:
                    secilen_ay = point['x'] # Örn: 'Ocak'
                    final_table_df = year_filtered_df[year_filtered_df['Bitiş Ayı Adı'] == secilen_ay]
                    st.success(f"✅ Şu an sadece **{secilen_ay} {selected_year}** döneminde biten sözleşmeler listeleniyor.")
            else:
                st.caption(f"📋 Şu an **{selected_year}** yılının tamamı listeleniyor.")

            # 4. ADIM: TABLOYU GÖSTERME (Kalan Gün Hesabı ve Renklendirme)
            today = pd.to_datetime("today")
            final_table_df['Kalan Gün'] = (final_table_df['Dağıtıcı ile Yapılan Sözleşme Bitiş Tarihi'] - today).dt.days
            final_table_df = final_table_df.sort_values(by='Kalan Gün', ascending=True)
            final_table_df['Bitiş Tarihi'] = final_table_df['Dağıtıcı ile Yapılan Sözleşme Bitiş Tarihi'].dt.strftime('%d/%m/%Y')

            display_cols = ['Unvan', 'BÖLGE', 'İl', 'ADF', 'Bitiş Tarihi', 'Kalan Gün']
            final_cols = [c for c in display_cols if c in final_table_df.columns]

            def highlight_urgent(val):
                color = ''
                if val < 0:
                    color = 'background-color: #ffcccc; color: black' # Süresi geçmiş (Kırmızı)
                elif val < 90:
                    color = 'background-color: #ffffcc; color: black' # Yaklaşan (Sarı)
                return color

            st.dataframe(
                final_table_df[final_cols].style.applymap(highlight_urgent, subset=['Kalan Gün']),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning("Görüntülenecek tarih verisi bulunamadı.")

else:
    st.info("Lütfen YENI.xlsx dosyasını program klasörüne ekleyiniz.")
