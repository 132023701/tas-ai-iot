# 🌡️ Proyek Akhir AI IoT: Monitoring Real-Time, Forecasting Prophet & Komentator Groq LLaMA 3

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)](https://streamlit.io/)
[![Groq API](https://img.shields.io/badge/Groq_API-LLaMA_3-f36c00?style=for-the-badge)](https://groq.com/)
[![License](https://img.shields.io/badge/Academic-UKSW-0055A5?style=for-the-badge)](https://www.uksw.edu/)

Dokumentasi dan repositori kode resmi untuk **Tugas Akhir Mata Kuliah Artificial Intelligence (BD002)**. Proyek ini mengintegrasikan ekosistem Internet of Things (IoT), peramalan deret waktu (*time-series forecasting*) berbasis Machine Learning, serta integrasi Large Language Model (LLM) sebagai analis lingkungan otomatis.

---

## 📌 Metadata Mahasiswa & Proyek

* **Nama Mahasiswa** : Yohanes Yoga D. S.
* **NIM** : 132023701
* **Institusi** : Universitas Kristen Satya Wacana (UKSW)
* **Mata Kuliah** : AI (BD002) - Semester Genap 2025/2026
* **Dosen Pengampu** : Dr. Suryasatriya Trihandaru, M.Sc.nat, Dr. Bambang Susanto, MS., Prof. Dr. Hanna Arini Parhusip, MSc.nat, Denny Indrajaya, Eko Sediyono
* **Tenggat Pengumpulan** : Sabtu, 25 Juli 2026 (23:59 WIB)
* **Repositori Git** : https://github.com/132023701/tas-ai-iot
* **Tautan Dashboard Live** : https://tas-ai-iot-132023701.streamlit.app/

---

## 🏗️ Arsitektur dan Alur Kerja Operasional Sistem ("Train Offline, Display Online")

Seluruh ekosistem proyek ini beroperasi melalui 4 tahapan berkesinambungan berbasis arsitektur **"Train Offline, Display Online"** untuk menjaga efisiensi daya, kestabilan peladen (*server anti-crash*) :

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ TAHAP A: CLOUD DATA RECORDING (24/7)                                                   │
│ [MQTT Broker HiveMQ] ──► [Streamlit Background Thread] ──► [GAS Code.gs] ──► [GSheets] │
└────────────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ TAHAP B: OFFLINE AI ENGINE & FORECASTING (LAPTOP .VENV)                                │
│ [Google Sheets] ──► predict.py (Resampling 1 Jam & Prophet) ──► Aset (PNG/CSV/TXT)     │
│                 ──► groq_commentator.py (Groq API LLaMA 3) ──► ulasan_groq.txt        │
└────────────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ TAHAP C: SINKRONISASI ASISTEN & DEPLOYMENT GITHUB                                       │
│ [Commit & Push Aset AI + Code] ──► [GitHub Repository: 132023701/tas-ai-iot]          │
└────────────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ TAHAP D: RENDERING & VISUALISASI STREAMLIT CLOUD                                       │
│ [Streamlit Cloud Auto-Reboot] ──► Display Monitoring, Prediksi Statis, & Eksplorasi  │
└────────────────────────────────────────────────────────────────────────────────────────┘

```
### 📡 Tahap A: Akuisisi & Perekaman Data Telemetri Cloud (24/7)
1. Publikasi Data Sensor: MQTT Broker HiveMQ (aifsmukswsurya-397a2de2.a03.euc1.aws.hivemq.cloud:8883 TLS) mempublikasikan payload telemetri suhu dan kelembaban udara secara otomatis setiap ~20 detik.
2. Perekam Background Thread: Berkas streamlit_app.py yang terpasang di Streamlit Cloud memanfaatkan fungsi @st.cache_resource dan multithreading Python untuk menjalankan fungsi listener MQTT di background tanpa mengganggu antarmuka pengguna.
3. Penyimpanan Cloud (Google Sheets): Setiap kali data baru diterima, thread pengirim akan meneruskan parameter suhu dan kelembaban via permintaan HTTP GET ke endpoint Google Apps Script (Code.gs). Data tersimpan secara otomatis dan real-time pada lembar spreadsheet Data_Realtime.
4. Peningkat Kestabilan (Anti-Sleep): Workflow GitHub Actions (.github/workflows/bangunkan_streamlit.yml) mengeksekusi pemicu (pinger) berkala setiap jam agar container Streamlit Cloud tidak tidur (sleep).

### ⚙️ Tahap B: Mesin Pemrosesan & Analytics AI Offline (Laptop)
Eksekusi pemrosesan AI berat dilakukan secara mandiri di laptop (.venv) pada Sabtu, 25 Juli 2026 untuk menjamin stabilitas peladen dan mencegah risiko Out of Memory (OOM):
1. Eksekusi Peramalan (python predict.py):
   * Pengambilan Data: Membaca data log mentah telemetri dari Google Sheets via export CSV URL.
   * Pembersihan & Resampling 1 Jam: Menerapkan Moving Average 3 periode untuk mengurangi noise sensor, dilanjutkan dengan agregasi rata-rata per 1 jam (resample('1h')). Hal ini memastikan durasi testing set 24 jam dan proyeksi 6 jam berada pada interval temporal yang presisi.
   * Pelatihan Facebook Prophet: Melatih model peramalan deret waktu untuk parameter Suhu Udara, serta melatih model Kelembaban Udara dengan menggunakan Suhu sebagai extra regressor.
   * Evaluasi Performa Model: Menghitung metrik kesalahan uji (testing set 24 jam) meliputi RMSE, MAE, dan MAPE.
   * Ekspor 5 Aset Luaran AI:
     ** grafik_prediksi.png (Visualisasi proyeksi suhu 6 jam ke depan).
     ** grafik_evaluasi.png (Visualisasi perbandingan data Aktual vs Prediksi Prophet 24 jam).
     ** hasil_prediksi.csv (Tabel angka hasil peramalan 6 jam ke depan).
     ** metrics_error.txt (Berkas teks berisi nilai RMSE, MAE, MAPE).
     ** metadata_prediksi.txt (Rincian rentang waktu training, testing, dan prediksi).
   

2. Eksekusi Analis Eksekutif LLM (python groq_commentator.py):
   * Membaca tabel ringkasan hasil_prediksi.csv.
   * Mengirimkan data konteks prediksi ke Groq Cloud API menggunakan model llama-3.3-70b-versatile (dengan fallback llama-3.1-8b-instant, temperature: 0.5, max_tokens: 200).
   * Menghasilkan berkas narasi analisis lingkungan ilmiah 3-4 kalimat ringkas ke dalam berkas ulasan_groq.txt.
   
### 📤 Tahap C: Sinkronisasi Kode & Aset ke Repositori GitHub
1. Keenam berkas aset hasil ciptaan AI (*.png, *.csv, *.txt) bersama dengan berkas skrip pemrogramannya (streamlit_app.py, predict.py, groq_commentator.py, Code.gs, requirements.txt, dan README.md) diunggah (commit & push) ke repositori resmi GitHub:
https://github.com/132023701/tas-ai-iot
2. Proses ini mengunci versi data sehingga seluruh angka di Laporan Word dan Dasbor Web berada dalam kondisi 100% sinkron, konsisten, dan terverifikasi.

### 💻 Tahap D: Rendering & Visualisasi pada Dashboard Streamlit Cloud
Setelah berkas berhasil masuk ke GitHub, peladen Streamlit Cloud mendeteksi perubahan dan melakukan pembaruan tampilan (auto-refresh/reboot). Dasbor web menyajikan data melalui 3 tab navigasi utama:
1. 📊 Monitoring Real-Time
      * Menampilkan metric card suhu dan kelembaban terkini dari variabel terbagi MQTT (auto-refresh fragment per 5 detik).
      * Memuat grafik garis interaktif dari Google Sheets dengan opsi filter resolusi temporal (24 Jam / 3 Hari / Semua Data).
      * Menampilkan tabel riwayat telemetri dengan pemfilteran tanggal dan pembatas jumlah log (limit display).

2. 🔮 Prediksi & Analisis AI
      * Membaca aset statis metadata_prediksi.txt untuk menampilkan ringkasan kartu informasi 3 rentang data (Training, Testing, dan Target Peramalan).
      * Menampilkan gambar grafik_prediksi.png dan grafik_evaluasi.png secara full-width.
      * Memuat tabel data hasil_prediksi.csv beserta kartu metrik akurasi dari metrics_error.txt.
      * Mengisi blok narasi eksekutif dari ulasan_groq.txt, serta menyediakan widget interaktif Expander Tanya Groq dan transparansi konfigurasi prompt engineering.
   
4. 🔍 Eksplorasi Data Telemetri
      * Ringkasan statistik deskriptif lengkap (Mean, Std Dev, Min, Max).
      * Scatter plot korelasi Pearson (Suhu vs Kelembaban) dengan garis tren regresi.
      * Histogram distribusi frekuensi data telemetri.
      * Boxplot pola fluktuasi distribusi suhu per jam (00:00 - 23:00 WIB).
  
  ---

## 📂 Struktur Repositori
```text
tas-ai-iot/
├── .github/workflows/
│   └── bangunkan_streamlit.yml    # Workflow Pinger GitHub Actions
├── Code.gs                        # Skrip Google Apps Script (doGet / doPost endpoint)
├── predict.py                     # Skrip offline training & forecasting Prophet
├── groq_commentator.py            # Skrip offline integrasi Groq LLaMA 3 API
├── streamlit_app.py               # Kode utama Dasbor Streamlit
├── requirements.txt               # Daftar dependensi modul Python
├── README.md                      # Dokumentasi resmi repositori
├── grafik_evaluasi.png            # Output Aset Visual Evaluasi Model
├── grafik_prediksi.png            # Output Aset Visual Proyeksi Prediksi 6 Jam
├── hasil_prediksi.csv             # Output Aset Tabel Data Hasil Prediksi
├── metadata_prediksi.txt          # Output Aset Teks Rentang Metadata Data
├── metrics_error.txt              # Output Aset Teks Metrik Performa Error
└── ulasan_groq.txt                # Output Aset Teks Ulasan Narasi Groq AI
```

---

© 2026 Yohanes Yoga D. S. — Universitas Kristen Satya Wacana (UKSW)
