import os
import re
from flask import Flask, Response
import feedparser
import requests

app = Flask(__name__)

# =============================================================
# HELPER FUNCTION: Centralizes feed fetching and filtering
# =============================================================
def process_generic_feed(source_url, regex_pattern, feed_title_override, exclude_sports_ent=False, inclusive=False):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        resp = requests.get(source_url, headers=headers, timeout=10)
        raw_feed = feedparser.parse(resp.text)
        
        compiled_regex = re.compile(regex_pattern, re.IGNORECASE) if regex_pattern else None
        items_xml = []

        for entry in raw_feed.entries:
            title = entry.get('title', '')
            link = entry.get('link', '')
            
            # --- OVERLAP AVOIDANCE (Deduplication) ---
            if exclude_sports_ent and link:
                url_lower = link.lower()
                if '/sport/' in url_lower or '/entertainment/' in url_lower:
                    continue  # Drop sports and entertainment articles from the main feed

            # --- FILTER LOGIC ---
            if compiled_regex:
                if inclusive:
                    # INCLUSIVE MODE: Skip the article if it does NOT match the phrases
                    if not compiled_regex.search(title):
                        continue
                else:
                    # EXCLUSIVE MODE (Blocklist): Skip the article if it matches the phrases
                    if compiled_regex.search(title):
                        continue  
                
            base_desc = entry.get('summary', entry.get('description', ''))
            pub_date = entry.get('published', entry.get('updated', ''))
            guid = entry.get('id', link)
            
            # Extract thumbnail images across different publisher structures
            img_url = ""
            if 'media_content' in entry and len(entry['media_content']) > 0:
                img_url = entry['media_content'][0].get('url', '')
            elif 'links' in entry:
                for l in entry['links']:
                    if 'image' in l.get('type', ''):
                        img_url = l.get('href', '')
                        break
            
            # Inject standard HTML tag for image rendering inside Inoreader
            if img_url:
                desc_html = f'<img src="{img_url}" style="max-width:100%; height:auto; margin-bottom:10px;" /><br/>{base_desc}'
            else:
                desc_html = base_desc

            # Standard XML escape rules
            title_clean = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            
            items_xml.append(f"""    <item>
        <title>{title_clean}</title>
        <link>{link}</link>
        <description><![CDATA[{desc_html}]]></description>
        <guid isPermaLink="false">{guid}</guid>
        <pubDate>{pub_date}</pubDate>
    </item>""")

        xml_output = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
    <title>{feed_title_override}</title>
    <link>{raw_feed.feed.get('link', '')}</link>
    <description>Filtered cloud stream</description>
    {"\n".join(items_xml)}
</channel>
</rss>"""
        return Response(xml_output, status=200, mimetype='application/rss+xml')
    except Exception as e:
        return Response(f"Error processing feed: {str(e)}", status=500, mimetype='text/plain')


# =============================================================
# INDIVIDUAL FEED PATHWAYS (ROUTES) & CONFIGURATIONS
# =============================================================

# The endpoints to be added in inoreader are a concatenation of "https://rss-filter-y4fa.onrender.com"
# (per https://dashboard.render.com/web/srv-d93apjho3t8c73f8cicg) and these app.routes below
# 
# e.g. https://dashboard.render.com/web/srv-d93apjho3t8c73f8cicg & '/indo_main.xml' = 'https://dashboard.render.com/web/srv-d93apjho3t8c73f8cicg/indo_main.xml'
# 
# https://dashboard.render.com/web/srv-d93apjho3t8c73f8cicg/indo_main.xml
# https://dashboard.render.com/web/srv-d93apjho3t8c73f8cicg/indo_sport.xml
# https://dashboard.render.com/web/srv-d93apjho3t8c73f8cicg/indo_sport_inclusive.xml
# https://dashboard.render.com/web/srv-d93apjho3t8c73f8cicg/indo_ent.xml
# https://dashboard.render.com/web/srv-d93apjho3t8c73f8cicg/indo_ent_inclusive.xml
# https://dashboard.render.com/web/srv-d93apjho3t8c73f8cicg/business_insider.xml
# https://dashboard.render.com/web/srv-d93apjho3t8c73f8cicg/forbes.xml
# https://dashboard.render.com/web/srv-d93apjho3t8c73f8cicg/wired.xml
# https://dashboard.render.com/web/srv-d93apjho3t8c73f8cicg/fortune.xml
# https://dashboard.render.com/web/srv-d93apjho3t8c73f8cicg/nyt_soccer.xml


# 1. Independent.ie Main Feed (With Sport & Entertainment Exclusion)
@app.route('/indo_main.xml')
def indo_main():
    BLOCKS = r"Garda|Gardai|abuse|rape|rapist|murder|crime|death|stabbing|killed|crisis|dire|euromillions|housing|insurance|tax|blood|safety|cruelty|offences|stolen|charged|prison|inmate|criminal" 
    return process_generic_feed("https://www.independent.ie/rss", BLOCKS, "Filtered Indo Main", exclude_sports_ent=True)

# 2. Independent.ie Sport Feed (Standard Blocklist)
@app.route('/indo_sport.xml')
def indo_sport():
    BLOCKS = r"israel games|\bpubs\b" 
    return process_generic_feed("https://www.independent.ie/sport/rss", BLOCKS, "Filtered Indo Sport")

# 3. NEW: Independent.ie Sport Feed (Inclusive Phrases Only)
@app.route('/indo_sport_inclusive.xml')
def indo_sport_inclusive():
    # Replace "phrase 1" and "phrase 2" with your actual allowed keywords
    ALLOWED = r"phrase 1|phrase 2"
    return process_generic_feed("https://www.independent.ie/sport/rss", ALLOWED, "Inclusive Indo Sport", inclusive=True)

# 4. Independent.ie Entertainment Feed (Standard Blocklist)
@app.route('/indo_ent.xml')
def indo_ent():
    BLOCKS = r"Niall Horan|diagnosis|hate" 
    return process_generic_feed("https://www.independent.ie/entertainment/rss", BLOCKS, "Filtered Indo Entertainment")

# 5. NEW: Independent.ie Entertainment Feed (Inclusive Phrases Only)
@app.route('/indo_ent_inclusive.xml')
def indo_ent_inclusive():
    # Replace "phrase 1" and "phrase 2" with your actual allowed keywords
    ALLOWED = r"horan|phrase 2"
    return process_generic_feed("https://www.independent.ie/entertainment/rss", ALLOWED, "Inclusive Indo Entertainment", inclusive=True)

# 6. Business Insider Feed
@app.route('/business_insider.xml')
def business_insider():
    BLOCKS = r"word1|word2" 
    return process_generic_feed("https://feeds.businessinsider.com/custom/all", BLOCKS, "Filtered Business Insider")

# 7. Forbes Pop Stories Feed
@app.route('/forbes.xml')
def forbes():
    BLOCKS = r"word1|word2" 
    return process_generic_feed("https://www.forbes.com/feeds/popstories.xml", BLOCKS, "Filtered Forbes Pop")

# 8. Wired Feed
@app.route('/wired.xml')
def wired():
    BLOCKS = r"word1|word2" 
    return process_generic_feed("https://www.wired.com/feed/rss", BLOCKS, "Filtered Wired")

# 9. Fortune Feed
@app.route('/fortune.xml')
def fortune():
    BLOCKS = r"word1|word2" 
    return process_generic_feed("https://fortune.com/rss", BLOCKS, "Filtered Fortune")

# 10. NY Times Soccer Feed
@app.route('/nyt_soccer.xml')
def nyt_soccer():
    BLOCKS = r"word1|word2" 
    return process_generic_feed("https://rss.nytimes.com/services/xml/rss/nyt/Soccer.xml", BLOCKS, "Filtered NYT Soccer")



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
