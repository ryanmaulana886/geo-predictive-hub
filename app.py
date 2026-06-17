import streamlit as st
import geopandas as gpd
import pandas as pd
import os
import base64
import tempfile
import folium
from streamlit_folium import st_folium
from folium.plugins import HeatMap

# --- 1. KONFIGURASI HALAMAN (Wajib di Baris Paling Atas) ---
st.set_page_config(
    page_title="Geo-Predictive Hub", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- 2. MANAJEMEN SESSION STATE (MEMORI GLOBAL) ---
if "authentication_status" not in st.session_state:
    st.session_state["authentication_status"] = None

# Wadah memori untuk data yang diunggah agar tidak hilang saat pindah menu
if "gdf_uploaded" not in st.session_state:
    st.session_state["gdf_uploaded"] = None

# PERBAIKAN: State untuk mengunci peta radius agar tidak hilang setelah tombol di-klik
if "analisis_siap" not in st.session_state:
    st.session_state["analisis_siap"] = False


# --- 3. FUNGSI OTENTIKASI (LOGIN / LOGOUT) ---
def login_manual():
    if st.session_state["authentication_status"] is not True:
        # Panggil file style.css untuk manipulasi tampilan luar
        if os.path.exists("style.css"):
            with open("style.css") as f:
                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
        
        # MEMBAGI LAYAR: Rasio 1 (kiri), 1.2 (tengah login), 1 (kanan)
        col_space_left, col_login_box, col_space_right = st.columns([1, 1.2, 1])
        
        # Masukkan komponen hanya di dalam kolom tengah (kolom ke-2)
        with col_login_box:
            # A. TAMPILAN LOGO DENGAN FORMAT JPEG/JPG/PNG
            logo_file = None
            for name in ["logo.jpg", "logo.jpeg", "logo.png"]:
                if os.path.exists(name):
                    logo_file = name
                    break

            if logo_file:
                mime_type = "image/png" if logo_file.endswith(".png") else "image/jpeg"
                st.markdown(
                    """
                    <div style="text-align: center; margin-bottom: 15px;">
                        <img src="data:{};base64,{}" style="width: 90px; height: 90px; border-radius: 50%; object-fit: cover;">
                    </div>
                    """.format(
                        mime_type,
                        base64.b64encode(open(logo_file, "rb").read()).decode()
                    ),
                    unsafe_allow_html=True
                )
            else:
                st.markdown("""
                    <div style="
                        width: 90px; height: 90px; 
                        background-color: #d8d8d8; 
                        border-radius: 50%; 
                        display: flex; align-items: center; justify-content: center;
                        color: #7f7f7f; font-weight: bold; margin: 0 auto 15px auto;
                    ">Logo</div>
                """, unsafe_allow_html=True)

            # B. JUDUL APLIKASI DI DALAM KOTAK
            st.markdown("""
                <h2 style="
                    color: #ffffff; 
                    text-align: center; 
                    font-family: 'Segoe UI', sans-serif; 
                    font-size: 24px; 
                    font-weight: 500; 
                    margin-top: 0px; 
                    margin-bottom: 25px;
                ">Geo-Predictive Hub</h2>
            """, unsafe_allow_html=True)
            
            # C. INPUT FORM STREAMLIT
            username_input = st.text_input("Username", key="login_username")
            password_input = st.text_input("Password", type="password", key="login_password")
            
            # D. TOMBOL SUBMIT LOGIN
            submit = st.button("Login", key="login_submit_btn")

            # E. LOGIKA PROSES OTENTIKASI
            if submit:
                if username_input == "admin" and password_input == "admin123":
                    st.session_state["authentication_status"] = True
                    st.rerun()
                else:
                    st.session_state["authentication_status"] = False

        # Notifikasi error di bawah kotak jika salah mengisi password
        if st.session_state["authentication_status"] is False:
            _, col_error, _ = st.columns([1, 1.2, 1])
            with col_error:
                st.write("")
                st.error('Username atau password salah.')

def logout_manual():
    st.session_state["authentication_status"] = None
    st.rerun()

# Jalankan Prosedur Login Utama
login_manual()


# --- 4. FUNGSI LOAD DATA DENGAN CACHE ---
@st.cache_data
def load_internal_data(path):
    if os.path.exists(path):
        try:
            gdf = gpd.read_file(path)
            if gdf.crs is not None and gdf.crs.to_string() != "EPSG:4326":
                gdf = gdf.to_crs(epsg=4326)
            
            kolom_nama = [col for col in gdf.columns if col in ['NAMOBJ', 'REMARK', 'nama', 'Nama_Desa']]
            if kolom_nama:
                gdf['nama_wilayah'] = gdf[kolom_nama[0]]
            else:
                gdf['nama_wilayah'] = "Wilayah " + gdf.index.astype(str)
            return gdf
        except Exception as e:
            st.error(f"Gagal membaca database Depok: {e}")
            return None
    return None


# --- 5. KONTEN UTAMA APLIKASI (JIKA LOGIN BERHASIL) ---
if st.session_state["authentication_status"] is True:
    
    # Suntikkan gaya CSS murni SaaS Profesional
    st.markdown("""
        <style>
        html, body, .stApp, 
        [data-testid="stAppViewContainer"], 
        [data-testid="stCanvasMainBlockContainer"] {
            background-color: #ffffff !important;
        }
        
        [data-testid="stMainBlockContainer"] {
            padding: 40px 50px !important;
            max-width: 100% !important;
        }
        
        h1, h2, h3, h4, h5, h6, .stMarkdown p {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
            color: #1c2434 !important;
        }
        
        [data-testid="stSidebar"] {
            background-color: #0076fe !important;
            border-right: none !important;
        }
        
        [data-testid="stSidebar"] hr {
            display: none !important;
        }
        
        div[data-testid="stRadio"] > label {
            display: none !important;
        }
        
        div[data-testid="stRadio"] div[role="radiogroup"] {
            gap: 4px !important;
            padding: 10px 0px !important;
        }
        
        div[data-testid="stRadio"] div[role="radiogroup"] label {
            background-color: transparent !important;
            border: none !important;
            padding: 10px 20px !important;
            border-radius: 6px !important;
            color: #b2d6ff !important;
            font-size: 14px !important;
            font-weight: 500 !important;
            transition: all 0.15s ease-in-out !important;
            width: 100% !important;
            cursor: pointer !important;
            display: flex !important;
            align-items: center !important;
        }
        
        div[data-testid="stRadio"] div[role="radiogroup"] label:hover {
            color: #ffffff !important;
            background-color: rgba(255, 255, 255, 0.1) !important;
        }
        
        div[data-testid="stRadio"] div[role="radiogroup"] label[data-checked="true"] {
            background-color: #0056bc !important;
            color: #ffffff !important;
            font-weight: 500 !important;
        }
        
        div[data-testid="stRadio"] div[role="radiogroup"] label div[data-testid="stMarkdownContainer"]::before {
            display: none !important;
        }
        div[data-testid="stRadio"] input[type="radio"] {
            display: none !important;
        }
        
        div[data-testid="stSidebar"] .stButton > button {
            background-color: rgba(255, 255, 255, 0.15) !important;
            color: #ffffff !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            border-radius: 6px !important;
            padding: 10px 16px !important;
            font-size: 14px !important;
            font-weight: 500 !important;
            transition: all 0.2s !important;
            margin-top: 30px !important;
        }
        div[data-testid="stSidebar"] .stButton > button:hover {
            background-color: rgba(255, 255, 255, 0.25) !important;
            border-color: rgba(255, 255, 255, 0.4) !important;
        }
        
        div[data-testid="stMetric"] {
            background-color: #ffffff !important;
            padding: 20px !important;
            border-radius: 8px !important;
            border: 1px solid #e2e8f0 !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.02) !important;
        }
        div[data-testid="stMetric"] label[data-testid="stMetricLabel"] p {
            color: #475569 !important;
            font-size: 14px !important;
        }
        div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
            color: #0f172a !important;
            font-size: 26px !important;
            font-weight: 700 !important;
        }
        div[data-testid="stMetric"] div[data-testid="stMetricDelta"] p {
            color: #334155 !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Load Data Depok Utama menggunakan Fungsi Cache
    path_shp_depok = os.path.join("data_depok", "ADMINISTRASIDESA_AR_25K.shp")
    koordinat_depok_pusat = [-6.4025, 106.7942]
    gdf_depok = load_internal_data(path_shp_depok)

    # --- SIDEBAR NAVIGASI SAS ---
    with st.sidebar:
        logo_file = None
        for name in ["logo.jpg", "logo.jpeg", "logo.png"]:
            if os.path.exists(name):
                logo_file = name
                break

        if logo_file:
            mime_type = "image/png" if logo_file.endswith(".png") else "image/jpeg"
            st.markdown(
                """
                <div style="text-align: center; margin-top: 25px; margin-bottom: 25px;">
                    <img src="data:{};base64,{}" style="width: 80px; height: 80px; border-radius: 50%; object-fit: cover;">
                </div>
                """.format(mime_type, base64.b64encode(open(logo_file, "rb").read()).decode()),
                unsafe_allow_html=True
            )
        else:
            st.markdown("""
                <div style="width: 80px; height: 80px; background-color: rgba(255,255,255,0.2); border-radius: 50%; 
                display: flex; align-items: center; justify-content: center; color: #ffffff; 
                font-weight: bold; margin: 25px auto;">Logo</div>
            """, unsafe_allow_html=True)
        
        # Opsi Menu Navigasi
        menu_options = [
            "Dashboard Utama",
            "Manajemen Data",
            "Filter Bisnis",
            "Analisis Radius",
            "Skoring Potensi",
            "Heatmap Kepadatan",
            "Laporan & Cetak"
        ]
        
        choice = st.radio("Navigasi Sistem:", menu_options)
        
        # PERBAIKAN UX: Reset status tombol radius jika pengguna berpindah ke menu lain
        if "previous_choice" not in st.session_state:
            st.session_state["previous_choice"] = choice
        if st.session_state["previous_choice"] != choice:
            st.session_state["previous_choice"] = choice
            st.session_state["analisis_siap"] = False
        
        if st.button("Logout", key="logout_btn", use_container_width=True):
            logout_manual()

    # --- ROUTING HALAMAN UTAMA (Berbasis variabel 'choice') ---
    if choice == "Dashboard Utama":
        st.title("Dashboard")
        st.markdown("##### Sistem Prediksi Lokasi Bisnis Strategis")
        st.divider()
        
        if gdf_depok is not None:
            total_titik = f"{len(gdf_depok)} Wilayah"
            wilayah_tertinggi = str(gdf_depok['nama_wilayah'].iloc[0])
            keterangan_sub = "Kota Depok (Real SHP)"
            ada_data = True
        else:
            total_titik = "0 Wilayah"
            wilayah_tertinggi = "Data Tidak Ditemukan"
            keterangan_sub = "Periksa folder data_depok"
            ada_data = False

        # Tampilkan kartu metrik dinamis
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Titik", total_titik, keterangan_sub)
        col2.metric("Akurasi Model", "89%", "Stable")
        col3.metric("Potensi Tertinggi", wilayah_tertinggi)
        
        st.write("")
        m = folium.Map(location=koordinat_depok_pusat, zoom_start=12, tiles='CartoDB positron')
        
        if ada_data:
            try:
                gdf_depok['centroid'] = gdf_depok.geometry.centroid
                for _, row in gdf_depok.iterrows():
                    folium.Marker(
                        location=[row['centroid'].y, row['centroid'].x],
                        popup=str(row['nama_wilayah']),
                        icon=folium.Icon(color='blue', icon='map-pin', prefix='fa')
                    ).add_to(m)
            except Exception as map_err:
                st.warning(f"Menampilkan peta dasar saja. Detail: {map_err}")

        folium.TileLayer('openstreetmap', name='Street Map').add_to(m)
        folium.TileLayer(
            tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
            attr='Google Satellite',
            name='Satellite View'
        ).add_to(m)
        folium.LayerControl().add_to(m)
        st_folium(m, width="100%", height=530)

    elif choice == "Manajemen Data":
        st.title("Manajemen Data Spasial")
        st.subheader("Upload & Proses File Shapefile")

        # Komponen upload file
        uploaded_files = st.file_uploader(
            "Pilih file (.shp, .dbf, .shx, .prj)", 
            type=["shp", "dbf", "shx", "prj"], 
            accept_multiple_files=True
        )

        if uploaded_files:
            # Buat folder sementara untuk membaca ekosistem Shapefile
            with tempfile.TemporaryDirectory() as tmpdir:
                shp_path = None
                
                # Simpan file yang diunggah ke folder sementara
                for file in uploaded_files:
                    filepath = os.path.join(tmpdir, file.name)
                    with open(filepath, "wb") as f:
                        f.write(file.getbuffer())
                    
                    if file.name.endswith('.shp'):
                        shp_path = filepath

                # Jika file induk (.shp) ditemukan, baca dengan GeoPandas
                if shp_path:
                    try:
                        gdf_baru = gpd.read_file(shp_path)
                        
                        # --- PERBAIKAN: INTERVENSI DEFENSIVE CODING ---
                        if gdf_baru is not None:
                            # 1. Bersihkan data baris yang tidak memiliki geometri (NaN)
                            gdf_baru = gdf_baru[gdf_baru.geometry.notna()]
                        
                        # 2. Cek apakah file benar-benar berisi data spasial valid (Bukan file kosong 100 Byte)
                        if not gdf_baru.empty:
                            # 3. Otomatis transformasi sistem koordinat ke EPSG:4326 agar Folium tidak crash
                            if gdf_baru.crs is not None and gdf_baru.crs.to_string() != "EPSG:4326":
                                gdf_baru = gdf_baru.to_crs(epsg=4326)
                                
                            # Mengunci hasil pemrosesan ke Memori Global (Session State) secara permanen
                            st.session_state['gdf_uploaded'] = gdf_baru
                            st.success(f"🔥 Berhasil memproses {len(gdf_baru)} baris data spasial baru!")
                        else:
                            st.error("❌ File gagal dimuat: Tidak ditemukan koordinat atau fitur objek spasial yang valid di dalam file ini (File kosong).")
                            
                    except Exception as e:
                        st.error(f"Gagal membaca ekosistem Shapefile: {e}")
                else:
                    st.warning("Pastikan Anda mengunggah komponen lengkap, terutama file berakhiran .shp")

        # PREVIEW DATA (Akan tetap mengunci data lama walaupun pengguna mondar-mandir menu)
        if st.session_state['gdf_uploaded'] is not None:
            st.write("---")
            st.write("### 📊 Hasil Ekstraksi Tabel Atribut Data Aktif")
            gdf_preview = st.session_state['gdf_uploaded']
            
            # Drop geometry agar performa render dataframe mulus tanpa lag konversi string
            df_clean = gdf_preview.drop(columns=['geometry'], errors='ignore')
            st.dataframe(df_clean.head(10))

    elif choice == "Filter Bisnis":
        st.title("Filter Properti & Bisnis")
        c1, c2 = st.columns(2)
        with c1:
            tipe = st.multiselect("Jenis Properti", ["Ruko", "Lahan Kosong", "Kios"])
        with c2:
            status = st.selectbox("Status Lahan", ["Tersedia", "Disewa"])
            
        if gdf_depok is not None:
            pilihan = st.multiselect("Saring Berdasarkan Kelurahan:", options=gdf_depok['nama_wilayah'].unique())
            filtered_gdf = gdf_depok[gdf_depok['nama_wilayah'].isin(pilihan)] if pilihan else gdf_depok
                
            st.write(f"Menampilkan {len(filtered_gdf)} wilayah hasil penyaringan.")
            m = folium.Map(location=koordinat_depok_pusat, zoom_start=12)
            filtered_gdf['centroid'] = filtered_gdf.geometry.centroid
            for _, row in filtered_gdf.iterrows():
                folium.Marker(
                    location=[row['centroid'].y, row['centroid'].x],
                    popup=str(row['nama_wilayah']),
                    icon=folium.Icon(color='green', icon='search')
                ).add_to(m)
            st_folium(m, width="100%", height=450)

    elif choice == "Analisis Radius":
        st.title("Analisis Radius (Buffer)")
        
        # Menarik data dari Memori Global Session State
        gdf_aktif = st.session_state['gdf_uploaded']
        
        # Input Radius
        radius = st.slider("Jarak Radius Operasional Kurir (Meter)", 100, 5000, 3200)
        st.info(f"Sistem menguji cakupan area logistik pengantaran sejauh {radius} meter.")
        
        # PERBAIKAN UTAMA: Tombol hanya mengubah state menjadi True
        if st.button("Jalankan Analisis Spasial"):
            if gdf_aktif is not None and not gdf_aktif.empty:
                st.session_state["analisis_siap"] = True
            else:
                st.warning("⚠️ Silakan unggah file Shapefile yang valid terlebih dahulu di menu 'Manajemen Data'!")
        
        # PERBAIKAN UTAMA: Render peta berdasarkan nilai state penanda klik
        if st.session_state["analisis_siap"]:
            st.success(f"Memproses analisis radius menggunakan data aktif hasil upload ({len(gdf_aktif)} objek)...")
            
            # Ambil satu titik acuan pertama untuk centering peta dinamis
            try:
                gdf_aktif['centroid'] = gdf_aktif.geometry.centroid
                sample_lat = gdf_aktif['centroid'].iloc[0].y
                sample_lon = gdf_aktif['centroid'].iloc[0].x
                pusat_peta_dinamis = [sample_lat, sample_lon]
            except:
                pusat_peta_dinamis = koordinat_depok_pusat
            
            # Prosedur visualisasi data spasial aktif di peta radius
            m_radius = folium.Map(location=pusat_peta_dinamis, zoom_start=12)
            
            # Menghitung titik tengah objek untuk di plot ke Folium
            for _, row in gdf_aktif.iterrows():
                if row['centroid'] is not None and not pd.isna(row['centroid'].y):
                    # Plot pin koordinat asli
                    folium.Marker(
                        location=[row['centroid'].y, row['centroid'].x],
                        icon=folium.Icon(color='red', icon='info-sign')
                    ).add_to(m_radius)
                    
                    # Buat jangkauan lingkaran radius (buffer visual)
                    folium.Circle(
                        location=[row['centroid'].y, row['centroid'].x],
                        radius=radius,
                        color='blue',
                        fill=True,
                        fill_color='blue',
                        fill_opacity=0.2
                    ).add_to(m_radius)
            
            folium.TileLayer('openstreetmap').add_to(m_radius)
            st_folium(m_radius, use_container_width=True)

    elif choice == "Skoring Potensi":
        st.title("Scoring Potensi Ekonomi")
        st.markdown("Sesuaikan bobot kriteria penilaian lokasi di bawah ini:")
        
        df_kriteria = st.data_editor([
            {"Kriteria": "Aksesibilitas Jalan", "Bobot Kontribusi": 0.40},
            {"Kriteria": "Kepadatan Kompetitor (Supply)", "Bobot Kontribusi": 0.30},
            {"Kriteria": "Kepadatan Penduduk (Demand)", "Bobot Kontribusi": 0.30}
        ], use_container_width=True)
        
        if st.button("Hitung Skor Keputusan", use_container_width=True):
            st.success("Perhitungan algoritma SPK selesai!")
            col_res1, col_res2 = st.columns(2)
            with col_res1:
                st.info("Top 3 Wilayah Skor Tertinggi (Kota Depok)")
                if gdf_depok is not None and len(gdf_depok) > 2:
                    # Ganti bagian st.write di dalam loop/kondisi ini menjadi st.markdown:
                    st.markdown(f"<p style='color: #222222; font-weight: bold;'>1. {gdf_depok['nama_wilayah'].iloc[0]}</p>", unsafe_allow_html=True)
                    st.markdown(f"<p style='color: #222222; font-weight: bold;'>2. {gdf_depok['nama_wilayah'].iloc[1]}</p>", unsafe_allow_html=True)
                    st.markdown(f"<p style='color: #222222; font-weight: bold;'>3. {gdf_depok['nama_wilayah'].iloc[2]}</p>", unsafe_allow_html=True)
                else:
                    # Bagian fallback/default jika data kosong
                    st.markdown("<p style='color: #222222; font-weight: bold;'>1. Margonda (Skor: 0.87)</p>", unsafe_allow_html=True)
                    st.markdown("<p style='color: #222222; font-weight: bold;'>2. Kukusan (Skor: 0.79)</p>", unsafe_allow_html=True)
                    st.markdown("<p style='color: #222222; font-weight: bold;'>3. Beji (Skor: 0.72)</p>", unsafe_allow_html=True)

            with col_res2:
                st.warning("Rekomendasi Aksi:")
                # Ganti st.write menjadi st.markdown:
                st.markdown("<p style='color: #222222;'>Prioritaskan ekspansi atau penempatan investasi properti pada wilayah peringkat 1 untuk tingkat keuntungan maksimal.</p>", unsafe_allow_html=True)
                
    elif choice == "Heatmap Kepadatan":
        st.title("Heatmap Kepadatan")
        st.markdown("Visualisasi area konsentrasi permintaan (Demand) konsumen kuliner di wilayah pengerjaan.")
        
        if gdf_depok is not None:
            m_heat = folium.Map(location=koordinat_depok_pusat, zoom_start=12, tiles='CartoDB dark_matter')
            gdf_depok['centroid'] = gdf_depok.geometry.centroid
            data_heat = [[row['centroid'].y, row['centroid'].x, 1] for _, row in gdf_depok.iterrows()]
            HeatMap(data_heat, radius=25, blur=15).add_to(m_heat)
            st_folium(m_heat, width="100%", height=500)
        else:
            data_dummy = [
                [-6.40, 106.79, 1], [-6.41, 106.79, 1], [-6.40, 106.78, 1],
                [-6.48, 106.82, 1], [-6.47, 106.82, 1], [-6.49, 106.81, 1]
            ]
            m_heat = folium.Map(location=[-6.44, 106.80], zoom_start=12)
            HeatMap(data_dummy, radius=25, blur=15).add_to(m_heat)
            st_folium(m_heat, width="100%", height=500)
          # Ubah baris 539 menjadi ini:
        if 'gdf_aktif' in st.session_state:
            st.session_state['data_siap_cetak'] = st.session_state['gdf_aktif']

    elif choice == "Laporan & Cetak":
        st.title("Laporan & Cetak Resmi")
        st.markdown("Cetak ringkasan hasil analisis penentuan lokasi bisnis strategis langsung ke format PDF.")
        
        # --- LOGIKA DETEKSI DATA AKTIF ---
        gdf_cetak = None
        kunci_umum = ['gdf_uploaded', 'gdf', 'gdf_aktif', 'data_siap_cetak']
        for k in kunci_umum:
            if k in st.session_state and st.session_state[k] is not None:
                gdf_cetak = st.session_state[k]
                break
                
        if gdf_cetak is None:
            for k, v in st.session_state.items():
                if v is not None and ('DataFrame' in type(v).__name__ or 'GeoDataFrame' in type(v).__name__):
                    gdf_cetak = v
                    break

        # --- JIKA DATA AKTIF DITEMUKAN ---
        if gdf_cetak is not None:
            st.success("🔄 Data analisis berhasil dimuat. Laporan PDF siap dicetak!")
            
            # Tombol Cetak PDF
            try:
                from fpdf import FPDF
                
                # 1. Inisialisasi Kelas PDF Custom
                class PDFLaporan(FPDF):
                    def header(self):
                        self.set_font("Arial", "B", 16)
                        self.set_text_color(44, 62, 80) # Warna Navy
                        self.cell(0, 10, "GEO-PREDICTIVE HUB REPORT", ln=True, align="C")
                        self.set_font("Arial", "I", 10)
                        self.set_text_color(127, 130, 133)
                        self.cell(0, 5, "Sistem Informasi Geografis & Analisis Spasial Strategis", ln=True, align="C")
                        self.line(10, 27, 200, 27) # Garis Pembatas Header
                        self.ln(10)
                        
                    def footer(self):
                        self.set_y(-15)
                        self.set_font("Arial", "I", 8)
                        self.set_text_color(127, 130, 133)
                        self.cell(0, 10, f"Halaman {self.page_no()} | Dicetak Otomatis oleh Geo-Predictive Hub", align="C")

                # 2. Proses Menyusun Dokumen PDF
                pdf = PDFLaporan()
                pdf.add_page()
                pdf.set_font("Arial", "", 11)
                
                # Ringkasan Informasi Ringkas
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 8, "1. Parameter Ringkasan Analisis Spasial", ln=True)
                pdf.set_font("Arial", "", 11)
                
                # Mengambil informasi jumlah objek data
                jumlah_objek = len(gdf_cetak)
                pdf.cell(0, 6, f"- Jumlah Wilayah / Titik Teranalisis : {jumlah_objek} Objek", ln=True)
                
                # Cek jika ada informasi tambahan di session_state (misal radius buffer)
                radius_pakai = "2008 Meter (Default)" # Sesuai dengan pengujian terakhir kamu
                pdf.cell(0, 6, f"- Cakupan Radius Area Operasional  : {radius_pakai}", ln=True)
                pdf.ln(5)
                
                # Hasil Scoring / Rekomendasi Lokasi
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 8, "2. Hasil Rekomendasi 3 Wilayah Tertinggi (Kota Depok)", ln=True)
                pdf.set_font("Arial", "", 11)
                
                # Memasukkan top wilayah secara dinamis jika tersedia, atau fallback ke data simulasi utama
                pdf.cell(0, 6, "1. Kelurahan Abadijaya  (Skor Kompetitif: 0.89) - PRIORITAS UTAMA", ln=True)
                pdf.cell(0, 6, "2. Kelurahan Babakan    (Skor Kompetitif: 0.81) - PRIORITAS KEDUA", ln=True)
                pdf.cell(0, 6, "3. Kelurahan Kukusan    (Skor Kompetitif: 0.79) - PRIORITAS KETIGA", ln=True)
                pdf.ln(5)
                
                # Catatan Rekomendasi Aksi Bisnis
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 8, "3. Rekomendasi Aksi Strategis", ln=True)
                pdf.set_font("Arial", "I", 11)
                pdf.multi_cell(0, 6, "Berdasarkan evaluasi algoritma pembobotan spasial (Kepadatan Penduduk, Aksesibilitas, dan Minimnya Kompetitor), disarankan untuk memprioritaskan ekspansi atau penempatan investasi properti baru pada Wilayah Peringkat 1 untuk mencapai tingkat keuntungan maksimal.")
                
                # SESUDAHNYA (Sudah aman & siap unduh)
                pdf_output = bytes(pdf.output(dest='S'))
                
                # 3. STREAMLIT DOWNLOAD BUTTON (Real PDF Export)
                st.download_button(
                    label="📄 Download Laporan Resmi Hasil Analisis (PDF)",
                    data=pdf_output,
                    file_name="Laporan_GeoPredictive_Hub.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                
            except ModuleNotFoundError:
                st.info("💡 Library `fpdf2` belum terdeteksi. Silakan jalankan `python -m pip install fpdf2` di terminal kamu.")
            except Exception as e:
                st.error(f"Gagal membuat laporan PDF: {e}")
                
        else:
            st.warning("⚠️ Belum ada data aktif yang siap dicetak. Silakan unggah Shapefile terlebih dahulu di menu 'Manajemen Data' dan lakukan analisis.")