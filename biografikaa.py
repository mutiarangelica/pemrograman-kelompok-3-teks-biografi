import streamlit as st
import os
import re
import csv
from datetime import datetime
from collections import Counter


# =========================================================
# KONFIGURASI HALAMAN
# =========================================================

st.set_page_config(
    page_title="BIOGRAFIKA AI",
    page_icon="🧠✨",
    layout="wide"
)


# =========================================================
# KONFIGURASI DATABASE
# =========================================================

FOLDER_DATABASE = "database"


# =========================================================
# KONFIGURASI DATA PENGGUNA & RIWAYAT
# =========================================================

FOLDER_DATA = "data"
FILE_PENGGUNA = os.path.join(FOLDER_DATA, "pengguna.csv")
FILE_RIWAYAT = os.path.join(FOLDER_DATA, "riwayat_pertanyaan.csv")


def siapkan_file_data():
    os.makedirs(FOLDER_DATA, exist_ok=True)

    if not os.path.exists(FILE_PENGGUNA):
        with open(FILE_PENGGUNA, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow(["nama", "kelas", "waktu_daftar"])

    if not os.path.exists(FILE_RIWAYAT):
        with open(FILE_RIWAYAT, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow([
                "nama", "kelas", "pertanyaan", "jawaban",
                "sumber_materi", "waktu"
            ])


def baca_csv(nama_file):
    if not os.path.exists(nama_file):
        return []

    try:
        with open(nama_file, "r", newline="", encoding="utf-8-sig") as file:
            return list(csv.DictReader(file))
    except Exception:
        return []


def simpan_pengguna(nama, kelas):
    siapkan_file_data()
    pengguna = baca_csv(FILE_PENGGUNA)

    # Jangan mencatat presensi berulang pada sesi yang sama.
    sudah_tercatat = any(
        item.get("nama", "").strip().lower() == nama.strip().lower()
        and item.get("kelas", "").strip().lower() == kelas.strip().lower()
        for item in pengguna
    )

    # Tetap mengembalikan identitas pengguna meskipun sudah pernah terdaftar.
    if sudah_tercatat:
        return

    with open(FILE_PENGGUNA, "a", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow([
            nama.strip(),
            kelas.strip(),
            datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        ])


def simpan_riwayat_pertanyaan(
    nama, kelas, pertanyaan, jawaban, sumber_materi
):
    siapkan_file_data()

    with open(FILE_RIWAYAT, "a", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow([
            nama.strip(),
            kelas.strip(),
            pertanyaan.strip(),
            jawaban.strip(),
            sumber_materi,
            datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        ])


# =========================================================
# FUNGSI MEMBACA DATABASE TXT
# =========================================================

def baca_database():

    data = []

    if not os.path.exists(FOLDER_DATABASE):
        os.makedirs(FOLDER_DATABASE)

    daftar_file = os.listdir(FOLDER_DATABASE)

    for nama_file in daftar_file:

        if nama_file.lower().endswith(".txt"):

            lokasi_file = os.path.join(
                FOLDER_DATABASE,
                nama_file
            )

            try:

                with open(
                    lokasi_file,
                    "r",
                    encoding="utf-8"
                ) as file:

                    isi = file.read()

                data.append({
                    "nama_file": nama_file,
                    "isi": isi
                })

            except Exception as error:

                st.error(
                    f"Gagal membaca {nama_file}: {error}"
                )

    return data


# =========================================================
# MEMBERSIHKAN TEKS
# =========================================================

def bersihkan_teks(teks):

    teks = teks.lower()

    teks = re.sub(
        r"[^a-zA-ZÀ-ÿ0-9\s]",
        " ",
        teks
    )

    teks = re.sub(
        r"\s+",
        " ",
        teks
    )

    return teks.strip()


# =========================================================
# STOPWORDS SEDERHANA
# =========================================================

STOPWORDS = {
    "yang",
    "dan",
    "di",
    "ke",
    "dari",
    "pada",
    "dengan",
    "untuk",
    "dalam",
    "adalah",
    "itu",
    "ini",
    "atau",
    "apa",
    "bagaimana",
    "mengapa",
    "sebutkan",
    "jelaskan",
    "jelaskanlah",
    "tentang",
    "suatu",
    "sebuah",
    "secara",
    "merupakan",
    "dapat",
    "akan",
    "sebagai",
    "oleh",
    "lebih",
    "juga",
    "tidak",
    "tersebut"
}


# =========================================================
# MENGAMBIL KATA KUNCI
# =========================================================

def ambil_kata_kunci(pertanyaan):

    teks = bersihkan_teks(pertanyaan)

    kata = teks.split()

    kata_kunci = []

    for item in kata:

        if len(item) > 2 and item not in STOPWORDS:

            kata_kunci.append(item)

    return kata_kunci


# =========================================================
# SISTEM PENILAIAN RELEVANSI
# =========================================================

def hitung_relevansi(pertanyaan, isi):

    kata_kunci = ambil_kata_kunci(pertanyaan)

    if len(kata_kunci) == 0:
        return 0

    teks_database = bersihkan_teks(isi)

    kata_database = teks_database.split()

    frekuensi = Counter(kata_database)

    skor = 0

    for kata in kata_kunci:

        if kata in frekuensi:

            jumlah = frekuensi[kata]

            if jumlah > 10:
                jumlah = 10

            skor += jumlah

    # Bonus jika frasa pertanyaan muncul
    pertanyaan_bersih = bersihkan_teks(
        pertanyaan
    )

    if pertanyaan_bersih in teks_database:

        skor += 20

    # Bonus jika kata kunci utama terdapat di judul
    baris_awal = teks_database[:500]

    for kata in kata_kunci:

        if kata in baris_awal:

            skor += 5

    return skor


# =========================================================
# MENCARI MATERI
# =========================================================

def cari_materi(pertanyaan, database):

    hasil = []

    for data in database:

        skor = hitung_relevansi(
            pertanyaan,
            data["isi"]
        )

        if skor > 0:

            hasil.append({
                "nama_file": data["nama_file"],
                "isi": data["isi"],
                "skor": skor
            })

    hasil.sort(
        key=lambda x: x["skor"],
        reverse=True
    )

    return hasil


# =========================================================
# MEMBUAT POTONGAN MATERI
# =========================================================

def ambil_potongan_relevan(
    pertanyaan,
    isi,
    jumlah_maksimal=1200
):

    kata_kunci = ambil_kata_kunci(
        pertanyaan
    )

    paragraf = re.split(
        r"\n\s*\n|\r\n",
        isi
    )

    paragraf_relevan = []

    for p in paragraf:

        p_bersih = bersihkan_teks(p)

        skor = 0

        for kata in kata_kunci:

            if kata in p_bersih:

                skor += 1

        if skor > 0:

            paragraf_relevan.append(
                (skor, p.strip())
            )

    paragraf_relevan.sort(
        key=lambda x: x[0],
        reverse=True
    )

    hasil = ""

    for skor, p in paragraf_relevan:

        if len(hasil) + len(p) <= jumlah_maksimal:

            hasil += p + "\n\n"

    if hasil.strip() == "":

        hasil = isi[:jumlah_maksimal]

    return hasil.strip()



# =========================================================
# LOAD DATABASE
# =========================================================

database = baca_database()
siapkan_file_data()

# =========================================================
# SESSION STATE
# =========================================================

if "nama_pengguna" not in st.session_state:
    st.session_state.nama_pengguna = ""

if "kelas_pengguna" not in st.session_state:
    st.session_state.kelas_pengguna = ""

if "sudah_presensi" not in st.session_state:
    st.session_state.sudah_presensi = False

if "riwayat" not in st.session_state:
    st.session_state.riwayat = []

if "hasil_terakhir" not in st.session_state:
    st.session_state.hasil_terakhir = None

if "pertanyaan_terakhir" not in st.session_state:
    st.session_state.pertanyaan_terakhir = ""

# =========================================================
# TAMPILAN / DEKORASI
# =========================================================

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background:#f8f7f4; }
[data-testid="stHeader"] { background:rgba(248,247,244,.9); }
.block-container { max-width:1180px; padding-top:2rem; padding-bottom:2rem; }
[data-testid="stSidebar"] { background:#fffdf9; border-right:1px solid #e9e3da; }
[data-testid="stSidebar"] .block-container { padding-top:2rem; }
.hero { position:relative; overflow:hidden; padding:34px 38px; border-radius:26px; background:linear-gradient(135deg,#efe7dc 0%,#f7f1e8 52%,#e7edf0 100%); border:1px solid #e2d9cc; box-shadow:0 12px 35px rgba(62,48,35,.07); margin-bottom:28px; }
.hero:after { content:"✦"; position:absolute; right:34px; top:18px; font-size:76px; color:rgba(120,93,63,.1); }
.hero-kicker { color:#8a6f52; font-size:13px; font-weight:700; letter-spacing:1.8px; text-transform:uppercase; margin-bottom:8px; }
.hero h1 { margin:0; color:#2f2924; font-size:40px; line-height:1.15; font-weight:750; }
.hero p { color:#6d6259; font-size:16px; max-width:720px; line-height:1.7; margin:10px 0 0; }
.section-label { color:#8a6f52; font-size:12px; font-weight:750; letter-spacing:1.4px; text-transform:uppercase; margin-bottom:5px; }
.section-title { color:#302a25; font-size:27px; font-weight:750; margin-bottom:14px; }
.feature-card { background:#fffdf9; border:1px solid #e9e2d8; border-radius:20px; padding:23px; min-height:150px; box-shadow:0 7px 22px rgba(62,48,35,.055); }
.feature-icon { font-size:25px; margin-bottom:10px; }
.feature-card h3 { color:#342d27; margin:0 0 7px; font-size:18px; }
.feature-card p { color:#746a61; line-height:1.6; margin:0; font-size:14px; }
.info-card { background:#fffdf9; border:1px solid #e9e2d8; border-radius:20px; padding:24px; box-shadow:0 7px 22px rgba(62,48,35,.045); }
textarea, input { border-radius:14px !important; }
.stButton > button { border-radius:12px; min-height:44px; font-weight:700; border:1px solid #ded4c8; transition:.2s ease; }
.stButton > button:hover { border-color:#a88a68; transform:translateY(-1px); }
div[data-testid="stMetric"] { background:#fffdf9; padding:16px; border-radius:16px; border:1px solid #e9e2d8; box-shadow:0 5px 16px rgba(62,48,35,.04); }
div[data-testid="stAlert"] { border-radius:14px; }
hr { border-color:#e7e0d7; }
.footer { text-align:center; color:#81776e; font-size:13px; padding:24px 0 8px; }
</style>
""", unsafe_allow_html=True)

# =========================================================
# HEADER
# =========================================================

st.markdown("""
<div class="hero">
    <div class="hero-kicker">Ruang Belajar Digital</div>
    <h1>🧠✨ BIOGRAFIKA AI</h1>
    <p>Temukan materi, ajukan pertanyaan, dan latih pemahaman Bahasa Indonesia melalui satu ruang belajar yang sederhana dan nyaman.</p>
</div>
""", unsafe_allow_html=True)

# =========================================================
# SIDEBAR MENU
# =========================================================

with st.sidebar:
    st.markdown("### 🧠✨ BIOGRAFIKA")
    st.caption("AI")
    st.markdown("**Navigasi**")

    menu = st.radio(
        "Pilih halaman:",
        [
            "🏠 Beranda",
            "📝 Presensi",
            "🔎 Tanya Materi",
            "📖 Daftar Materi",
            "📝 Kuis Mini",
            "👥 Data Pengguna",
            "🕘 Riwayat Pertanyaan",
            "ℹ️ Tentang",
        ],
        label_visibility="collapsed"
    )

    if st.session_state.sudah_presensi:
        st.success(
            f"👤 {st.session_state.nama_pengguna}\n"
            f"🏫 {st.session_state.kelas_pengguna}"
        )
    else:
        st.warning("Belum melakukan presensi.")

    st.divider()

    st.markdown("### 📊 Knowledge Base")
    st.metric("File materi", len(database))

    if database:
        st.success("Database siap digunakan ✨")
    else:
        st.warning("Folder database masih kosong.")

    st.divider()
    st.caption("💡 Tip: gunakan pertanyaan yang spesifik agar hasil pencarian lebih relevan.")
    st.caption("🔐 Data pengguna dan pertanyaan tersimpan di folder `data/`.")

# =========================================================
# BERANDA
# =========================================================

if menu == "🏠 Beranda":

    st.markdown('<div class="section-label">Mulai dari sini</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Selamat datang 👋</div>', unsafe_allow_html=True)
    st.write("Pilih fitur yang ingin digunakan. Semua materi bersumber dari Knowledge Base pada folder `database/`.")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🔎</div>
            <h3>Tanya Materi</h3>
            <p>Ajukan pertanyaan dan sistem akan mencari materi yang paling relevan.</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📖</div>
            <h3>Jelajahi Materi</h3>
            <p>Lihat daftar file TXT yang tersedia sebagai sumber belajar.</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📝</div>
            <h3>Kuis Mini</h3>
            <p>Uji pemahaman dengan pertanyaan singkat Bahasa Indonesia.</p>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.subheader("💬 Contoh Pertanyaan")

    contoh = [
        "Apa yang dimaksud dengan Biografi?",
        "Apa pengertian teks Biografi?",
        "Apa saja ciri-ciri teks Biografi?",
        "Apa saja jenis teks biografi?",
    ]

    for item in contoh:
        st.markdown(f"🌼 **{item}**")

    st.info("💡 Gunakan menu di sebelah kiri untuk mulai belajar.")


# =========================================================
# PRESENSI
# =========================================================

elif menu == "📝 Presensi":

    st.markdown('<div class="section-label">Identitas Pengguna</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📝 Presensi Pengguna</div>', unsafe_allow_html=True)
    st.write(
        "Isi nama dan kelas terlebih dahulu agar aktivitas bertanya "
        "dapat tercatat dengan jelas."
    )

    with st.container(border=True):
        nama = st.text_input(
            "👤 Nama lengkap",
            value=st.session_state.nama_pengguna,
            placeholder="Contoh: Aisyah Putri"
        )

        kelas = st.text_input(
            "🏫 Kelas",
            value=st.session_state.kelas_pengguna,
            placeholder="Contoh: VIII A"
        )

        if st.button("✅ Simpan Presensi", use_container_width=True):
            if not nama.strip() or not kelas.strip():
                st.warning("Nama dan kelas wajib diisi.")
            else:
                st.session_state.nama_pengguna = nama.strip()
                st.session_state.kelas_pengguna = kelas.strip()
                st.session_state.sudah_presensi = True
                simpan_pengguna(nama, kelas)
                st.success(
                    f"Presensi berhasil! Selamat belajar, **{nama.strip()}** 🌷"
                )

    if st.session_state.sudah_presensi:
        st.info(
            f"Anda masuk sebagai **{st.session_state.nama_pengguna}** "
            f"({st.session_state.kelas_pengguna}). "
            "Silakan gunakan menu **🔎 Tanya Materi**."
        )


# =========================================================
# TANYA MATERI
# =========================================================

elif menu == "🔎 Tanya Materi":

    if not st.session_state.sudah_presensi:
        st.warning("📝 Silakan lakukan presensi terlebih dahulu.")
        st.info("Buka menu **📝 Presensi** untuk mengisi nama dan kelas.")
        st.stop()

    st.subheader("💬 Tanyakan Sesuatu")
    st.caption(
        f"👤 {st.session_state.nama_pengguna} • "
        f"🏫 {st.session_state.kelas_pengguna}"
    )

    pertanyaan = st.text_area(
        "Masukkan pertanyaan Anda:",
        value=st.session_state.pertanyaan_terakhir,
        placeholder="Contoh: Apa yang dimaksud dengan kalimat efektif?",
        height=120
    )

    col1, col2 = st.columns([3, 1])

    with col1:
        tombol = st.button("🔍 TANYAKAN", use_container_width=True)

    with col2:
        hapus = st.button("🗑️ Bersihkan", use_container_width=True)

    if hapus:
        st.session_state.pertanyaan_terakhir = ""
        st.session_state.hasil_terakhir = None
        st.rerun()

    if tombol:

        if pertanyaan.strip() == "":
            st.warning("Silakan masukkan pertanyaan terlebih dahulu.")

        elif len(database) == 0:
            st.error("Database TXT belum ditemukan.")

        else:
            with st.spinner("🌸 Sedang mencari materi..."):
                hasil = cari_materi(pertanyaan, database)

            st.session_state.pertanyaan_terakhir = pertanyaan
            st.session_state.hasil_terakhir = hasil

            st.session_state.riwayat.insert(0, pertanyaan)
            st.session_state.riwayat = st.session_state.riwayat[:10]

            if hasil:
                hasil_utama_simpan = hasil[0]
                jawaban_simpan = ambil_potongan_relevan(
                    pertanyaan,
                    hasil_utama_simpan["isi"]
                )
                simpan_riwayat_pertanyaan(
                    st.session_state.nama_pengguna,
                    st.session_state.kelas_pengguna,
                    pertanyaan,
                    jawaban_simpan,
                    hasil_utama_simpan["nama_file"]
                )
            else:
                simpan_riwayat_pertanyaan(
                    st.session_state.nama_pengguna,
                    st.session_state.kelas_pengguna,
                    pertanyaan,
                    "Materi tidak ditemukan dalam database.",
                    "-"
                )

    hasil = st.session_state.hasil_terakhir

    if hasil:

        hasil_utama = hasil[0]

        st.success("✨ Materi yang paling relevan ditemukan.")

        st.subheader("💡 Jawaban")

        jawaban = ambil_potongan_relevan(
            st.session_state.pertanyaan_terakhir,
            hasil_utama["isi"]
        )

        st.info(jawaban)

        col1, col2 = st.columns(2)

        with col1:
            st.metric("🎯 Skor relevansi", hasil_utama["skor"])

        with col2:
            st.metric("✨ Materi ditemukan", len(hasil))

        st.subheader("📚 Sumber Materi")
        st.write(f"**{hasil_utama['nama_file']}**")

        if len(hasil) > 1:
            st.subheader("📑 Materi Terkait")

            for item in hasil[1:4]:
                with st.expander("📄 " + item["nama_file"]):
                    potongan = ambil_potongan_relevan(
                        st.session_state.pertanyaan_terakhir,
                        item["isi"],
                        800
                    )
                    st.write(potongan)

    elif hasil == []:
        st.warning(
            "Maaf, materi yang Anda tanyakan belum ditemukan dalam database."
        )
        st.write("Coba gunakan kata kunci yang lebih spesifik.")

# =========================================================
# DAFTAR MATERI
# =========================================================

elif menu == "📖 Daftar Materi":

    st.subheader("📖 Daftar Materi")

    if len(database) == 0:
        st.warning("Belum ada file TXT di folder database.")
    else:
        st.write(f"✨ Tersedia **{len(database)}** file materi.")

        for nomor, data in enumerate(database, start=1):

            nama = data["nama_file"]
            judul = os.path.splitext(nama)[0].replace("_", " ").title()

            with st.expander(f"📘 {nomor}. {judul}"):
                jumlah_kata = len(data["isi"].split())

                c1, c2 = st.columns(2)
                with c1:
                    st.metric("📝 Jumlah kata", jumlah_kata)
                with c2:
                    st.metric("📄 Format", "TXT")

                st.write(data["isi"][:1200])

                if len(data["isi"]) > 1200:
                    st.caption("Menampilkan cuplikan 1.200 karakter pertama.")

# =========================================================
# KUIS MINI
# =========================================================

elif menu == "📝 Kuis Mini":

    st.subheader("📝 Kuis Mini Biografi dan Bahasa Indonesia")
    st.write("Pilih satu jawaban yang paling tepat. Terdapat 15 soal biografi. 🌷")

    soal = [
        {
            "q": "1. Secara harfiah, kata biografi yang berasal dari bahasa Yunani bios dan graphien berarti...",
            "opsi": [
                "A. catatan perjalanan seorang tokoh",
                "B. tulisan tentang kehidupan seseorang",
                "C. cerita rekaan tentang seorang tokoh",
                "D. kumpulan karya seorang penulis",
                "E. laporan penelitian ilmiah tentang suatu peristiwa"
            ],
            "jawaban": "B. tulisan tentang kehidupan seseorang",
            "pembahasan": "Bios berarti kehidupan dan graphien berarti menulis; biografi adalah tulisan tentang kehidupan seseorang."
        },
        {
            "q": "2. Perhatikan kalimat berikut.\n\"Sejak kecil, Ki Hajar Dewantara dikenal sebagai anak yang cerdas dan peduli pada nasib rakyat kecil.\"\nKalimat tersebut menunjukkan ciri biografi, yaitu...",
            "opsi": [
                "A. ditulis oleh tokoh sendiri dengan sudut pandang orang pertama",
                "B. memakai bahasa tidak baku agar akrab dengan pembaca",
                "C. berisi cerita rekaan yang tidak perlu dibuktikan",
                "D. hanya memuat opini penulis tentang tokoh",
                "E. ditulis oleh orang lain dengan sudut pandang orang ketiga"
            ],
            "jawaban": "E. ditulis oleh orang lain dengan sudut pandang orang ketiga",
            "pembahasan": "Tokoh disebut dengan namanya, sesuai sudut pandang orang ketiga dalam biografi."
        },
        {
            "q": "3. Jenis biografi berdasarkan isi yang menitikberatkan pada usaha, pengorbanan, dan rintangan yang dihadapi tokoh untuk mencapai tujuan disebut biografi...",
            "opsi": [
                "A. perjuangan",
                "B. perjalanan hidup",
                "C. karier",
                "D. tokoh intelektual",
                "E. kumpulan tokoh"
            ],
            "jawaban": "A. perjuangan",
            "pembahasan": "Biografi perjuangan menyoroti usaha, pengorbanan, dan rintangan tokoh."
        },
        {
            "q": "4. Biografi yang ditulis dengan izin, persetujuan, dan kerja sama langsung dengan tokoh atau keluarganya disebut biografi...",
            "opsi": [
                "A. unauthorized",
                "B. otobiografi",
                "C. authorized",
                "D. memoar",
                "E. profil"
            ],
            "jawaban": "C. authorized",
            "pembahasan": "Authorized berarti penulisan biografi mendapat izin atau persetujuan tokoh atau keluarganya."
        },
        {
            "q": "5. Susunan struktur teks biografi yang tepat adalah...",
            "opsi": [
                "A. peristiwa penting, orientasi, reorientasi",
                "B. reorientasi, orientasi, peristiwa penting",
                "C. orientasi, reorientasi, peristiwa penting",
                "D. orientasi, peristiwa penting, reorientasi",
                "E. orientasi, komplikasi, resolusi"
            ],
            "jawaban": "D. orientasi, peristiwa penting, reorientasi",
            "pembahasan": "Orientasi memperkenalkan tokoh, peristiwa penting menguraikan perjalanan hidup, dan reorientasi menjadi penutup."
        },
        {
            "q": "6. Perhatikan kutipan berikut.\n\"Pada tahun 1921, Hatta berangkat ke Belanda untuk melanjutkan studi di bidang ekonomi. Di sana ia aktif dalam Perhimpunan Indonesia dan memperjuangkan kemerdekaan melalui tulisan dan pidato. Kegiatannya itu membuat ia ditangkap oleh pemerintah Belanda pada tahun 1927.\"\nKutipan tersebut termasuk bagian struktur biografi, yaitu...",
            "opsi": [
                "A. orientasi",
                "B. reorientasi",
                "C. komplikasi",
                "D. evaluasi",
                "E. peristiwa penting"
            ],
            "jawaban": "E. peristiwa penting",
            "pembahasan": "Kutipan menguraikan peristiwa studi, perjuangan, dan penangkapan dalam perjalanan hidup Hatta."
        },
        {
            "q": "7. Kata sejak, ketika, setelah, kemudian, dan akhirnya yang banyak muncul dalam teks biografi termasuk...",
            "opsi": [
                "A. konjungsi temporal",
                "B. konjungsi kausalitas",
                "C. kata kerja mental",
                "D. kata sifat",
                "E. kata depan"
            ],
            "jawaban": "A. konjungsi temporal",
            "pembahasan": "Pilihan A paling sesuai karena kata-kata tersebut menandai waktu atau urutan peristiwa. Secara lebih rinci, kemudian dan akhirnya juga dapat berfungsi sebagai adverbia penanda urutan."
        },
        {
            "q": "8. Urutan langkah menulis biografi yang benar adalah...",
            "opsi": [
                "A. menyusun kerangka, menentukan tokoh, mengumpulkan data, menulis",
                "B. mengumpulkan data, menulis, menentukan tokoh, menyusun kerangka",
                "C. menentukan tokoh, mengumpulkan data, menyusun kerangka, mengembangkan menjadi tulisan",
                "D. menentukan tokoh, menulis, mengumpulkan data, menyusun kerangka",
                "E. menyusun kerangka, mengumpulkan data, menentukan tokoh, menulis"
            ],
            "jawaban": "C. menentukan tokoh, mengumpulkan data, menyusun kerangka, mengembangkan menjadi tulisan",
            "pembahasan": "Penulis memilih tokoh, mencari data, menyusun kerangka, lalu mengembangkannya menjadi tulisan."
        },
        {
            "q": "9. Penulis mengamati langsung rumah masa kecil tokoh dan lokasi bersejarah yang berkaitan dengannya untuk menggambarkan latar dengan lebih hidup. Teknik pengumpulan data tersebut adalah...",
            "opsi": [
                "A. wawancara",
                "B. observasi",
                "C. studi dokumen",
                "D. angket",
                "E. diskusi kelompok"
            ],
            "jawaban": "B. observasi",
            "pembahasan": "Observasi adalah pengumpulan data melalui pengamatan langsung."
        },
        {
            "q": "10. Perbedaan memoar dengan otobiografi adalah...",
            "opsi": [
                "A. memoar ditulis oleh orang lain, sedangkan otobiografi ditulis oleh tokoh sendiri",
                "B. memoar memakai sudut pandang orang ketiga, sedangkan otobiografi memakai orang pertama",
                "C. memoar hanya berisi data singkat tokoh saat ini, sedangkan otobiografi berisi kenangan",
                "D. memoar mengambil periode tertentu yang berkesan, sedangkan otobiografi mencakup seluruh perjalanan hidup",
                "E. memoar bersifat fiktif, sedangkan otobiografi berdasarkan fakta"
            ],
            "jawaban": "D. memoar mengambil periode tertentu yang berkesan, sedangkan otobiografi mencakup seluruh perjalanan hidup",
            "pembahasan": "Memoar berfokus pada pengalaman atau periode tertentu; otobiografi umumnya mengisahkan perjalanan hidup secara lebih menyeluruh."
        },
        {
            "q": "11. Film biopik berbeda dari film dokumenter biografi karena biopik...",
            "opsi": [
                "A. hanya memakai rekaman asli dan foto arsip",
                "B. tidak memerlukan tokoh nyata",
                "C. tidak pernah memuat peristiwa penting tokoh",
                "D. tidak boleh memuat dialog",
                "E. diperankan oleh aktor dan dapat mengalami dramatisasi dari fakta"
            ],
            "jawaban": "E. diperankan oleh aktor dan dapat mengalami dramatisasi dari fakta",
            "pembahasan": "Biopik menyajikan kehidupan tokoh melalui pemeranan aktor dan dapat menggunakan dramatisasi."
        },
        {
            "q": "12. Kalimat berikut yang merupakan opini adalah...",
            "opsi": [
                "A. Kartini lahir di Jepara pada 21 April 1879.",
                "B. Susi Susanti meraih medali emas Olimpiade Barcelona 1992.",
                "C. Bob Sadino adalah pengusaha paling berani yang pernah dimiliki Indonesia.",
                "D. Soekarno mendirikan Partai Nasional Indonesia pada 1927.",
                "E. Soekarno membacakan pidato Indonesia Menggugat di Bandung pada 1930."
            ],
            "jawaban": "C. Bob Sadino adalah pengusaha paling berani yang pernah dimiliki Indonesia.",
            "pembahasan": "Frasa paling berani merupakan penilaian subjektif, sehingga kalimat itu termasuk opini."
        },
        {
            "q": "13. Kalimat yang menggunakan bahasa inspiratif dan tidak menggurui adalah...",
            "opsi": [
                "A. \"Kamu harus bekerja keras seperti tokoh ini agar sukses.\"",
                "B. \"Kegagalan yang dialaminya tidak menghentikan langkahnya. Ia terus belajar dan mencoba hingga akhirnya berhasil.\"",
                "C. \"Jika kamu malas, kamu tidak akan menjadi apa-apa.\"",
                "D. \"Kamu wajib meneladani semua sikap tokoh ini.\"",
                "E. \"Semua orang harus mencontoh tokoh ini tanpa terkecuali.\""
            ],
            "jawaban": "B. \"Kegagalan yang dialaminya tidak menghentikan langkahnya. Ia terus belajar dan mencoba hingga akhirnya berhasil.\"",
            "pembahasan": "Kalimat memberi inspirasi melalui pengalaman tokoh tanpa memerintah atau merendahkan pembaca."
        },
        {
            "q": "14. Dalam sebuah biografi tertulis: \"Meskipun telah meraih banyak prestasi, ia tetap menghargai orang-orang di sekitarnya dan tidak pernah menyombongkan diri.\" Nilai moral yang terkandung dalam kutipan tersebut adalah...",
            "opsi": [
                "A. rendah hati",
                "B. pantang menyerah",
                "C. disiplin",
                "D. cinta tanah air",
                "E. tanggung jawab"
            ],
            "jawaban": "A. rendah hati",
            "pembahasan": "Tidak menyombongkan diri meskipun berprestasi menunjukkan sikap rendah hati."
        },
        {
            "q": "15. Dalam pembelajaran sejarah, biografi sebaiknya dibaca bersama sumber lain karena...",
            "opsi": [
                "A. biografi tidak pernah memuat fakta",
                "B. biografi selalu berisi informasi yang salah",
                "C. sumber sejarah lain tidak diperlukan jika sudah membaca biografi",
                "D. biografi bisa mengandung sudut pandang atau kepentingan penulisnya",
                "E. biografi hanya boleh ditulis tentang tokoh yang sudah meninggal"
            ],
            "jawaban": "D. biografi bisa mengandung sudut pandang atau kepentingan penulisnya",
            "pembahasan": "Perbandingan dengan sumber lain membantu memeriksa informasi dan mengenali sudut pandang penulis."
        },
    ]
    skor = 0
    pilihan_pengguna = []

    for i, item in enumerate(soal):
        pilihan = st.radio(
            item["q"],
            item["opsi"],
            index=None,
            key=f"kuis_biografi_v2_{i}"

        )

        pilihan_pengguna.append(pilihan)
        if pilihan == item["jawaban"]:
            skor += 1

    if st.button("✨ Periksa Jawaban", use_container_width=True):
        if any(pilihan is None for pilihan in pilihan_pengguna):
            st.warning("Lengkapi semua jawaban terlebih dahulu sebelum memeriksa hasil.")
        else:
            nilai = skor / len(soal) * 100
            st.success(f"🎉 Skormu: **{skor}/{len(soal)}** · Nilai: **{nilai:.1f}/100**")
            if skor == len(soal):
                st.balloons()
                st.write("🌟 Hebat! Semua jawaban benar!")
            elif nilai >= 70:
                st.write("👏 Bagus! Pelajari pembahasan untuk meningkatkan pemahamanmu.")
            else:
                st.write("🌱 Yuk pelajari kembali materi dan pembahasannya!")

            with st.expander("📖 Lihat kunci jawaban dan pembahasan", expanded=True):
                for item, pilihan in zip(soal, pilihan_pengguna):
                    benar = pilihan == item["jawaban"]
                    st.markdown(f"**{item['q']}**")
                    st.write(f"{'✅ Benar' if benar else '❌ Belum tepat'} — Jawabanmu: {pilihan}")
                    st.write(f"Kunci jawaban: {item['jawaban']}")
                    st.caption(item.get("pembahasan", f"Jawaban yang tepat adalah {item['jawaban']}."))

    st.divider()
    st.subheader("✍️ Kuis Esai")
    st.write("Jawablah 5 pertanyaan berikut dengan jelas dan lengkap.")

    soal_esai = [
        {
            "nomor": 1,
            "soal": "Jelaskan perbedaan biografi dan autobiografi dari tiga aspek, yaitu penulis, sudut pandang, dan tingkat objektivitas. Berikan satu contoh kalimat untuk masing-masing!",
            "jawaban": "Penulis: biografi ditulis orang lain, autobiografi ditulis tokoh sendiri. Sudut pandang: biografi memakai orang ketiga (ia, nama tokoh), autobiografi memakai orang pertama (aku, saya). Objektivitas: biografi cenderung lebih objektif tetapi berisiko salah data atau salah tafsir, sedangkan autobiografi cenderung subjektif dan bisa bias karena tokoh menonjolkan sisi baiknya. Contoh kalimat harus sesuai dengan sudut pandang masing-masing."
        },
        {
            "nomor": 2,
            "soal": "Sebutkan tiga bagian struktur teks biografi, lalu jelaskan isi dan fungsi masing-masing bagian beserta contohnya!",
            "jawaban": "Orientasi: pembuka berisi pengenalan tokoh seperti nama, tempat dan tanggal lahir, keluarga, masa kecil, dan hal yang membuatnya dikenal; berfungsi memberi pegangan awal kepada pembaca. Peristiwa penting: inti teks berisi rangkaian kejadian penting secara kronologis seperti pendidikan, perjuangan, kesulitan, dan keberhasilan; di sinilah keteladanan paling terlihat. Reorientasi: penutup berisi penilaian atau kesimpulan penulis, pesan, atau keadaan terakhir tokoh; membuat tulisan terasa utuh. Contoh disesuaikan dengan isi tiap bagian."
        },
        {
            "nomor": 3,
            "soal": "Jelaskan lima langkah menulis biografi, mulai dari menentukan tokoh sampai menyunting tulisan. Selain itu, jelaskan mengapa data penting seperti tanggal dan nama sebaiknya diperiksa dengan minimal dua sumber!",
            "jawaban": "Lima langkah: menentukan tokoh; riset dan pengumpulan data; menyusun kerangka; menulis biografi; serta menyunting atau merevisi. Data diperiksa dengan minimal dua sumber untuk menghindari kesalahan data karena satu sumber bisa keliru, memastikan kebenaran fakta, dan menjaga kepercayaan pembaca."
        },
        {
            "nomor": 4,
            "soal": """Bacalah kutipan berikut.

"Puncak karier Susi terjadi pada Olimpiade Barcelona 1992. Ia meraih medali emas nomor tunggal putri dan menjadi penyumbang medali emas pertama bagi Indonesia dalam sejarah Olimpiade. Setelah pensiun sebagai atlet, Susi tetap berkontribusi bagi dunia bulu tangkis sebagai pelatih dan pembina. Ia dikenal sebagai atlet yang disiplin, tekun, dan rendah hati."

a. Tentukan dua nilai keteladanan dari kutipan tersebut beserta alasannya!

b. Jelaskan bagaimana kedua nilai itu dapat diterapkan oleh pelajar pada kehidupan saat ini!""",
            "jawaban": "Nilai yang dapat dipilih antara lain disiplin dan kerja keras, rendah hati, cinta tanah air/kebanggaan membawa nama bangsa, serta kepedulian. Setiap nilai harus disertai alasan berdasarkan kutipan. Penerapan harus konkret, misalnya membuat jadwal belajar dan menaatinya, berlatih konsisten dalam ekstrakurikuler, atau tetap sopan dan menghargai teman saat meraih prestasi."
        },
        {
            "nomor": 5,
            "soal": "Jelaskan satu kelebihan dan satu kekurangan biografi di media sosial (thread, carousel, atau video pendek) dibandingkan biografi dalam buku cetak. Lalu sebutkan tiga prinsip yang harus dijaga ketika mengubah biografi menjadi konten digital!",
            "jawaban": "Kelebihan media sosial dapat berupa singkat, visual menarik, cepat, mudah diakses dan dibagikan, atau interaktif. Kekurangannya: informasi terlalu dipadatkan sehingga rawan salah, kurang konteks, atau hanya menampilkan sisi tertentu tokoh, sedangkan buku cetak memuat uraian lebih lengkap dan mendalam. Prinsip yang dijaga: fakta tidak boleh diubah demi tampilan menarik; gaya bahasa disesuaikan dengan platform dan pembaca tetapi tetap sopan; sumber dicantumkan; tokoh dihormati; serta tidak melanggar hak cipta gambar atau musik."
        },
    ]

    jawaban_esai = {}
    for item in soal_esai:
        st.markdown(f"**{item['nomor']}. {item['soal']}**")
        jawaban_esai[item["nomor"]] = st.text_area(
            f"Jawaban soal {item['nomor']}",
            key=f"esai_{item['nomor']}",
            height=180,
            placeholder="Tuliskan jawabanmu di sini...",
        )

    if st.button("📋 Kumpulkan Jawaban Esai", use_container_width=True):
        kosong = [n for n, j in jawaban_esai.items() if not j.strip()]
        if kosong:
            st.warning(
                "Lengkapi semua jawaban terlebih dahulu. "
                f"Soal yang masih kosong: {', '.join(map(str, kosong))}."
            )
        else:
            st.success("🎉 Semua jawaban esai berhasil dikumpulkan!")
            with st.expander("📖 Lihat pedoman jawaban", expanded=True):
                for item in soal_esai:
                    st.markdown(f"**Soal {item['nomor']} — Pedoman jawaban:**")
                    st.write(item["jawaban"])
                    st.divider()


# =========================================================
# DATA PENGGUNA
# =========================================================

elif menu == "👥 Data Pengguna":

    st.markdown('<div class="section-label">Pemantauan Pengguna</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">👥 Data Pengguna</div>', unsafe_allow_html=True)

    pengguna = baca_csv(FILE_PENGGUNA)

    if not pengguna:
        st.info("Belum ada pengguna yang melakukan presensi.")
    else:
        st.write(f"Total pengguna terdaftar: **{len(pengguna)}**")

        # Tampilkan tabel tanpa library tambahan.
        header = ["No.", "Nama", "Kelas", "Waktu Presensi"]
        rows = []
        for nomor, item in enumerate(pengguna, start=1):
            rows.append({
                "No.": nomor,
                "Nama": item.get("nama", ""),
                "Kelas": item.get("kelas", ""),
                "Waktu Presensi": item.get("waktu_daftar", "")
            })

        st.dataframe(rows, use_container_width=True, hide_index=True)


# =========================================================
# RIWAYAT PERTANYAAN
# =========================================================

elif menu == "🕘 Riwayat Pertanyaan":

    st.markdown('<div class="section-label">Aktivitas Belajar</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🕘 Riwayat Pertanyaan</div>', unsafe_allow_html=True)

    riwayat_data = baca_csv(FILE_RIWAYAT)

    if not riwayat_data:
        st.info("Belum ada pertanyaan yang diajukan.")
    else:
        st.write(f"Total pertanyaan tersimpan: **{len(riwayat_data)}**")

        for nomor, item in enumerate(reversed(riwayat_data), start=1):
            nama = item.get("nama", "-")
            kelas = item.get("kelas", "-")
            pertanyaan = item.get("pertanyaan", "-")
            waktu = item.get("waktu", "-")
            sumber = item.get("sumber_materi", "-")
            jawaban = item.get("jawaban", "-")

            with st.expander(
                f"💬 {nomor}. {nama} — {kelas} | {waktu}"
            ):
                st.markdown(f"**Pertanyaan:** {pertanyaan}")
                st.markdown(f"**Sumber:** {sumber}")
                st.markdown("**Jawaban:**")
                st.write(jawaban)

        st.divider()
        st.subheader("📌 Riwayat Sesi Ini")

        if not st.session_state.riwayat:
            st.info("Belum ada pertanyaan dari sesi ini.")
        else:
            for i, item in enumerate(st.session_state.riwayat, start=1):
                st.markdown(f"**{i}.** {item}")


# =========================================================
# TENTANG
# =========================================================

elif menu == "ℹ️ Tentang":

    st.subheader("ℹ️ Tentang BIOGRAFIKA AI")

    st.markdown("""
    <div class="card">
        <h3>🧠✨ BIOGRAFIKA AI</h3>
        <p>
        Aplikasi pembelajaran berbasis <b>Python + Streamlit</b>
        yang menggunakan file TXT sebagai Knowledge Base.
        </p>
        <p>
        Sistem mencari materi berdasarkan kata kunci pertanyaan,
        menghitung relevansi, kemudian menampilkan bagian materi
        yang paling sesuai.
        </p>
        <p>
        AI ini dibuat oleh mahasiswa Pendidikan Bahasa dan Sastra 
        Indonesia Reguler C 2023 kelompok 3
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    st.subheader("🛠️ Teknologi")
    st.write("🐍 Python")
    st.write("🎈 Streamlit")
    st.write("📄 TXT Knowledge Base")
    st.write("🔎 Sistem pencarian berbasis kata kunci")
    st.write("👥 Presensi & riwayat pengguna berbasis CSV")

# =========================================================
# FOOTER
# =========================================================

st.divider()

st.markdown(
    """
    <div class="footer">
        <b>BIOGRAFIKA AI</b><br>
        Belajar • Bertanya • Berlatih • Berkembang
    </div>
    """,
    unsafe_allow_html=True
)
