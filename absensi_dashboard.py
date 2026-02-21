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
st.title("Dashboard Absensi Staff PT RISUM")

# ================= MODE =================
mode = st.sidebar.selectbox("Login Sebagai", ["Karyawan", "Admin"])
password = ""
if mode == "Admin":
    password = st.sidebar.text_input("Password Admin", type="password")

# ================= GPS (untuk karyawan) =================
kantor = (-7.76479975133688, 110.48149545435504)
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

# ================= LOAD MASTER (nama & posisi) =================
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

# ================= MODE KARYAWAN (HP) =================
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

# ================= MODE ADMIN (LAPTOP) =================
if mode == "Admin" and password == "risum771":

    st.divider()
    st.subheader("💻 Dashboard Admin")

    tab1, tab2, tab3 = st.tabs(["Hari Ini", "Bulanan", "Semua Data"])

    # ---------- TAB 1: REKAP HARI INI ----------
    with tab1:
        today = now_wib().strftime("%Y-%m-%d")
        res = supabase.table("absensi")\
            .select("id,nama_id,posisi_id,tanggal,jam_masuk,jam_pulang,status,keterangan")\
            .eq("tanggal", today)\
            .order("jam_masuk")\
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

            st.subheader("🗑 Hapus Data")
            pilih = st.selectbox(
                "Pilih data",
                rows,
                format_func=lambda x: f"{x['Nama']} - {x['Tanggal']} - {x['Status']}"
            )
            if st.button("Hapus Data"):
                supabase.table("absensi").delete().eq("id", pilih["ID"]).execute()
                st.success("Data berhasil dihapus")
                st.rerun()
        else:
            st.info("Belum ada absensi hari ini")

    # ---------- TAB 2: REKAP BULANAN ----------
    # ---------- TAB 2: REKAP BULANAN ----------
with tab2:
    bulan = st.selectbox("Bulan", list(range(1,13)))
    tahun = st.selectbox("Tahun", list(range(2024,2031)))

    # ambil jumlah hari dalam bulan
    jumlah_hari = monthrange(tahun, bulan)[1]

    res = supabase.table("absensi")\
        .select("id,nama_id,posisi_id,tanggal,jam_masuk,jam_pulang,status,keterangan")\
        .gte("tanggal", f"{tahun}-{str(bulan).zfill(2)}-01")\
        .lte("tanggal", f"{tahun}-{str(bulan).zfill(2)}-{jumlah_hari}")\
        .order("tanggal")\
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

    # ---------- TAB 3: SEMUA DATA (opsional) ----------
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

