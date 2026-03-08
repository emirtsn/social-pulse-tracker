import re
import numpy as np
import pandas as pd
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from scipy.stats import pearsonr


nltk.download('wordnet', quiet=True)
nltk.download('stopwords', quiet=True)

class SocialPulseAnalytics:
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        self.stop_words.update(['http', 'https', 'co', 'rt', 'amp'])

    def clean_text(self, text):
        """Lemmatization destekli gelişmiş temizlik."""
        text = re.sub(r'http\S+|[^a-zA-Z\s]', '', text.lower())
        tokens = [self.lemmatizer.lemmatize(w) for w in text.split()
                  if w not in self.stop_words and len(w) > 2]
        return " ".join(tokens)

    def get_topics(self, texts, n_topics=2):
        if len(texts) < 10: return ["Yetersiz Veri"]

        cleaned_texts = [self.clean_text(t) for t in texts]
        vectorizer = CountVectorizer(max_features=500, ngram_range=(1, 2))
        data_vectorized = vectorizer.fit_transform(cleaned_texts)

        lda = LatentDirichletAllocation(n_components=n_topics, random_state=42)
        lda.fit(data_vectorized)

        words = vectorizer.get_feature_names_out()
        topic_results = []
        used_words = set()

        for topic in lda.components_:
            top_indices = topic.argsort()[::-1]
            current_topic_words = []

            for idx in top_indices:
                word = words[idx]
                if word not in used_words and len(current_topic_words) < 5:
                    current_topic_words.append(word)
                    used_words.add(word)

            topic_results.append(" • ".join(current_topic_words))
        return topic_results

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
        if len(sentiments) < 5 or len(set(prices)) < 2:
            return 0.0
        try:
            corr, _ = pearsonr(sentiments, prices)
            return round(corr, 4) if not np.isnan(corr) else 0.0
        except:
            return 0.0
