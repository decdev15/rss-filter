import os
import re
from flask import Flask, Response
import feedparser
import requests

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
        
        compiled_regex = re.compile(BLOCKED_WORDS, re.IGNORECASE)
        
        # We'll build the XML string directly to avoid strict library conversion crashes
        items_xml = []

        for entry in raw_feed.entries:
            title = entry.get('title', '')
            
            # Filter check
            if compiled_regex.search(title):
                continue  
                
            link = entry.get('link', '')
            desc = entry.get('summary', entry.get('description', ''))
            pub_date = entry.get('published', entry.get('updated', ''))
            guid = entry.get('id', link)
            
            # Clean up potential XML breaking characters in text fields
            title_clean = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            
            item_block = f"""    <item>
        <title>{title_clean}</title>
        <link>{link}</link>
        <description><![CDATA[{desc}]]></description>
        <guid isPermaLink="false">{guid}</guid>
        <pubDate>{pub_date}</pubDate>
    </item>"""
            items_xml.append(item_block)

        # Assemble the final valid RSS feed structure
        feed_title = raw_feed.feed.get('title', 'Filtered Feed').replace("&", "&amp;")
        feed_link = raw_feed.feed.get('link', '')
        feed_desc = raw_feed.feed.get('description', 'Cleaned Feed').replace("&", "&amp;")
        
        xml_output = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
    <title>{feed_title}</title>
    <link>{feed_link}</link>
    <description>{feed_desc}</description>
    <language>en-US</language>
{"\n".join(items_xml)}
</channel>
</rss>"""

        return Response(xml_output, status=200, mimetype='application/rss+xml')
        
    except Exception as e:
        return Response(f"Error processing feed: {str(e)}", status=500, mimetype='text/plain')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
