import requests
import json
import pandas as pd
import os

# ==========================================
# 1. KONFIGURASI API GROQ LLaMA 3
# ==========================================
# TODO: Ganti teks di bawah dengan API Key Groq Anda
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "PASTE_YOUR_GROQ_API_KEY_HERE")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# ==========================================
# 2. MEMBACA DATA HASIL PREDIKSI (TAHAP B)
# ==========================================
print("📥 Membaca data hasil prediksi 6 jam terakhir...")
try:
    df_hasil = pd.read_csv("hasil_prediksi.csv")
    
    # Menghitung rata-rata untuk diberikan ke AI sebagai ringkasan
    suhu_avg = round(df_hasil['Prediksi Suhu (°C)'].mean(), 1)
    hum_avg = round(df_hasil['Prediksi Kelembaban (%)'].mean(), 1)
    
    suhu_min, suhu_max = round(df_hasil['Prediksi Suhu (°C)'].min(), 1), round(df_hasil['Prediksi Suhu (°C)'].max(), 1)
    
    data_konteks = f"Dalam 6 jam ke depan, prediksi suhu bergerak di rentang {suhu_min}°C hingga {suhu_max}°C (rata-rata {suhu_avg}°C), dengan rata-rata kelembaban {hum_avg}%."
except Exception as e:
    print(f"❌ Gagal membaca hasil_prediksi.csv. Pastikan skrip predict.py sudah dijalankan sebelumnya. Error: {e}")
    exit()

# ==========================================
# 3. MENYUSUN PROMPT & MENGIRIM KE CLOUD
# ==========================================
system_prompt = (
    "Anda adalah asisten AI analis lingkungan ilmiah. "
    "Berikan ulasan eksekutif (maksimal 3-4 kalimat) mengenai proyeksi cuaca 6 jam ke depan berdasarkan data yang diberikan. "
    "Gunakan bahasa Indonesia baku, lugas, dan berikan kesimpulan apakah kondisi stabil atau ada anomali."
)

user_prompt = f"Data telemetri IoT: {data_konteks}. Tolong buatkan ulasan narasinya."

headers = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "model": "llama3-8b-8192", # Model LLaMA 3 yang sangat cepat dan ringan
    "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ],
    "temperature": 0.5,
    "max_tokens": 150
}

print("🤖 Menghubungi mesin Groq AI LLaMA-3 (via Requests)...")
try:
    response = requests.post(GROQ_API_URL, headers=headers, json=payload)
    response.raise_for_status() # Cek apakah ada eror dari server
    
    # Mengekstrak teks jawaban dari struktur JSON balasan
    hasil_json = response.json()
    ulasan_teks = hasil_json['choices'][0]['message']['content']
    
    # ==========================================
    # 4. MENYIMPAN HASIL UNTUK DIBACA DASHBOARD
    # ==========================================
    with open("ulasan_groq.txt", "w", encoding="utf-8") as f:
        f.write(ulasan_teks.strip())
        
    print("✅ ulasan_groq.txt berhasil dibuat! Berikut isi narasinya:")
    print("=" * 60)
    print(ulasan_teks.strip())
    print("=" * 60)
    
except requests.exceptions.RequestException as e:
    print(f"❌ Gagal menghubungi server Groq. Cek koneksi internet atau validitas API Key Anda. Error: {e}")