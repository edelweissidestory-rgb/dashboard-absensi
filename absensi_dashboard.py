import streamlit as st
from datetime import datetime
import pytz
import time
from geopy.distance import geodesic
from streamlit_js_eval import get_geolocation

# ================== Koneksi Database ==================
from supabase import create_client

SUPABASE_URL = "https://jogrrtkttwzlqkveujxa.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpvZ3JydGt0dHd6bHFrdmV1anhhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzE2OTI3NDQsImV4cCI6MjA4NzI2ODc0NH0.5tSvQvbqXTNCukMpWE6KDzDmzZLkaCGcRxHr0zATDqw"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


from streamlit_autorefresh import st_autorefresh

# ===== HEADER RAPI CENTER =====
st.markdown("""
<style>
.header {
    text-align: center;
    margin-top: -20px;
}

.logo {
    margin-bottom: -20px;
}

.judul {
    font-size: 28px;
    font-weight: 700;
    margin-bottom: -10px;
    color: #1b5e20;
}

.jam {
    font-size: 16px;
    color: #444;
    margin-top: 0px;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header">', unsafe_allow_html=True)

st.image("logo.png", width=170)

st.markdown(
    '<div class="judul">Dashboard Absensi Staff PT RISUM</div>',
    unsafe_allow_html=True
)

st_autorefresh(interval=1000, key="clockrefresh")

wib = pytz.timezone("Asia/Jakarta")
now = datetime.now(wib).strftime("%A, %d %B %Y | %H:%M:%S")

st.markdown(
    f'<div class="jam">🕒 {now}</div>',
    unsafe_allow_html=True
)

st.markdown('</div>', unsafe_allow_html=True)

mode = st.sidebar.selectbox("Login Sebagai", ["Karyawan", "Admin"])

if mode == "Admin":
    password = st.sidebar.text_input("Password Admin", type="password")


st.markdown("""
<style>

/* background utama */
[data-testid="stAppViewContainer"] {
    background: #f4f6f9;
}

/* judul */
h1 {
    color: #1b5e20;
    text-align: center;
    font-weight: 700;
}

/* semua text */
label, p, span {
    color: #111 !important;
    font-size: 15px;
}

/* selectbox */
.stSelectbox > div {
    background: white;
    border-radius: 10px;
}

/* radio */
.stRadio label {
    color: #111 !important;
}

/* tombol */
.stButton>button {
    background-color: #2e7d32;
    color: white;
    font-weight: bold;
    border-radius: 10px;
    height: 45px;
}

/* kotak lokasi valid */
.kotak-hijau {
    background-color: #e8f5e9;
    padding: 20px;
    border-radius: 12px;
    border-left: 8px solid #2e7d32;
    box-shadow: 0 6px 14px rgba(0,0,0,0.08);
    margin-bottom: 20px;
    color: #1b5e20;
}

/* kotak lokasi tidak valid */
.kotak-merah {
    background-color: #ffebee;
    padding: 20px;
    border-radius: 12px;
    border-left: 8px solid #c62828;
    box-shadow: 0 6px 14px rgba(0,0,0,0.08);
    margin-bottom: 20px;
    color: #7f0000;
    font-weight: 600;
}

/* sidebar */
section[data-testid="stSidebar"] {
    background-color: #1e1e2f;
}

section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span {
    color: white !important;
}

</style>
""", unsafe_allow_html=True)
# ================== Koordinat Kantor ==================
kantor = (-7.76479975133688, 110.48149545435504)
radius = 200
# ================== Ambil Lokasi GPS ==================
loc = get_geolocation()

lat = None
lon = None
lokasi_valid = False

if loc:
    lat = loc["coords"]["latitude"]
    lon = loc["coords"]["longitude"]

    jarak = geodesic(kantor, (lat, lon)).meters

    if jarak <= radius:
        lokasi_valid = True
        st.markdown(f"""
        <div class="kotak-hijau">
            <h4>📍 Kamu berada di area kantor</h4>
            <p>Jarak dari kantor: {round(jarak,2)} meter</p>
        </div>
        """, unsafe_allow_html=True)

    else:
        lokasi_valid = False
        st.markdown(f"""
        <div class="kotak-merah">
            <h4>📍 Kamu TIDAK berada di area kantor</h4>
            <p>Jarak dari kantor: {round(jarak,2)} meter</p>
        </div>
        """, unsafe_allow_html=True)

else:
    st.warning("Izinkan akses lokasi untuk melakukan absensi!")

# ================== Pilih Nama ==================
response = supabase.table("nama").select("*").order("nama").execute()
nama_options = response.data
nama_dict = {n["nama"]: n["id"] for n in nama_options}
selected_nama = st.selectbox("Pilih Nama", list(nama_dict.keys()))

# ================== Pilih Posisi ==================
response = supabase.table("posisi").select("*").order("posisi").execute()
posisi_options = response.data
posisi_dict = {p["posisi"]: p["id"] for p in posisi_options}
selected_posisi = st.selectbox("Posisi", list(posisi_dict.keys()))

# ================== Datang / Pulang ==================
datang_pulang = st.radio("Datang atau Pulang?", ("Datang", "Pulang"))

# ================== Status ==================
status = st.radio("Status Kehadiran", ("Hadir", "Izin", "Sakit", "Lembur"))
keterangan = ""
if status in ["Izin", "Sakit", "Lembur"]:
    keterangan = st.text_area("Keterangan (Wajib)")

# ================== Tombol Submit ==================
# ================== Tombol Submit ==================
if st.button("Submit Absen"):
    if not lokasi_valid:
        st.error("Kamu harus berada di kantor untuk absen!")

    else:
        import pytz
        wib = pytz.timezone("Asia/Jakarta")
        now_wib = datetime.now(wib)
        tanggal = now_wib.strftime("%Y-%m-%d")
        jam_sekarang = now_wib.strftime("%H:%M:%S")

        # ================= DATANG =================
        if datang_pulang == "Datang":

            c.execute("""
                SELECT * FROM absensi
                WHERE nama_id=? AND tanggal=?
            """, (nama_dict[selected_nama], tanggal))
            exists = c.fetchone()

            if exists:
                st.warning("Kamu sudah absen datang hari ini!")
            else:
                supabase.table("absensi").insert({
                      "nama_id": nama_dict[selected_nama],
                      "posisi_id": posisi_dict[selected_posisi],
                      "tanggal": tanggal,
                      "jam_masuk": jam_sekarang,
                      "status": status,
                      "keterangan": keterangan
                }).execute()
                st.success("Absen Datang berhasil!")

        # ================= PULANG =================
        elif datang_pulang == "Pulang":

            c.execute("""
                SELECT * FROM absensi
                WHERE nama_id=? AND tanggal=?
            """, (nama_dict[selected_nama], tanggal))
            data = c.fetchone()

            if not data:
                st.warning("Kamu belum absen datang!")
            else:
                supabase.table("absensi") \
                    .update({"jam_pulang": jam_sekarang}) \
                    .eq("nama_id", nama_dict[selected_nama]) \
                    .eq("tanggal", tanggal) \
                    .execute()
                st.success("Absen Pulang berhasil!")
# ================== REKAP ADMIN ==================
# ================== REKAP ADMIN ==================
if mode == "Admin" and password == "risum771":

    st.markdown("---")
    st.subheader("📊 Dashboard Rekap Absensi")

    tab1, tab2 = st.tabs(["📊 Rekap Harian", "📅 Rekap Bulanan"])


    # ================= TAB HARIAN =================
    with tab1:

        wib = pytz.timezone("Asia/Jakarta")
        today = datetime.now(wib).strftime("%Y-%m-%d")

        response = supabase.table("absensi") \
            .select("*, nama(nama), posisi(posisi)") \
            .eq("tanggal", today) \
            .order("jam_masuk") \
            .execute()

        data = response.data

        if data:
            import pandas as pd

            df = pd.DataFrame(data, columns=[
                "ID", "Nama", "Posisi", "Tanggal",
                "Jam Datang", "Jam Pulang",
                "Status", "Keterangan"
            ])

            st.dataframe(df.drop(columns=["ID"]), use_container_width=True)

        else:
            st.info("Belum ada absensi hari ini")


    # ================= TAB BULANAN =================
    with tab2:

        import pandas as pd

        bulan = st.selectbox(
            "Pilih Bulan",
            list(range(1,13)),
            format_func=lambda x: datetime(2000, x, 1).strftime("%B")
        )

        tahun = st.selectbox(
            "Pilih Tahun",
            list(range(2024, 2031))
        )

        response = supabase.table("absensi") \
            .select("*, nama(nama), posisi(posisi)") \
            .gte("tanggal", f"{tahun}-{str(bulan).zfill(2)}-01") \
            .lte("tanggal", f"{tahun}-{str(bulan).zfill(2)}-31") \
            .execute()

        data_bulan = response.data
        

        if data_bulan:

            df_bulan = pd.DataFrame(data_bulan, columns=[
                "ID", "Nama", "Posisi", "Tanggal",
                "Jam Datang", "Jam Pulang",
                "Status", "Keterangan"
            ])

            st.dataframe(df_bulan.drop(columns=["ID"]), use_container_width=True)

            st.markdown("### 🗑️ Hapus Data Absensi")

            id_hapus = st.selectbox(
                "Pilih data yang mau dihapus",
                options=df_bulan["ID"].tolist(),
                format_func=lambda x: f"{df_bulan[df_bulan['ID']==x]['Nama'].values[0]} - {df_bulan[df_bulan['ID']==x]['Tanggal'].values[0]}"
            )

            if st.button("Hapus Data"):
                c.execute("DELETE FROM absensi WHERE id=?", (id_hapus,))
                conn.commit()
                st.success("Data berhasil dihapus!")
                st.rerun()

        else:
            st.info("Belum ada data absensi bulan ini")


