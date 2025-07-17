# --- 1. IMPORT SEMUA LIBRARY YANG DIBUTUHKAN ---
from flask import Flask, render_template, jsonify
import numpy as np
import pandas as pd
import yfinance as yf
from tensorflow.keras.models import load_model
import joblib
import warnings

# Menonaktifkan pesan peringatan dari TensorFlow yang tidak relevan
warnings.filterwarnings('ignore', category=FutureWarning)

# --- 2. INISIALISASI APLIKASI FLASK DAN MEMUAT ASET AI ---
app = Flask(__name__)

# Memuat "otak" AI dan "kunci" scaler saat server pertama kali dijalankan
try:
    model = load_model('saved_models/bitcoin_lstm_model.h5')
    scaler = joblib.load('data/target_scaler.pkl')
    print("✅ Model dan Scaler berhasil dimuat.")
except Exception as e:
    print(f"❌ Error saat memuat model atau scaler: {e}")
    model = None
    scaler = None

# --- 3. MEMBUAT ROUTE UNTUK HALAMAN UTAMA ---
@app.route('/')
def home():
    """Menampilkan halaman dashboard utama (index.html)."""
    return render_template('index.html')

# --- 4. MEMBUAT API ENDPOINT UNTUK DATA LIVE ---
# Ini adalah "jembatan" yang akan dipanggil oleh JavaScript
@app.route('/api/live_data')
def get_live_data():
    """Mengambil data live, membuat prediksi, dan mengirimkannya sebagai JSON."""
    if model is None or scaler is None:
        return jsonify({"error": "Model atau scaler tidak berhasil dimuat."}), 500

    try:
        # Mengambil data 5 menit terakhir dari Yahoo Finance
        btc_data = yf.download(tickers='BTC-USD', period='2d', interval='5m')
        
        if len(btc_data) < 60:
            return jsonify({"error": "Data historis tidak cukup untuk prediksi."})

        # Menyiapkan data untuk prediksi
        input_df = btc_data['Close'].tail(60)
        input_scaled = scaler.transform(input_df.values.reshape(-1, 1))
        input_reshaped = np.reshape(input_scaled, (1, 60, 1))

        # Melakukan prediksi
        prediction_scaled = model.predict(input_reshaped)
        prediction_price = scaler.inverse_transform(prediction_scaled)[0][0]

        # Menyiapkan data untuk dikirim ke frontend
        live_data = {
            "current_price": btc_data['Close'].iloc[-1],
            "high_24h": btc_data['High'].iloc[-288:].max(), # 288 interval 5 menit dalam 24 jam
            "low_24h": btc_data['Low'].iloc[-288:].min(),
            "prediction": prediction_price,
            # Mengirim 100 data terakhir untuk grafik candlestick
            "chart_data": btc_data.tail(100).reset_index().to_dict(orient='records')
        }
        
        # Mengembalikan data dalam format JSON
        return jsonify(live_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- 5. MENJALANKAN SERVER ---
if __name__ == '__main__':
    # 'debug=True' agar server otomatis restart saat ada perubahan kode
    app.run(debug=True)

