import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

ticker = "micron-tech"
json_path = Path(__file__).parent / "tickers" / ticker / f"master_{ticker}_articles.jsonl"

articles = []
with open(json_path, 'r', encoding='utf-8') as f:
    for line in f:
        articles.append(json.loads(line))

articles = [a for a in articles if a['type'] != 'Pro' and "Investing.com’s stocks of the week" not in a['title']]

news_by_date = defaultdict(list)
for article in articles:
    date = article['time'].split()[0]
    news_by_date[date].append(article)

for date in sorted(news_by_date.keys(), reverse=True):
    print(f"\n{date} ({len(news_by_date[date])} articles)")
    for article in news_by_date[date]:
        print(f"  - {article['title']}")
