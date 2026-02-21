import streamlit as st
from datetime import datetime
import pytz
from geopy.distance import geodesic
from streamlit_js_eval import get_geolocation
from supabase import create_client
from streamlit_autorefresh import st_autorefresh
import pandas as pd

# ================== SUPABASE ==================
SUPABASE_URL = "https://jogrrtkttwzlqkveujxa.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpvZ3JydGt0dHd6bHFrdmV1anhhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzE2OTI3NDQsImV4cCI6MjA4NzI2ODc0NH0.5tSvQvbqXTNCukMpWE6KDzDmzZLkaCGcRxHr0zATDqw"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 🔥 TEST KONEKSI SUPABASE (TARUH DI SINI)
test = supabase.table("nama").select("*").limit(1).execute()
st.write("HASIL TEST SUPABASE:", test)

# ================== HEADER ==================
st_autorefresh(interval=1000, key="clockrefresh")

wib = pytz.timezone("Asia/Jakarta")
now = datetime.now(wib).strftime("%A, %d %B %Y | %H:%M:%S")

st.markdown(f"### 🕒 {now}")
st.title("Dashboard Absensi Staff PT RISUM")

mode = st.sidebar.selectbox("Login Sebagai", ["Karyawan", "Admin"])
if mode == "Admin":
    password = st.sidebar.text_input("Password Admin", type="password")

# ================== GPS ==================
kantor = (-7.76479975133688, 110.48149545435504)
radius = 200

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

# ================== LOAD MASTER DATA ==================
nama_res = supabase.table("nama").select("*").order("nama").execute()
nama_options = nama_res.data
nama_dict = {n["nama"]: n["id"] for n in nama_options}

posisi_res = supabase.table("posisi").select("*").order("posisi").execute()
posisi_options = posisi_res.data
posisi_dict = {p["posisi"]: p["id"] for p in posisi_options}

selected_nama = st.selectbox("Pilih Nama", list(nama_dict.keys()))
selected_posisi = st.selectbox("Posisi", list(posisi_dict.keys()))

datang_pulang = st.radio("Datang / Pulang", ["Datang", "Pulang"])
status = st.radio("Status", ["Hadir", "Izin", "Sakit", "Lembur"])

keterangan = ""
if status != "Hadir":
    keterangan = st.text_area("Keterangan")

# ================== SUBMIT ABSEN ==================
if st.button("Submit Absen"):

    if not lokasi_valid:
        st.error("Harus berada di kantor!")
    else:
        now_wib = datetime.now(wib)
        tanggal = now_wib.strftime("%Y-%m-%d")
        jam = now_wib.strftime("%H:%M:%S")

        # cek sudah absen belum
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

        else:  # pulang

            if not cek.data:
                st.warning("Belum absen datang")
            else:
                supabase.table("absensi")\
                    .update({"jam_pulang": jam})\
                    .eq("nama_id", nama_dict[selected_nama])\
                    .eq("tanggal", tanggal)\
                    .execute()

                st.success("Absen pulang berhasil!")

# ================== ADMIN DASHBOARD ==================
if mode == "Admin" and password == "risum771":

    st.divider()
    st.subheader("📊 Rekap Absensi")

    tab1, tab2 = st.tabs(["Harian", "Bulanan"])

    # ================= HARIAN =================
    with tab1:

        today = datetime.now(wib).strftime("%Y-%m-%d")

        res = supabase.table("absensi")\
            .select("id, tanggal, jam_masuk, jam_pulang, status, keterangan, nama(nama), posisi(posisi)")\
            .eq("tanggal", today)\
            .order("jam_masuk")\
            .execute()

        if res.data:
            rows = []
            for r in res.data:
                rows.append({
                    "ID": r["id"],
                    "Nama": r["nama"]["nama"],
                    "Posisi": r["posisi"]["posisi"],
                    "Tanggal": r["tanggal"],
                    "Jam Datang": r["jam_masuk"],
                    "Jam Pulang": r["jam_pulang"],
                    "Status": r["status"],
                    "Keterangan": r["keterangan"]
                })

            df = pd.DataFrame(rows)
            st.dataframe(df.drop(columns=["ID"]), use_container_width=True)
        else:
            st.info("Belum ada absensi hari ini")

    # ================= BULANAN =================
    with tab2:

        bulan = st.selectbox("Bulan", list(range(1,13)))
        tahun = st.selectbox("Tahun", list(range(2024,2031)))

        res = supabase.table("absensi")\
            .select("id, tanggal, jam_masuk, jam_pulang, status, keterangan, nama(nama), posisi(posisi)")\
            .gte("tanggal", f"{tahun}-{str(bulan).zfill(2)}-01")\
            .lte("tanggal", f"{tahun}-{str(bulan).zfill(2)}-31")\
            .execute()

        if res.data:
            rows = []
            for r in res.data:
                rows.append({
                    "ID": r["id"],
                    "Nama": r["nama"]["nama"],
                    "Posisi": r["posisi"]["posisi"],
                    "Tanggal": r["tanggal"],
                    "Jam Datang": r["jam_masuk"],
                    "Jam Pulang": r["jam_pulang"],
                    "Status": r["status"],
                    "Keterangan": r["keterangan"]
                })

            df = pd.DataFrame(rows)
            st.dataframe(df.drop(columns=["ID"]), use_container_width=True)

            # DELETE DATA
            st.subheader("Hapus Data")

            id_hapus = st.selectbox(
                "Pilih data",
                df["ID"].tolist(),
                format_func=lambda x: f"{df[df['ID']==x]['Nama'].values[0]} - {df[df['ID']==x]['Tanggal'].values[0]}"
            )

            if st.button("Hapus"):
                supabase.table("absensi").delete().eq("id", id_hapus).execute()
                st.success("Data dihapus")
                st.rerun()

        else:
            st.info("Belum ada data bulan ini")


