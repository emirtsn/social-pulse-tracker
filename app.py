import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
import config
from analytics import SocialPulseAnalytics

# 1. Sayfa Konfigürasyonu
st.set_page_config(
    page_title="Social Pulse | Tech Market Intelligence",
    page_icon="🚀",
    layout="wide"
)

# 2. Singleton Pattern
@st.cache_resource
def get_analytics_engine():
    return SocialPulseAnalytics()

engine = get_analytics_engine()

# 3. Veritabanı Bağlantısı ve Caching
@st.cache_data(ttl=600)
def load_all_data(query):
    try:
        conn = psycopg2.connect(**config.DB_CONFIG)
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Veritabanı bağlantı hatası: {e}")
        return pd.DataFrame()

# --- SIDEBAR ---
st.sidebar.title("🔍 Pulse Filters")
st.sidebar.markdown("---")

tech_list_df = load_all_data("SELECT DISTINCT keyword FROM tech_buzz_trends")
selected_tech = st.sidebar.selectbox("Teknoloji Seçin", tech_list_df['keyword'] if not tech_list_df.empty else ["Veri Yok"])

refresh_btn = st.sidebar.button("Verileri Güncelle")
if refresh_btn:
    st.cache_data.clear() # Cache'i temizle ve yeni veriyi çek

# --- (Dashboard) ---
st.title(f"📈 {selected_tech} Market Intelligence")
st.markdown(f"Son 24 saat içinde toplanan verilerin analizi.")

# Veriyi Filtreleyerek Çekelim
raw_data = load_all_data(f"SELECT * FROM tech_buzz_trends WHERE keyword = '{selected_tech}' ORDER BY created_at DESC")

if not raw_data.empty:
    sentiments = raw_data['sentiment_polarity'].tolist()
    pulse_score = engine.calculate_pulse_index(sentiments)
    total_posts = len(raw_data)

# Grid Düzeni
m1, m2, m3 = st.columns(3)

with m1:
    st.metric("Social Pulse Index", f"{pulse_score}", delta=None)
    st.caption("Sentiment x log10(Volume)")

with m2:
    st.metric("Toplam Yorum Sayısı", f"{total_posts}", delta="Real-time")
    st.caption("BlueSky verisinden çekilen post sayısı")

with m3:
    avg_sent = round(sum(sentiments) / total_posts, 2)
    st.metric("Ortalama Duygu", f"{avg_sent}", delta="VADER Score")
    st.caption("-1 (Negatif) ile +1 (Pozitif) arası")

st.markdown("---")
st.subheader("🔥 Hype Cycle (Smoothed Sentiment)")

raw_data = raw_data.sort_values('created_at')
raw_data['moving_avg'] = raw_data['sentiment_polarity'].rolling(window=30).mean()

# Plotly ile Çizgi Grafiği
fig = px.line(
    raw_data,
    x='created_at',
    y=['sentiment_polarity', 'moving_avg'],
    template="plotly_dark",
    labels={'value': 'Hype Skoru', 'created_at': 'Zaman'},
    color_discrete_map={
        'sentiment_polarity': 'rgba(0, 204, 150, 0.2)',
        'moving_avg': '#00CC96'
    }
)


fig.add_hline(y=0.05, line_dash="dash", line_color="gray", annotation_text="Pozitif Eşik")
fig.update_layout(height=600)
st.plotly_chart(fig, use_container_width=True)


st.markdown("---")
st.subheader(f"📢 {selected_tech} Hakkında Ne Konuşuluyor?")


top_texts = raw_data['post_text'].head(500).tolist()

if len(top_texts) > 10:
    with st.spinner('Yorumlar analiz ediliyor...'):

        topics = engine.get_topics(top_texts, n_topics=2)

        # 3 Kolonlu Konu Kutuları
        t1, t2 = st.columns(2)
        cols = [t1, t2]

    for i, topic in enumerate(topics):
        # Kart tasarımı (CSS ile)
        st.markdown(f"""
            <div style="background-color: #1e2129; padding: 20px; border-radius: 10px; border-left: 5px solid #00CC96; margin-bottom: 10px;">
                <h4 style="margin: 0; color: #00CC96;">Ana Tema {i + 1}</h4>
                    <p style="margin: 5px 0 0 0; font-size: 1.1rem; font-style: italic;">{topic}</p>
            </div>
        """, unsafe_allow_html=True)
else:
    st.info("Bu teknoloji için henüz yeterli derinlikte analiz yapılamıyor.")


# --- BÖLÜM 5: CANLI VERİ AKIŞI (RAW DATA) ---
st.markdown("---")
st.subheader("📄 Detaylı Duygu Analizi Akışı")

display_df = raw_data[['created_at', 'post_text', 'sentiment_polarity']].head(100).copy()

def get_sentiment_bar(val):
    pct = abs(val * 100)
    color = "#ff4b4b" if val < 0 else "#28a745"

    return f'''
        <div style="width: 100px; background-color: #31333f; border-radius: 5px;">
            <div style="width: {pct}px; background-color: {color}; height: 10px; border-radius: 5px;"></div>
        </div>
        <small>{val*100:.1f}%</small>
    '''


with st.container(height=400):
    html_table = '<table style="width:100%; border-collapse: collapse;">'
    html_table += '<tr style="text-align:left; border-bottom: 1px solid #444;"><th>Zaman</th><th>Yorum</th><th>Duygu Durumu</th></tr>'

    for _, row in display_df.iterrows():
        bar_html = get_sentiment_bar(row['sentiment_polarity'])
        time_str = row['created_at'].strftime('%H:%M:%S')
        html_table += f'<tr style="border-bottom: 1px solid #222;"><td style="padding:10px;">{time_str}</td><td>{row["post_text"][:100]}...</td><td>{bar_html}</td></tr>'

    html_table += '</table>'

    st.write(html_table, unsafe_allow_html=True)


symbol_map = {
    "nvidia": "NVDA",
    "openai": "MSFT",
    "claude": "GOOGL",
    "apple": "AAPL",
    "tesla": "TSLA",
    "amazon": "AMZN",
    "amd": "AMD",
    "meta": "META"
}

tech_key = selected_tech.lower()
selected_symbol = symbol_map.get(tech_key)

if selected_symbol:

    price_query = f"SELECT price_date, close_price FROM stock_prices WHERE symbol = '{selected_symbol}' ORDER BY price_date ASC"
    df_price = load_all_data(price_query)

    if not df_price.empty:
        st.markdown("---")
        st.subheader(f"💰 Market vs. Hype: {selected_tech} ({selected_symbol})")

        raw_data['created_at'] = pd.to_datetime(raw_data['created_at'])
        df_price['price_date'] = pd.to_datetime(df_price['price_date'])

        merged_data = pd.merge_asof(
            raw_data.sort_values('created_at'),
            df_price.sort_values('price_date'),
            left_on='created_at',
            right_on='price_date',
            direction='backward'
        ).dropna()

        if not merged_data.empty:

            r_value = engine.get_market_correlation(
                merged_data['sentiment_polarity'].tolist(),
                merged_data['close_price'].tolist()
            )

            c1, c2 = st.columns([1, 4])
            with c1:
                st.metric("Korelasyon (r)", f"{r_value}", help="Duygu ve Fiyat arasındaki matematiksel bağ.")
                if abs(r_value) > 0.5:
                    st.success("Anlamlı İlişki! 📈")
                elif r_value == 0:
                    st.info("Piyasa Kapalı ⏸️")
                else:
                    st.warning("Zayıf İlişki 📉")

            import plotly.graph_objects as go
            from plotly.subplots import make_subplots

            fig_dual = make_subplots(specs=[[{"secondary_y": True}]])

            fig_dual.add_trace(
                go.Scatter(
                    x=merged_data['created_at'],
                    y=merged_data['moving_avg'],
                    name="Duygu (Smoothed)",
                    line=dict(color="#00CC96", width=3)
                ),
                secondary_y=False,
            )

            fig_dual.add_trace(
                go.Scatter(
                    x=merged_data['created_at'],
                    y=merged_data['close_price'],
                    name="Hisse Fiyatı ($)",
                    line=dict(color="#FFA500", width=3, dash='dot')
                ),
                secondary_y=True,
            )

            fig_dual.update_layout(
                title_text=f"{selected_tech} Duygu Trendi vs {selected_symbol} Fiyatı",
                template="plotly_dark",
                height=450,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )

            fig_dual.update_yaxes(title_text="<b>Duygu</b> Skoru", secondary_y=False)
            fig_dual.update_yaxes(title_text="<b>Hisse</b> Fiyatı ($)", secondary_y=True)

            st.plotly_chart(fig_dual, use_container_width=True)

    else:
        st.sidebar.warning(f"⚠️ {selected_symbol} için veritabanında fiyat bilgisi yok.")
else:
    st.sidebar.info(f"ℹ️ {selected_tech} için hisse takibi pasif.")

