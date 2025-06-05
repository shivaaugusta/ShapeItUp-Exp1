# --- Streamlit App for ShapeItUp - Eksperimen 1 (Final: Latihan Ketat, Eksperimen Fleksibel) ---
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from datetime import datetime
import random
import os
import gspread
from google.oauth2.service_account import Credentials

# --- Autentikasi Google Sheets ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(st.secrets["google_sheets"], scopes=scope)
client = gspread.authorize(creds)
spreadsheet = client.open_by_key("1aZ0LjvdZs1WHGphqb_nYrvPma8xEG9mxfM-O1_fsi3g")
worksheet = spreadsheet.worksheet("Eksperimen_1")

# --- Konfigurasi Shape Pool ---
SHAPE_FOLDER = "shapes"
SHAPE_POOL = sorted([f for f in os.listdir(SHAPE_FOLDER) if f.endswith(".png")])

SHAPE_CATEGORIES = {
    "filled": [s for s in SHAPE_POOL if "filled" in s],
    "unfilled": [s for s in SHAPE_POOL if "unfilled" in s and "dash" not in s],
    "open": [s for s in SHAPE_POOL if "dash" in s or "open" in s],
}

if len(SHAPE_POOL) == 0:
    st.error("❌ Folder 'shapes' kosong atau tidak ditemukan.")
    st.stop()

# --- Inisialisasi session state ---
if "task_index" not in st.session_state:
    st.session_state.task_index = 0
    st.session_state.total_tasks = 53  # 3 latihan + 50 eksperimen
    st.session_state.correct = 0
    st.session_state.mode = "latihan"

# Tentukan mode
if st.session_state.task_index < 3:
    st.session_state.mode = "latihan"
    st.subheader(f"Latihan #{st.session_state.task_index + 1}")
else:
    st.session_state.mode = "eksperimen"
    st.subheader(f"Eksperimen #{st.session_state.task_index - 2} dari 50")

st.title("🧠 Eksperimen 1: Pilih Kategori dengan Rata-rata Y Tertinggi")

# --- Setup eksperimen hanya saat pertama kali ---
index = st.session_state.task_index

if f"x_data_{index}" not in st.session_state:
    shape_types = ["filled", "unfilled", "open"]
    # urutkan agar tiap mode digunakan merata (filled, unfilled, open, repeat)
    selected_type = shape_types[index % len(shape_types)]
    selected_pool = SHAPE_CATEGORIES[selected_type]

    if len(selected_pool) < 3:
        st.error(f"❌ Tidak cukup shape untuk tipe: {selected_type}. Cek folder shapes.")
        st.stop()

    N = random.choice(range(2, min(9, len(selected_pool))))
    chosen_shapes = random.sample(selected_pool, N)
    means = np.random.uniform(0.2, 1.0, N)
    target_idx = random.randint(0, N - 1)
    means[target_idx] += 0.25
    y_data = [np.random.normal(loc=m, scale=0.05, size=20) for m in means]
    x_data = [np.random.uniform(0.0, 1.5, 20) for _ in range(N)]
    shape_labels = [s.replace(".png", "").replace("-", " ").replace("_", " ").title() for s in chosen_shapes]

    st.session_state[f"x_data_{index}"] = x_data
    st.session_state[f"y_data_{index}"] = y_data
    st.session_state[f"chosen_shapes_{index}"] = chosen_shapes
    st.session_state[f"shape_labels_{index}"] = shape_labels
    st.session_state[f"selected_type_{index}"] = selected_type

# --- Ambil data dari session state ---
x_data = st.session_state[f"x_data_{index}"]
y_data = st.session_state[f"y_data_{index}"]
chosen_shapes = st.session_state[f"chosen_shapes_{index}"]
shape_labels = st.session_state[f"shape_labels_{index}"]
selected_type = st.session_state[f"selected_type_{index}"]

# --- Plot scatter tanpa legend ---
fig, ax = plt.subplots()
for i in range(len(x_data)):
    for x, y in zip(x_data[i], y_data[i]):
        path = os.path.join(SHAPE_FOLDER, chosen_shapes[i])
        img = Image.open(path).convert("RGBA").resize((15, 15))
        im = OffsetImage(img, zoom=1.0)
        ab = AnnotationBbox(im, (x, y), frameon=False)
        ax.add_artist(ab)

ax.set_xlim(-0.1, 1.6)
ax.set_ylim(-0.1, 1.6)
ax.set_xlabel("X")
ax.set_ylabel("Y")
st.pyplot(fig)

# --- Input jawaban peserta ---
selected_label = st.selectbox("📍 Pilih kategori dengan rata-rata Y tertinggi:", shape_labels)
selected_index = shape_labels.index(selected_label)

# --- Submit ---
if st.button("🚀 Submit Jawaban"):
    true_idx = int(np.argmax([np.mean(y) for y in y_data]))
    benar = selected_index == true_idx
    mode = st.session_state.mode

    if benar:
        st.session_state.correct += 1
        st.success(f"✅ Jawaban benar! {shape_labels[true_idx]} memiliki Y tertinggi.")
    else:
        st.error(f"❌ Jawaban salah. Jawaban benar: {shape_labels[true_idx]}.")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Simpan jawaban hanya untuk eksperimen (50 soal)
    if mode == "eksperimen":
        response = [
            timestamp, mode, index + 1, len(x_data),
            selected_label, shape_labels[true_idx], "Benar" if benar else "Salah",
            ", ".join(chosen_shapes), selected_type
        ]
        try:
            worksheet.append_row(response)
        except Exception as e:
            st.error(f"Gagal menyimpan ke Google Sheets: {e}")

    # Untuk latihan: hanya lanjut jika benar
    if mode == "latihan" and not benar:
        st.warning("Latihan harus dijawab benar untuk lanjut.")
        st.stop()

    st.session_state.task_index += 1
    try:
        st.rerun()
    except AttributeError:
        st.experimental_rerun()

# --- Akhiran ---
if st.session_state.task_index >= st.session_state.total_tasks:
    st.success(f"🎉 Eksperimen selesai! Skor akhir Anda: {st.session_state.correct} dari 50.")
    st.balloons()
