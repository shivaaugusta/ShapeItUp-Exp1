# --- Streamlit App for ShapeItUp - Eksperimen 1 (Shape Legend Fix) ---
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
worksheet = spreadsheet.worksheet("Eksperimen_1")  # sheet khusus untuk eksperimen 1

# --- Konfigurasi Shape Pool ---
SHAPE_FOLDER = "shapes"
SHAPE_POOL = sorted([f for f in os.listdir(SHAPE_FOLDER) if f.endswith(".png")])

SHAPE_CATEGORIES = {
    "filled": [s for s in SHAPE_POOL if "filled" in s],
    "unfilled": [s for s in SHAPE_POOL if "unfilled" in s and "dash" not in s],
    "open": [s for s in SHAPE_POOL if "dash" in s or "open" in s],
}

# Debug jika pool kosong
if len(SHAPE_POOL) == 0:
    st.error("❌ Folder 'shapes' kosong atau tidak ditemukan.")
    st.stop()

# --- Inisialisasi session state ---
if "task_index" not in st.session_state:
    st.session_state.task_index = 0
    st.session_state.total_tasks = 53
    st.session_state.correct = 0
    st.session_state.mode = "latihan"

st.title("🧠 Eksperimen 1: Pilih Kategori dengan Rata-rata Y Tertinggi")

if st.session_state.task_index < 3:
    st.subheader(f"Latihan #{st.session_state.task_index + 1}")
else:
    if st.session_state.task_index == 3:
        st.session_state.mode = "eksperimen"
    st.subheader(f"Eksperimen #{st.session_state.task_index - 2} dari 50")

# --- Pilih satu jenis shape: filled/unfilled/open ---
shape_types = ["filled", "unfilled", "open"]
selected_type = random.choice(shape_types)
selected_pool = SHAPE_CATEGORIES[selected_type]

if len(selected_pool) < 3:
    st.error(f"❌ Tidak cukup shape untuk tipe: {selected_type}. Cek folder shapes.")
    st.stop()

N = random.choice(range(2, min(9, len(selected_pool))))
chosen_shapes = random.sample(selected_pool, N)

# --- Buat data koordinat dengan satu kategori dominan ---
means = np.random.uniform(0.2, 1.0, N)
target_idx = random.randint(0, N - 1)
means[target_idx] += 0.25
y_data = [np.random.normal(loc=m, scale=0.05, size=20) for m in means]
x_data = [np.random.uniform(0.0, 1.5, 20) for _ in range(N)]

# --- Plot scatter dengan label sesuai bentuk ---
fig, ax = plt.subplots()
for i in range(N):
    for x, y in zip(x_data[i], y_data[i]):
        path = os.path.join(SHAPE_FOLDER, chosen_shapes[i])
        img = Image.open(path).convert("RGBA").resize((20, 20))
        im = OffsetImage(img, zoom=1.0)
        ab = AnnotationBbox(im, (x, y), frameon=False)
        ax.add_artist(ab)
    label = chosen_shapes[i].replace(".png", "").replace("-", " ").replace("_", " ").title()
    ax.scatter([], [], label=label)

ax.set_xlim(-0.1, 1.6)
ax.set_ylim(-0.1, 1.6)
ax.set_xlabel("X")
ax.set_ylabel("Y")
ax.legend()
st.pyplot(fig)

# --- Input jawaban peserta ---
selected = st.selectbox("📍 Pilih kategori dengan rata-rata Y tertinggi:",
                        [f"Kategori {i+1}" for i in range(N)])

# --- Submit ---
if st.button("🚀 Submit Jawaban"):
    true_idx = int(np.argmax([np.mean(y) for y in y_data])) + 1
    user_idx = int(selected.split(" ")[1])
    benar = user_idx == true_idx
    mode = st.session_state.mode

    if benar:
        st.session_state.correct += 1
        st.success(f"✅ Jawaban benar! Kategori {true_idx} memiliki Y tertinggi.")
    else:
        st.error(f"❌ Jawaban salah. Jawaban benar: Kategori {true_idx}.")

    if mode == "latihan" and not benar:
        st.warning("Latihan harus benar untuk lanjut.")
        st.stop()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    response = [
        timestamp, mode, st.session_state.task_index + 1, N,
        selected, f"Kategori {true_idx}", "Benar" if benar else "Salah",
        ", ".join(chosen_shapes), selected_type
    ]
    try:
        worksheet.append_row(response)
    except Exception as e:
        st.error(f"Gagal menyimpan ke Google Sheets: {e}")

    st.session_state.task_index += 1

if st.session_state.task_index >= st.session_state.total_tasks:
    st.success(f"🎉 Eksperimen selesai! Skor akhir Anda: {st.session_state.correct} dari 50.")
    st.balloons()
