import pandas as pd
import requests
import os
import time

def get_indodax_data(pair='btcidr', resolution='60', count=1000):
    """
    Mengambil data riwayat k-line (OHLCV) dari Indodax menggunakan endpoint TradingView.
    pair: Pasangan trading (contoh: 'btcidr')
    resolution: Resolusi waktu dalam menit/hari/minggu (contoh: '60' untuk 1 jam, '1D' untuk 1 hari)
    count: Perkiraan jumlah data candle yang akan diambil
    """
    # Endpoint API Indodax yang benar sesuai dokumentasi
    url = "https://indodax.com/tradingview/history_v2"
    
    # Menyesuaikan format pair ke format simbol yang dibutuhkan API (e.g., btcidr -> BTCIDR)
    symbol = pair.upper()
    
    # Menghitung timestamp 'from' dan 'to'
    # Resolusi dalam menit, kita perlu mengubahnya ke detik untuk kalkulasi
    # Untuk resolusi harian/mingguan, logika ini mungkin perlu disesuaikan, tapi untuk per jam sudah benar.
    try:
        resolution_minutes = int(resolution)
        time_delta = resolution_minutes * 60 * count
    except ValueError:
        # Asumsi kasar jika formatnya '1D', '1W', dll. Ini bisa disempurnakan.
        if 'D' in resolution:
            time_delta = int(resolution.replace('D', '')) * 24 * 60 * 60 * count
        elif 'W' in resolution:
            time_delta = int(resolution.replace('W', '')) * 7 * 24 * 60 * 60 * count
        else:
            time_delta = 60 * 60 * count # Default 1 jam jika format tidak dikenali

    to_timestamp = int(time.time())
    from_timestamp = to_timestamp - time_delta
    
    params = {
        'symbol': symbol,
        'tf': resolution, # tf adalah timeframe (e.g., '60' for 60 minutes)
        'from': from_timestamp,
        'to': to_timestamp
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    print(f"Mencoba mengambil data dari Indodax untuk simbol {symbol}...")
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)

        if response.status_code == 200:
            try:
                data = response.json()
                
                if not data or not isinstance(data, list):
                    print("Tidak ada data yang diterima atau format data salah.")
                    return None

                df = pd.DataFrame(data)
                
                # Mengubah nama kolom agar konsisten (dari PascalCase ke snake_case)
                df.rename(columns={
                    'Time': 'timestamp', 'Open': 'open', 'High': 'high', 
                    'Low': 'low', 'Close': 'close', 'Volume': 'volume'
                }, inplace=True)

                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
                df.set_index('timestamp', inplace=True)
                
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    df[col] = pd.to_numeric(df[col])

                print("Data berhasil diambil dan diproses.")
                return df

            except (requests.exceptions.JSONDecodeError, KeyError) as e:
                print(f"Error: Gagal memproses respons dari Indodax. Error: {e}")
                print("Teks mentah yang diterima:", response.text)
                return None
        else:
            print(f"Error: Permintaan gagal dengan status code {response.status_code}")
            print("Teks mentah yang diterima:", response.text)
            return None

    except requests.exceptions.RequestException as e:
        print(f"Terjadi error saat melakukan permintaan: {e}")
        return None

if __name__ == "__main__":
    # Mengambil data dari Indodax, tf='60' untuk 1 jam
    df = get_indodax_data(pair='btcidr', resolution='60', count=1000)

    if df is not None:
        script_dir = os.path.dirname(__file__)
        data_dir = os.path.join(script_dir, '..', 'data')
        os.makedirs(data_dir, exist_ok=True)
        file_path = os.path.join(data_dir, 'latest_data.csv')
        df.to_csv(file_path)
        print(f"Data berhasil disimpan ke {file_path}")
    else:
        print("Proses dihentikan karena gagal mengambil data.")
