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

# ================= CSV BACKUP =================
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
            st.error("Harus berada di area kantor")
            st.stop()

        tanggal = now_wib().strftime("%Y-%m-%d")
        jam = now_wib().strftime("%H:%M:%S")

        cek = supabase.table("absensi")\
            .select("*")\
            .eq("nama_id", nama_dict[selected_nama])\
            .eq("tanggal", tanggal)\
            .eq("is_deleted", False)\
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
                    "keterangan": keterangan,
                    "is_deleted": False
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
                    .eq("is_deleted", False)\
                    .execute()
                st.success("Absen pulang berhasil!")

# ================= ADMIN DASHBOARD =================
if mode == "Admin" and password == "risum771":

    st.divider()
    st.header("💻 Dashboard Admin")

    tab1, tab2, tab3, tab4 = st.tabs(
        ["Hari Ini", "Bulanan", "Semua Data", "♻️ Data Terhapus"]
    )

    def tampilkan_data(res, prefix):

        if not res.data:
            st.info("Tidak ada data.")
            return

        rows = [{
            "ID": r["id"],
            "Nama": nama_map.get(r["nama_id"], "-"),
            "Posisi": posisi_map.get(r["posisi_id"], "-"),
            "Tanggal": r["tanggal"],
            "Jam Masuk": r["jam_masuk"],
            "Jam Pulang": r["jam_pulang"],
            "Status": r["status"],
            "Keterangan": r["keterangan"]
        } for r in res.data]

        df = pd.DataFrame(rows)
        st.dataframe(df.drop(columns=["ID"]), use_container_width=True)

        csv_data = generate_csv(res)
        if csv_data:
            st.download_button(
                "⬇️ Backup CSV",
                csv_data,
                f"backup_{prefix}_{now_wib().strftime('%Y%m%d_%H%M')}.csv",
                "text/csv",
                key=f"{prefix}_backup"
            )

        selected = st.selectbox(
            "Pilih Data",
            rows,
            format_func=lambda x: f"{x['Nama']} - {x['Tanggal']} - {x['Status']}",
            key=f"{prefix}_select"
        )

        # ========= EDIT SEMUA KOLOM =========
        with st.expander("✏️ Edit Data Lengkap"):

            edit_nama = st.selectbox(
                "Nama",
                list(nama_dict.keys()),
                index=list(nama_dict.keys()).index(selected["Nama"]),
                key=f"{prefix}_nama"
            )

            edit_posisi = st.selectbox(
                "Posisi",
                list(posisi_dict.keys()),
                index=list(posisi_dict.keys()).index(selected["Posisi"]),
                key=f"{prefix}_posisi"
            )

            edit_tanggal = st.date_input(
                "Tanggal",
                pd.to_datetime(selected["Tanggal"]),
                key=f"{prefix}_tanggal"
            )

            edit_jam_masuk = st.text_input(
                "Jam Masuk (HH:MM:SS)",
                selected["Jam Masuk"] or "",
                key=f"{prefix}_masuk"
            )

            edit_jam_pulang = st.text_input(
                "Jam Pulang (HH:MM:SS)",
                selected["Jam Pulang"] or "",
                key=f"{prefix}_pulang"
            )

            edit_status = st.selectbox(
                "Status",
                ["Hadir","Izin","Sakit","Lembur"],
                index=["Hadir","Izin","Sakit","Lembur"].index(selected["Status"]),
                key=f"{prefix}_status"
            )

            edit_keterangan = st.text_area(
                "Keterangan",
                selected["Keterangan"] or "",
                key=f"{prefix}_ket"
            )

            if st.button("💾 Simpan Semua Perubahan", key=f"{prefix}_save"):

                supabase.table("absensi").update({
                    "nama_id": nama_dict[edit_nama],
                    "posisi_id": posisi_dict[edit_posisi],
                    "tanggal": str(edit_tanggal),
                    "jam_masuk": edit_jam_masuk,
                    "jam_pulang": edit_jam_pulang,
                    "status": edit_status,
                    "keterangan": edit_keterangan
                }).eq("id", selected["ID"]).execute()

                st.success("Data berhasil diperbarui.")
                st.rerun()

        # ========= SOFT DELETE =========
        with st.expander("🗑 Hapus Data (Soft Delete)"):

            confirm = st.checkbox(
                "Saya yakin ingin menghapus data ini",
                key=f"{prefix}_confirm"
            )

            if confirm:
                if st.button("Hapus Sekarang", key=f"{prefix}_delete"):
                    supabase.table("absensi")\
                        .update({"is_deleted": True})\
                        .eq("id", selected["ID"])\
                        .execute()
                    st.success("Data dipindahkan ke Data Terhapus")
                    st.rerun()

    # TAB HARI INI
    with tab1:
        today = now_wib().strftime("%Y-%m-%d")
        res = supabase.table("absensi")\
            .select("*")\
            .eq("tanggal", today)\
            .eq("is_deleted", False)\
            .order("jam_masuk")\
            .execute()
        tampilkan_data(res, "hariini")

    # TAB BULANAN
    with tab2:
        bulan = st.selectbox("Bulan", list(range(1,13)), key="bulan")
        tahun = st.selectbox("Tahun", list(range(2024,2031)), key="tahun")
        jumlah_hari = monthrange(tahun, bulan)[1]

        res = supabase.table("absensi")\
            .select("*")\
            .gte("tanggal", f"{tahun}-{str(bulan).zfill(2)}-01")\
            .lte("tanggal", f"{tahun}-{str(bulan).zfill(2)}-{jumlah_hari}")\
            .eq("is_deleted", False)\
            .order("tanggal")\
            .execute()

        tampilkan_data(res, "bulanan")

    # TAB SEMUA DATA
    with tab3:
        res = supabase.table("absensi")\
            .select("*")\
            .eq("is_deleted", False)\
            .order("tanggal", desc=True)\
            .execute()
        tampilkan_data(res, "semua")

    # TAB RESTORE
    with tab4:
        st.subheader("♻️ Data Terhapus")

        res = supabase.table("absensi")\
            .select("*")\
            .eq("is_deleted", True)\
            .order("tanggal", desc=True)\
            .execute()

        if not res.data:
            st.info("Tidak ada data terhapus.")
        else:
            rows = [{
                "ID": r["id"],
                "Nama": nama_map.get(r["nama_id"], "-"),
                "Tanggal": r["tanggal"],
                "Status": r["status"]
            } for r in res.data]

            selected = st.selectbox(
                "Pilih data untuk restore",
                rows,
                format_func=lambda x: f"{x['Nama']} - {x['Tanggal']} - {x['Status']}"
            )

            if st.button("Restore Data"):
                supabase.table("absensi")\
                    .update({"is_deleted": False})\
                    .eq("id", selected["ID"])\
                    .execute()

                st.success("Data berhasil direstore")
                st.rerun()
