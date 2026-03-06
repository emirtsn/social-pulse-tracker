import config
from textblob import TextBlob
from atproto import Client

# Giriş bilgilerin
client = Client()
client.login(config.BSKY_HANDLE, config.BSKY_PASSWORD)

# "NVIDIA" hakkında en son paylaşımları arayalım
params = {'q': 'NVIDIA',}
response = client.app.bsky.feed.search_posts(params=params)

#for post in response.posts:
    #print(f"Yorum: {post.record.text}\n---")

for post in response.posts:
    text = post.record.text
    analysis = TextBlob(text)

    # Skor: -1 (Çok Negatif) ile +1 (Çok Pozitif) arasındadır
    score = analysis.sentiment.polarity

    # Duyguyu isimlendirelim
    sentiment = "Nötr"
    if score > 0:
        sentiment = "Pozitif 😊"
    elif score < 0:
        sentiment = "Negatif 😡"

    created_at = post.record.created_at
    print(f"Zaman: {created_at}")  # Ne kadar taze olduğunu buradan göreceksin
    print(f"Yorum: {text}")
    print(f"Hype Skoru: {score:.2f} | Durum: {sentiment}")
    print("-" * 30)