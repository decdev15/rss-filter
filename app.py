import os
import re
from flask import Flask, Response
import feedparser
import requests

app = Flask(__name__)

# -------------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------------
# 1. Blocklist Configuration (Case-Insensitive)
# This flags the exact phrase "israel games" or the standalone word "pubs"
BLOCKED_WORDS = r"israel games|\bpubs\b"

# 2. Target RSS feed URL
SOURCE_FEED_URL = "https://www.independent.ie/sport/rss"
# -------------------------------------------------------------

@app.route('/feed.xml')
def filter_rss():
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        resp = requests.get(SOURCE_FEED_URL, headers=headers, timeout=10)
        raw_feed = feedparser.parse(resp.text)
        
        # re.IGNORECASE makes the filter completely case-insensitive
        compiled_regex = re.compile(BLOCKED_WORDS, re.IGNORECASE)
        items_xml = []

        for entry in raw_feed.entries:
            title = entry.get('title', '')
            
            # If the title matches our blocked phrase or word, drop it immediately
            if compiled_regex.search(title):
                continue  
                
            link = entry.get('link', '')
            base_desc = entry.get('summary', entry.get('description', ''))
            pub_date = entry.get('published', entry.get('updated', ''))
            guid = entry.get('id', link)
            
            # Extract Independent.ie thumbnail images
            img_url = ""
            if 'media_content' in entry and len(entry['media_content']) > 0:
                img_url = entry['media_content'][0].get('url', '')
            elif 'links' in entry:
                for l in entry['links']:
                    if 'image' in l.get('type', ''):
                        img_url = l.get('href', '')
                        break
            
            # Prepend the image to the description block for Inoreader compatibility
            if img_url:
                desc_html = f'<img src="{img_url}" style="max-width:100%; height:auto; margin-bottom:10px;" /><br/>{base_desc}'
            else:
                desc_html = base_desc

            # Clean up potential XML breaking characters in text fields
            title_clean = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            
            item_block = f"""    <item>
        <title>{title_clean}</title>
        <link>{link}</link>
        <description><![CDATA[{desc_html}]]></description>
        <guid isPermaLink="false">{guid}</guid>
        <pubDate>{pub_date}</pubDate>
    </item>"""
            items_xml.append(item_block)

        # Assemble the final RSS stream layout
        feed_title = f"Filtered Sport - {raw_feed.feed.get('title', 'Independent.ie')}".replace("&", "&amp;")
        feed_link = raw_feed.feed.get('link', '')
        feed_desc = raw_feed.feed.get('description', 'Cleaned Feed').replace("&", "&amp;")
        
        xml_output = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
    <title>{feed_title}</title>
    <link>{feed_link}</link>
    <description>{feed_desc}</description>
    <language>en-IE</language>
{"\n".join(items_xml)}
</channel>
</rss>"""

        return Response(xml_output, status=200, mimetype='application/rss+xml')
        
    except Exception as e:
        return Response(f"Error processing feed: {str(e)}", status=500, mimetype='text/plain')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
