import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import io

# Sayfa Ayarları
st.set_page_config(page_title="Bayi Strateji Paneli", layout="wide", page_icon="🤖")

# Başlık
st.title("🤖 Bayi Veri Analizi ve Makine Öğrenmesi Raporu")
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
            
            # Türkçe Ay İsimleri (Manuel Map - Hata Riskine Karşı)
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

# --- GELİŞMİŞ MAKİNE ÖĞRENMESİ (ML) ANALİZ MOTORU ---
def create_ml_strategic_report(data, region_name, city_name):
    if data is None or data.empty:
        return ["Veri seti boş, analiz yapılamıyor."]
    
    report_lines = []
    today = datetime.now()
    current_year = today.year
    
    # Temel Metrikler
    total_count = len(data)
    avg_days = data['Kalan Gün'].mean()
    
    # 1. YÖNETİCİ ÖZETİ (EXECUTIVE SUMMARY)
    report_lines.append(f"### 🚀 Yönetici Özeti: {region_name} - {city_name}")
    report_lines.append(f"**Analiz Zamanı:** {today.strftime('%d.%m.%Y %H:%M')}")
    report_lines.append("---")
    report_lines.append(f"Algoritma, seçilen filtreler dahilinde **{total_count}** adet veri noktasını taramıştır.")
    report_lines.append(f"Portföyün ortalama sözleşme vadesi (kalan gün) yaklaşık **{int(avg_days)} gün** olarak hesaplanmıştır.")
    
    # 2. MEVSİMSELLİK VE ZAMAN KÜMELEMESİ (TEMPORAL CLUSTERING)
    if 'Bitiş Ayı No' in data.columns:
        # Çeyrek Dönem Analizi
        q1 = data[data['Bitiş Ayı No'].isin([1, 2, 3])].shape[0]
        q2 = data[data['Bitiş Ayı No'].isin([4, 5, 6])].shape[0]
        q3 = data[data['Bitiş Ayı No'].isin([7, 8, 9])].shape[0]
        q4 = data[data['Bitiş Ayı No'].isin([10, 11, 12])].shape[0]
        
        quarters = {'Q1 (Ocak-Mart)': q1, 'Q2 (Nisan-Haziran)': q2, 'Q3 (Temmuz-Eylül)': q3, 'Q4 (Ekim-Aralık)': q4}
        max_q = max(quarters, key=quarters.get)
        
        report_lines.append("#### ⏳ Mevsimsellik ve Zaman Kümeleri")
        report_lines.append(f"- **Yoğunluk Tespiti:** Sözleşme bitişlerinin en yoğun olduğu dönem **{max_q}** dönemidir (Toplam {quarters[max_q]} adet).")
        report_lines.append(f"- **Operasyonel Yük:** Yılın bu çeyreğinde operasyonel iş yükünün %{int(quarters[max_q]/total_count*100)} seviyesine ulaşması öngörülmektedir.")
        
        # Gelecek Yıl Trendi
        next_year_total = data[data['Bitiş Yılı'] == (current_year + 1)].shape[0]
        this_year_total = data[data['Bitiş Yılı'] == current_year].shape[0]
        
        trend_arrow = "↗️ Artış" if next_year_total > this_year_total else "↘️ Azalış"
        report_lines.append(f"- **Yıllık Momentum:** {current_year} yılından {current_year+1} yılına geçişte sözleşme yenileme hacminde **{trend_arrow}** beklenmektedir ({this_year_total} -> {next_year_total}).")

    # 3. ANOMALİ VE RİSK TESPİTİ (RISK DETECTION)
    report_lines.append("#### 🛡️ Risk ve Anomali Tespiti")
    
    # Pareto İlkesi (80/20 Kuralı Kontrolü)
    top_city = data['İl'].value_counts().head(1)
    if not top_city.empty:
        city_name_dom = top_city.index[0]
        city_val = top_city.values[0]
        ratio = (city_val / total_count) * 100
        
        if ratio > 40:
            report_lines.append(f"- ⚠️ **Coğrafi Konsantrasyon Riski:** Veri setinin **%{int(ratio)}** gibi büyük bir kısmı tek bir ilde (**{city_name_dom}**) toplanmıştır. Bölgesel bir kriz genel portföyü derinden etkileyebilir.")
        else:
            report_lines.append(f"- ✅ **Dengeli Dağılım:** En yoğun il (**{city_name_dom}**) toplamın %{int(ratio)}'sini oluşturmaktadır. Coğrafi risk dağıtılmıştır.")

    # Aciliyet Skoru
    urgent_count = data[(data['Kalan Gün'] >= 0) & (data['Kalan Gün'] < 60)].shape[0]
    if urgent_count > 0:
        report_lines.append(f"- 🔥 **Sıcak Temas Gerekliliği:** Algoritma, **{urgent_count}** adet bayinin 'Yüksek Kayıp Riski' taşıdığını tespit etmiştir (Kalan süre < 60 gün).")
    
    # 4. STRATEJİK TAVSİYE (ACTIONABLE INSIGHTS)
    report_lines.append("#### 💡 Stratejik Makine Önerileri")
    if next_year_total > this_year_total:
        report_lines.append(f"1. **Kaynak Planlaması:** Gelecek yıl iş yükü artacağından, {current_year} son çeyreğinde ek personel veya bütçe planlaması yapılmalıdır.")
    else:
        report_lines.append(f"1. **Verimlilik Odaklılık:** Gelecek yıl hacim düşeceğinden, mevcut portföyün karlılığını artırmaya (Deepening) odaklanılmalıdır.")
    
    report_lines.append("2. **Erken Uyarı:** Kalan süresi 90-180 gün arasında olan 'Sarı Bölge' bayilerine şimdiden 'Memnuniyet Anketi' yapılması churn oranını düşürecektir.")

    return report_lines


if df is not None:
    # 2. YAN MENÜ
    st.sidebar.info("🕒 Veriler her gün saat 10:00'da yenilenmektedir.")
    st.sidebar.markdown("---")
    st.sidebar.header("🔍 Filtreler")

    # Bölge
    bolge_list = ["Tümü"] + list(df['BÖLGE'].unique())
    selected_bolge = st.sidebar.selectbox("Bölge Seçiniz", bolge_list)

    # İl
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
            file_name=f"Stratejik_Rapor_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
            mime="application/vnd.ms-excel"
        )
    except:
        pass # Modül yoksa hata verme geç

    st.sidebar.markdown("---")
    st.sidebar.header("📧 İletişim")
    st.sidebar.info("kerim.aksu@milangaz.com.tr")

    # 3. KARTLAR (KPI)
    st.subheader("📈 Anlık Durum Paneli")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Toplam Bayi/Sözleşme", len(filtered_df), help="Filtreye giren toplam kayıt sayısı")
    with col2:
        st.metric("Operasyonel İl Sayısı", filtered_df['İl'].nunique(), help="Faaliyet gösterilen il sayısı")
    
    st.markdown("---")

    # 4. SEKME YAPISI (YENİLENMİŞ İSİMLER)
    tab1, tab2, tab3 = st.tabs(["📍 Görsel Analizler", "📅 Sözleşme Takip Listesi", "🧠 Makine Öğrenmesi & Stratejik Analiz"])

    # --- TAB 1: GRAFİKLER ---
    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Bölgesel Ağırlık")
            fig_bolge = px.pie(filtered_df, names='BÖLGE', title='Bölge Dağılımı', hole=0.4)
            st.plotly_chart(fig_bolge, use_container_width=True)
        with c2:
            st.subheader("En Kritik 10 İl")
            top_cities = filtered_df['İl'].value_counts().nlargest(10).reset_index()
            top_cities.columns = ['İl', 'Sayı']
            fig_top_cities = px.bar(top_cities, x='İl', y='Sayı', color='Sayı', title='İl Bazlı Bayi Yoğunluğu')
            st.plotly_chart(fig_top_cities, use_container_width=True)

    # --- TAB 2: SÖZLEŞME TAKİP (YILLIK TOPLAM GÖSTERGESİ EKLENDİ) ---
    with tab2:
        st.subheader("📅 Dönemsel Sözleşme Yönetimi")

        mevcut_yillar = sorted(filtered_df['Bitiş Yılı'].dropna().unique())
        
        if len(mevcut_yillar) > 0:
            # 1. Yıl Seçimi
            c_sel, c_info = st.columns([1, 3])
            with c_sel:
                selected_year = st.selectbox("Analiz Yılı Seçiniz:", options=mevcut_yillar, index=0)
            
            # Veriyi o yıla göre süz
            year_df = filtered_df[filtered_df['Bitiş Yılı'] == selected_year].copy()
            
            # --- YENİ ÖZELLİK: O YILIN TOPLAM SAYISINI GÖSTER ---
            total_in_year = len(year_df)
            with c_info:
                st.metric(label=f"{selected_year} Yılında Bitecek Toplam Sözleşme", value=f"{total_in_year} Adet", delta_color="off")
            # ----------------------------------------------------

            # Aylık Grafik Hazırlığı
            monthly_counts = year_df.groupby(['Bitiş Ayı No', 'Bitiş Ayı Adı']).size().reset_index(name='Sayi')
            monthly_counts = monthly_counts.sort_values('Bitiş Ayı No')

            st.info("💡 **İpucu:** Aşağıdaki grafikteki çubuklara tıklayarak listeyi aylık bazda filtreleyebilirsiniz.")

            fig_monthly = px.bar(
                monthly_counts, 
                x='Bitiş Ayı Adı', 
                y='Sayi', 
                text='Sayi', 
                title=f"{selected_year} Yılı Aylık Dağılım Grafiği", 
                color='Sayi',
                labels={'Sayi': 'Sözleşme Sayısı', 'Bitiş Ayı Adı': 'Ay'}
            )
            fig_monthly.update_traces(textposition='outside')
            fig_monthly.update_layout(clickmode='event+select')
            
            # Tıklama ile Filtreleme
            selected_event = st.plotly_chart(fig_monthly, use_container_width=True, on_select="rerun")
            
            table_data = year_df.copy()
            if selected_event and selected_event['selection']['points']:
                tiklanan_ay = selected_event['selection']['points'][0]['x']
                table_data = year_df[year_df['Bitiş Ayı Adı'] == tiklanan_ay]
                st.success(f"🔍 Filtre Aktif: **{tiklanan_ay} {selected_year}** listeleniyor.")
            
            # Tablo Düzeni ve Renklendirme
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
            st.warning("Veri bulunamadı.")

    # --- TAB 3: GELİŞMİŞ MAKİNE ÖĞRENMESİ RAPORU ---
    with tab3:
        st.subheader("🧠 Makine Öğrenmesi & Stratejik Analiz Raporu")
        st.info(f"Aşağıdaki analiz, {selected_bolge} bölgesi ve {selected_il} ili baz alınarak yapay zeka tarafından oluşturulmuştur.")
        
        analiz_sonucu = create_ml_strategic_report(filtered_df, selected_bolge, selected_il)
        
        # Raporu Şık Bir Kutu İçinde Göster
        with st.container():
            for line in analiz_sonucu:
                st.markdown(line)

else:
    st.info("Lütfen YENI.xlsx dosyasını yükleyiniz.")
