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
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpvZ3JydGt0dHd6bHFrdmV1anhhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzE2OTI3NDQsImV4cCI6MjA4NzI2ODc0NH0.5tSvQvbqXTNCukMpWE6KDzDmzZLkaCGcRxHr0zATDqw"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ================= WAKTU =================
wib = pytz.timezone("Asia/Jakarta")
def now_wib():
    return datetime.now(wib)

st.markdown(f"### 🕒 {now_wib().strftime('%A, %d %B %Y | %H:%M:%S')}")
st.title("Presensi Karyawan PT Risum Indo Lestari")

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
@st.cache_data(ttl=60)
def load_master():
    nama_res = supabase.table("nama").select("*").order("nama").execute().data
    posisi_res = supabase.table("posisi").select("*").order("posisi").execute().data
    nama_dict = {n["nama"]: n["id"] for n in nama_res}
    posisi_dict = {p["posisi"]: p["id"] for p in posisi_res}
    nama_map = {n["id"]: n["nama"] for n in nama_res}
    posisi_map = {p["id"]: p["posisi"] for p in posisi_res}
    return nama_dict, posisi_dict, nama_map, posisi_map

nama_dict, posisi_dict, nama_map, posisi_map = load_master()

# ================= BACKUP CSV =================
def generate_csv(res):
    if not res.data:
        return None
    rows = [{
        "Nama": nama_map.get(r["nama_id"], "-"),
        "Posisi": posisi_map.get(r["posisi_id"], "-"),
        "Tanggal": r["tanggal"],
        "Jam Masuk": r["jam_masuk"],
        "Jam Pulang": r["jam_pulang"],
        "Status": r["status"],
        "Keterangan": r["keterangan"]
    } for r in res.data]
    df = pd.DataFrame(rows)
    return df.to_csv(index=False).encode("utf-8")

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

# ================= ADMIN DASHBOARD =================
if mode == "Admin" and password == "risum771":

    st.divider()
    st.subheader("💻 Dashboard Admin")

    today = now_wib().strftime("%Y-%m-%d")

    # QUERY DATA
    res_hari = supabase.table("absensi").select("*").eq("tanggal", today).order("jam_masuk").execute()

    bulan_now = int(now_wib().strftime("%m"))
    tahun_now = int(now_wib().strftime("%Y"))
    jumlah_hari = monthrange(tahun_now, bulan_now)[1]

    res_bulan = supabase.table("absensi")\
        .select("*")\
        .gte("tanggal", f"{tahun_now}-{str(bulan_now).zfill(2)}-01")\
        .lte("tanggal", f"{tahun_now}-{str(bulan_now).zfill(2)}-{jumlah_hari}")\
        .execute()

    res_semua = supabase.table("absensi").select("*").execute()

    # BACKUP BUTTON
    st.subheader("📥 BACKUP DATA CSV")

    col1, col2, col3 = st.columns(3)

    with col1:
        csv_hari = generate_csv(res_hari)
        if csv_hari:
            st.download_button("⬇️ Backup Hari Ini", csv_hari,
                               f"backup_harian_{today}.csv", "text/csv")

    with col2:
        csv_bulan = generate_csv(res_bulan)
        if csv_bulan:
            st.download_button("⬇️ Backup Bulanan", csv_bulan,
                               f"backup_bulanan_{bulan_now}_{tahun_now}.csv", "text/csv")

    with col3:
        csv_all = generate_csv(res_semua)
        if csv_all:
            st.download_button("⬇️ Backup Semua Data", csv_all,
                               f"backup_semua_{today}.csv", "text/csv")

    st.divider()
