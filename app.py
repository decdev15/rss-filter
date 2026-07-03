import os
import re
from flask import Flask, Response
import feedparser
import requests
# Logging:
import sys
import logging

app = Flask(__name__)

# =============================================================
# Global variables
# =============================================================

G_BLOCK_NEGATIVE = (
r"Garda|Gardai|abuse|rape|rapist|murder|war|Israel|Palestine|Trump|Military|strikes|crime|death|dead|dies|stabbing|killed|crisis|"
r"dire|blood|safety|cruelty|paedophile|paedophilia|offences|stolen|prison|inmate|criminal|demise|rolf harris|jimmy savile|"
r"struggles|diagnosis|hate|miserable|"
r"abused|rapes|raped|murdered|murders|killing|kills|"
r"fatal|fatality|fatalities|deathly|deadly|"
r"attack|attacks|attacked|"
r"assault|assaulted|assaults|"
r"violence|violent|"
r"bomb|bombing|bombed|explosion|explosions|"
r"shooting|shot|gunfire|gunman|"
r"stabbed|stabbing|"
r"terror|terrorism|terrorist|extremism|extremist|"
r"hostage|hostages|"
r"kidnap|kidnapped|kidnapping|abduction|abducted|"
r"fraud|scam|scams|scamming|"
r"corruption|bribery|"
r"emergency|disaster|catastrophe|collapse|collapsed|collapsing|devastation|"
r"tragedy|tragic|"
r"hospitalised|hospitalized|critical|critical condition|"
r"terminal|terminally ill|"
r"missing|missing person|"
r"overdose|overdosed|"
r"suicide|self-harm|"
r"grief|mourning|bereavement|"
r"burial|funeral"
)

G_BLOCK_OTHER = r"euromillions|housing|insurance|tax"

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
def process_generic_feed(source_url, regex_pattern, feed_title_override,
                          exclude_sports_ent=False, inclusive=False):

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        resp = requests.get(source_url, headers=headers, timeout=10)
        raw_feed = feedparser.parse(resp.text)

        compiled_regex = re.compile(regex_pattern, re.IGNORECASE) if regex_pattern else None
        items_xml = []

        for entry in raw_feed.entries:
            title = entry.get('title', '')
            link = entry.get('link', '')

            # --- OVERLAP AVOIDANCE ---
            if exclude_sports_ent and link:
                url_lower = link.lower()
                if '/sport/' in url_lower or '/entertainment/' in url_lower:
                    continue

            # =====================================================
            # FILTER LOGIC (TITLE + URL ONLY)
            # =====================================================
            if compiled_regex:
                title_l = title.lower()
                link_l = link.lower()

                # DEBUG OUTPUT (ONLY ACTIVE WHEN FILTER EXISTS)
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
            guid = entry.get('id', link)

            # Extract thumbnail images
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
    {"\n".join(items_xml)}
</channel>
</rss>"""

        return Response(xml_output, status=200, mimetype='application/rss+xml')

    except Exception as e:
        print("ERROR:", str(e))
        return Response(f"Error processing feed: {str(e)}", status=500, mimetype='text/plain')


# =============================================================
# ROUTES (UNCHANGED)
# =============================================================

# The endpoints to be added in inoreader are a concatenation of "https://rss-filter-y4fa.onrender.com" and these app.routes below 
# ("https://rss-filter-y4fa.onrender.com" per https://dashboard.render.com/web/srv-d93apjho3t8c73f8cicg) 
# 
# https://rss-filter-y4fa.onrender.com/indo_main.xml 
# https://rss-filter-y4fa.onrender.com/indo_main_inclusive.xml 
# https://rss-filter-y4fa.onrender.com/indo_sport.xml 
# https://rss-filter-y4fa.onrender.com/indo_sport_inclusive.xml 
# https://rss-filter-y4fa.onrender.com/indo_ent.xml 
# https://rss-filter-y4fa.onrender.com/indo_ent_inclusive.xml 
# https://rss-filter-y4fa.onrender.com/business_insider.xml 
# https://rss-filter-y4fa.onrender.com/forbes.xml 
# https://rss-filter-y4fa.onrender.com/wired.xml 
# https://rss-filter-y4fa.onrender.com/fortune.xml 
# https://rss-filter-y4fa.onrender.com/nyt_soccer.xml 
# ... 
# "FO: " means filtered out i.e. articles with certain words and phrases in their title are filtered out 
# "FI: " means filtered in i.e. only articles with certain words and phrases are displayed

# Independent.ie Main Feed (With Sport & Entertainment Exclusion)
@app.route('/indo_main.xml')
def indo_main():
    BLOCKS = f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}|word 1"
    return process_generic_feed(
        "https://www.independent.ie/rss",
        BLOCKS,
        "FO: Indo Main",
        exclude_sports_ent=True
    )

# Independent.ie Main Feed (Inclusive Phrases Only) 
# Use this to test the exlusions above dont cause many false positives
@app.route('/indo_main_inclusive.xml')
def indo_main_inclusive():
    ALLOWED = f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}|phrase 2"
    return process_generic_feed(
        "https://www.independent.ie/rss",
        ALLOWED,
        "FI: Indo Main",
        inclusive=True
    )


# Independent.ie Sport Feed (Standard Blocklist)
@app.route('/indo_sport.xml')
def indo_sport():
    BLOCKS = f"{G_BLOCK_NEGATIVE}|Liverpool|\\bpubs\\b"
    return process_generic_feed(
        "https://www.independent.ie/sport/rss",
        BLOCKS,
        "FO: Indo Sport"
    )

# Independent.ie Sport Feed (Inclusive Phrases Only) 
# Liverpool blocked in the sport feed above, so such stories will only appear here 
# Liverpool not required to be blocked from the main feed, as links with sports and ent in the url are blocked there. 
# Therefore general Liverpool stories could still appear there.

@app.route('/indo_sport_inclusive.xml')
def indo_sport_inclusive():
    ALLOWED = r"Liverpool|phrase 2"
    return process_generic_feed(
        "https://www.independent.ie/sport/rss",
        ALLOWED,
        "FI: Indo Sport",
        inclusive=True
    )

# Independent.ie Entertainment Feed (Standard Blocklist)
@app.route('/indo_ent.xml')
def indo_ent():
    BLOCKS = f"McNally"
    return process_generic_feed(
        "https://www.independent.ie/entertainment/rss",
        BLOCKS,
        "FO: Indo Entertainment"
    )

# Independent.ie Entertainment Feed (Inclusive Phrases Only)
@app.route('/indo_ent_inclusive.xml')
def indo_ent_inclusive():
    ALLOWED = r"horan|McNally"
    return process_generic_feed(
        "https://www.independent.ie/entertainment/rss",
        ALLOWED,
        "FI: Indo Entertainment",
        inclusive=True
    )

# Business Insider Feed
@app.route('/business_insider.xml')
def business_insider():
    BLOCKS = f"{G_BLOCK_NEGATIVE}|word1|word2"
    return process_generic_feed(
        "https://feeds.businessinsider.com/custom/all",
        BLOCKS,
        "FO: Business Insider"
    )

# Forbes Pop Stories Feed
@app.route('/forbes.xml')
def forbes():
    BLOCKS = f"{G_BLOCK_NEGATIVE}|word1|word2"
    return process_generic_feed(
        "https://www.forbes.com/feeds/popstories.xml",
        BLOCKS,
        "FO: Forbes"
    )

# Wired Feed
@app.route('/wired.xml')
def wired():
    BLOCKS = f"{G_BLOCK_NEGATIVE}|word1|word2"
    return process_generic_feed(
        "https://www.wired.com/feed/rss",
        BLOCKS,
        "FO: Wired"
    )

# Fortune Feed
@app.route('/fortune.xml')
def fortune():
    BLOCKS = f"{G_BLOCK_NEGATIVE}|word1|word2"
    return process_generic_feed(
        "https://fortune.com/rss",
        BLOCKS,
        "FO: Fortune"
    )

# NY Times Soccer Feed
@app.route('/nyt_soccer.xml')
def nyt_soccer():
    BLOCKS = f"{G_BLOCK_NEGATIVE}|word1|word2"
    return process_generic_feed(
        "https://rss.nytimes.com/services/xml/rss/nyt/Soccer.xml",
        BLOCKS,
        "FO: NYT Soccer"
    )

# The Athletic (Inclusive Phrases Only)
@app.route('/athletic_inclusive.xml')
def athletic_inclusive():
    ALLOWED = r"Liverpool|phrase 2"
    return process_generic_feed(
        "https://www.nytimes.com/athletic/rss/uk",
        ALLOWED,
        "FI: The Athletic",
        inclusive=True
    )

# The Athletic (Standard Blocklist)
@app.route('/athletic.xml')
def athletic():
    BLOCKS = f"{G_BLOCK_NEGATIVE}|Liverpool|word2"
    return process_generic_feed(
        "https://www.nytimes.com/athletic/rss/uk",
        BLOCKS,
        "FO: The Athletic"
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
