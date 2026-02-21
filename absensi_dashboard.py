import streamlit as st
from datetime import datetime
import pytz
from supabase import create_client
import pandas as pd
from calendar import monthrange
from geopy.distance import geodesic
from streamlit_js_eval import get_geolocation

# ================= SUPABASE =================
SUPABASE_URL = "https://jogrrtkttwzlqkveujxa.supabase.co"
SUPABASE_KEY = "ISI_SUPABASE_KEY_KAMU"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ================= STARTUP MODERN THEME (FIX TEXT) =================
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #dff6ff 0%, #e6f7ff 40%, #f0fff4 100%);
    background-attachment: fixed;
}

[data-testid="stSidebar"] {
    background: rgba(255,255,255,0.75);
    backdrop-filter: blur(18px);
    border-right: 1px solid rgba(255,255,255,0.4);
}

.block-container {
    background: rgba(255,255,255,0.65);
    backdrop-filter: blur(18px);
    border-radius: 24px;
    padding: 2rem;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.08);
}

html, body, p, span, label, div {
    color: #0f172a !important;
}

h1 {
    color: #020617 !important;
    font-weight: 800;
}

h2, h3 {
    color: #0f172a !important;
    font-weight: 600;
}

.stButton > button {
    background: linear-gradient(90deg, #00c6ff 0%, #00ffb3 100%);
    color: white !important;
    border-radius: 16px;
    border: none;
    padding: 0.6rem 1.2rem;
    font-weight: 600;
    box-shadow: 0 8px 20px rgba(0, 198, 255, 0.25);
}

.stSelectbox > div > div,
.stTextInput > div > div,
.stTextArea textarea {
    background: rgba(255,255,255,0.9);
    border-radius: 14px;
    color: #020617 !important;
}

.stRadio label {
    color: #020617 !important;
}

button[data-baseweb="tab"] {
    color: #020617 !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
    background: linear-gradient(90deg, #00c6ff, #00ffb3);
    color: white !important;
    border-radius: 12px;
}

thead tr th {
    background: rgba(0,198,255,0.15) !important;
    color: #020617 !important;
}

tbody tr td {
    color: #020617 !important;
}
</style>
""", unsafe_allow_html=True)

# ================= WAKTU =================
wib = pytz.timezone("Asia/Jakarta")
def now_wib():
    return datetime.now(wib)

# ================= HEADER LOGO =================
col1, col2 = st.columns([1,5])

with col1:
    st.image("logo.png", width=70)

with col2:
    st.markdown("""
    <h1 style='margin-bottom:0;'>Dashboard Absensi</h1>
    <p style='margin-top:0;color:#64748b;'>PT RISUM</p>
    """, unsafe_allow_html=True)

st.markdown(f"🕒 {now_wib().strftime('%A, %d %B %Y | %H:%M:%S')}")

# ================= MODE =================
mode = st.sidebar.selectbox("Login Sebagai", ["Karyawan", "Admin"])
password = ""
if mode == "Admin":
    password = st.sidebar.text_input("Password Admin", type="password")

# ================= GPS =================
kantor = (-7.7509616760437385, 110.36579129415266)
radius = 200

def gps_block():
    loc = get_geolocation()
    lokasi_valid = False
    if loc:
        lat = loc["coords"]["latitude"]
        lon = loc["coords"]["longitude"]
        jarak = geodesic(kantor, (lat, lon)).meters
        if jarak <= radius:
            lokasi_valid = True
            st.success(f"📍 Dalam area kantor ({round(jarak,2)} m)")
        else:
            st.error(f"📍 Di luar area kantor ({round(jarak,2)} m)")
    else:
        st.warning("Izinkan akses lokasi!")
    return lokasi_valid

# ================= LOAD MASTER =================
@st.cache_data(ttl=300)
def load_master():
    nama_res = supabase.table("nama").select("*").order("nama").execute().data
    posisi_res = supabase.table("posisi").select("*").order("posisi").execute().data
    nama_dict = {n["nama"]: n["id"] for n in nama_res}
    posisi_dict = {p["posisi"]: p["id"] for p in posisi_res}
    nama_map = {n["id"]: n["nama"] for n in nama_res}
    posisi_map = {p["id"]: p["posisi"] for p in posisi_res}
    return nama_dict, posisi_dict, nama_map, posisi_map

nama_dict, posisi_dict, nama_map, posisi_map = load_master()

# ================= MODE KARYAWAN =================
if mode == "Karyawan":

    st.subheader("📱 Absensi Karyawan")
    lokasi_valid = gps_block()

    selected_nama = st.selectbox("Pilih Nama", list(nama_dict.keys()))
    selected_posisi = st.selectbox("Posisi", list(posisi_dict.keys()))

    datang_pulang = st.radio("Datang / Pulang", ["Datang", "Pulang"], horizontal=True)
    status = st.radio("Status", ["Hadir", "Izin", "Sakit", "Lembur"], horizontal=True)

    keterangan = ""
    if status != "Hadir":
        keterangan = st.text_area("Keterangan")

    if st.button("Submit Absen", use_container_width=True):

        if not lokasi_valid:
            st.error("Anda harus berada di area kantor untuk absen")
            st.stop()

        tanggal = now_wib().strftime("%Y-%m-%d")
        jam = now_wib().strftime("%H:%M:%S")

        cek = supabase.table("absensi")\
            .select("*")\
            .eq("nama_id", nama_dict[selected_nama])\
            .eq("tanggal", tanggal)\
            .execute()

        if datang_pulang == "Datang":
            if cek.data:
                st.warning("Sudah absen datang hari ini")
            else:
                supabase.table("absensi").insert({
                    "nama_id": nama_dict[selected_nama],
                    "posisi_id": posisi_dict[selected_posisi],
                    "tanggal": tanggal,
                    "jam_masuk": jam,
                    "status": status,
                    "keterangan": keterangan
                }).execute()
                st.success("Absen datang berhasil!")

        else:
            if not cek.data:
                st.warning("Belum absen datang")
            else:
                supabase.table("absensi")\
                    .update({"jam_pulang": jam})\
                    .eq("nama_id", nama_dict[selected_nama])\
                    .eq("tanggal", tanggal)\
                    .execute()
                st.success("Absen pulang berhasil!")

# ================= MODE ADMIN =================
if mode == "Admin" and password == "risum771":

    st.divider()
    st.subheader("💻 Dashboard Admin")

    tab1, tab2, tab3 = st.tabs(["Hari Ini", "Bulanan", "Semua Data"])

    # TAB HARI INI
    with tab1:
        today = now_wib().strftime("%Y-%m-%d")

        res = supabase.table("absensi")\
            .select("id,nama_id,posisi_id,tanggal,jam_masuk,jam_pulang,status,keterangan")\
            .eq("tanggal", today)\
            .execute()

        if res.data:
            rows = []
            for r in res.data:
                rows.append({
                    "ID": r["id"],
                    "Nama": nama_map.get(r["nama_id"], "-"),
                    "Posisi": posisi_map.get(r["posisi_id"], "-"),
                    "Tanggal": r["tanggal"],
                    "Jam Masuk": r["jam_masuk"],
                    "Jam Pulang": r["jam_pulang"],
                    "Status": r["status"],
                    "Keterangan": r["keterangan"]
                })
            df = pd.DataFrame(rows)
            st.dataframe(df.drop(columns=["ID"]), use_container_width=True)
        else:
            st.info("Belum ada absensi hari ini")

    # TAB BULANAN
    with tab2:
        bulan = st.selectbox("Bulan", list(range(1,13)))
        tahun = st.selectbox("Tahun", list(range(2024,2031)))
        jumlah_hari = monthrange(tahun, bulan)[1]

        res = supabase.table("absensi")\
            .select("id,nama_id,posisi_id,tanggal,jam_masuk,jam_pulang,status,keterangan")\
            .gte("tanggal", f"{tahun}-{str(bulan).zfill(2)}-01")\
            .lte("tanggal", f"{tahun}-{str(bulan).zfill(2)}-{jumlah_hari}")\
            .execute()

        if res.data:
            rows = []
            for r in res.data:
                rows.append({
                    "Nama": nama_map.get(r["nama_id"], "-"),
                    "Posisi": posisi_map.get(r["posisi_id"], "-"),
                    "Tanggal": r["tanggal"],
                    "Jam Masuk": r["jam_masuk"],
                    "Jam Pulang": r["jam_pulang"],
                    "Status": r["status"],
                    "Keterangan": r["keterangan"]
                })
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Belum ada data bulan ini")

    # TAB SEMUA DATA
    with tab3:
        res = supabase.table("absensi")\
            .select("id,nama_id,posisi_id,tanggal,jam_masuk,jam_pulang,status,keterangan")\
            .order("tanggal", desc=True)\
            .limit(1000)\
            .execute()

        if res.data:
            rows = []
            for r in res.data:
                rows.append({
                    "Nama": nama_map.get(r["nama_id"], "-"),
                    "Posisi": posisi_map.get(r["posisi_id"], "-"),
                    "Tanggal": r["tanggal"],
                    "Jam Masuk": r["jam_masuk"],
                    "Jam Pulang": r["jam_pulang"],
                    "Status": r["status"],
                    "Keterangan": r["keterangan"]
                })
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Belum ada data")
