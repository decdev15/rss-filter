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
    #      if '/sport/' in url_lower or '/entertainment/' in url_lower or '/politics/' in url_lower or '/courts/' in url_lower or '/county/' in url_lower or '/business/' in url_lower or '/world-news/' in url_lower or '/irish-news/' in url_lower or '/weather/' in url_lower:
    #          continue

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
                         rugby_only=False, gaa_only=False, soccer_only=False, golf_only=False, other_sports_only=False, 
                         sport_podcasts_only=False, sport_irish_news_only=False, sport_county_only=False,  # <-- ADDED THESE THREE HERE
                         podcasts_only=False, # (Keep this if used elsewhere)
                         irish_business_only=False, money_only=False, world_only=False, technology_only=False, commercial_property_only=False,
                         theatre_arts_only=False, celebrity_only=False, music_only=False, television_only=False, books_only=False, horoscopes_only=False, movies_only=False):

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

# =====================================================
            # --- SPORT-SPECIFIC MODES & EXCLUSIONS ---
            # =====================================================
            if source_url == "https://www.independent.ie/sport/rss":
                # 1. Sub-feed filtering (If a selector is True, filter strictly)
                if rugby_only and '/rugby/' not in url_lower:
                    continue
                if gaa_only and '/gaa/' not in url_lower:
                    continue
                if soccer_only and '/soccer/' not in url_lower: 
                    continue
                if golf_only and '/golf/' not in url_lower:
                    continue
                if other_sports_only and '/other-sports/' not in url_lower:
                    continue
                if sport_podcasts_only and '/podcasts/' not in url_lower:
                    continue
                if sport_irish_news_only and '/irish-news/' not in url_lower:
                    continue
                if sport_county_only and '/county/' not in url_lower:
                    continue
                
                # 2. Main feed filtering (If no sub-feed selector is active, strip sub-channel items)
                if not (rugby_only or gaa_only or soccer_only or golf_only or other_sports_only or sport_podcasts_only or sport_irish_news_only or sport_county_only):
                    # Added '/podcasts/' here so they are stripped out of the main general sports feed
                    if '/rugby/' in url_lower or '/gaa/' in url_lower or '/soccer/' in url_lower or '/golf/' in url_lower or '/other-sports/' in url_lower or '/podcasts/' in url_lower or '/irish-news/' in url_lower or '/county/' in url_lower:
                        continue

            # =====================================================
            # --- BUSINESS-SPECIFIC MODES & EXCLUSIONS ---
            # =====================================================
            if source_url == "https://www.independent.ie/business/rss":
                # 1. Sub-feed filtering (If a selector is True, filter strictly)
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

                # 2. Main feed filtering (If no sub-feed selector is active, strip sub-channel items)
                if not (irish_business_only or money_only or world_only or technology_only or commercial_property_only):
                    if '/irish-business/' in url_lower or '/money/' in url_lower or '/world/' in url_lower or '/technology/' in url_lower or '/commercial-property/' in url_lower:
                        continue

            # =====================================================
            # --- ENTERTAINMENT-SPECIFIC MODES & EXCLUSIONS ---
            # =====================================================
            if source_url == "https://www.independent.ie/entertainment/rss":
                # 1. Sub-feed filtering (If a selector is True, filter strictly)
                if theatre_arts_only and '/theatre-arts/' not in url_lower:
                    continue
                if celebrity_only and '/celebrity/' not in url_lower:
                    continue
                if music_only and '/music/' not in url_lower:
                    continue
                if television_only and '/television/' not in url_lower:
                    continue
                if books_only and '/books/' not in url_lower:
                    continue
                if horoscopes_only and '/horoscopes/' not in url_lower:
                    continue
                if movies_only and '/movies/' not in url_lower:
                    continue

                # 2. Main feed filtering (If no sub-feed selector is active, strip sub-channel items)
                if not (theatre_arts_only or celebrity_only or music_only or television_only or books_only or horoscopes_only or movies_only):
                    if '/theatre-arts/' in url_lower or '/celebrity/' in url_lower or '/music/' in url_lower or '/television/' in url_lower or '/books/' in url_lower or '/horoscopes/' in url_lower or '/movies/' in url_lower:
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

# The endpoints to be added in inoreader are a concatenation of "https://rss-filter-y4fa.onrender.com" and these app.routes below 
# ("https://rss-filter-y4fa.onrender.com" per https://dashboard.render.com/web/srv-d93apjho3t8c73f8cicg) 
# 
# ... 
# "FO: " means filtered out i.e. articles with certain words and phrases in their title are filtered out 
    # removed this for now, so if not FI, then it is FO 
# "FI: " means filtered in i.e. only articles with certain words and phrases are displayed

########################### INDO MAIN FEEDS 

# https://rss-filter-y4fa.onrender.com/indo_main.xml 
@app.route('/indo_main.xml')
def indo_main():
    BLOCKS = r"asdf|word 1"
    return process_generic_feed(
        "https://www.independent.ie/rss",
        BLOCKS,
        "Indo Main",
        exclude_groups_of_links=True
    )

# https://rss-filter-y4fa.onrender.com/indo_main_inclusive.xml
@app.route('/indo_main_inclusive.xml')
def indo_main_inclusive():
    ALLOWED = r"asdf|phrase 2"
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=ALLOWED,
        feed_title_override="Indo Main (FI)",
        exclude_groups_of_links=True,
        inclusive=True
    )

# https://rss-filter-y4fa.onrender.com/indo_sport.xml
@app.route('/indo_sport.xml')
def indo_sport():
    BLOCKS = r"Liverpool|\\bpubs\\b"
    return process_generic_feed(
        "https://www.independent.ie/sport/rss",
        BLOCKS,
        "Indo Sport"
    )

# https://rss-filter-y4fa.onrender.com/indo_sport_inclusive.xml
@app.route('/indo_sport_inclusive.xml')
def indo_sport_inclusive():
    ALLOWED = r"Liverpool|phrase 2"
    return process_generic_feed(
        "https://www.independent.ie/sport/rss",
        ALLOWED,
        "Indo Sport (FI)",
        inclusive=True
    )

# https://rss-filter-y4fa.onrender.com/indo_ent.xml
@app.route('/indo_ent.xml')
def indo_ent():
    BLOCKS = f"asdf"
    return process_generic_feed(
        "https://www.independent.ie/entertainment/rss",
        BLOCKS,
        "Indo Entertainment"
    )

# https://rss-filter-y4fa.onrender.com/indo_ent_inclusive.xml
@app.route('/indo_ent_inclusive.xml')
def indo_ent_inclusive():
    ALLOWED = r"horan|McNally"
    return process_generic_feed(
        "https://www.independent.ie/entertainment/rss",
        ALLOWED,
        "Indo Entertainment (FI)",
        inclusive=True
    )

# https://rss-filter-y4fa.onrender.com/indo_business.xml
@app.route('/indo_business.xml')
def indo_business():
    BLOCKS = f"asdf"
    return process_generic_feed(
        "https://www.independent.ie/business/rss",
        BLOCKS,
        "Indo Business"
    )


########################### INDO MISC FEEDS

# https://rss-filter-y4fa.onrender.com/indo_politics.xml
@app.route('/indo_politics.xml')
def indo_politics():
    BLOCKS = r"asdf|word 1"
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=BLOCKS,
        feed_title_override="Indo Main: Politics",
        politics_only=True 
    )

# https://rss-filter-y4fa.onrender.com/indo_courts.xml
@app.route('/indo_courts.xml')
def indo_courts():
    BLOCKS = r"asdf|word 1"
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=BLOCKS,
        feed_title_override="Indo Main: Courts",
        courts_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_county.xml
@app.route('/indo_county.xml')
def indo_county():
    BLOCKS = r"asdf|word 1"
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=BLOCKS,
        feed_title_override="Indo Main: County",
        county_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_world_news.xml
@app.route('/indo_world_news.xml')
def indo_world_news():
    BLOCKS = r"asdf|word 1"
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=BLOCKS,
        feed_title_override="Indo Main: World News",
        world_news_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_irish_news.xml
@app.route('/indo_irish_news.xml')
def indo_irish_news():
    BLOCKS = r"asdf|word 1"
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=BLOCKS,
        feed_title_override="Indo Main: Irish News",
        irish_news_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_weather.xml
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

# https://rss-filter-y4fa.onrender.com/indo_rugby.xml
@app.route('/indo_rugby.xml')
def indo_rugby():
    BLOCKS = r"asdf|word 1"
    return process_generic_feed(
        source_url="https://www.independent.ie/sport/rss",
        regex_pattern=BLOCKS,
        feed_title_override="Indo Sport: Rugby",
        rugby_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_gaa.xml
@app.route('/indo_gaa.xml')
def indo_gaa():
    BLOCKS = r"asdf|word 1"
    return process_generic_feed(
        source_url="https://www.independent.ie/sport/rss",
        regex_pattern=BLOCKS,
        feed_title_override="Indo Sport: GAA",
        gaa_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_soccer.xml
@app.route('/indo_soccer.xml')
def indo_soccer():
    BLOCKS = r"asdf|word 1"
    return process_generic_feed(
        source_url="https://www.independent.ie/sport/rss",
        regex_pattern=BLOCKS,
        feed_title_override="Indo Sport: Soccer",
        soccer_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_golf.xml
@app.route('/indo_golf.xml')
def indo_golf():
    BLOCKS = r"asdf|word 1"
    return process_generic_feed(
        source_url="https://www.independent.ie/sport/rss",
        regex_pattern=BLOCKS,
        feed_title_override="Indo Sport: Golf",
        golf_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_other_sports.xml
@app.route('/indo_other_sports.xml')
def indo_other_sports():
    BLOCKS = r"asdf|word 1"
    return process_generic_feed(
        source_url="https://www.independent.ie/sport/rss",
        regex_pattern=BLOCKS,
        feed_title_override="Indo Sport: Other Sports",
        other_sports_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_podcasts.xml
@app.route('/indo_podcasts.xml')
def indo_podcasts():
    BLOCKS = r"asdf|word 1"
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=BLOCKS,
        feed_title_override="Indo Sport: Podcasts",
        sport_podcasts_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_sport_irish_news.xml
@app.route('/indo_sport_irish_news.xml')
def indo_sport_irish_news():
    BLOCKS = r"asdf|word 1"
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=BLOCKS,
        feed_title_override="Indo Sport: irish_news",
        sport_irish_news_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_sport_county.xml
@app.route('/indo_sport_county.xml')
def indo_sport_county():
    BLOCKS = r"asdf|word 1"
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=BLOCKS,
        feed_title_override="Indo Sport: county",
        sport_county_only=True
    )


########################### INDO BUSINESS FEEDS

# https://rss-filter-y4fa.onrender.com/indo_irish_business.xml
@app.route('/indo_irish_business.xml')
def indo_irish_business():
    BLOCKS = r"asdf|word 1"
    return process_generic_feed(
        source_url="https://www.independent.ie/business/rss",
        regex_pattern=BLOCKS,
        feed_title_override="Indo Business: Irish",
        irish_business_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_money.xml
@app.route('/indo_money.xml')
def indo_money():
    BLOCKS = r"asdf|word 1"
    return process_generic_feed(
        source_url="https://www.independent.ie/business/rss",
        regex_pattern=BLOCKS,
        feed_title_override="Indo Business: Money",
        money_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_world_business.xml
@app.route('/indo_world_business.xml')
def indo_world_business():
    BLOCKS = r"asdf|word 1"
    return process_generic_feed(
        source_url="https://www.independent.ie/business/rss",
        regex_pattern=BLOCKS,
        feed_title_override="Indo Business: World",
        world_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_technology.xml
@app.route('/indo_technology.xml')
def indo_technology():
    BLOCKS = r"asdf|word 1"
    return process_generic_feed(
        source_url="https://www.independent.ie/business/rss",
        regex_pattern=BLOCKS,
        feed_title_override="Indo Business: Technology",
        technology_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_commercial_property.xml
@app.route('/indo_commercial_property.xml')
def indo_commercial_property():
    BLOCKS = r"asdf|word 1"
    return process_generic_feed(
        source_url="https://www.independent.ie/business/rss",
        regex_pattern=BLOCKS,
        feed_title_override="Indo Business: Commercial Property",
        commercial_property_only=True
    )


########################### INDO ENTERTAINMENT FEEDS

# https://rss-filter-y4fa.onrender.com/indo_theatre_arts.xml
@app.route('/indo_theatre_arts.xml')
def indo_theatre_arts():
    BLOCKS = r"asdf|word 1"
    return process_generic_feed(
        source_url="https://www.independent.ie/entertainment/rss",
        regex_pattern=BLOCKS,
        feed_title_override="Indo Entertainment: Theatre & Arts",
        theatre_arts_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_celebrity.xml
@app.route('/indo_celebrity.xml')
def indo_celebrity():
    BLOCKS = r"asdf|word 1"
    return process_generic_feed(
        source_url="https://www.independent.ie/entertainment/rss",
        regex_pattern=BLOCKS,
        feed_title_override="Indo Entertainment: Celebrity",
        celebrity_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_music.xml
@app.route('/indo_music.xml')
def indo_music():
    BLOCKS = r"asdf|word 1"
    return process_generic_feed(
        source_url="https://www.independent.ie/entertainment/rss",
        regex_pattern=BLOCKS,
        feed_title_override="Indo Entertainment: Music",
        music_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_television.xml
@app.route('/indo_television.xml')
def indo_television():
    BLOCKS = r"asdf|word 1"
    return process_generic_feed(
        source_url="https://www.independent.ie/entertainment/rss",
        regex_pattern=BLOCKS,
        feed_title_override="Indo Entertainment: Television",
        television_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_books.xml
@app.route('/indo_books.xml')
def indo_books():
    BLOCKS = r"asdf|word 1"
    return process_generic_feed(
        source_url="https://www.independent.ie/entertainment/rss",
        regex_pattern=BLOCKS,
        feed_title_override="Indo Entertainment: Books",
        books_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_horoscopes.xml
@app.route('/indo_horoscopes.xml')
def indo_horoscopes():
    BLOCKS = r"asdf|word 1"
    return process_generic_feed(
        source_url="https://www.independent.ie/entertainment/rss",
        regex_pattern=BLOCKS,
        feed_title_override="Indo Entertainment: Horoscopes",
        horoscopes_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_movies.xml
@app.route('/indo_movies.xml')
def indo_movies():
    BLOCKS = r"asdf|word 1"
    return process_generic_feed(
        source_url="https://www.independent.ie/entertainment/rss",
        regex_pattern=BLOCKS,
        feed_title_override="Indo Entertainment: Movies",
        movies_only=True
    )


########################### OTHER FEEDS

# https://rss-filter-y4fa.onrender.com/business_insider.xml
@app.route('/business_insider.xml')
def business_insider():
    BLOCKS = f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}|word1|word2"
    return process_generic_feed(
        "https://feeds.businessinsider.com/custom/all",
        BLOCKS,
        "Business Insider"
    )

# https://rss-filter-y4fa.onrender.com/forbes.xml
@app.route('/forbes.xml')
def forbes():
    BLOCKS = f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}|word1|word2"
    return process_generic_feed(
        "https://www.forbes.com/feeds/popstories.xml",
        BLOCKS,
        "Forbes"
    )

# https://rss-filter-y4fa.onrender.com/wired.xml
@app.route('/wired.xml')
def wired():
    BLOCKS = f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}|word1|word2"
    return process_generic_feed(
        "https://www.wired.com/feed/rss",
        BLOCKS,
        "Wired"
    )

# https://rss-filter-y4fa.onrender.com/fortune.xml
@app.route('/fortune.xml')
def fortune():
    BLOCKS = f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}|word1|word2"
    return process_generic_feed(
        "https://fortune.com/rss",
        BLOCKS,
        "Fortune"
    )

# https://rss-filter-y4fa.onrender.com/nyt_soccer.xml
@app.route('/nyt_soccer.xml')
def nyt_soccer():
    BLOCKS = f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}|word1|word2"
    return process_generic_feed(
        "https://rss.nytimes.com/services/xml/rss/nyt/Soccer.xml",
        BLOCKS,
        "NYT Soccer"
    )


# https://rss-filter-y4fa.onrender.com/athletic.xml
@app.route('/athletic.xml')
def athletic():
    BLOCKS = f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}|Liverpool|word2"
    return process_generic_feed(
        "https://www.nytimes.com/athletic/rss/uk",
        BLOCKS,
        "The Athletic"
    )
 
# https://rss-filter-y4fa.onrender.com/athletic_inclusive.xml
@app.route('/athletic_inclusive.xml')
def athletic_inclusive():
    ALLOWED = r"Liverpool|phrase 2"
    return process_generic_feed(
        "https://www.nytimes.com/athletic/rss/uk",
        ALLOWED,
        "The Athletic (FI)",
        inclusive=True
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
