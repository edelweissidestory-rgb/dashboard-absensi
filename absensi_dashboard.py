import streamlit as st
import sqlite3
from datetime import datetime
from geopy.distance import geodesic
from streamlit_js_eval import get_geolocation

# ================== Koneksi Database ==================
conn = sqlite3.connect("absensi.db", check_same_thread=False)
c = conn.cursor()
# Tambah kolom jam_pulang kalau belum ada
try:
    c.execute("ALTER TABLE absensi ADD COLUMN jam_pulang TEXT")
    conn.commit()
except:
    pass


st.title("Dashboard Absensi Staff PT RISUM")
mode = st.sidebar.selectbox("Login Sebagai", ["Karyawan", "Admin"])

if mode == "Admin":
    password = st.sidebar.text_input("Password Admin", type="password")


st.markdown("""
<style>

[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #e8f5e9, #ffffff);
}

h1 {
    color: #2e7d32;
    text-align: center;
}

.block-container {
    padding-top: 2rem;
}

.kotak-hijau {
    background-color: #e8f5e9;
    padding: 20px;
    border-radius: 12px;
    border-left: 6px solid #2e7d32;
    box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    margin-bottom: 15px;
}

.kotak-merah {
    background-color: #ffebee;
    padding: 20px;
    border-radius: 12px;
    border-left: 6px solid #c62828;
    box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    margin-bottom: 15px;
}

</style>
""", unsafe_allow_html=True)

# ================== Koordinat Kantor ==================
kantor = (-7.7509616760437385, 110.36579129415266)
radius = 150
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
c.execute("SELECT id, nama FROM nama ORDER BY nama")
nama_options = c.fetchall()
nama_dict = {n[1]: n[0] for n in nama_options}
selected_nama = st.selectbox("Pilih Nama", list(nama_dict.keys()))

# ================== Pilih Posisi ==================
c.execute("SELECT id, posisi FROM posisi")
posisi_options = c.fetchall()
posisi_dict = {p[1]: p[0] for p in posisi_options}
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
        tanggal = datetime.now().strftime("%Y-%m-%d")
        jam_sekarang = datetime.now().strftime("%H:%M:%S")

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
                c.execute("""
                    INSERT INTO absensi (nama_id, posisi_id, tanggal, status, jam_masuk, keterangan)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    nama_dict[selected_nama],
                    posisi_dict[selected_posisi],
                    tanggal,
                    status,  # Hadir / Izin / Sakit
                    jam_sekarang,
                    keterangan
                ))
                conn.commit()
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
                c.execute("""
                    UPDATE absensi
                    SET jam_pulang=?
                    WHERE nama_id=? AND tanggal=?
                """, (jam_sekarang, nama_dict[selected_nama], tanggal))
                conn.commit()
                st.success("Absen Pulang berhasil!")
# ================== REKAP ADMIN ==================
# ================== REKAP ADMIN ==================
# ================== REKAP ADMIN ==================
if mode == "Admin" and password == "risum771":

    st.markdown("---")
    st.subheader("📊 Rekap Absensi Hari Ini")

    today = datetime.now().strftime("%Y-%m-%d")

    c.execute("""
    SELECT a.id, n.nama, p.posisi, a.tanggal,
           a.jam_masuk, a.jam_pulang,
           a.status, a.keterangan
    FROM absensi a
    JOIN nama n ON a.nama_id = n.id
    JOIN posisi p ON a.posisi_id = p.id
    WHERE a.tanggal = ?
    ORDER BY 
    a.tanggal DESC,
    CASE WHEN a.jam_pulang IS NULL THEN 0 ELSE 1 END,
    a.jam_masuk ASC
    """, (today,))

    data = c.fetchall()

    if data:
        import pandas as pd

        df = pd.DataFrame(data, columns=[
            "ID", "Nama", "Posisi", "Tanggal",
            "Jam Datang", "Jam Pulang",
            "Status", "Keterangan"
        ])

        st.dataframe(df.drop(columns=["ID"]), use_container_width=True)

        st.markdown("### 🗑️ Hapus Data Absensi")

        id_hapus = st.selectbox(
            "Pilih Data yang Mau Dihapus",
            df["ID"],
            format_func=lambda x: f"{df[df['ID']==x]['Nama'].values[0]} - {df[df['ID']==x]['Jam Datang'].values[0]}"
        )

        if st.button("Hapus Data"):
            c.execute("DELETE FROM absensi WHERE id=?", (id_hapus,))
            conn.commit()
            st.success("Data berhasil dihapus!")
            st.rerun()

    else:
        st.info("Belum ada absensi hari ini")