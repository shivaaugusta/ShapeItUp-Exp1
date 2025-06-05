# --- Streamlit App ShapeItUp Final ---
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
worksheet = client.open_by_key("1aZ0LjvdZs1WHGphqb_nYrvPma8xEG9mxfM-O1_fsi3g").sheet1

# --- Konfigurasi Shape Pool ---
SHAPE_FOLDER = "shapes"
SHAPE_POOL = sorted([f for f in os.listdir(SHAPE_FOLDER) if f.endswith(".png")])
SHAPE_CATEGORIES = {
    "filled": [s for s in SHAPE_POOL if "filled" in s],
    "unfilled": [s for s in SHAPE_POOL if "unfilled" in s],
    "open": [s for s in SHAPE_POOL if "dash" in s or "open" in s],
}

# --- Inisialisasi session state ---
if "task_index" not in st.session_state:
    st.session_state.task_index = 0
    st.session_state.total_tasks = 53  # 3 latihan + 50 eksperimen
    st.session_state.correct = 0
    st.session_state.mode = "latihan"

st.title("🎯 Eksperimen ShapeItUp: Estimasi Rata-rata Y")

if st.session_state.task_index < 3:
    st.subheader(f"Tugas Latihan #{st.session_state.task_index + 1}")
else:
    if st.session_state.task_index == 3:
        st.session_state.mode = "eksperimen"
    st.subheader(f"Tugas Eksperimen #{st.session_state.task_index - 2} dari 50")

# --- Konfigurasi jumlah kategori dan shape secara acak ---
N = random.choice(range(2, 11))
x_data = [np.random.uniform(0, 1.5, 20) for _ in range(N)]
y_data = [np.random.uniform(0, 1.5, 20) for _ in range(N)]

# --- Ambil acak bentuk dari kombinasi kategori shape ---
shape_types = ["filled", "unfilled", "open"]
chosen_shapes = []
while len(chosen_shapes) < N:
    cat = random.choice(shape_types)
    s = random.choice(SHAPE_CATEGORIES[cat])
    if s not in chosen_shapes:
        chosen_shapes.append(s)

# --- Plot scatter ---
fig, ax = plt.subplots()
for i in range(N):
    for x, y in zip(x_data[i], y_data[i]):
        path = os.path.join(SHAPE_FOLDER, chosen_shapes[i])
        img = Image.open(path).convert("RGBA").resize((20, 20))
        im = OffsetImage(img, zoom=1.0)
        ab = AnnotationBbox(im, (x, y), frameon=False)
        ax.add_artist(ab)
    ax.scatter([], [], label=f"Kategori {i+1}")  # dummy legend

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

    # Tugas latihan harus dijawab benar semua
    if mode == "latihan" and not benar:
        st.warning("Latihan harus benar untuk lanjut.")
        st.stop()

    # Simpan ke Google Sheets
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    response = [
        timestamp, mode, st.session_state.task_index + 1, N,
        selected, f"Kategori {true_idx}", "Benar" if benar else "Salah",
        ", ".join(chosen_shapes)
    ]
    try:
        worksheet.append_row(response)
    except Exception as e:
        st.error(f"Gagal menyimpan data: {e}")

    # Update indeks tugas
    st.session_state.task_index += 1

# --- Selesai eksperimen ---
if st.session_state.task_index >= st.session_state.total_tasks:
    st.success(f"🎉 Eksperimen selesai! Skor akhir Anda: {st.session_state.correct} dari 50.")
    st.balloons()

