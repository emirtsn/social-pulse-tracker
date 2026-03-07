import psycopg2
import re
import logging
import yfinance as yf
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from atproto import Client
from apscheduler.schedulers.blocking import BlockingScheduler
import config
import time
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
analyzer = SentimentIntensityAnalyzer()

TECH_MAP = {
    "Generative_AI": {
        "OpenAI": "MSFT",    # OpenAI'ın en büyük ortağı
        "ChatGPT": "MSFT",
        "Claude": "GOOGL",   # Anthropic ortağı Google/Amazon
        "Gemini AI": "GOOGL"
    },
    "Semiconductors": {
        "NVIDIA": "NVDA",
        "AMD": "AMD",
        "Intel": "INTC",
        "TSMC": "TSM"
    },
    "Big_Tech": {
        "Apple": "AAPL",
        "Microsoft": "MSFT",
        "Meta": "META",
        "Alphabet": "GOOGL",
        "Tesla": "TSLA",
        "Amazon": "AMZN"
    },
    "Infrastructure": {
        "Docker": None,      # Borsada yok, sadece sosyal medya takibi
        "Kubernetes": None,
        "PostgreSQL": None
    }
}

def clean_text(text):
    """Metni linklerden ve etiketlerden arındırır."""
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'@\S+', '', text)
    return text.strip()

def analyze_sentiment_vader(text):
    """VADER ile hassas analiz: Compound skoru (-1 ile +1 arası) döner."""
    scores = analyzer.polarity_scores(text)
    return scores['compound'], scores['pos'], scores['neg']


def save_to_db(cursor, data):
    """Tek bir satır veriyi PostgreSQL'e yazar."""
    query = """
            INSERT INTO tech_buzz_trends
            (created_at, author_handle, post_text, sentiment_polarity, sentiment_subjectivity, keyword, category)
            VALUES (%s, %s, %s, %s, %s, %s, %s) \
            ON CONFLICT (author_handle, post_text) DO NOTHING;    
            """
    cursor.execute(query, data)

def fetch_stock_price(cursor, symbol):
    """Hisse fiyatını çeker ve kaydeder."""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1d")
        if not hist.empty:
            raw_price = hist['Close'].iloc[0]
            price = float(raw_price)
            date = hist.index[0].date()
            query = """
            INSERT INTO stock_prices (symbol, price_date, close_price)
            VALUES (%s, %s, %s) ON CONFLICT (symbol, price_date) DO NOTHING;
            """
            cursor.execute(query, (symbol, date, price))
            logging.info(f"📈 {symbol} Fiyatı Kaydedildi: ${price:.2f}")
    except Exception as e:
        logging.error(f"❌ Hisse çekme hatası ({symbol}): {e}")



def run_pipeline():
    try:
        # BlueSky Giriş
        client = Client()
        client.login(config.BSKY_HANDLE, config.BSKY_PASSWORD)

        # DB Bağlantısı
        conn = psycopg2.connect(**config.DB_CONFIG)
        cur = conn.cursor()

        for category, keywords in TECH_MAP.items():
            for tech,ticker in keywords.items() :
                if ticker:
                    logging.info(f"📈 {tech} için {ticker} fiyatı çekiliyor...")
                    fetch_stock_price(cur, ticker)

                logging.info(f"🔍 {category} -> {tech} taranıyor...")
                time.sleep(1.5)

                response = client.app.bsky.feed.search_posts(params={'q': tech, 'lang': 'en', 'limit': 25})

                for post in response.posts:
                    cleaned = clean_text(post.record.text)
                    if cleaned:
                        compound, pos, neg = analyze_sentiment_vader(cleaned)

                        data = (
                            post.record.created_at,
                            post.author.handle,
                            cleaned,
                            float(compound),
                            float(pos),
                            tech,
                            category
                        )
                        save_to_db(cur, data)
            conn.commit()

        cur.close()
        conn.close()
        logging.info("🌟 Tüm evren başarıyla tarandı ve veritabanı güncellendi!")

    except Exception as e:
        logging.error(f"❌ Hata oluştu: {e}")

if __name__ == "__main__":
    logging.info("⚙️ Sistem başlatıldı. Her 30 dakikada bir veri toplanacak...")
    run_pipeline() # Hemen bir tur çalıştır

    # Ardından her 30 dakikada bir uyanacak şekilde ayarla
    scheduler = BlockingScheduler()
    scheduler.add_job(run_pipeline, 'interval', minutes=10)
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logging.info("👋 Sistem kapatılıyor...")