import streamlit as st
import paho.mqtt.client as mqtt
import requests
import threading
import time
from datetime import datetime

# Konfigurasi tampilan halaman utama dashboard
st.set_page_config(page_title="IoT Monitoring - TAS AI", layout="centered")

st.title("📡 Sistem Monitoring & Perekam Data IoT")
st.write("Sistem ini berjalan 24 jam di cloud untuk merekam data suhu dan kelembaban dari alat dosen.")

# ==========================================
# GANTI URL DI BAWAH INI DENGAN WEB APP URL-MU!
# ==========================================
WEB_APP_URL = "https://script.google.com/macros/s/AKfycby4X8j7ReTskH9zESGVxYRhOndyaiXXXPLXibu-2VjOEQxX_o53z-3Mr4plXSUpAkJ9Sw/exec"

# --- BACKGROUND LISTENER MQTT ---
@st.cache_resource
def start_mqtt_listener(web_app_url):
    # Menyimpan data sementara dalam dictionary agar bisa diakses antar-fungsi
    shared_data = {
        "suhu": None,
        "kelembaban": None,
        "last_update": "Belum ada data",
        "last_sent_time": 0
    }
    
    def on_message(client, userdata, msg):
        try:
            payload = msg.payload.decode()
            value = float(payload)
            topic = msg.topic
            
            # Memilah data masuk berdasarkan topik sensor dosen
            if "suhu" in topic:
                shared_data["suhu"] = value
            elif "kelembaban" in topic:
                shared_data["kelembaban"] = value
            
            shared_data["last_update"] = datetime.now().strftime("%H:%M:%S WIB")
            
            # Kirim data ke Google Sheets jika kedua data (suhu & kelembaban) sudah terisi
            # dan berikan jeda minimal 15 detik dari pengiriman terakhir agar tidak ganda
            now = time.time()
            if (shared_data["suhu"] is not None and 
                shared_data["kelembaban"] is not None and 
                (now - shared_data["last_sent_time"] > 15)):
                
                params = {
                    "suhu": shared_data["suhu"],
                    "kelembaban": shared_data["kelembaban"]
                }
                # Mengirimkan data ke Google Sheets lewat Google Apps Script (Metode GET)
                requests.get(web_app_url, params=params, timeout=10)
                shared_data["last_sent_time"] = now
        except Exception as e:
            pass

    def mqtt_thread_func():
        client = mqtt.Client()
        client.username_pw_set("mhsw", "ukswsal3") # Akun MQTT dari dosen
        client.tls_set() # Wajib aktif karena menggunakan Port 8883 (TLS-SSL)
        client.on_message = on_message
        
        while True:
            try:
                # Menghubungkan ke broker HiveMQ dosen
                client.connect("aifsmukswsurya-397a2de2.a03.euc1.aws.hivemq.cloud", 8883, 60)
                client.subscribe("tas_ai_surya_fsm_uksw/suhu")
                client.subscribe("tas_ai_surya_fsm_uksw/kelembaban")
                client.loop_forever()
            except Exception as e:
                # Jika koneksi internet server putus, coba hubungkan kembali dalam 5 detik
                time.sleep(5)

    # Menjalankan fungsi di atas di background (latar belakang) agar tidak mengganggu UI Streamlit
    t = threading.Thread(target=mqtt_thread_func, daemon=True)
    t.start()
    return shared_data

# Verifikasi apakah pengguna sudah mengganti URL bawaan
if WEB_APP_URL == "TEMPEL_URL_GOOGLE_APPS_SCRIPT_MU_DI_SINI":
    st.warning("⚠️ PERINGATAN: Silakan ganti nilai variabel `WEB_APP_URL` di dalam kode dengan URL Google Apps Script milikmu terlebih dahulu!")
else:
    shared_data = start_mqtt_listener(WEB_APP_URL)
    
    # Tampilan Widget Angka Real-Time di Halaman Web
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Suhu Aktual", value=f"{shared_data['suhu']} °C" if shared_data['suhu'] is not None else "Menunggu data...")
    with col2:
        st.metric(label="Kelembaban Aktual", value=f"{shared_data['kelembaban']} %" if shared_data['kelembaban'] is not None else "Menunggu data...")
        
    st.info(f"🔄 **Status Perekaman:** AKTIF di Background Server. Update data terakhir: {shared_data['last_update']}")
    st.success("✅ Sistem otomatis mengalirkan data ke Google Spreadsheet milikmu tanpa perlu laptopmu menyala.")
    st.write("---")
    st.write("*Catatan: Tampilan dashboard ini akan kita lengkapi nanti dengan visualisasi grafik, forecasting, dan analisis LLM.*")
