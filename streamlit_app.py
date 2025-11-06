import streamlit as st
import sqlite3
import qrcode
from PIL import Image
import os
import pandas as pd
from io import BytesIO
import base64

# --- Konfigurasi Direktori Aman untuk Cloud ---
BASE_DIR = os.path.join(os.getcwd(), "temp_data")
os.makedirs(BASE_DIR, exist_ok=True)

DB_PATH = os.path.join(BASE_DIR, "data_produksi.db")
QR_FOLDER = os.path.join(BASE_DIR, "qr_codes")
os.makedirs(QR_FOLDER, exist_ok=True)

# --- Koneksi & Buat Tabel Database ---
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS produksi (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id TEXT,
    tanggal TEXT,
    pic TEXT,
    tempat_produksi TEXT,
    varian_produksi TEXT
)
""")
conn.commit()

# --- Fungsi Tambah Data ---
def tambah_data(batch_id, tanggal, pic, tempat, varian):
    cursor.execute("""
        INSERT INTO produksi (batch_id, tanggal, pic, tempat_produksi, varian_produksi)
        VALUES (?, ?, ?, ?, ?)
    """, (batch_id, tanggal, pic, tempat, varian))
    conn.commit()

    qr_text = (
        f"Batch ID: {batch_id}\n"
        f"Tanggal: {tanggal}\n"
        f"PIC: {pic}\n"
        f"Tempat Produksi: {tempat}\n"
        f"Varian Produksi: {varian}"
    )
    qr = qrcode.make(qr_text)
    qr_path = os.path.join(QR_FOLDER, f"{batch_id}.png")
    qr.save(qr_path)
    return qr_path

# --- Fungsi QR ke Base64 ---
def image_to_base64(path):
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# --- Tampilan Streamlit ---
st.set_page_config(page_title="QR Tracking Harlur Coffee", page_icon="☕", layout="wide")
st.title("QR Tracking Harlur Coffee")
st.markdown("Mencatat data produksi dan membuat QR code untuk setiap batch produk Harlur Coffee.")

menu = st.sidebar.selectbox("Pilih Menu", ["Tambah Data", "Lihat Data"])

# ===================== TAMBAH DATA =====================
if menu == "Tambah Data":
    st.subheader("📦 Input Data Produksi Baru")

    with st.form("form_produksi"):
        batch_id = st.text_input("Batch ID")
        tanggal = st.date_input("Tanggal Produksi")
        pic = st.text_input("Nama PIC")
        tempat = st.text_input("Tempat Produksi")
        varian = st.text_input("Varian Produksi (jenis kopi, rasa, dll.)")
        submitted = st.form_submit_button("Simpan Data & Buat QR")

        if submitted:
            if all([batch_id, tanggal, pic, tempat, varian]):
                qr_path = tambah_data(batch_id, str(tanggal), pic, tempat, varian)
                st.success("✅ Data berhasil disimpan!")
                st.image(qr_path, caption=f"QR Code untuk Batch {batch_id}", width=200)
            else:
                st.error("⚠️ Harap isi semua kolom sebelum menyimpan.")

# ===================== LIHAT DATA =====================
elif menu == "Lihat Data":
    st.subheader("📋 Daftar Data Produksi")
    df = pd.read_sql_query("SELECT * FROM produksi", conn)

    if not df.empty:
        df["QR_Code_Path"] = df["batch_id"].apply(lambda x: os.path.join(QR_FOLDER, f"{x}.png"))

        def make_img_tag(path):
            if os.path.exists(path):
                img_b64 = image_to_base64(path)
                return f'<img src="data:image/png;base64,{img_b64}" width="100">'
            else:
                return "❌ Tidak ditemukan"

        df["QR_Code"] = df["QR_Code_Path"].apply(make_img_tag)
        df_display = df[["batch_id", "tanggal", "pic", "tempat_produksi", "varian_produksi", "QR_Code"]]
        df_display.columns = ["Batch ID", "Tanggal", "PIC", "Tempat Produksi", "Varian Produksi", "QR Code"]

        st.markdown(df_display.to_html(escape=False, index=False), unsafe_allow_html=True)
    else:
        st.info("Belum ada data produksi tersimpan.")

st.caption("Made with ❤️ by Kelompok 11 – Harlur Coffee Project")
