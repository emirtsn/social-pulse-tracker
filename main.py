import psycopg2
import re
import logging
from textblob import TextBlob
from atproto import Client
import config
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def clean_text(text):
    """Metni linklerden ve etiketlerden arındırır."""
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'@\S+', '', text)
    return text.strip()

def analyze_sentiment(text):
    """Metni analiz eder ve skorları döner."""
    analysis = TextBlob(text)
    return analysis.sentiment.polarity, analysis.sentiment.subjectivity


def save_to_db(cursor, data):
    """Tek bir satır veriyi PostgreSQL'e yazar."""
    query = """
            INSERT INTO tech_buzz_trends
            (created_at, author_handle, post_text, sentiment_polarity, sentiment_subjectivity, keyword)
            VALUES (%s, %s, %s, %s, %s, %s) \
            ON CONFLICT (author_handle, post_text) DO NOTHING;    
            """
    cursor.execute(query, data)


def run_pipeline(keyword):
    """Ana veri akışını yönetir."""
    logging.info(f"🔍 {keyword} taraması başlıyor...")


    try:
        # BlueSky Giriş
        client = Client()
        client.login(config.BSKY_HANDLE, config.BSKY_PASSWORD)

        # Veri Çekme (Sadece İngilizce)
        response = client.app.bsky.feed.search_posts(
            params={'q': keyword, 'lang': 'en', 'limit': 30}
        )

        # DB Bağlantısı
        conn = psycopg2.connect(**config.DB_CONFIG)
        cur = conn.cursor()

        success_count = 0
        for post in response.posts:
            cleaned = clean_text(post.record.text)
            if cleaned:  # Boş değilse analiz et
                polarity, subjectivity = analyze_sentiment(cleaned)
                data = (
                    post.record.created_at,
                    post.author.handle,
                    cleaned,
                    polarity,
                    subjectivity,
                    keyword
                )
                save_to_db(cur, data)
                success_count += 1

        conn.commit()
        logging.info(f"✅ {keyword} için {success_count} post başarıyla işlendi.")
        cur.close()
        conn.close()

    except Exception as e:
        logging.error(f"❌ Kritik Hata: {e}")


if __name__ == "__main__":
    # İstediğin teknolojileri buraya ekleyebilirsin
    keywords = ["NVIDIA", "ChatGPT", "PostgreSQL", "Data Engineering"]
    for kw in keywords:
        run_pipeline(kw)