import re
import numpy as np
import pandas as pd
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from scipy.stats import pearsonr

# Gerekli NLTK paketlerini bir kez indiriyoruz
nltk.download('wordnet', quiet=True)
nltk.download('stopwords', quiet=True)

class SocialPulseAnalytics:
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        # Teknik terimleri stop_words listesine ekleyebiliriz
        self.stop_words.update(['http', 'https', 'co', 'rt', 'amp'])

    def clean_text(self, text):
        """Lemmatization destekli gelişmiş temizlik."""
        text = re.sub(r'http\S+|[^a-zA-Z\s]', '', text.lower())
        tokens = [self.lemmatizer.lemmatize(w) for w in text.split()
                  if w not in self.stop_words and len(w) > 2]
        return " ".join(tokens)

    def get_topics(self, texts, n_topics=3):
        """LDA ile gizli konu başlıklarını bulur."""
        if len(texts) < 10: return ["Yetersiz Veri"]

        cleaned_texts = [self.clean_text(t) for t in texts]
        vectorizer = CountVectorizer(max_features=500, ngram_range=(1, 2))
        data_vectorized = vectorizer.fit_transform(cleaned_texts)

        lda = LatentDirichletAllocation(n_components=n_topics, random_state=42)
        lda.fit(data_vectorized)

        words = vectorizer.get_feature_names_out()
        topics = []
        for topic in lda.components_:
            top_indices = topic.argsort()[:-6:-1]
            topics.append(" + ".join([words[i] for i in top_indices]))
        return topics

    def calculate_pulse_index(self, sentiments):
        """
        Formül: Sentiment * log10(Volume + 1)
        """
        volume = len(sentiments)
        avg_sentiment = np.mean(sentiments)
        pulse_score = avg_sentiment * np.log10(volume + 1)
        return round(pulse_score, 4)

    def get_market_correlation(self, sentiments, prices):
        """Duygu ve Fiyat arasındaki Pearson korelasyonunu hesaplar."""
        if len(sentiments) < 5 or len(sentiments) != len(prices):
            return 0.0
        # Pearson Katsayısı (r) hesaplama
        corr, _ = pearsonr(sentiments, prices)
        return round(corr, 4)
