import streamlit as st
from datetime import datetime
import pytz
from supabase import create_client
import pandas as pd

# ================= SUPABASE =================
SUPABASE_URL = "https://jogrrtkttwzlqkveujxa.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpvZ3JydGt0dHd6bHFrdmV1anhhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzE2OTI3NDQsImV4cCI6MjA4NzI2ODc0NH0.5tSvQvbqXTNCukMpWE6KDzDmzZLkaCGcRxHr0zATDqw"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ================= HEADER =================
wib = pytz.timezone("Asia/Jakarta")
now = datetime.now(wib).strftime("%A, %d %B %Y | %H:%M:%S")

st.markdown(f"### 🕒 {now}")
st.title("Dashboard Absensi Staff PT RISUM")

mode = st.sidebar.selectbox("Login Sebagai", ["Karyawan", "Admin"])
password = ""
if mode == "Admin":
    password = st.sidebar.text_input("Password Admin", type="password")

# ================= LOAD MASTER DATA =================
nama_res = supabase.table("nama").select("*").order("nama").execute()
posisi_res = supabase.table("posisi").select("*").order("posisi").execute()

nama_options = nama_res.data
posisi_options = posisi_res.data

nama_dict = {n["nama"]: n["id"] for n in nama_options}
posisi_dict = {p["posisi"]: p["id"] for p in posisi_options}

selected_nama = st.selectbox("Pilih Nama", list(nama_dict.keys()))
selected_posisi = st.selectbox("Posisi", list(posisi_dict.keys()))

datang_pulang = st.radio("Datang / Pulang", ["Datang", "Pulang"])
status = st.radio("Status", ["Hadir", "Izin", "Sakit", "Lembur"])
keterangan = st.text_area("Keterangan")

# ================= SUBMIT ABSEN =================
if st.button("Submit Absen"):

    now_wib = datetime.now(wib)
    tanggal = now_wib.strftime("%Y-%m-%d")
    jam = now_wib.strftime("%H:%M:%S")

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
    st.subheader("📊 Rekap Absensi")

    res = supabase.table("absensi")\
        .select("id,nama_id,posisi_id,tanggal,jam_masuk,jam_pulang,status,keterangan")\
        .order("tanggal", desc=True)\
        .execute()

    if res.data:

        # ambil master nama & posisi
        nama_master = supabase.table("nama").select("*").execute().data
        posisi_master = supabase.table("posisi").select("*").execute().data

        nama_map = {n["id"]: n["nama"] for n in nama_master}
        posisi_map = {p["id"]: p["posisi"] for p in posisi_master}

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
        st.info("Belum ada data absensi")

