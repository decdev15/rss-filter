import os
import re
import feedparser
import requests
import time
import sys
import logging
from flask import Flask, Response

app = Flask(__name__)

# =============================================================
# Readme
# =============================================================

# "Indo Main" and "FI: Indo Main" include all articles except for:
# those containing the block words above;
# links included in this block of code (or similar as will be updated):
#
# # --- OVERLAP AVOIDANCE ---
# if exclude_groups_of_links and url_lower:
#     if '/sport/' in url_lower or '/entertainment/' in url_lower or '/politics/' in url_lower or '/courts/' in url_lower or '/county/' in url_lower or '/business/' in url_lower or '/world-news/' in url_lower or '/irish-news/' in url_lower or '/weather/' in url_lower:
#         continue

# =============================================================
# Global variables
# =============================================================

G_BLOCK_NEGATIVE = (
    r"test123"
)

G_BLOCK_OTHER = (
    r"testing12"
)

# =============================================================
# DEBUG HELPER
# =============================================================
def debug_match(title, link, compiled_regex):
    """Print exactly what is being checked and what matches."""
    title_l = title.lower()
    link_l = link.lower()

    print("\n================ FEED ITEM DEBUG ================")
    print("TITLE:", title)
    print("LINK:", link)

    if compiled_regex:
        title_match = compiled_regex.search(title_l)
        link_match = compiled_regex.search(link_l)

        print("TITLE MATCH:", bool(title_match))
        print("LINK MATCH:", bool(link_match))

        if title_match:
            print("➡ MATCHED IN TITLE")
        if link_match:
            print("➡ MATCHED IN LINK")

    print("=================================================\n")


# ============================================================= 
# HELPER FUNCTION
# =============================================================
def process_generic_feed(source_url, regex_pattern, feed_title_override, exclude_groups_of_links=False, inclusive=False, 
                         politics_only=False, courts_only=False, county_only=False, business_only=False, 
                         world_news_only=False, irish_news_only=False, weather_only=False, 
                         rugby_only=False, gaa_only=False, soccer_only=False, golf_only=False, other_sports_only=False, podcasts_only=False,
                         irish_business_only=False, money_only=False, world_only=False, technology_only=False, commercial_property_only=False):

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        resp = requests.get(source_url, headers=headers, timeout=10)
        raw_feed = feedparser.parse(resp.text)

        compiled_regex = re.compile(regex_pattern, re.IGNORECASE) if regex_pattern else None
        items_xml = []

        for entry in raw_feed.entries:
            title = entry.get('title', '')
            link = entry.get('link', '')

            # Create url_lower immediately here if link exists so it is globally available below
            url_lower = link.lower() if link else ""

            # --- OVERLAP AVOIDANCE ---
            if exclude_groups_of_links and url_lower:
                if '/sport/' in url_lower or '/entertainment/' in url_lower or '/business/' in url_lower or '/politics/' in url_lower or '/courts/' in url_lower or '/county/' in url_lower or '/world-news/' in url_lower or '/irish-news/' in url_lower or '/weather/' in url_lower:
                    continue

            # --- MAIN SECTION MODES ---
            if politics_only and '/politics/' not in url_lower:
                continue
            if courts_only and '/courts/' not in url_lower:
                continue
            if county_only and '/county/' not in url_lower:
                continue
            if business_only and '/business/' not in url_lower:
                continue
            if world_news_only and '/world-news/' not in url_lower:
                continue
            if irish_news_only and '/irish-news/' not in url_lower:
                continue
            if weather_only and '/weather/' not in url_lower:
                continue

            # --- SPORT-SPECIFIC EXCLUSIONS ---
            if source_url == "https://www.independent.ie/sport/rss" and not rugby_only and '/rugby/' in url_lower:
                continue
            if source_url == "https://www.independent.ie/sport/rss" and not gaa_only and '/gaa/' in url_lower:
                continue
            if source_url == "https://www.independent.ie/sport/rss" and not soccer_only and '/soccer/' in url_lower:
                continue
            if source_url == "https://www.independent.ie/sport/rss" and not golf_only and '/golf/' in url_lower:
                continue
            if source_url == "https://www.independent.ie/sport/rss" and other_sports_only:
                if '/rugby/' in url_lower or '/gaa/' in url_lower or '/soccer/' in url_lower or '/golf/' in url_lower:
                    continue

            # --- SPORT ONLY MODES ---
            if rugby_only and '/rugby/' not in url_lower:
                continue
            if gaa_only and '/gaa/' not in url_lower:
                continue
            if soccer_only and '/soccer/' not in url_lower:
                continue
            if golf_only and '/golf/' not in url_lower:
                continue
            if other_sports_only and ('/sport/' not in url_lower or '/rugby/' in url_lower or '/gaa/' in url_lower or '/soccer/' in url_lower or '/golf/' in url_lower):
                continue
            if podcasts_only and '/podcasts/' not in url_lower:
                continue

            # --- BUSINESS SUB-FEED EXCLUSIONS ---
            # If pulling from the main business RSS feed, strip out specific sub-channels if we aren't targeting them
            if source_url == "https://www.independent.ie/business/rss":
                if not irish_business_only and '/irish-business/' in url_lower:
                    continue
                if not money_only and '/money/' in url_lower:
                    continue
                if not world_only and '/world/' in url_lower:
                    continue
                if not technology_only and '/technology/' in url_lower:
                    continue
                if not commercial_property_only and '/commercial-property/' in url_lower:
                    continue

            # --- BUSINESS SUB-FEED ONLY MODES ---
            if irish_business_only and '/irish-business/' not in url_lower:
                continue
            if money_only and '/money/' not in url_lower:
                continue
            if world_only and '/world/' not in url_lower:
                continue
            if technology_only and '/technology/' not in url_lower:
                continue
            if commercial_property_only and '/commercial-property/' not in url_lower:
                continue

            # =====================================================
            # FILTER LOGIC (TITLE + URL ONLY)
            # =====================================================
            if compiled_regex:
                title_l = title.lower()
                link_l = link.lower()

                debug_match(title, link, compiled_regex)

                if inclusive:
                    if not (compiled_regex.search(title_l) or compiled_regex.search(link_l)):
                        print("➡ EXCLUDED (inclusive mode)")
                        continue
                else:
                    if compiled_regex.search(title_l) or compiled_regex.search(link_l):
                        print("➡ BLOCKED (negative match)")
                        continue

            base_desc = entry.get('summary', entry.get('description', ''))
            pub_date = entry.get('published', entry.get('updated', ''))
            guid = f"{link}#{hash(title)}"

            img_url = ""
            if 'media_content' in entry and len(entry['media_content']) > 0:
                img_url = entry['media_content'][0].get('url', '')
            elif 'links' in entry:
                for l in entry['links']:
                    if 'image' in l.get('type', ''):
                        img_url = l.get('href', '')
                        break

            if img_url:
                desc_html = f'<img src="{img_url}" style="max-width:100%; height:auto; margin-bottom:10px;" /><br/>{base_desc}'
            else:
                desc_html = base_desc

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
    <lastBuildDate>{time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime())}</lastBuildDate>
    {"\n".join(items_xml)}
</channel>
</rss>"""

        response = Response(xml_output, status=200, mimetype='application/rss+xml')
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'

        return response

    except Exception as e:
        print("ERROR:", str(e))
        return Response(f"Error processing feed: {str(e)}", status=500, mimetype='text/plain')


# =============================================================
# ROUTES
# =============================================================

########################### INDO MAIN FEEDS 

@app.route('/indo_main.xml')
def indo_main():
    BLOCKS = r"asdf|word 1"
    return process_generic_feed(
        "https://www.independent.ie/rss",
        BLOCKS,
        "Indo Main",
        exclude_groups_of_links=True
    )

@app.route('/indo_main_inclusive.xml')
def indo_main_inclusive():
    ALLOWED = r"asdf|phrase 2"
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=ALLOWED,
        feed_title_override="FI: Indo Main",
        exclude_groups_of_links=True,
        inclusive=True
    )

@app.route('/indo_sport.xml')
def indo_sport():
    BLOCKS = r"Liverpool|\\bpubs\\b"
    return process_generic_feed(
        "https://www.independent.ie/sport/rss",
        BLOCKS,
        "Indo Sport"
    )

@app.route('/indo_sport_inclusive.xml')
def indo_sport_inclusive():
    ALLOWED = r"Liverpool|phrase 2"
    return process_generic_feed(
        "https://www.independent.ie/sport/rss",
        ALLOWED,
        "FI: Indo Sport",
        inclusive=True
    )

@app.route('/indo_ent.xml')
def indo_ent():
    BLOCKS = f"asdf"
    return process_generic_feed(
        "https://www.independent.ie/entertainment/rss",
        BLOCKS,
        "Indo Entertainment"
    )

@app.route('/indo_ent_inclusive.xml')
def indo_ent_inclusive():
    ALLOWED = r"horan|McNally"
    return process_generic_feed(
        "https://www.independent.ie/entertainment/rss",
        ALLOWED,
        "FI: Indo Entertainment",
        inclusive=True
    )

@app.route('/indo_business.xml')
def indo_business():
    BLOCKS = f"asdf"
    return process_generic_feed(
        "https://www.independent.ie/business/rss",
        BLOCKS,
        "Indo Business"
    )


########################### INDO MISC FEEDS

@app.route('/indo_politics.xml')
def indo_politics():
    BLOCKS = r"asdf|word 1"
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=BLOCKS,
        feed_title_override="Indo Main: Politics",
        politics_only=True 
    )

@app.route('/indo_courts.xml')
def indo_courts():
    BLOCKS = r"asdf|word 1"
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=BLOCKS,
        feed_title_override="Indo Main: Courts",
        courts_only=True
    )

@app.route('/indo_county.xml')
def indo_county():
    BLOCKS = r"asdf|word 1"
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=BLOCKS,
        feed_title_override="Indo Main: County",
        county_only=True
    )

@app.route('/indo_world_news.xml')
def indo_world_news():
    BLOCKS = r"asdf|word 1"
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=BLOCKS,
        feed_title_override="Indo Main: World News",
        world_news_only=True
    )

@app.route('/indo_irish_news.xml')
def indo_irish_news():
    BLOCKS = r"asdf|word 1"
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=BLOCKS,
        feed_title_override="Indo Main: Irish News",
        irish_news_only=True
    )

@app.route('/indo_weather.xml')
def indo_weather():
    BLOCKS = r"asdf|word 1"
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=BLOCKS,
        feed_title_override="Indo Main: Weather",
        weather_only=True
    )


########################### INDO SPORTS FEEDS

@app.route('/indo_rugby.xml')
def indo_rugby():
    BLOCKS = r"asdf|word 1"
    return process_generic_feed(
        source_url="https://www.independent.ie/sport/rss",
        regex_pattern=BLOCKS,
        feed_title_override="Indo Sport: Rugby",
        rugby_only=True
    )

@app.route('/indo_gaa.xml')
def indo_gaa():
    BLOCKS = r"asdf|word 1"
    return process_generic_feed(
        source_url="https://www.independent.ie/sport/rss",
        regex_pattern=BLOCKS,
        feed_title_override="Indo Sport: GAA",
        gaa_only=True
    )

@app.route('/indo_soccer.xml')
def indo_soccer():
    BLOCKS = r"asdf|word 1"
    return process_generic_feed(
        source_url="https://www.independent.ie/sport/rss",
        regex_pattern=BLOCKS,
        feed_title_override="Indo Sport: Soccer",
        soccer_only=True
    )

@app.route('/indo_golf.xml')
def indo_golf():
    BLOCKS = r"asdf|word 1"
    return process_generic_feed(
        source_url="https://www.independent.ie/sport/rss",
        regex_pattern=BLOCKS,
        feed_title_override="Indo Sport: Golf",
        golf_only=True
    )

@app.route('/indo_other_sports.xml')
def indo_other_sports():
    BLOCKS = r"asdf|word 1"
    return process_generic_feed(
        source_url="https://www.independent.ie/sport/rss",
        regex_pattern=BLOCKS,
        feed_title_override="Indo Sport: Other Sports",
        other_sports_only=True
    )

@app.route('/indo_podcasts.xml')
def indo_podcasts():
    BLOCKS = r"asdf|word 1"
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=BLOCKS,
        feed_title_override="Indo Sport: Podcasts",
        podcasts_only=True
    )


########################### INDO BUSINESS FEEDS

@app.route('/indo_irish_business.xml')
def indo_irish_business():
    BLOCKS = r"asdf|word 1"
    return process_generic_feed(
        source_url="https://www.independent.ie/business/rss",
        regex_pattern=BLOCKS,
        feed_title_override="Indo Business: Irish Business",
        irish_business_only=True
    )

@app.route('/indo_money.xml')
def indo_money():
    BLOCKS = r"asdf|word 1"
    return process_generic_feed(
        source_url="https://www.independent.ie/business/rss",
        regex_pattern=BLOCKS,
        feed_title_override="Indo Business: Money",
        money_only=True
    )

@app.route('/indo_world_business.xml')
def indo_world_business():
    BLOCKS = r"asdf|word 1"
    return process_generic_feed(
        source_url="https://www.independent.ie/business/rss",
        regex_pattern=BLOCKS,
        feed_title_override="Indo Business: World Business",
        world_only=True
    )

@app.route('/indo_technology.xml')
def indo_technology():
    BLOCKS = r"asdf|word 1"
    return process_generic_feed(
        source_url="https://www.independent.ie/business/rss",
        regex_pattern=BLOCKS,
        feed_title_override="Indo Business: Technology",
        technology_only=True
    )

@app.route('/indo_commercial_property.xml')
def indo_commercial_property():
    BLOCKS = r"asdf|word 1"
    return process_generic_feed(
        source_url="https://www.independent.ie/business/rss",
        regex_pattern=BLOCKS,
        feed_title_override="Indo Business: Commercial Property",
        commercial_property_only=True
    )


########################### OTHER FEEDS

@app.route('/business_insider.xml')
def business_insider():
    BLOCKS = f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}|word1|word2"
    return process_generic_feed(
        "https://feeds.businessinsider.com/custom/all",
        BLOCKS,
        "Business Insider"
    )

@app.route('/forbes.xml')
def forbes():
    BLOCKS = f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}|word1|word2"
    return process_generic_feed(
        "https://www.forbes.com/feeds/popstories.xml",
        BLOCKS,
        "Forbes"
    )

@app.route('/wired.xml')
def wired():
    BLOCKS = f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}|word1|word2"
    return process_generic_feed(
        "https://www.wired.com/feed/rss",
        BLOCKS,
        "Wired"
    )

@app.route('/fortune.xml')
def fortune():
    BLOCKS = f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}|word1|word2"
    return process_generic_feed(
        "https://fortune.com/rss",
        BLOCKS,
        "Fortune"
    )

@app.route('/nyt_soccer.xml')
def nyt_soccer():
    BLOCKS = f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}|word1|word2"
    return process_generic_feed(
        "https://rss.nytimes.com/services/xml/rss/nyt/Soccer.xml",
        BLOCKS,
        "NYT Soccer"
    )

@app.route('/athletic_inclusive.xml')
def athletic_inclusive():
    ALLOWED = r"Liverpool|phrase 2"
    return process_generic_feed(
        "https://www.nytimes.com/athletic/rss/uk",
        ALLOWED,
        "FI: The Athletic",
        inclusive=True
    )

@app.route('/athletic.xml')
def athletic():
    BLOCKS = f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}|Liverpool|word2"
    return process_generic_feed(
        "https://www.nytimes.com/athletic/rss/uk",
        BLOCKS,
        "The Athletic"
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
