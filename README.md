# Social Pulse: Tech Buzz Tracker

Bu proje, sosyal medya (BlueSky) üzerindeki teknoloji trendlerini gerçek zamanlı olarak takip eden ve duygu analizi (sentiment analysis) yapan bir veri mühendisliği çalışmasıdır.

## 🔗 Özellikler
- **Veri Çekme:** BlueSky API (AT Protocol) üzerinden canlı veri akışı.
- **Analiz:** TextBlob kütüphanesi ile NLP tabanlı duygu skoru hesaplama.
- **Depolama:** PostgreSQL ile verilerin tarihsel olarak saklanması.
- **Görselleştirme:** (Planlanan) Streamlit ile interaktif bir dashboard.

## 🛠️ Teknolojiler
- **Dil:** Python
- **Veritabanı:** PostgreSQL
- **Kütüphaneler:** `atproto`, `textblob`, `psycopg2`
- **Donanım:** Apple M2 MacBook Air (Optimizasyon odaklı çalışma)

## 🚀 Başlangıç
1. Projeyi klonlayın.
2. `pip install -r requirements.txt` komutuyla bağımlılıkları yükleyin.
3. `config.py` dosyasını oluşturun ve API anahtarlarınızı ekleyin.