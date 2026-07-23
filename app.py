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
    #       if '/sport/' in url_lower or '/entertainment/' in url_lower or '/politics/' in url_lower or '/courts/' in url_lower or '/county/' in url_lower or '/business/' in url_lower or '/world-news/' in url_lower or '/irish-news/' in url_lower or '/weather/' in url_lower:
    #           continue

# =============================================================
# Global variables
# =============================================================

G_BLOCK_NEGATIVE = (
    r"jellyfish|struck|dangerous|investment|Geaney|verdict|argument"
)

G_BLOCK_OTHER = (
    r"Enoch|Trump|Farage"
)


# G_BLOCK_NEGATIVE = (
# r"Garda|Gardai|abuse|rape|rapist|murder|war|Israel|Palestine|Ukraine|Missiles|Trump|Military|strikes|crime|death|dead|dies|stabbing|killed|crisis|"
# r"dire|blood|safety|cruelty|paedophile|paedophilia|offences|stolen|prison|inmate|criminal|demise|rolf harris|jimmy savile|anger|angry|"
# r"struggles|diagnosis|hate|miserable|"
# r"abused|rapes|raped|murdered|murders|killing|kills|"
# r"fatal|fatality|fatalities|deathly|deadly|"
# r"attack|attacks|attacked|"
# r"assault|assaulted|assaults|"
# r"violence|violent|"
# r"racism|racist|ku klux Klan|kkk"
# r"bomb|bombing|bombed|explosion|explosions|"
# r"shooting|shot|gunfire|gunman|"
# r"stabbed|stabbing|"
# r"terror|terrorism|terrorist|extremism|extremist|"
# r"hostage|hostages|"
# r"kidnap|kidnapped|kidnapping|abduction|abducted|"
# r"fraud|scam|scams|scamming|"
# r"corruption|bribery|"
# r"emergency|disaster|catastrophe|collapse|collapsed|collapsing|devastation|"
# r"tragedy|tragic|"
# r"hospitalised|hospitalized|critical|critical condition|"
# r"terminal|terminally ill|"
# r"missing|missing person|"
# r"overdose|overdosed|"
# r"suicide|self-harm|"
# r"grief|mourning|bereavement|"
# r"burial|funeral|"
# r"ordeal|burglary|aggravated|vicious|protest|vandalism"
# )

# G_BLOCK_OTHER = (
# r"euromillions|housing|insurance|tax|election|"
# r"queer|pride|lesbian|gay|LGBQT|"
# r"shelbourne|bohemians|league of ireland|LOI|"
# r"Lowe|Schmidt|Cian Tracey|Ian Madigan|Leinster Rugby|Munster Rugby|Joey Carberry|Ronan O'Gara|Wallabies|Springboks|Prendergast|"
# r"Eurobasket|"
# r"Selena Gomez|Bieber|theatre|Lily Allen"
# )

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

                        # Irish Independent
                        
                        comment_only=False, courts_only=False, county_only=False, farming_only=False, irish_news_only=False, 
                        lifestyle_only=False, podcasts_only=False, politics_only=False, weather_only=False, world_news_only=False, 
                        
                        sport_county_only=False, soccer_only=False, gaa_only=False, golf_only=False, 
                        sport_irish_news_only=False, other_sports_only=False, sport_podcasts_only=False, 
                        rugby_only=False, 
                        
                        commercial_property_only=False, county_business_only=False, irish_business_only=False, irish_news_business_only=False, 
                        money_only=False, technology_only=False, world_only=False, 
                        
                        books_only=False, celebrity_only=False, comment_ent_only=False, county_ent_only=False, horoscopes_only=False, 
                        irish_news_ent_only=False, lifestyle_ent_only=False, music_only=False, movies_only=False, radio_only=False, 
                        television_only=False, theatre_arts_only=False,

                        # Business Insider
                        
                        bi_ai_only=False, bi_careers_only=False, 
                        bi_defense_only=False, bi_economy_only=False, bi_entertainment_only=False, 
                        bi_finance_only=False, bi_health_only=False, bi_media_only=False, 
                        bi_parenting_only=False, bi_real_estate_only=False, bi_retail_only=False, 
                        bi_sports_only=False, bi_tech_only=False, 
                        bi_transportation_only=False, bi_travel_only=False,
                        
                        return_filtered_out=False):

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        resp = requests.get(source_url, headers=headers, timeout=10)
        raw_feed = feedparser.parse(resp.text)

        compiled_regex = re.compile(regex_pattern, re.IGNORECASE) if regex_pattern else None
        items_xml = []
        filtered_out_items_xml = []

        # --- MAP STRING ENDPOINTS TO ACCURATE VALUE/SLUG PAIRS ---
        main_filters = {
            '/comment/': comment_only,
            '/courts/': courts_only,
            '/county/': county_only,
            '/farming/': farming_only,  
            '/irish-news/': irish_news_only,
            '/lifestyle/': lifestyle_only,
            '/podcasts/': podcasts_only,
            '/politics/': politics_only,
            '/weather/': weather_only,
            '/world-news/': world_news_only
        }

        sport_filters = {
            '/county/': sport_county_only,
            '/soccer/': soccer_only,
            '/gaa/': gaa_only,
            '/golf/': golf_only,
            '/irish-news/': sport_irish_news_only,
            '/other-sports/': other_sports_only,
            '/podcasts/': sport_podcasts_only,
            '/rugby/': rugby_only
        }

        business_filters = {
            '/commercial-property/': commercial_property_only,
            '/county/': county_business_only,
            '/irish-business/': irish_business_only,
            '/irish-news/': irish_news_business_only,
            '/money/': money_only,
            '/technology/': technology_only,
            '/world/': world_only     
        }

        entertainment_filters = {
            '/books/': books_only,
            '/celebrity/': celebrity_only,
            '/comment/': comment_ent_only,
            '/county/': county_ent_only,
            '/horoscopes/': horoscopes_only,
            '/irish-news/': irish_news_ent_only,
            '/lifestyle/': lifestyle_ent_only,
            '/movies/': movies_only,
            '/music/': music_only,
            '/radio/': radio_only,
            '/television/': television_only,
            '/theatre-arts/': theatre_arts_only
        }

        feed_config = {
            "https://www.independent.ie/sport/rss": sport_filters,
            "https://www.independent.ie/business/rss": business_filters,
            "https://www.independent.ie/entertainment/rss": entertainment_filters
        }
        
        # Primary feed processing loop
        for entry in raw_feed.entries:
            title = entry.get('title', '')
            link = entry.get('link', '')
            
            if isinstance(link, list) and len(link) > 0:
                link = link[0].get('href', '')
            elif not link and 'links' in entry:
                for l in entry['links']:
                    if l.get('rel') == 'alternate' or 'href' in l:
                        link = l.get('href', '')
                        break            
            
            url_lower = link.lower() if link else ""

            # --- OVERLAP AVOIDANCE ---
            if exclude_groups_of_links and url_lower:
                if any(slug in url_lower for slug in 
                [
                    '/sport/', '/entertainment/', '/business/',    
                    '/comment/', '/courts/', '/county/', '/farming/',
                    '/irish-news/', '/lifestyle/', '/podcasts/', 
                    '/politics/', '/weather/', '/world-news/'
                ]):
                    continue  

            # --- MAIN SECTION MODES ---
            if any(is_active and slug not in url_lower for slug, is_active in main_filters.items()):
                continue

            # --- SUB-FEED & SUB-CHANNEL SPECIFIC MODES ---
            if source_url in feed_config:
                current_map = feed_config[source_url]
                
                # Check if ANY of the sub-feed flags are True
                any_flag_active = any(is_active for is_active in current_map.values())

                if any_flag_active:
                    # Strict filtering: Only keep items matching the active sub-channel(s)
                    if any(is_active and slug not in url_lower for slug, is_active in current_map.items()):
                        continue
                else:
                    # Catch-all strip-out strategy for the main section route:
                    # Skip items if they match ANY of the sub-channels that have their own feeds
                    if any(slug in url_lower for slug in current_map.keys()):
                        continue


            # --- BUSINESS INSIDER METADATA FILTERING ENGINE ---
            if source_url == "https://feeds.businessinsider.com/custom/all":
                item_categories = []
                if hasattr(entry, 'tags'):
                    item_categories = [tag.term.lower() for tag in entry.tags if hasattr(tag, 'term')]

                # In the main xml, use "scheme="https://www.businessinsider.com/" to locate these categories
                insider_filters = {
                    'artificial-intelligence': bi_ai_only,
                    'careers': bi_careers_only,
                    'defense': bi_defense_only,
                    'economy': bi_economy_only,
                    'entertainment': bi_entertainment_only,
                    'finance': bi_finance_only,
                    'health': bi_health_only,
                    'media': bi_media_only,
                    'parenting': bi_parenting_only,
                    'real-estate': bi_real_estate_only,
                    'retail': bi_retail_only,
                    'sports': bi_sports_only,
                    'tech': bi_tech_only,
                    'transportation': bi_transportation_only,
                    'travel': bi_travel_only
                }

                any_insider_active = any(insider_filters.values())

                if any_insider_active:
                    # SUB-FEED ROUTE: Strict filtering to keep only matching active sub-channels
                    match_found = False
                    for category, flag_active in insider_filters.items():
                        if flag_active:
                            # Special case check: Match both 'tech' and 'technology' slugs safely
                            if category == 'tech':
                                if 'tech' in item_categories or 'technology' in item_categories:
                                    match_found = True
                                    break
                            elif category in item_categories:
                                match_found = True
                                break
                    if not match_found:
                        continue
                else:
                    # MAIN FEED ROUTE: Define which specific sub-feed tags to strip out.
                    # This ensures the main feed only drops items covered by your dedicated sub-feeds.
                    active_sub_feed_tags = {
                        'artificial-intelligence', 'careers', 'defense', 'economy', 
                        'entertainment', 'finance', 'health', 'media', 'parenting', 
                        'real-estate', 'retail', 'sports', 'tech', 'technology', 'transportation', 'travel'
                    }
                    if any(category in active_sub_feed_tags for category in item_categories):
                        continue


            # =====================================================
            # XML CONSTRUCTION
            # =====================================================
            base_desc = entry.get('summary', entry.get('description', ''))
            pub_date = entry.get('published', entry.get('updated', ''))
            guid = f"{link}#{hash(title)}"

            img_url = ""
            
            # --- DEBUG LOGGING FOR BUSINESS INSIDER IMAGE TRACKING ---
            if "businessinsider.com" in source_url and not img_url:
                # This will print the internal keys of the first item to your Render console log
                print("DEBUG BI ENTRY KEYS:", entry.keys())
                if 'links' in entry:
                    print("DEBUG BI LINKS:", entry['links'])

            # 1. Direct tag parsing
            if 'media_content' in entry and len(entry['media_content']) > 0:
                img_url = entry['media_content'][0].get('url', '')
            
            # 2. Check if feedparser assigned it straight to a flat media_content key string
            elif 'media_content' in entry and isinstance(entry['media_content'], dict):
                img_url = entry['media_content'].get('url', '')

            # 3. Handle specific custom namespaces feedparser drops in entries
            elif 'media_thumbnail' in entry and len(entry['media_thumbnail']) > 0:
                img_url = entry['media_thumbnail'][0].get('url', '')
                
            # 4. Standard enclosure check
            elif 'enclosures' in entry and len(entry['enclosures']) > 0:
                img_url = entry['enclosures'][0].get('url', '')

            # 5. Fallback scan inside the standard links array mapping
            if not img_url and 'links' in entry:
                for l in entry['links']:
                    href = l.get('href', '')
                    rel = l.get('rel', '')
                    type_str = l.get('type', '')
                    # Look for anything screaming image or enclosure link
                    if 'image' in type_str or rel == 'enclosure' or '.jpg' in href or '.png' in href:
                        img_url = href
                        break

            # 6. HTML string scraping backup
            if not img_url and base_desc:
                html_img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', base_desc)
                if html_img_match:
                    img_url = html_img_match.group(1)

            # Rebuild clean final output string safely
            if img_url and img_url not in base_desc:
                desc_html = f'<img src="{img_url}" style="max-width:100%; height:auto; margin-bottom:10px;" /><br/>{base_desc}'
            else:
                desc_html = base_desc







            title_clean = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

            xml_block = f"""    <item>
        <title>{title_clean}</title>
        <link>{link}</link>
        <description><![CDATA[{desc_html}]]></description>
        <guid isPermaLink="false">{guid}</guid>
        <pubDate>{pub_date}</pubDate>
    </item>"""


            # =====================================================
            # FILTER LOGIC (TITLE + URL REGEX MATCHING)
            # =====================================================
            if compiled_regex:
                title_l = title.lower()
                link_l = url_lower

                debug_match(title, link, compiled_regex)

                is_match = bool(compiled_regex.search(title_l) or compiled_regex.search(link_l))

                if inclusive:
                    if is_match:
                        items_xml.append(xml_block)
                    else:
                        print("➡ EXCLUDED (inclusive mode)")
                        filtered_out_items_xml.append(xml_block)
                else:
                    if is_match:
                         # Article belonged to this sub-feed, but failed regex check
                        print("➡ BLOCKED (negative match)")
                        filtered_out_items_xml.append(xml_block)
                    else:
                        items_xml.append(xml_block)
            else:
                items_xml.append(xml_block)

        # Select which payload to construct
        selected_items = filtered_out_items_xml if return_filtered_out else items_xml


        feed_title_clean = feed_title_override.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        xml_output = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
    <title>{feed_title_clean}</title>
    <link>{raw_feed.feed.get('link', '')}</link>
    <description>Filtered cloud stream</description>
    <lastBuildDate>{time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime())}</lastBuildDate>
    {"\n".join(selected_items)}
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
    BLOCKS = f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}|word1|word2"
    return process_generic_feed(
        "https://www.independent.ie/rss",
        BLOCKS,
        "Indo Main",
        exclude_groups_of_links=True
    )

    # The like of the following main feed filter is still required, even though the sub-feeds also have filters:
    
    # if I filter articles out from the main feeds, surely they wont reach the sub-feeds in order to be filtered there?

    # That would be true if the feeds were chained together in a pipeline — but in Flask, each route is completely independent.

    # When a user or RSS reader hits a sub-feed endpoint (like /indo_politics.xml), Flask executes only that specific function. It makes a brand-new, fresh HTTP request directly to the original source ([https://www.independent.ie/rss](https://www.independent.ie/rss)), fetches the entire raw feed, and applies the sub-feed filtering rules from scratch.

    # Here is how the data flows:

    # [ https://www.independent.ie/rss (Raw Source) ]
           # │
           # ├──► Hitting /indo_main.xml ─────► Fetches raw source ──► Applies Main Blocks
           # │
           # └──► Hitting /indo_politics.xml ──► Fetches raw source ──► Applies Politics Filter + Main Blocks
           
    # Because /indo_main.xml never modifies or saves the data on your server, filtering an article out of indo_main has zero impact on indo_politics.
    # Every sub-feed gets a clean slate directly from the source every single time it runs.

# https://rss-filter-y4fa.onrender.com/indo_main_filterout.xml
@app.route('/indo_main_filterout.xml')
def indo_main_filterout():
    BLOCKS = f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}|word1|word2"
    return process_generic_feed(
        "https://www.independent.ie/rss",
        BLOCKS,
        "Indo Main Filter Out",
        exclude_groups_of_links=True,
        return_filtered_out=True
    )

# https://rss-filter-y4fa.onrender.com/indo_main_inclusive.xml
@app.route('/indo_main_inclusive.xml')
def indo_main_inclusive():
    ALLOWED = r"Liverpool|Roscommon"
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
    BLOCKS = f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}|word1|word2"
    return process_generic_feed(
        "https://www.independent.ie/sport/rss",
        BLOCKS,
        "Indo Sport"
    )

# https://rss-filter-y4fa.onrender.com/indo_sport_filterout.xml
@app.route('/indo_sport_filterout.xml')
def indo_sport_filterout():
    BLOCKS = f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}|word1|word2"
    return process_generic_feed(
        "https://www.independent.ie/sport/rss",
        BLOCKS,
        "Indo Sport Filter Out",
        return_filtered_out=True
    )


# https://rss-filter-y4fa.onrender.com/indo_sport_inclusive.xml
@app.route('/indo_sport_inclusive.xml')
def indo_sport_inclusive():
    ALLOWED = r"Liverpool|Roscommon"
    return process_generic_feed(
        "https://www.independent.ie/sport/rss",
        ALLOWED,
        "Indo Sport (FI)",
        inclusive=True
    )

# https://rss-filter-y4fa.onrender.com/indo_business.xml
@app.route('/indo_business.xml')
def indo_business():
    BLOCKS = f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}|word1|word2"
    return process_generic_feed(
        "https://www.independent.ie/business/rss",
        BLOCKS,
        "Indo Business"
    )

# https://rss-filter-y4fa.onrender.com/indo_business_filterout.xml
@app.route('/indo_business_filterout.xml')
def indo_business_filterout():
    BLOCKS = f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}|word1|word2"
    return process_generic_feed(
        "https://www.independent.ie/business/rss",
        BLOCKS,
        "Indo Business Filter Out",
        return_filtered_out=True
    )
    

    
# https://rss-filter-y4fa.onrender.com/indo_ent.xml
@app.route('/indo_ent.xml')
def indo_ent():
    BLOCKS = f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}|word1|word2"
    return process_generic_feed(
        "https://www.independent.ie/entertainment/rss",
        BLOCKS,
        "Indo Entertainment"
    )

# https://rss-filter-y4fa.onrender.com/indo_ent_filterout.xml
@app.route('/indo_ent_filterout.xml')
def indo_ent_filterout():
    BLOCKS = f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}|word1|word2"
    return process_generic_feed(
        "https://www.independent.ie/entertainment/rss",
        BLOCKS,
        "Indo Entertainment Filter Out",
        return_filtered_out=True
    )


# https://rss-filter-y4fa.onrender.com/indo_ent_inclusive.xml
@app.route('/indo_ent_inclusive.xml')
def indo_ent_inclusive():
    ALLOWED = r"Liverpool|Roscommon"
    return process_generic_feed(
        "https://www.independent.ie/entertainment/rss",
        ALLOWED,
        "Indo Entertainment (FI)",
        inclusive=True
    )


########################### INDO MAIN SUB-FEEDS

# https://rss-filter-y4fa.onrender.com/indo_comment.xml
@app.route('/indo_comment.xml')
def indo_comment():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Main: Comment",
        comment_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_comment_filterout.xml
@app.route('/indo_comment_filterout.xml')
def indo_comment_filterout():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Main: Comment Filtered Out",
        comment_only=True,
        return_filtered_out=True
    )

# https://rss-filter-y4fa.onrender.com/indo_courts.xml
@app.route('/indo_courts.xml')
def indo_courts():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Main: Courts",
        courts_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_courts_filterout.xml
@app.route('/indo_courts_filterout.xml')
def indo_courts_filterout():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Main: Courts Filtered Out",
        courts_only=True,
        return_filtered_out=True
    )

# https://rss-filter-y4fa.onrender.com/indo_county.xml
@app.route('/indo_county.xml')
def indo_county():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Main: County",
        county_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_county_filterout.xml
@app.route('/indo_county_filterout.xml')
def indo_county_filterout():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Main: County Filtered Out",
        county_only=True,
        return_filtered_out=True
    )

# https://rss-filter-y4fa.onrender.com/indo_farming.xml
@app.route('/indo_farming.xml')
def indo_farming():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Main: Farming",
        farming_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_farming_filterout.xml
@app.route('/indo_farming_filterout.xml')
def indo_farming_filterout():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Main: Farming Filtered Out",
        farming_only=True,
        return_filtered_out=True
    )

# https://rss-filter-y4fa.onrender.com/indo_irish_news.xml
@app.route('/indo_irish_news.xml')
def indo_irish_news():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Main: Irish News",
        irish_news_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_irish_news_filterout.xml
@app.route('/indo_irish_news_filterout.xml')
def indo_irish_news_filterout():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Main: Irish News Filtered Out",
        irish_news_only=True,
        return_filtered_out=True
    )

# https://rss-filter-y4fa.onrender.com/indo_lifestyle.xml
@app.route('/indo_lifestyle.xml')
def indo_lifestyle():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Main: Lifestyle",
        lifestyle_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_lifestyle_filterout.xml
@app.route('/indo_lifestyle_filterout.xml')
def indo_lifestyle_filterout():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Main: Lifestyle Filtered Out",
        lifestyle_only=True,
        return_filtered_out=True
    )

# https://rss-filter-y4fa.onrender.com/indo_podcasts.xml
@app.route('/indo_podcasts.xml')
def indo_podcasts():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Main: Podcasts",
        podcasts_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_podcasts_filterout.xml
@app.route('/indo_podcasts_filterout.xml')
def indo_podcasts_filterout():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Main: Podcasts Filtered Out",
        podcasts_only=True,
        return_filtered_out=True
    )

# https://rss-filter-y4fa.onrender.com/indo_politics.xml
@app.route('/indo_politics.xml')
def indo_politics():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Main: Politics",
        politics_only=True 
    )

# https://rss-filter-y4fa.onrender.com/indo_politics_filterout.xml
@app.route('/indo_politics_filterout.xml')
def indo_politics_filterout():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Main: Politics Filtered Out",
        politics_only=True,
        return_filtered_out=True
    )

# https://rss-filter-y4fa.onrender.com/indo_weather.xml
@app.route('/indo_weather.xml')
def indo_weather():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Main: Weather",
        weather_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_weather_filterout.xml
@app.route('/indo_weather_filterout.xml')
def indo_weather_filterout():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Main: Weather Filtered Out",
        weather_only=True,
        return_filtered_out=True
    )

# https://rss-filter-y4fa.onrender.com/indo_world_news.xml
@app.route('/indo_world_news.xml')
def indo_world_news():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Main: World News",
        world_news_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_world_news_filterout.xml
@app.route('/indo_world_news_filterout.xml')
def indo_world_news_filterout():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Main: World News Filtered Out",
        world_news_only=True,
        return_filtered_out=True
    )


########################### INDO SPORT SUB-FEEDS

# https://rss-filter-y4fa.onrender.com/indo_sport_county.xml
@app.route('/indo_sport_county.xml')
def indo_sport_county():
    return process_generic_feed(
        source_url="https://www.independent.ie/sport/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Sport: County",
        sport_county_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_sport_county_filterout.xml
@app.route('/indo_sport_county_filterout.xml')
def indo_sport_county_filterout():
    return process_generic_feed(
        source_url="https://www.independent.ie/sport/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Sport: County Filtered Out",
        sport_county_only=True,
        return_filtered_out=True
    )

# https://rss-filter-y4fa.onrender.com/indo_soccer.xml
@app.route('/indo_soccer.xml')
def indo_soccer():
    return process_generic_feed(
        source_url="https://www.independent.ie/sport/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Sport: Soccer",
        soccer_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_soccer_filterout.xml
@app.route('/indo_soccer_filterout.xml')
def indo_soccer_filterout():
    return process_generic_feed(
        source_url="https://www.independent.ie/sport/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Sport: Soccer Filtered Out",
        soccer_only=True,
        return_filtered_out=True
    )

# https://rss-filter-y4fa.onrender.com/indo_gaa.xml
@app.route('/indo_gaa.xml')
def indo_gaa():
    return process_generic_feed(
        source_url="https://www.independent.ie/sport/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Sport: GAA",
        gaa_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_gaa_filterout.xml
@app.route('/indo_gaa_filterout.xml')
def indo_gaa_filterout():
    return process_generic_feed(
        source_url="https://www.independent.ie/sport/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Sport: GAA Filtered Out",
        gaa_only=True,
        return_filtered_out=True
    )

# https://rss-filter-y4fa.onrender.com/indo_golf.xml
@app.route('/indo_golf.xml')
def indo_golf():
    return process_generic_feed(
        source_url="https://www.independent.ie/sport/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Sport: Golf",
        golf_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_golf_filterout.xml
@app.route('/indo_golf_filterout.xml')
def indo_golf_filterout():
    return process_generic_feed(
        source_url="https://www.independent.ie/sport/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Sport: Golf Filtered Out",
        golf_only=True,
        return_filtered_out=True
    )

# https://rss-filter-y4fa.onrender.com/indo_sport_irish_news.xml
@app.route('/indo_sport_irish_news.xml')
def indo_sport_irish_news():
    return process_generic_feed(
        source_url="https://www.independent.ie/sport/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Sport: Irish News",
        sport_irish_news_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_sport_irish_news_filterout.xml
@app.route('/indo_sport_irish_news_filterout.xml')
def indo_sport_irish_news_filterout():
    return process_generic_feed(
        source_url="https://www.independent.ie/sport/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Sport: Irish News Filtered Out",
        sport_irish_news_only=True,
        return_filtered_out=True
    )

# https://rss-filter-y4fa.onrender.com/indo_other_sports.xml
@app.route('/indo_other_sports.xml')
def indo_other_sports():
    return process_generic_feed(
        source_url="https://www.independent.ie/sport/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Sport: Other Sports",
        other_sports_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_other_sports_filterout.xml
@app.route('/indo_other_sports_filterout.xml')
def indo_other_sports_filterout():
    return process_generic_feed(
        source_url="https://www.independent.ie/sport/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Sport: Other Sports Filtered Out",
        other_sports_only=True,
        return_filtered_out=True
    )

# https://rss-filter-y4fa.onrender.com/indo_sports_podcasts.xml
@app.route('/indo_sports_podcasts.xml')
def indo_sports_podcasts():
    return process_generic_feed(
        source_url="https://www.independent.ie/sport/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Sport: Podcasts",
        sport_podcasts_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_sports_podcasts_filterout.xml
@app.route('/indo_sports_podcasts_filterout.xml')
def indo_sports_podcasts_filterout():
    return process_generic_feed(
        source_url="https://www.independent.ie/sport/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Sport: Podcasts Filtered Out",
        sport_podcasts_only=True,
        return_filtered_out=True
    )

# https://rss-filter-y4fa.onrender.com/indo_rugby.xml
@app.route('/indo_rugby.xml')
def indo_rugby():
    return process_generic_feed(
        source_url="https://www.independent.ie/sport/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Sport: Rugby",
        rugby_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_rugby_filterout.xml
@app.route('/indo_rugby_filterout.xml')
def indo_rugby_filterout():
    return process_generic_feed(
        source_url="https://www.independent.ie/sport/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Sport: Rugby Filtered Out",
        rugby_only=True,
        return_filtered_out=True
    )


########################### INDO BUSINESS SUB-FEEDS

# https://rss-filter-y4fa.onrender.com/indo_commercial_property.xml
@app.route('/indo_commercial_property.xml')
def indo_commercial_property():
    return process_generic_feed(
        source_url="https://www.independent.ie/business/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Business: Commercial Property",
        commercial_property_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_commercial_property_filterout.xml
@app.route('/indo_commercial_property_filterout.xml')
def indo_commercial_property_filterout():
    return process_generic_feed(
        source_url="https://www.independent.ie/business/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Business: Commercial Property Filtered Out",
        commercial_property_only=True,
        return_filtered_out=True
    )

# https://rss-filter-y4fa.onrender.com/indo_county_business.xml
@app.route('/indo_county_business.xml')
def indo_county_business():
    return process_generic_feed(
        source_url="https://www.independent.ie/business/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Business: County",
        county_business_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_county_business_filterout.xml
@app.route('/indo_county_business_filterout.xml')
def indo_county_business_filterout():
    return process_generic_feed(
        source_url="https://www.independent.ie/business/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Business: County Filtered Out",
        county_business_only=True,
        return_filtered_out=True
    )

# https://rss-filter-y4fa.onrender.com/indo_irish_business.xml
@app.route('/indo_irish_business.xml')
def indo_irish_business():
    return process_generic_feed(
        source_url="https://www.independent.ie/business/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Business: Irish",
        irish_business_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_irish_business_filterout.xml
@app.route('/indo_irish_business_filterout.xml')
def indo_irish_business_filterout():
    return process_generic_feed(
        source_url="https://www.independent.ie/business/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Business: Irish Filtered Out",
        irish_business_only=True,
        return_filtered_out=True
    )

# https://rss-filter-y4fa.onrender.com/indo_irish_news_business.xml
@app.route('/indo_irish_news_business.xml')
def indo_irish_news_business():
    return process_generic_feed(
        source_url="https://www.independent.ie/business/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Business: Irish News",
        irish_news_business_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_irish_news_business_filterout.xml
@app.route('/indo_irish_news_business_filterout.xml')
def indo_irish_news_business_filterout():
    return process_generic_feed(
        source_url="https://www.independent.ie/business/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Business: Irish News Filtered Out",
        irish_news_business_only=True,
        return_filtered_out=True
    )

# https://rss-filter-y4fa.onrender.com/indo_money.xml
@app.route('/indo_money.xml')
def indo_money():
    return process_generic_feed(
        source_url="https://www.independent.ie/business/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Business: Money",
        money_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_money_filterout.xml
@app.route('/indo_money_filterout.xml')
def indo_money_filterout():
    return process_generic_feed(
        source_url="https://www.independent.ie/business/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Business: Money Filtered Out",
        money_only=True,
        return_filtered_out=True
    )

# https://rss-filter-y4fa.onrender.com/indo_technology.xml
@app.route('/indo_technology.xml')
def indo_technology():
    return process_generic_feed(
        source_url="https://www.independent.ie/business/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Business: Technology",
        technology_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_technology_filterout.xml
@app.route('/indo_technology_filterout.xml')
def indo_technology_filterout():
    return process_generic_feed(
        source_url="https://www.independent.ie/business/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Business: Technology Filtered Out",
        technology_only=True,
        return_filtered_out=True
    )

# https://rss-filter-y4fa.onrender.com/indo_world_business.xml
@app.route('/indo_world_business.xml')
def indo_world_business():
    return process_generic_feed(
        source_url="https://www.independent.ie/business/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Business: World",
        world_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_world_business_filterout.xml
@app.route('/indo_world_business_filterout.xml')
def indo_world_business_filterout():
    return process_generic_feed(
        source_url="https://www.independent.ie/business/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Business: World Filtered Out",
        world_only=True,
        return_filtered_out=True
    )


########################### INDO ENTERTAINMENT SUB-FEEDS

# https://rss-filter-y4fa.onrender.com/indo_books.xml
@app.route('/indo_books.xml')
def indo_books():
    return process_generic_feed(
        source_url="https://www.independent.ie/entertainment/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Entertainment: Books",
        books_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_books_filterout.xml
@app.route('/indo_books_filterout.xml')
def indo_books_filterout():
    return process_generic_feed(
        source_url="https://www.independent.ie/entertainment/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Entertainment: Books Filtered Out",
        books_only=True,
        return_filtered_out=True
    )

# https://rss-filter-y4fa.onrender.com/indo_celebrity.xml
@app.route('/indo_celebrity.xml')
def indo_celebrity():
    return process_generic_feed(
        source_url="https://www.independent.ie/entertainment/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Entertainment: Celebrity",
        celebrity_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_celebrity_filterout.xml
@app.route('/indo_celebrity_filterout.xml')
def indo_celebrity_filterout():
    return process_generic_feed(
        source_url="https://www.independent.ie/entertainment/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Entertainment: Celebrity Filtered Out",
        celebrity_only=True,
        return_filtered_out=True
    )

# https://rss-filter-y4fa.onrender.com/indo_comment_ent.xml
@app.route('/indo_comment_ent.xml')
def indo_comment_ent():
    return process_generic_feed(
        source_url="https://www.independent.ie/entertainment/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Entertainment: Comment",
        comment_ent_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_comment_ent_filterout.xml
@app.route('/indo_comment_ent_filterout.xml')
def indo_comment_ent_filterout():
    return process_generic_feed(
        source_url="https://www.independent.ie/entertainment/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Entertainment: Comment Filtered Out",
        comment_ent_only=True,
        return_filtered_out=True
    )

# https://rss-filter-y4fa.onrender.com/indo_county_ent.xml
@app.route('/indo_county_ent.xml')
def indo_county_ent():
    return process_generic_feed(
        source_url="https://www.independent.ie/entertainment/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Entertainment: County",
        county_ent_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_county_ent_filterout.xml
@app.route('/indo_county_ent_filterout.xml')
def indo_county_ent_filterout():
    return process_generic_feed(
        source_url="https://www.independent.ie/entertainment/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Entertainment: County Filtered Out",
        county_ent_only=True,
        return_filtered_out=True
    )

# https://rss-filter-y4fa.onrender.com/indo_horoscopes.xml
@app.route('/indo_horoscopes.xml')
def indo_horoscopes():
    return process_generic_feed(
        source_url="https://www.independent.ie/entertainment/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Entertainment: Horoscopes",
        horoscopes_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_horoscopes_filterout.xml
@app.route('/indo_horoscopes_filterout.xml')
def indo_horoscopes_filterout():
    return process_generic_feed(
        source_url="https://www.independent.ie/entertainment/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Entertainment: Horoscopes Filtered Out",
        horoscopes_only=True,
        return_filtered_out=True
    )

# https://rss-filter-y4fa.onrender.com/indo_irish_news_ent.xml
@app.route('/indo_irish_news_ent.xml')
def indo_irish_news_ent():
    return process_generic_feed(
        source_url="https://www.independent.ie/entertainment/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Entertainment: Irish News",
        irish_news_ent_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_irish_news_ent_filterout.xml
@app.route('/indo_irish_news_ent_filterout.xml')
def indo_irish_news_ent_filterout():
    return process_generic_feed(
        source_url="https://www.independent.ie/entertainment/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Entertainment: Irish News Filtered Out",
        irish_news_ent_only=True,
        return_filtered_out=True
    )

# https://rss-filter-y4fa.onrender.com/indo_lifestyle_ent.xml
@app.route('/indo_lifestyle_ent.xml')
def indo_lifestyle_ent():
    return process_generic_feed(
        source_url="https://www.independent.ie/entertainment/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Entertainment: Lifestyle",
        lifestyle_ent_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_lifestyle_ent_filterout.xml
@app.route('/indo_lifestyle_ent_filterout.xml')
def indo_lifestyle_ent_filterout():
    return process_generic_feed(
        source_url="https://www.independent.ie/entertainment/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Entertainment: Lifestyle Filtered Out",
        lifestyle_ent_only=True,
        return_filtered_out=True
    )

# https://rss-filter-y4fa.onrender.com/indo_movies.xml
@app.route('/indo_movies.xml')
def indo_movies():
    return process_generic_feed(
        source_url="https://www.independent.ie/entertainment/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Entertainment: Movies",
        movies_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_movies_filterout.xml
@app.route('/indo_movies_filterout.xml')
def indo_movies_filterout():
    return process_generic_feed(
        source_url="https://www.independent.ie/entertainment/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Entertainment: Movies Filtered Out",
        movies_only=True,
        return_filtered_out=True
    )

# https://rss-filter-y4fa.onrender.com/indo_music.xml
@app.route('/indo_music.xml')
def indo_music():
    return process_generic_feed(
        source_url="https://www.independent.ie/entertainment/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Entertainment: Music",
        music_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_music_filterout.xml
@app.route('/indo_music_filterout.xml')
def indo_music_filterout():
    return process_generic_feed(
        source_url="https://www.independent.ie/entertainment/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Entertainment: Music Filtered Out",
        music_only=True,
        return_filtered_out=True
    )

# https://rss-filter-y4fa.onrender.com/indo_radio.xml
@app.route('/indo_radio.xml')
def indo_radio():
    return process_generic_feed(
        source_url="https://www.independent.ie/entertainment/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Entertainment: Radio",
        radio_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_radio_filterout.xml
@app.route('/indo_radio_filterout.xml')
def indo_radio_filterout():
    return process_generic_feed(
        source_url="https://www.independent.ie/entertainment/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Entertainment: Radio Filtered Out",
        radio_only=True,
        return_filtered_out=True
    )

# https://rss-filter-y4fa.onrender.com/indo_television.xml
@app.route('/indo_television.xml')
def indo_television():
    return process_generic_feed(
        source_url="https://www.independent.ie/entertainment/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Entertainment: Television",
        television_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_television_filterout.xml
@app.route('/indo_television_filterout.xml')
def indo_television_filterout():
    return process_generic_feed(
        source_url="https://www.independent.ie/entertainment/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Entertainment: Television Filtered Out",
        television_only=True,
        return_filtered_out=True
    )

# https://rss-filter-y4fa.onrender.com/indo_theatre_arts.xml
@app.route('/indo_theatre_arts.xml')
def indo_theatre_arts():
    return process_generic_feed(
        source_url="https://www.independent.ie/entertainment/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Entertainment: Theatre & Arts",
        theatre_arts_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_theatre_arts_filterout.xml
@app.route('/indo_theatre_arts_filterout.xml')
def indo_theatre_arts_filterout():
    return process_generic_feed(
        source_url="https://www.independent.ie/entertainment/rss",
        regex_pattern=f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}",
        feed_title_override="Indo Entertainment: Theatre & Arts Filtered Out",
        theatre_arts_only=True,
        return_filtered_out=True
    )




########################### Business Insider Feeds

    
# https://rss-filter-y4fa.onrender.com/business_insider.xml
@app.route('/business_insider.xml')
def business_insider():
    BLOCKS = f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}|word1|word2"
    return process_generic_feed(
        "https://feeds.businessinsider.com/custom/all",
        BLOCKS,
        "Business Insider"
    )

# https://rss-filter-y4fa.onrender.com/bi_artificial_intelligence.xml
@app.route('/bi_artificial_intelligence.xml')
def bi_artificial_intelligence():
    BLOCKS = f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}"
    return process_generic_feed(
        source_url="https://feeds.businessinsider.com/custom/all",
        regex_pattern=BLOCKS,
        feed_title_override="BI: Artificial-intelligence",
        bi_ai_only=True
    )

# https://rss-filter-y4fa.onrender.com/bi_careers.xml
@app.route('/bi_careers.xml')
def bi_careers():
    BLOCKS = f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}"
    return process_generic_feed(
        source_url="https://feeds.businessinsider.com/custom/all",
        regex_pattern=BLOCKS,
        feed_title_override="BI: Careers",
        bi_careers_only=True
    )

# https://rss-filter-y4fa.onrender.com/bi_defense.xml
@app.route('/bi_defense.xml')
def bi_defense():
    BLOCKS = f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}"
    return process_generic_feed(
        source_url="https://feeds.businessinsider.com/custom/all",
        regex_pattern=BLOCKS,
        feed_title_override="BI: Defense",
        bi_defense_only=True
    )

# https://rss-filter-y4fa.onrender.com/bi_economy.xml
@app.route('/bi_economy.xml')
def bi_economy():
    BLOCKS = f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}"
    return process_generic_feed(
        source_url="https://feeds.businessinsider.com/custom/all",
        regex_pattern=BLOCKS,
        feed_title_override="BI: Economy",
        bi_economy_only=True
    )

# https://rss-filter-y4fa.onrender.com/bi_entertainment.xml
@app.route('/bi_entertainment.xml')
def bi_entertainment():
    BLOCKS = f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}"
    return process_generic_feed(
        source_url="https://feeds.businessinsider.com/custom/all",
        regex_pattern=BLOCKS,
        feed_title_override="BI: Entertainment",
        bi_entertainment_only=True
    )

# https://rss-filter-y4fa.onrender.com/bi_finance.xml
@app.route('/bi_finance.xml')
def bi_finance():
    BLOCKS = f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}"
    return process_generic_feed(
        source_url="https://feeds.businessinsider.com/custom/all",
        regex_pattern=BLOCKS,
        feed_title_override="BI: Finance",
        bi_finance_only=True
    )

# https://rss-filter-y4fa.onrender.com/bi_health.xml
@app.route('/bi_health.xml')
def bi_health():
    BLOCKS = f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}"
    return process_generic_feed(
        source_url="https://feeds.businessinsider.com/custom/all",
        regex_pattern=BLOCKS,
        feed_title_override="BI: Health",
        bi_health_only=True
    )

# https://rss-filter-y4fa.onrender.com/bi_media.xml
@app.route('/bi_media.xml')
def bi_media():
    BLOCKS = f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}"
    return process_generic_feed(
        source_url="https://feeds.businessinsider.com/custom/all",
        regex_pattern=BLOCKS,
        feed_title_override="BI: Media",
        bi_media_only=True
    )

# https://rss-filter-y4fa.onrender.com/bi_parenting.xml
@app.route('/bi_parenting.xml')
def bi_parenting():
    BLOCKS = f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}"
    return process_generic_feed(
        source_url="https://feeds.businessinsider.com/custom/all",
        regex_pattern=BLOCKS,
        feed_title_override="BI: Parenting",
        bi_parenting_only=True
    )

# https://rss-filter-y4fa.onrender.com/bi_real_estate.xml
@app.route('/bi_real_estate.xml')
def bi_real_estate():
    BLOCKS = f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}"
    return process_generic_feed(
        source_url="https://feeds.businessinsider.com/custom/all",
        regex_pattern=BLOCKS,
        feed_title_override="BI: Real-estate",
        bi_real_estate_only=True
    )

# https://rss-filter-y4fa.onrender.com/bi_retail.xml
@app.route('/bi_retail.xml')
def bi_retail():
    BLOCKS = f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}"
    return process_generic_feed(
        source_url="https://feeds.businessinsider.com/custom/all",
        regex_pattern=BLOCKS,
        feed_title_override="BI: Retail",
        bi_retail_only=True
    )

# https://rss-filter-y4fa.onrender.com/bi_sports.xml
@app.route('/bi_sports.xml')
def bi_sports():
    BLOCKS = f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}"
    return process_generic_feed(
        source_url="https://feeds.businessinsider.com/custom/all",
        regex_pattern=BLOCKS,
        feed_title_override="BI: Sports",
        bi_sports_only=True
    )

# https://rss-filter-y4fa.onrender.com/bi_tech.xml
@app.route('/bi_tech.xml')
def bi_tech():
    BLOCKS = f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}"
    return process_generic_feed(
        source_url="https://feeds.businessinsider.com/custom/all",
        regex_pattern=BLOCKS,
        feed_title_override="BI: Technology",
        bi_tech_only=True
    )

# https://rss-filter-y4fa.onrender.com/bi_transportation.xml
@app.route('/bi_transportation.xml')
def bi_transportation():
    BLOCKS = f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}"
    return process_generic_feed(
        source_url="https://feeds.businessinsider.com/custom/all",
        regex_pattern=BLOCKS,
        feed_title_override="BI: Transportation",
        bi_transportation_only=True
    )

# https://rss-filter-y4fa.onrender.com/bi_travel.xml
@app.route('/bi_travel.xml')
def bi_travel():
    BLOCKS = f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}"
    return process_generic_feed(
        source_url="https://feeds.businessinsider.com/custom/all",
        regex_pattern=BLOCKS,
        feed_title_override="BI: Travel",
        bi_travel_only=True
    )








########################### OTHER FEEDS

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

# https://rss-filter-y4fa.onrender.com/forbes.xml
@app.route('/forbes.xml')
def forbes():
    BLOCKS = f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}|word1|word2"
    return process_generic_feed(
        "https://www.forbes.com/feeds/popstories.xml",
        BLOCKS,
        "Forbes"
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
    
# https://rss-filter-y4fa.onrender.com/wired.xml
@app.route('/wired.xml')
def wired():
    BLOCKS = f"{G_BLOCK_NEGATIVE}|{G_BLOCK_OTHER}|word1|word2"
    return process_generic_feed(
        "https://www.wired.com/feed/rss",
        BLOCKS,
        "Wired"
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
