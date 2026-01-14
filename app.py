import os
import requests
import redis
import json
from flask import Flask, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Konfigurasi Redis
# Host: localhost, Port: 6379
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

API_KEY = os.getenv("API_KEY")
BASE_URL = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/"

@app.route('/weather/<city>', methods=['GET'])
def get_weather(city):
    city = city.lower() # Standarisasi nama kota jadi huruf kecil

    # 1. Cek apakah data ada di Cache (Redis)
    cached_data = r.get(city)
    if cached_data:
        print(f"Mengambil data dari CACHE untuk: {city}")
        return jsonify(json.loads(cached_data))

    # 2. Jika tidak ada di cache, ambil dari API Pihak Ketiga
    print(f"Mengambil data dari API PIHAK KETIGA untuk: {city}")
    url = f"{BASE_URL}{city}?unitGroup=metric&key={API_KEY}&contentType=json"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            result = {
                "city": city,
                "temp": data['currentConditions']['temp'],
                "description": data['description'],
                "source": "api_external"
            }
            
            # 3. Simpan hasil ke Redis dengan masa berlaku (TTL) 12 jam (43200 detik)
            r.setex(city, 43200, json.dumps(result))
            
            return jsonify(result)
        else:
            return jsonify({"error": "Kota tidak ditemukan"}), response.status_code
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)