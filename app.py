import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import io

# -----------------------------------------------------------------------------
# 1. SAYFA AYARLARI (En başta olmalı)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Bayi Makina Analizi", layout="wide", page_icon="📊")

# -----------------------------------------------------------------------------
# 2. GİRİŞ SİSTEMİ (AUTHENTICATION)
# -----------------------------------------------------------------------------

# Session state'de giriş durumu yoksa false olarak başlat
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

def login_screen():
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    
    with c2:
        st.markdown("<h2 style='text-align: center;'>🔒 Güvenli Giriş</h2>", unsafe_allow_html=True)
        st.info("Lütfen yetkili kullanıcı bilgilerinizi giriniz.")
        
        with st.form("login_form"):
            username = st.text_input("Kullanıcı Adı")
            password = st.text_input("Şifre", type="password")
            submit_button = st.form_submit_button("Giriş Yap", use_container_width=True)

            if submit_button:
                if username == "LO2025" and password == "OL2025":
                    st.session_state["logged_in"] = True
                    st.success("Giriş Başarılı! Yönlendiriliyorsunuz...")
                    st.rerun()
                else:
                    st.error("Hatalı kullanıcı adı veya şifre!")

# EĞER GİRİŞ YAPILMAMIŞSA SADECE LOGİN EKRANINI GÖSTER VE DUR
if not st.session_state["logged_in"]:
    login_screen()
    st.stop()  # Kodun geri kalanını okumayı durdur

# -----------------------------------------------------------------------------
# 3. ANA UYGULAMA (Giriş Başarılıysa Burası Çalışır)
# -----------------------------------------------------------------------------

# Başlık
st.title("📊 Bayi Veri ve Makina Analizi")

# Çıkış Butonu (Sağ üst köşe gibi davranması için sidebar'a ekliyoruz)
if st.sidebar.button("🚪 Çıkış Yap"):
    st.session_state["logged_in"] = False
    st.rerun()

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
            
        # --- İL İSİMLERİNİ STANDARDİZE ETME ---
        if 'İl' in df.columns:
            table = str.maketrans("iı", "İI") 
            df['Harita_İl'] = df['İl'].astype(str).apply(lambda x: x.translate(table).upper().strip())
            
        return df
    except Exception as e:
        st.error(f"Veri okunurken hata oluştu: {e}")
        return None

df = load_data()

# HARİTA KOORDİNATLARI (SABİT)
SEHIR_KOORDINATLARI = {
    "ADANA": [37.0000, 35.3213], "ADIYAMAN": [37.7648, 38.2786], "AFYONKARAHİSAR": [38.7507, 30.5567],
    "AĞRI": [39.7191, 43.0503], "AMASYA": [40.6499, 35.8353], "ANKARA": [39.9334, 32.8597],
    "ANTALYA": [36.8841, 30.7056], "ARTVİN": [41.1828, 41.8183], "AYDIN": [37.8560, 27.8416],
    "BALIKESİR": [39.6484, 27.8826], "BİLECİK": [40.1451, 29.9799], "BİNGÖL": [38.8854, 40.4980],
    "BİTLİS": [38.4006, 42.1095], "BOLU": [40.7350, 31.6061], "BURDUR": [37.7204, 30.2908],
    "BURSA": [40.1885, 29.0610], "ÇANAKKALE": [40.1553, 26.4142], "ÇANKIRI": [40.6013, 33.6134],
    "ÇORUM": [40.5506, 34.9556], "DENİZLİ": [37.7765, 29.0864], "DİYARBAKIR": [37.9144, 40.2306],
    "EDİRNE": [41.6818, 26.5623], "ELAZIĞ": [38.6810, 39.2264], "ERZİNCAN": [39.7500, 39.5000],
    "ERZURUM": [39.9000, 41.2700], "ESKİŞEHİR": [39.7767, 30.5206], "GAZİANTEP": [37.0662, 37.3833],
    "GİRESUN": [40.9128, 38.3895], "GÜMÜŞHANE": [40.4600, 39.4700], "HAKKARİ": [37.5833, 43.7333],
    "HATAY": [36.4018, 36.3498], "ISPARTA": [37.7648, 30.5566], "MERSİN": [36.8000, 34.6333],
    "İSTANBUL": [41.0082, 28.9784], "İZMİR": [38.4189, 27.1287], "KARS": [40.6167, 43.1000],
    "KASTAMONU": [41.3887, 33.7827], "KAYSERİ": [38.7312, 35.4787], "KIRKLARELİ": [41.7333, 27.2167],
    "KIRŞEHİR": [39.1425, 34.1709], "KOCAELİ": [40.8533, 29.8815], "KONYA": [37.8667, 32.4833],
    "KÜTAHYA": [39.4167, 29.9833], "MALATYA": [38.3552, 38.3095], "MANİSA": [38.6191, 27.4289],
    "KAHRAMANMARAŞ": [37.5858, 36.9371], "MARDİN": [37.3212, 40.7245], "MUĞLA": [37.2153, 28.3636],
    "MUŞ": [38.9462, 41.7539], "NEVŞEHİR": [38.6939, 34.6857], "NİĞDE": [37.9667, 34.6833],
    "ORDU": [40.9839, 37.8764], "RİZE": [41.0201, 40.5234], "SAKARYA": [40.7569, 30.3783],
    "SAMSUN": [41.2928, 36.3313], "SİİRT": [37.9333, 41.9500], "SİNOP": [42.0231, 35.1531],
    "SİVAS": [39.7477, 37.0179], "TEKİRDAĞ": [40.9833, 27.5167], "TOKAT": [40.3167, 36.5500],
    "TRABZON": [41.0015, 39.7178], "TUNCELİ": [39.1079, 39.5401], "ŞANLIURFA": [37.1591, 38.7969],
    "UŞAK": [38.6823, 29.4082], "VAN": [38.4891, 43.4089], "YOZGAT": [39.8181, 34.8147],
    "ZONGULDAK": [41.4564, 31.7987], "AKSARAY": [38.3687, 34.0370], "BAYBURT": [40.2552, 40.2249],
    "KARAMAN": [37.1759, 33.2287], "KIRIKKALE": [39.8468, 33.5153], "BATMAN": [37.8812, 41.1351],
    "ŞIRNAK": [37.5164, 42.4611], "BARTIN": [41.6344, 32.3375], "ARDAHAN": [41.1105, 42.7022],
    "IĞDIR": [39.9196, 44.0404], "YALOVA": [40.6500, 29.2667], "KARABÜK": [41.2061, 32.6204],
    "KİLİS": [36.7184, 37.1212], "OSMANİYE": [37.0742, 36.2467], "DÜZCE": [40.8438, 31.1565]
}

# --- MAKİNA ANALİZİ RAPORU ---
def create_machine_analysis_report(data):
    if data is None or data.empty:
        return

    today = datetime.now()
    current_year = today.year
    next_year = current_year + 1
    
    st.markdown(f"### 📊 Detaylı Makina Analiz Raporu ({next_year} Vizyonu)")
    st.markdown("---")

    next_year_data = data[data['Bitiş Yılı'] == next_year]
    total_next = len(next_year_data)

    if next_year_data.empty:
        st.warning(f"{next_year} yılı için veri yok.")
        return

    # 1. BÖLÜM: ZAMAN VE İL ANALİZİ
    st.markdown(f"#### 1. {next_year} Yılı Genel Projeksiyonu")
    peak_month_idx = next_year_data['Bitiş Ayı No'].value_counts().idxmax()
    peak_count = next_year_data['Bitiş Ayı No'].value_counts().max()
    ay_map_tr = {1: 'Ocak', 2: 'Şubat', 3: 'Mart', 4: 'Nisan', 5: 'Mayıs', 6: 'Haziran', 7: 'Temmuz', 8: 'Ağustos', 9: 'Eylül', 10: 'Ekim', 11: 'Kasım', 12: 'Aralık'}
    peak_month_name = ay_map_tr[peak_month_idx]

    st.info(f"📅 **Zaman Analizi:** {next_year} yılında toplam **{total_next}** adet sözleşme sona erecektir. En yoğun dönem **{peak_month_name}** ayıdır (Toplam: {peak_count}).")

    st.markdown(f"**📍 {next_year} Yılı İl Bazlı Risk Tablosu:**")
    city_counts = next_year_data['İl'].value_counts().reset_index()
    city_counts.columns = ['İl Adı', 'Bitecek Sözleşme Sayısı']
    city_counts['Pay (%)'] = (city_counts['Bitecek Sözleşme Sayısı'] / total_next * 100).round(1)
    st.dataframe(city_counts, use_container_width=True, hide_index=True)

    st.markdown("---")

    # 2. BÖLÜM: ADF ANALİZİ
    st.markdown(f"#### 2. {next_year} Yılında Bitecek Sözleşmelerin ADF Analizi")
    if 'ADF' in next_year_data.columns:
        adf_counts = next_year_data['ADF'].value_counts()
        if not adf_counts.empty:
            top_adf = adf_counts.index[0]
            top_adf_count = adf_counts.iloc[0]
            
            col1, col2 = st.columns([2, 1])
            with col1:
                st.write(f"Gelecek yıl en çok **{top_adf}** grubuna ait sözleşmeler ({top_adf_count} adet) sona erecektir.")
                adf_df = adf_counts.reset_index()
                adf_df.columns = ['ADF Kodu', 'Bitecek Adet']
                adf_df['Pay (%)'] = (adf_df['Bitecek Adet'] / total_next * 100).round(1)
                st.dataframe(adf_df, use_container_width=True, hide_index=True)
            with col2:
                fig_adf = px.pie(adf_df, names='ADF Kodu', values='Bitecek Adet', title=f"{next_year} ADF Dağılımı", hole=0.4)
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

    st.sidebar.markdown("---")
    st.sidebar.header("📥 Rapor İndir")
    try:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            filtered_df.to_excel(writer, index=False, sheet_name='Rapor')
        st.sidebar.download_button(label="📄 Excel İndir", data=buffer.getvalue(), file_name=f"Rapor_{datetime.now().strftime('%Y-%m-%d')}.xlsx", mime="application/vnd.ms-excel")
    except:
        pass

    st.sidebar.markdown("---")
    st.sidebar.info("kerim.aksu@milangaz.com.tr")

    # KARTLAR
    st.subheader("📈 Genel Durum")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Toplam Bayi", len(filtered_df))
    with col2:
        st.metric("İl Sayısı", filtered_df['İl'].nunique())
    
    st.markdown("---")

    # SEKME YAPISI
    tab1, tab2, tab3 = st.tabs(["📍 Harita & Grafikler", "📅 Sözleşme Takip", "🧠 Makina Analizi"])

    # --- TAB 1 ---
    with tab1:
        # HARİTA
        st.subheader("🗺️ Türkiye Bayi Yoğunluk Haritası")
        map_data = filtered_df['Harita_İl'].value_counts().reset_index()
        map_data.columns = ['Harita_İl', 'Sayı']
        
        def get_lat(city): return SEHIR_KOORDINATLARI.get(city, [None, None])[0]
        def get_lon(city): return SEHIR_KOORDINATLARI.get(city, [None, None])[1]
        
        map_data['lat'] = map_data['Harita_İl'].apply(get_lat)
        map_data['lon'] = map_data['Harita_İl'].apply(get_lon)
        map_data = map_data.dropna(subset=['lat', 'lon'])

        if not map_data.empty:
            fig_map = px.scatter_mapbox(
                map_data, lat="lat", lon="lon", size="Sayı", color="Sayı",
                hover_name="Harita_İl", color_continuous_scale=px.colors.sequential.Viridis,
                size_max=40, zoom=4.8, center={"lat": 39.0, "lon": 35.0},
                title="İl Bazlı Bayi Dağılımı (Büyüklük = Bayi Sayısı)"
            )
            fig_map.update_layout(mapbox_style="carto-positron", margin={"r":0,"t":40,"l":0,"b":0}, height=500)
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.warning("Harita verisi oluşturulamadı.")

        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Bölge Dağılımı")
            fig_bolge = px.pie(filtered_df, names='BÖLGE', title='Bölge Bazlı Oranlar', hole=0.4)
            st.plotly_chart(fig_bolge, use_container_width=True)
        with c2:
            st.subheader("İl Bazlı Dağılım (Tümü)")
            all_cities = filtered_df['İl'].value_counts().reset_index()
            all_cities.columns = ['İl', 'Sayı']
            fig_all = px.bar(all_cities, x='İl', y='Sayı', color='Sayı', title='Tüm İllerin Dağılımı')
            st.plotly_chart(fig_all, use_container_width=True)
        
        if 'ADF' in filtered_df.columns:
            st.subheader("Genel ADF Dağılımı")
            adf_genel = filtered_df['ADF'].value_counts().reset_index()
            adf_genel.columns = ['ADF', 'Sayı']
            fig_adf = px.bar(adf_genel, x='ADF', y='Sayı', color='Sayı', title="Portföy ADF Dağılımı")
            st.plotly_chart(fig_adf, use_container_width=True)

    # --- TAB 2 (SÖZLEŞME TAKİP) ---
    with tab2:
        st.subheader("📅 Yıllık Takip")
        mevcut_yillar = sorted(filtered_df['Bitiş Yılı'].dropna().unique())
        if len(mevcut_yillar) > 0:
            selected_year = st.selectbox("Yıl Seçiniz:", options=mevcut_yillar)
            year_df = filtered_df[filtered_df['Bitiş Yılı'] == selected_year].copy()
            st.metric(f"{selected_year} Toplam", len(year_df))
            
            c_g1, c_g2 = st.columns([2,1])
            with c_g1:
                monthly_counts = year_df.groupby(['Bitiş Ayı No', 'Bitiş Ayı Adı']).size().reset_index(name='Sayi').sort_values('Bitiş Ayı No')
                
                fig_monthly = px.bar(
                    monthly_counts, 
                    x='Bitiş Ayı Adı', 
                    y='Sayi', 
                    text='Sayi',
                    title=f"{selected_year} Aylık Dağılım", 
                    color='Sayi'
                )
                fig_monthly.update_traces(textposition='outside', textfont=dict(size=14, color='black'))
                max_val = monthly_counts['Sayi'].max()
                fig_monthly.update_layout(yaxis=dict(range=[0, max_val * 1.2]), clickmode='event+select')
                
                selected_event = st.plotly_chart(fig_monthly, use_container_width=True, on_select="rerun")
            
            with c_g2:
                if 'ADF' in year_df.columns:
                    adf_y = year_df['ADF'].value_counts().reset_index()
                    adf_y.columns=['ADF','S']
                    fig_ay = px.pie(adf_y, names='ADF', values='S', title=f"{selected_year} ADF", hole=0.3)
                    st.plotly_chart(fig_ay, use_container_width=True)

            st.info("Tabloyu filtrelemek için grafiğe tıklayın. Sıfırlamak için çift tıklayın.")
            
            table_data = year_df.copy()
            if selected_event and selected_event['selection']['points']:
                tiklanan_ay = selected_event['selection']['points'][0]['x']
                table_data = year_df[year_df['Bitiş Ayı Adı'] == tiklanan_ay]
            
            table_data = table_data.sort_values('Kalan Gün')
            table_data['Bitiş Tarihi'] = table_data['Dağıtıcı ile Yapılan Sözleşme Bitiş Tarihi'].dt.strftime('%d/%m/%Y')
            cols = [c for c in ['Unvan', 'İl', 'ADF', 'Bitiş Tarihi', 'Kalan Gün'] if c in table_data.columns]
            
            def highlight(val):
                if isinstance(val, int):
                    if val < 0: return 'background-color: #ffcccc'
                    elif val < 90: return 'background-color: #ffffcc'
                return ''
            
            st.dataframe(table_data[cols].style.map(highlight, subset=['Kalan Gün']), use_container_width=True, hide_index=True)

    # --- TAB 3 ---
    with tab3:
        create_machine_analysis_report(filtered_df)

else:
    st.info("Lütfen YENI.xlsx dosyasını yükleyiniz.")
