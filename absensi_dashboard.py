import streamlit as st
from datetime import datetime
import pytz
from geopy.distance import geodesic
from streamlit_js_eval import get_geolocation
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

# ================= LOAD MASTER =================
nama_res = supabase.table("nama").select("*").execute()
posisi_res = supabase.table("posisi").select("*").execute()

nama_dict = {n["nama"]: n["id"] for n in nama_res.data}
posisi_dict = {p["posisi"]: p["id"] for p in posisi_res.data}

selected_nama = st.selectbox("Pilih Nama", list(nama_dict.keys()))
selected_posisi = st.selectbox("Posisi", list(posisi_dict.keys()))

datang_pulang = st.radio("Datang / Pulang", ["Datang", "Pulang"])
status = st.radio("Status", ["Hadir", "Izin", "Sakit", "Lembur"])
keterangan = st.text_area("Keterangan")

# ================= SUBMIT =================
if st.button("Submit Absen"):

    now_wib = datetime.now(wib)
    tanggal = now_wib.strftime("%Y-%m-%d")
    jam = now_wib.strftime("%H:%M:%S")

    supabase.table("absensi").insert({
        "nama_id": nama_dict[selected_nama],
        "posisi_id": posisi_dict[selected_posisi],
        "tanggal": tanggal,
        "jam_masuk": jam,
        "status": status,
        "keterangan": keterangan
    }).execute()

    st.success("Absen berhasil!")

# ================= ADMIN =================
if mode == "Admin" and password == "risum771":

    st.divider()
    st.subheader("Rekap Absensi")

    res = supabase.table("absensi").select("*").execute()

    if res.data:
        df = pd.DataFrame(res.data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Belum ada data")
