import os
import re
from flask import Flask, Response
import feedparser
import requests
from rfeed import Item, Feed, Guid

app = Flask(__name__)

# -------------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------------
# 1. Paste your 100-200 words here inside the parenthesis, separated by | pipes.
# Keep them lowercase, with NO spaces directly next to the pipes.
BLOCKED_WORDS = r"\b(crypto|sponsored|giveaway|word1|word2|word3)\b"

# 2. Replace this URL with your actual target RSS feed URL
SOURCE_FEED_URL = "https://rss.nytimes.com/services/xml/rss/nyt/Homepage.xml"
# -------------------------------------------------------------

@app.route('/feed.xml')
def filter_rss():
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        resp = requests.get(SOURCE_FEED_URL, headers=headers, timeout=10)
        raw_feed = feedparser.parse(resp.text)
        
        filtered_items = []
        compiled_regex = re.compile(BLOCKED_WORDS, re.IGNORECASE)

        for entry in raw_feed.entries:
            title = entry.get('title', '')
            
            if compiled_regex.search(title):
                continue  
                
            # Fallbacks to guarantee HTML structure isn't stripped or broken
            desc = entry.get('summary', entry.get('description', ''))
            
            item = Item(
                title=title,
                link=entry.get('link', ''),
                description=desc,
                guid=Guid(entry.get('id', entry.get('link', ''))),
                pubDate=entry.get('published', '')
            )
            filtered_items.append(item)

        feed = Feed(
            title=raw_feed.feed.get('title', 'Filtered Feed'),
            link=raw_feed.feed.get('link', ''),
            description=raw_feed.feed.get('description', 'Cleaned Feed'),
            language=raw_feed.feed.get('language', 'en-US'),
            items=filtered_items
        )

        # FIX: Explicitly prepend standard XML declarations so Inoreader accepts it
        xml_output = '<?xml version="1.0" encoding="UTF-8" ?>\n' + feed.rss()

        return Response(xml_output, status=200, mimetype='application/rss+xml')
        
    except Exception as e:
        return Response(f"Error processing feed: {str(e)}", status=500, mimetype='text/plain')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
