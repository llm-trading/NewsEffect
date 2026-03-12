from flask import Flask, render_template, jsonify
import json
import pandas as pd
from pathlib import Path
from collections import defaultdict

app = Flask(__name__)

ticker = "micron-tech"

def load_news():
    json_path = Path(__file__).parent / "tickers" / ticker / f"processed_{ticker}_articles.jsonl"
    articles = []
    with open(json_path, 'r', encoding='utf-8') as f:
        for line in f:
            articles.append(json.loads(line))
    articles = [a for a in articles if a['type'] != 'Pro' and "Investing.com's stocks of the week" not in a['title']]
    
    news_by_date = defaultdict(list)
    for article in articles:
        date = article['time'].split()[0]
        news_by_date[date].append(article)
    
    # Sort articles within each date by time (most recent first)
    for date in news_by_date:
        news_by_date[date].sort(key=lambda x: x['time'], reverse=True)
    
    return news_by_date

def load_price_data():
    csv_path = Path(__file__).parent / "tickers" / ticker / f"Micron Stock Price History.csv"
    df = pd.read_csv(csv_path)
    df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y')
    df = df.sort_values('Date')
    df['Vol.'] = df['Vol.'].str.replace('M', '').astype(float)
    return df

@app.route('/')
def index():
    return render_template('index.html', ticker=ticker.replace('-', ' ').title())

@app.route('/api/data')
def get_data():
    df = load_price_data()
    news_by_date = load_news()
    
    data = []
    for _, row in df.iterrows():
        date_str = row['Date'].strftime('%Y-%m-%d')
        news_items = news_by_date.get(date_str, [])
        
        # Determine sentiment colors for each news item (reversed for bottom-to-top display)
        sentiment_colors = []
        if news_items:
            # Reverse the order so oldest is at bottom, newest at top
            for article in reversed(news_items):
                sentiment = article.get('sentiment', 'neutral')
                if sentiment == 'positive':
                    sentiment_colors.append('#10b981')  # green
                elif sentiment == 'negative':
                    sentiment_colors.append('#ef4444')  # red
                else:
                    sentiment_colors.append('#eab308')  # yellow
        
        data.append({
            'date': date_str,
            'open': float(row['Open']),
            'high': float(row['High']),
            'low': float(row['Low']),
            'close': float(row['Price']),
            'volume': float(row['Vol.']),
            'hasNews': date_str in news_by_date,
            'newsCount': len(news_items),
            'sentimentColors': sentiment_colors
        })
    
    return jsonify({'data': data, 'news': dict(news_by_date)})

if __name__ == '__main__':
    app.run(debug=True)
