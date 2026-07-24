import pandas as pd
import numpy as np
from prophet import Prophet
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, mean_absolute_error
import os

print("📥 Membaca data telemetri dari Google Sheets...")
CSV_URL = "https://docs.google.com/spreadsheets/d/1yNHSjZWAn6GbSRrMV6vWqvvQqjkCtivwhd4pxnbruJQ/export?format=csv&gid=0"

try:
    df = pd.read_csv(CSV_URL)
    df.columns = df.columns.str.strip().str.title()
    
    if 'Waktu' in df.columns:
        df.rename(columns={'Waktu': 'Timestamp'}, inplace=True)
    elif 'Tanggal' in df.columns:
        df.rename(columns={'Tanggal': 'Timestamp'}, inplace=True)
        
    for col in ['Suhu', 'Kelembaban']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '.', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce', dayfirst=True)
    df = df.dropna(subset=['Timestamp', 'Suhu', 'Kelembaban']).sort_values('Timestamp')

    # Pembersihan Noise Sensor (Moving Average 3 periode)
    df['Suhu_Clean'] = df['Suhu'].rolling(window=3, min_periods=1).mean()
    df['Kelembaban_Clean'] = df['Kelembaban'].rolling(window=3, min_periods=1).mean()

    # --- AGGREGASI RESAMPLING 1 JAM (Agar 1 baris = 1 Jam Penuh) ---
    df_hourly = df.set_index('Timestamp').resample('1h').agg({
        'Suhu': 'mean',
        'Kelembaban': 'mean',
        'Suhu_Clean': 'mean',
        'Kelembaban_Clean': 'mean'
    }).reset_index().dropna()

    print(f"✅ Data berhasil dimuat: {len(df)} log mentah terkonversi menjadi {len(df_hourly)} jam data teragregasi.")
except Exception as e:
    print(f"❌ Gagal memuat data: {e}")
    exit()

# -------------------------------------------------------------
# TAHAP 1: PREDIKSI SUHU UDARA
# -------------------------------------------------------------
print("⚙️ Melatih model Prophet untuk Suhu...")
df_suhu = df_hourly[['Timestamp', 'Suhu_Clean']].rename(columns={'Timestamp': 'ds', 'Suhu_Clean': 'y'})

m_suhu = Prophet(
    changepoint_prior_scale=0.05,
    daily_seasonality=True,
    weekly_seasonality=True,
    yearly_seasonality=False
)
m_suhu.fit(df_suhu)

future_suhu = m_suhu.make_future_dataframe(periods=6, freq='h')
forecast_suhu = m_suhu.predict(future_suhu)

# -------------------------------------------------------------
# TAHAP 2: PREDIKSI KELEMBABAN (DENGAN EXTRA REGRESSOR SUHU)
# -------------------------------------------------------------
print("⚙️ Melatih model Prophet untuk Kelembaban...")
df_hum = df_hourly[['Timestamp', 'Kelembaban_Clean', 'Suhu_Clean']].rename(
    columns={'Timestamp': 'ds', 'Kelembaban_Clean': 'y', 'Suhu_Clean': 'suhu_reg'}
)

m_hum = Prophet(
    changepoint_prior_scale=0.05,
    daily_seasonality=True,
    weekly_seasonality=True,
    yearly_seasonality=False
)
m_hum.add_regressor('suhu_reg')
m_hum.fit(df_hum)

future_hum = m_hum.make_future_dataframe(periods=6, freq='h')
future_hum['suhu_reg'] = forecast_suhu['yhat'].values

forecast_hum = m_hum.predict(future_hum)

# -------------------------------------------------------------
# TAHAP 3: EVALUASI METRIK ERROR & EKSPOR HASIL
# -------------------------------------------------------------
test_len = min(24, len(df_hourly)) # 24 data point per jam = 24 JAM PENUH!
y_true_s = df_hourly['Suhu'].tail(test_len).values
y_pred_s = forecast_suhu['yhat'].iloc[-test_len-6:-6].values

rmse = np.sqrt(mean_squared_error(y_true_s, y_pred_s))
mae = mean_absolute_error(y_true_s, y_pred_s)
mape = np.mean(np.abs((y_true_s - y_pred_s) / y_true_s)) * 100

# 1. Cetak metrics_error.txt
with open("metrics_error.txt", "w", encoding="utf-8") as f:
    f.write(f"{rmse:.2f} °C\n")
    f.write(f"{mae:.2f} °C\n")
    f.write(f"{mape:.2f} %\n")

# 2. Cetak hasil_prediksi.csv
df_6jam = pd.DataFrame({
    'Timestamp Prediksi': forecast_suhu['ds'].tail(6).dt.strftime('%d-%m-%Y %H:%M WIB'),
    'Prediksi Suhu (°C)': forecast_suhu['yhat'].tail(6).round(1).values,
    'Prediksi Kelembaban (%)': forecast_hum['yhat'].tail(6).round(1).values
})
df_6jam.to_csv("hasil_prediksi.csv", index=False)

# 3. Cetak metadata_prediksi.txt (Rentang Data Testing Kini Benar 24 Jam)
train_start_str = df_hourly['Timestamp'].min().strftime('%d-%m-%Y %H:%M WIB')
train_end_str = df_hourly['Timestamp'].max().strftime('%d-%m-%Y %H:%M WIB')
total_logs_str = f"{len(df):,}".replace(',', '.')

test_start_str = df_hourly['Timestamp'].iloc[-test_len].strftime('%d-%m-%Y %H:%M WIB')
test_end_str = df_hourly['Timestamp'].iloc[-1].strftime('%d-%m-%Y %H:%M WIB')

pred_start_str = forecast_suhu['ds'].tail(6).iloc[0].strftime('%d-%m-%Y %H:%M WIB')
pred_end_str = forecast_suhu['ds'].tail(6).iloc[-1].strftime('%d-%m-%Y %H:%M WIB')

with open("metadata_prediksi.txt", "w", encoding="utf-8") as f:
    f.write(f"{train_start_str}\n")
    f.write(f"{train_end_str}\n")
    f.write(f"{total_logs_str}\n")
    f.write(f"{test_start_str}\n")
    f.write(f"{test_end_str}\n")
    f.write(f"{pred_start_str}\n")
    f.write(f"{pred_end_str}\n")

# 4. Grafik Prediksi 6 Jam
plt.figure(figsize=(10, 4))
plt.plot(df_hourly['Timestamp'].tail(48), df_hourly['Suhu'].tail(48), label='Historis Suhu (Rata-rata 1 Jam)', color='#D97706')
plt.plot(forecast_suhu['ds'].tail(6), forecast_suhu['yhat'].tail(6), '--o', label='Prediksi Suhu (6 Jam)', color='#B45309')
plt.title("Proyeksi Prediksi Suhu 6 Jam ke Depan", fontweight='bold')
plt.legend()
plt.grid(True, linestyle=':', alpha=0.6)
plt.tight_layout()
plt.savefig("grafik_prediksi.png", dpi=150)
plt.close()

# 5. Grafik Evaluasi Model (Rentang X Benar-benar 24 Jam)
plt.figure(figsize=(10, 4))
plt.plot(df_hourly['Timestamp'].tail(test_len), y_true_s, label='Aktual (Suhu)', color='#059669')
plt.plot(df_hourly['Timestamp'].tail(test_len), y_pred_s, '--', label='Prediksi Prophet', color='#D97706')
plt.title("Evaluasi Akurasi Model (Testing Set 24 Jam)", fontweight='bold')
plt.legend()
plt.grid(True, linestyle=':', alpha=0.6)
plt.tight_layout()
plt.savefig("grafik_evaluasi.png", dpi=150)
plt.close()

print("✅ Proses prediksi sukses! Seluruh 5 file luaran AI berhasil diperbarui dengan rentang 24 jam presisi.")