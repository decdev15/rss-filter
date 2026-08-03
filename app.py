import os
import re
import feedparser
import requests
import time
import sys
import logging
import hashlib
from flask import Flask, Response

app = Flask(__name__)

# =============================================================
# Readme
# =============================================================

# Irish Independent:
# Level 1 feeds are Main, Sport, Business, Entertainment.  Word filters applied here. 
# Level 2 feeds are sub-feeds e.g. Main / County 
# Level 3 feeds are sub-feeds of those e.g. Main / County / Wicklow 

# Feeds that appear in one level should not appear in other levels.



# "Indo Main" and "FI: Indo Main" include all articles except for:
# those containing the block words above;
# links included in this block of code (or similar as will be updated):
    #
    # # --- OVERLAP AVOIDANCE ---
    # if exclude_groups_of_links and url_lower:
    #       if '/sport/' in url_lower or '/entertainment/' in url_lower or '/politics/' in url_lower or '/courts/' in url_lower or '/county/' in url_lower or '/business/' in url_lower or '/world-news/' in url_lower or '/irish-news/' in url_lower or '/weather/' in url_lower:
    #           continue

# TODO Common items that will break this - need alerts for when they happen?
# W_ variables will stop working if "|" at the end of a line
# If xml lines indented, python thinks they are nested, therefore be very careful with indentation 


# =============================================================
# Global variables
# =============================================================

# Word patterns
W_CHARITIES = r"charity|charities|fundraising|fundraisers"
W_LGBQT = r"lesbian|gay|LGBQT|queer|bisexual|trans|transvestite|tranny|pride parade|HIV"

# TEST OUT Football: LOI first 
W_LOI = r"shelbourne|bohemians|league of ireland|LOI|sligo rovers|bohs|shels|youth tournament|dundalk fc|St Patrick’s Athletic|Bray Wanderers|shamrock rovers|stephen bradley"

W_PEOPLE = r"Hitler|Andrew Tate|Tate brothers|Madeleine McCann|Ann Widdecombe|Starmer|Burnham|Selena Gomez|Bieber|Lily Allen|Trump|Tubridy|Conor McGregor|Katie Price|Winkleman|Influencer|Influencers|Blake Lively|Baldoni|Niall Horan|Rhys Mcclenaghan|Adeleke|Luke Littler|Seamus Power|Martin O'Neill|Guardiola|Lewis Hamilton|Lando Norris|Philly McMahon|Putin|Zelensky|Netanyahu|Jong-un|Khamenei|Maduro|Lukashenko|al-Assad|Enoch|Martina Burke" 
W_PLACES = r"Afghan|Afghanistan|Ethiopia|Ethiopian|Gaza|Iran|Iranian|Iraq|Iraqi|israel|israeli|Kiev|Lebanese|Lebanon|Moscow|Palestine|palestinian|Petersburg|Russia|Russian|Syria|Syrian|Ukraine|Ukrainian|Yemen|Yemeni"
W_SCAMS = r"scam|scammed|scammer|scammers|scamming|scams"
W_HOUSING = r"apartments|council houses|council housing|derelict|development|holding|homes|homeless|housing|leaseback|lettings|mortgage|mortgaged|mortgages|on the market|properties|property|renovation|renovations|rentals|renting|residential|retail space|rezoned|rezoning|tenancy|tenant|tenants|tender|unzoned|vacant|zoned"

# TODO These should be words that are always negative in every context, therefore a global block.  e.g. whether in main feed or entertainment feed.  
# Use other blocks where there is ambiguity e.g. "hit" can relate to music or an attack.  
F_ALWAYS_NEGATIVE = (
r"\b("
    r"aaaa|"
    # A
    r"abduct|abducted|abducting|abduction|abductions|abductor|abductors|"
    r"abuse|abused|abuser|abusers|abuses|abusing|abusive|"
    r"adjourned|adjourn|"
    r"anti-social|"
    r"armed|"
    r"arrested|arrests|"
    r"arson|arsonists|arsonist|"
    r"assault|assaulted|assaulting|assaults|"
    r"asylum seekers|"
    # B
    r"balaclava|balaclavas|balaclava-clad|"
    r"bankrupt|bankruptcy|"
    r"bereaved|bereavement|bereavements|"
    r"blackmail|blackmailed|blackmailer|blackmailers|"
    r"bleed|bleeding|bloodshed|bloody|"
    r"body found|body was found|"
    r"bomb|bombed|bomber|bombers|bombing|bombings|bombs|"
    r"boy racer|boy racers|"
    r"bribe|bribery|bribes|bribing|"
    r"burglar|burglaries|burglars|burglary|burgled|break-in|break-ins|"
    r"burial|burials|buried|"
    # C
    r"cancer|cancerous|leukemia|"
    r"carjack|carjacked|carjacking|carjackings|"
    r"catastrophe|catastrophes|catastrophic|"
    r"man charged|woman charged|men charged|women charged|"
    r"co-accused|co-defendant|"
    r"community service|"
    r"confront|confrontation|confronting|"
    r"corrupt|corrupted|corrupting|corruption|corrupts|"
    r"cost-of-living|cost of living|"
    r"crime|crimes|criminal|criminals|"
    r"crisis|crises|"
    r"critical condition|criticism|"
    r"cruelty|"
    r"culprit|culprits|"
    r"curse|cursed|"
    # D
    r"dangerous|dangers|"
    r"deadliest|deadly|"
    r"deathly|in memory|in memorial|"
    r"dementia|"
    r"demise|"
    r"devastate|devastated|devastating|devastation|"
    r"diagnose|diagnosed|diagnoses|diagnosing|diagnosis|"
    r"diarrhoea|"
    r"die|died|dies|dying|"
    r"dire|"
    r"disabled|disability|disabilities|"
    r"drugged|cocaine|heroin|ketamin|overdose|overdosed|overdoses|overdosing|drunk|"
    # E
    r"embezzle|embezzled|embezzlement|"
    r"emergencies|emergency|"
    r"epidemic|epidemics|"
    r"evacuation|evacuate|evacuated|evacuates|"
    r"executor|"
    r"explosives|"
    r"exposed himself|"
    r"extortion|extorted|"
    r"extradite|extradition|"
    r"extremism|extremist|extremists|"
    # F
    r"famine|famines|"
    r"fatal|fatalities|fatality|fatally|"
    r"firearm|firearms|"
    r"flooding|flood|floods|"
    r"fraud|fraudster|fraudsters|fraudulent|fraudulently|frauds|"
    r"fright|frighten|frightening|"
    r"funeral|funerals|"
    # G
    r"gardai investigating|garda investigation|"
    r"grief|grieving|grieve|grieves|grievance|grievances|"
    r"gruesome|"
    r"gunfire|gunman|gunmen|gunshot|gunshots|"
    # H
    r"harm|harmful|harmed|"
    r"hateful|hater|haters|hatred|"
    r"hit-and-run|"
    r"horrific|horrifically|"
    r"horror|horrible|"
    r"hospitalise|hospitalised|hospitalises|hospitalising|hospitalize|hospitalized|hospitalizes|hospitalizing|"
    r"hostage|hostages|"
    r"hunger|"
    # I
    r"illness|ill|"
    r"inmate|inmates|"
    r"insolvent|insolvency|"
    r"intruder|intrude|"
    r"investigation|investigate|investigates|investigator|investigators|"
    # J
    r"jailed|jails|jailing|"
    # K
    r"kidnap|kidnapped|kidnapper|kidnappers|kidnapping|kidnappings|kidnaps|"
    r"kill|killed|killer|killers|killing|killings|kills|"
    r"knife|knives|knifed|"
    r"kkk|ku klux klan|"
    # L
    # M
    r"macabre|"
    r"malpractice|"
    r"manslaughter|"
    r"miserable|miserably|misery|"
    r"missile|missiles|"
    r"missing|missing person|missing persons|last seen|"
    r"mourn|mourned|mourner|mourners|mourning|mourns|"
    r"murder|murdered|murderer|murderers|murdering|murderous|murders|"
    # N
    r"nazi|nazis|"
    # O
    r"offence|offences|offend|offended|offender|offenders|offending|offends|"
    r"ordeal|ordeals|"
    # P
    r"paedophile|paedophiles|paedophilia|pedophile|pedophiles|pedophilia|Epstein|rolf harris|Cosby|house of horrors|savile|"
    r"pandemic|pandemics|"
    r"perjury|"
    r"prison|prisoner|prisoners|prisons|imprisoned|"
    r"protested|protester|protesters|protesting|"
    # R
    r"racism|racist|racists|"
    r"rape|raped|raper|rapes|raping|rapist|rapists|"
    r"reckless|"
    r"remains of boy|remains of girl|remains of man|remains of woman|"
    r"robbers|robbery|robberies|"
    r"rubbish|"
    # S
    r"sadist|sadistic|sadism|"
    r"safeties|unsafe|"
    f"{W_SCAMS}|"
    r"scourge|"
    r"seizure|"
    r"self-harm|self-harming|self-harmed|"
    r"sentences|sentencing|"
    r"sex act|sex acts|"
    r"sewage|"
    r"shock|shocking|"
    r"slapping|slap|slapped|"
    r"spectre|"
    r"sportswashing|"
    r"stab|stabbed|stabber|stabbers|stabbing|stabbings|stabs|"
    r"stardust survivor|stardust survivors|"
    r"starvation|"
    r"steal|stealing|steals|stolen|"
    r"strangling|strangled|strangle|"
    r"struggle|struggled|struggles|struggling|"
    r"subpoena|subpoenas|"
    r"suicidal|suicide|suicides|pieta|darkness into light|"
    r"syndrome|syndromes|"
    # T
    r"terminal|terminally|terminally ill|"
    r"terror|terrorism|terrorist|terrorists|terrorise|terrorised|terrorize|terrorized|"
    r"theft|thefts|thieves|thief|thieving|"
    r"threat|threaten|threatens|"
    r"torture|tortured|tortures|torturing|"
    r"trafficking|trafficked|"
    r"tragedy|tragic|tragically|"
    r"trauma|traumatic|traumatise|traumatising|"
    # U
    r"ugly|"
    r"uninsured|"
    r"unkempt|"
    # V
    r"vandal|vandalise|vandalised|vandalism|vandals|"
    r"vicious|viciously|"
    r"victim|victims|victimised|"
    r"violence|violent|violently|"
    # W
    r"warfare|warship|warships|"
    r"warning|warn|warns|"
    r"weapon|weapons|weaponise|"
    r"wildfire|wildfires|"
    r"woe|woes|"
    r"worrying|worry|"
    r"wrangle|wrangled|"
    r"zzzz"
r")\b"
)

# Business Insider, and Fortune, and Forbes - These are business therefore create new filter for them e.g. remove filters for kill, shot, hates, 


# TODO These should be words that I always want to avoid, in every context, therefore a global block.  e.g. whether in main feed or entertainment feed

F_ALWAYS_AVOID = (
r"\b("
    r"aaaa|"
    r"Around the districts|"
    # Charities
    f"{W_CHARITIES}|"
    r"divorce|divorcee|"
    r"Eurobasket|"
    r"e-scooters|"
    r"fines|levies|"
    r"gridlock|"
    f"{W_HOUSING}|"
    f"inflation|inflationary|"
    # League of Ireland football
    f"{W_LOI}|"
    r"legal|legality|legalities|subpoenas|subpoena|"
    r"lotto|lottery|euromillions|"
    # People: I want to avoid articles about, good or bad
    f"{W_PEOPLE}|"
    # Places
    f"{W_PLACES}|"
    # Politics   
    r"trump|fianna fail|fianna gael|labour party|republican|republicans|democratic|democrats|democracy|autocratic|dictator|dictatorship|politics|politician|politicians|referendum|"
    f"{W_LGBQT}|"
    # Religion
    r"cleric|clerical|clerics|priest|priests|bishop|bishops|cardinal|cardinals|pope|church|churches|religious|religion|parish|archbishop|"
    r"solicitor|solicitors|"
    # Sports
    r"softball|camogie|basketball|"
    r"tax|taxes|"
    r"zzzz"
r")\b"
)

# These are words that I want to filter out from a feed specifically
F_MAIN = (
r"\b("
    r"aaaa|"
    r"apocalyptic|"
    r"dead|death|deaths|"
    r"explosive|"
    r"fighting|"
    r"monster|"
    r"zzzz"
r")\b"
)

# These are words that I want to filter out from a feed specifically
F_SPORT = (
r"\b("
    r"aaaa|"
    r"Cuala GAA|"
    f"{W_LGBQT}|"
    f"{W_LOI}|Celtic|"
    f"{W_PEOPLE}|"
    f"{W_PLACES}|"
    f"rowing|"
    f"tour de france|"
    r"zzzz"
r")\b"
)

# These are words that I want to filter out from a feed specifically
F_ENTERTAINMENT = (
r"\b("
    r"aaaa|"
    r"asylum|"
    r"divorce|divorcee|"
    r"DWTS|dancing with the stars|"
    f"{W_HOUSING}|"
    f"{W_LGBQT}|"
    f"{W_PEOPLE}|"
    f"{W_PLACES}|"
    r"period drama|"
    r"top TV|"
    r"what to watch on tv|"
    r"zzzz"
r")\b"
)

# These are words that I want to filter out from a feed specifically
F_BUSINESS = (
r"\b("
    r"aaaa|"
    r"accumulated profits|"
    r"Budget|Budgets|"
    f"{W_CHARITIES}|"
    f"ECB|Central Bank|"
    f"{W_HOUSING}|"
    f"inflation|inflationary|"
    f"insurer|insurance|"
    f"{W_LGBQT}|"
    f"oil|crude|"
    f"{W_PEOPLE}|"
    f"{W_PLACES}|"
    f"{W_SCAMS}|"
    f"trade war|"
    r"zzzz"
r")\b"
)

# These are words that I want to filter in to a feed specifically

FI_INDO = (
r"\b("
    r"aaaa|"
    r"Liverpool|Roscommon|"
    r"zzzz"
r")\b"
)


FI_BUSINESS_INSIDER = (
r"\b("
    r"aaaa|"
    r"AI|OpenAI|"
    r"zzzz"
r")\b"
)





# =============================================================
# INCLUSIVE FEED CARVE-OUT
# =============================================================
# Any article matching a section's "allow list" (e.g. Liverpool|Roscommon)
# is meant to live ONLY in that section's dedicated *_inclusive.xml feed -
# never in the main "kept" feed, never in the filterout feed, and never in
# any of that section's sub-feeds. This maps each source RSS URL to the
# allow-list pattern used by its *_inclusive route.
INCLUSIVE_PATTERNS = {
    "https://www.independent.ie/rss": f"{FI_INDO}|word1|word2",
    "https://www.independent.ie/sport/rss": f"{FI_INDO}|word1|word2",
    "https://www.independent.ie/entertainment/rss": f"{FI_INDO}|word1|word2",
    "https://www.independent.ie/business/rss": f"{FI_INDO}|word1|word2",  
    "https://feeds.businessinsider.com/custom/all": f"{FI_BUSINESS_INSIDER}|word1|word2", 
}


f"{FI_INDO}|word1|word2"


# =============================================================
# DEBUG HELPER
# =============================================================
def debug_match(title, link, compiled_regex):
    """Prints TITLE, LINK, and MATCH details ONLY when a match occurs."""
    if not compiled_regex:
        return

    title_l = title.lower()
    link_l = link.lower()

    title_match = compiled_regex.search(title_l)
    link_match = compiled_regex.search(link_l)

    # Only print to console if there is at least one match
    if title_match or link_match:
        print("\n================ MATCH FOUND ================")
        print("TITLE:", title)
        print("LINK:", link)
        if title_match:
            print("➡ TITLE MATCH:", title_match.group(0))
        if link_match:
            print("➡ LINK MATCH:", link_match.group(0))
        print("=============================================\n")


# ============================================================= 
# HELPER FUNCTION
# =============================================================

def process_generic_feed(source_url, regex_pattern, feed_title_override, exclude_groups_of_links=False, inclusive=False, 

    # Irish Independent: Main
                        
    comment_only=False, courts_only=False, county_only=False, 
                        
    county_antrim_only=False, county_armagh_only=False, county_carlow_only=False, county_cavan_only=False, county_clare_only=False, 
    county_cork_only=False, county_derry_only=False, county_donegal_only=False, county_down_only=False, county_dublin_only=False, 
    county_fermanagh_only=False, county_galway_only=False, county_kerry_only=False, county_kildare_only=False, county_kilkenny_only=False, 
    county_laois_only=False, county_leitrim_only=False, county_limerick_only=False, county_longford_only=False, county_louth_only=False, 
    county_mayo_only=False, county_meath_only=False, county_monaghan_only=False, county_offaly_only=False, county_roscommon_only=False, 
    county_sligo_only=False, county_tipperary_only=False, county_tyrone_only=False, county_waterford_only=False, county_westmeath_only=False, 
    county_wexford_only=False, county_wicklow_only=False,                        

    farming_only=False, irish_news_only=False,  seachtain_only=False, 
    lifestyle_only=False, podcasts_only=False, politics_only=False, weather_only=False, world_news_only=False, 

    # Irish Independent: Sport 
    
    sport_county_only=False, soccer_only=False, soccer_loi_only=False, gaa_only=False, golf_only=False, 
    sport_irish_news_only=False, other_sports_only=False, sport_podcasts_only=False, 
    rugby_only=False, horse_racing_only=False,

    # Irish Independent: Business
    
    commercial_property_only=False, county_business_only=False, irish_business_only=False, irish_news_business_only=False, 
    money_only=False, technology_only=False, world_only=False, 

    # Irish Independent: Entertainment
    
    books_only=False, celebrity_only=False, comment_ent_only=False, county_ent_only=False, horoscopes_only=False, 
    irish_news_ent_only=False, lifestyle_ent_only=False, music_only=False, movies_only=False, 
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

        # An inclusive-mode call (the *_inclusive.xml routes) IS the allow-list
        # feed, so it should not exclude its own matches. Every other route
        # sharing this source_url excludes them so they only ever appear here.
        inclusive_carveout_pattern = INCLUSIVE_PATTERNS.get(source_url)
        compiled_inclusive_carveout = (
            re.compile(inclusive_carveout_pattern, re.IGNORECASE)
            if (inclusive_carveout_pattern and not inclusive)
            else None
        )

        # --- MAP STRING ENDPOINTS TO ACCURATE VALUE/SLUG PAIRS ---
        main_filters = {
            '/comment/': comment_only,
            '/courts/': courts_only,
            '/county/': county_only,
            
            '/county/antrim/': county_antrim_only,
            '/county/armagh/': county_armagh_only,
            '/county/carlow/': county_carlow_only,
            '/county/cavan/': county_cavan_only,
            '/county/clare/': county_clare_only,
            '/county/cork/': county_cork_only,
            '/county/derry/': county_derry_only,
            '/county/donegal/': county_donegal_only,
            '/county/down/': county_down_only,
            '/county/dublin/': county_dublin_only,
            '/county/fermanagh/': county_fermanagh_only,
            '/county/galway/': county_galway_only,
            '/county/kerry/': county_kerry_only,
            '/county/kildare/': county_kildare_only,
            '/county/kilkenny/': county_kilkenny_only,
            '/county/laois/': county_laois_only,
            '/county/leitrim/': county_leitrim_only,
            '/county/limerick/': county_limerick_only,
            '/county/longford/': county_longford_only,
            '/county/louth/': county_louth_only,
            '/county/mayo/': county_mayo_only,
            '/county/meath/': county_meath_only,
            '/county/monaghan/': county_monaghan_only,
            '/county/offaly/': county_offaly_only,
            '/county/roscommon/': county_roscommon_only,
            '/county/sligo/': county_sligo_only,
            '/county/tipperary/': county_tipperary_only,
            '/county/tyrone/': county_tyrone_only,
            '/county/waterford/': county_waterford_only,
            '/county/westmeath/': county_westmeath_only,
            '/county/wexford/': county_wexford_only,
            '/county/wicklow/': county_wicklow_only,           

            '/farming/': farming_only,  
            '/irish-news/': irish_news_only,
            '/lifestyle/': lifestyle_only,
            '/podcasts/': podcasts_only,
            '/seachtain/': seachtain_only,
            '/politics/': politics_only,
            '/weather/': weather_only,
            '/world-news/': world_news_only
        }

        # The four named counties are a nested layer *inside* the generic '/county/' feed - '/county/' is a substring of '/county/wexford/' etc,
        # so without this, the generic county feed would also show every named-county article. Same pattern as the sport/business/ent
        # sub-channel carve-out below, just one level deeper.
        main_county_L3_filters = {
        
            '/county/antrim/': county_antrim_only,
            '/county/armagh/': county_armagh_only,
            '/county/carlow/': county_carlow_only,
            '/county/cavan/': county_cavan_only,
            '/county/clare/': county_clare_only,
            '/county/cork/': county_cork_only,
            '/county/derry/': county_derry_only,
            '/county/donegal/': county_donegal_only,
            '/county/down/': county_down_only,
            '/county/dublin/': county_dublin_only,
            '/county/fermanagh/': county_fermanagh_only,
            '/county/galway/': county_galway_only,
            '/county/kerry/': county_kerry_only,
            '/county/kildare/': county_kildare_only,
            '/county/kilkenny/': county_kilkenny_only,
            '/county/laois/': county_laois_only,
            '/county/leitrim/': county_leitrim_only,
            '/county/limerick/': county_limerick_only,
            '/county/longford/': county_longford_only,
            '/county/louth/': county_louth_only,
            '/county/mayo/': county_mayo_only,
            '/county/meath/': county_meath_only,
            '/county/monaghan/': county_monaghan_only,
            '/county/offaly/': county_offaly_only,
            '/county/roscommon/': county_roscommon_only,
            '/county/sligo/': county_sligo_only,
            '/county/tipperary/': county_tipperary_only,
            '/county/tyrone/': county_tyrone_only,
            '/county/waterford/': county_waterford_only,
            '/county/westmeath/': county_westmeath_only,
            '/county/wexford/': county_wexford_only,
            '/county/wicklow/': county_wicklow_only
        }

        sport_filters = {
            '/county/': sport_county_only,
            '/soccer/': soccer_only,
            '/soccer/league-of-ireland/': soccer_loi_only,
            '/gaa/': gaa_only,
            '/golf/': golf_only,
            '/irish-news/': sport_irish_news_only,
            '/other-sports/': other_sports_only,
            '/podcasts/': sport_podcasts_only,
            '/rugby/': rugby_only,
            '/horse-racing/': horse_racing_only
        }

        sport_soccer_L3_filters = {
            '/soccer/league-of-ireland/': soccer_loi_only
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

            # --- INCLUSIVE FEED CARVE-OUT ---
            # If this article matches this section's allow-list pattern, it belongs
            # exclusively to the *_inclusive.xml feed - skip it here (main, filterout,
            # and every sub-feed for this section).
            if compiled_inclusive_carveout and (
                compiled_inclusive_carveout.search(title) or compiled_inclusive_carveout.search(url_lower)
            ):
                continue
                
            # --- OVERLAP AVOIDANCE ---
            # Only strip items belonging to a sub-section when we're building the
            # "kept" (main) feed. When we're building the filtered-out feed, we
            # deliberately let sub-section items through so that anything blocked
            # by the regex still shows up in the filterout feed, regardless of
            # which section it belongs to.
            if exclude_groups_of_links and url_lower and not return_filtered_out and not inclusive:
                if any(slug in url_lower for slug in 
                [
                    '/sport/', '/entertainment/', '/business/',    
                    '/comment/', '/courts/', '/county/', 

                    '/county/antrim/', '/county/armagh/', '/county/carlow/', '/county/cavan/', '/county/clare/', '/county/cork/', '/county/derry/', '/county/donegal/', '/county/down/', '/county/dublin/', '/county/fermanagh/', '/county/galway/', '/county/kerry/', '/county/kildare/', '/county/kilkenny/', '/county/laois/', '/county/leitrim/', '/county/limerick/', '/county/longford/', '/county/louth/', '/county/mayo/', '/county/meath/', '/county/monaghan/', '/county/offaly/', '/county/roscommon/', '/county/sligo/', '/county/tipperary/', '/county/tyrone/', '/county/waterford/', '/county/westmeath/', '/county/wexford/', '/county/wicklow/', 

                    '/farming/', '/irish-news/', '/lifestyle/', '/podcasts/', '/seachtain/', 
                    '/politics/', '/weather/', '/world-news/'
                ]):
                    continue  

            # --- MAIN SECTION MODES ---
            if any(is_active and slug not in url_lower for slug, is_active in main_filters.items()):
                continue

            # --- COUNTY SUB-CHANNEL CARVE-OUT (nested inside /county/) ---
            any_county_child_active = any(main_county_L3_filters.values())
            if any_county_child_active:
                # Strict filtering: only keep items matching the active named county
                if any(is_active and slug not in url_lower for slug, is_active in main_county_L3_filters.items()):
                    continue
            elif county_only and not return_filtered_out and not inclusive:
                # Generic /county/ route: strip out articles belonging to one of the
                # four named counties, since they have their own dedicated feeds.
                if any(slug in url_lower for slug in main_county_L3_filters.keys()):
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
                elif not return_filtered_out and not inclusive:
                    # Catch-all strip-out strategy for the main section route:
                    # Skip items if they match ANY of the sub-channels that have their own feeds
                    if any(slug in url_lower for slug in current_map.keys()):
                        continue


            # --- SOCCER SUB-CHANNEL CARVE-OUT (nested inside /soccer/) ---
            any_soccer_l3_active = any(sport_soccer_L3_filters.values())
            if any_soccer_l3_active:
                # Strict filtering: only keep items matching the active soccer sub-channel
                if any(is_active and slug not in url_lower for slug, is_active in sport_soccer_L3_filters.items()):
                    continue
            elif soccer_only and not return_filtered_out and not inclusive:
                # Generic /soccer/ route: strip out League of Ireland articles, since
                # they have their own dedicated feed.
                if any(slug in url_lower for slug in sport_soccer_L3_filters.keys()):
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
                elif not return_filtered_out and not inclusive:
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
            # Use a deterministic hash (not Python's built-in hash(), which is
            # randomised per process) so guids stay stable across restarts/cold-starts -
            # otherwise Render spinning the app down and back up would make every
            # article look "new" again to feed readers.
            title_hash = hashlib.md5(title.encode('utf-8')).hexdigest()
            guid = f"{link}#{title_hash}"

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
    BLOCKS = f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_MAIN}|word1|word2"
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

# https://rss-filter-y4fa.onrender.com/indo_main_filterout_1.xml
@app.route('/indo_main_filterout_1.xml')
def indo_main_filterout_1():
    BLOCKS = f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_MAIN}|word1|word2"
    return process_generic_feed(
        "https://www.independent.ie/rss",
        BLOCKS,
        "Filter Out: Indo Main",
        exclude_groups_of_links=True,
        return_filtered_out=True
    )

# https://rss-filter-y4fa.onrender.com/indo_main_inclusive.xml
@app.route('/indo_main_inclusive.xml')
def indo_main_inclusive():
    ALLOWED = f"{FI_INDO}|word1|word2"
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=ALLOWED,
        feed_title_override="Filter In: Indo Main",
        exclude_groups_of_links=True,
        inclusive=True
    )

# https://rss-filter-y4fa.onrender.com/indo_sport.xml
@app.route('/indo_sport.xml')
def indo_sport():
    BLOCKS = f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_SPORT}"
    return process_generic_feed(
        "https://www.independent.ie/sport/rss",
        BLOCKS,
        "Indo Sport"
    )

# https://rss-filter-y4fa.onrender.com/indo_sport_filterout_1.xml
@app.route('/indo_sport_filterout_1.xml')
def indo_sport_filterout_1():
    BLOCKS = f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_SPORT}"
    return process_generic_feed(
        "https://www.independent.ie/sport/rss",
        BLOCKS,
        "Filter Out: Indo Sport",
        return_filtered_out=True
    )


# https://rss-filter-y4fa.onrender.com/indo_sport_inclusive.xml
@app.route('/indo_sport_inclusive.xml')
def indo_sport_inclusive():
    ALLOWED = f"{FI_INDO}|word1|word2"
    return process_generic_feed(
        "https://www.independent.ie/sport/rss",
        ALLOWED,
        "Filter In: Indo Sport",
        inclusive=True
    )

# https://rss-filter-y4fa.onrender.com/indo_business.xml
@app.route('/indo_business.xml')
def indo_business():
    BLOCKS = f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_BUSINESS}"
    return process_generic_feed(
        "https://www.independent.ie/business/rss",
        BLOCKS,
        "Indo Business"
    )

# https://rss-filter-y4fa.onrender.com/indo_business_filterout_1.xml
@app.route('/indo_business_filterout_1.xml')
def indo_business_filterout_1():
    BLOCKS = f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_BUSINESS}"
    return process_generic_feed(
        "https://www.independent.ie/business/rss",
        BLOCKS,
        "Filter Out: Indo Business",
        return_filtered_out=True
    )
    
# https://rss-filter-y4fa.onrender.com/indo_business_inclusive.xml
@app.route('/indo_business_inclusive.xml')
def indo_business_inclusive():
    ALLOWED = f"{FI_INDO}|word1|word2"
    return process_generic_feed(
        "https://www.independent.ie/business/rss",
        ALLOWED,
        "Filter In: Indo Business",
        inclusive=True
    )
    
# https://rss-filter-y4fa.onrender.com/indo_ent.xml
@app.route('/indo_ent.xml')
def indo_ent():
    BLOCKS = f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_ENTERTAINMENT}"
    return process_generic_feed(
        "https://www.independent.ie/entertainment/rss",
        BLOCKS,
        "Indo Entertainment"
    )

# https://rss-filter-y4fa.onrender.com/indo_ent_filterout_1.xml
@app.route('/indo_ent_filterout_1.xml')
def indo_ent_filterout_1():
    BLOCKS = f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_ENTERTAINMENT}"
    return process_generic_feed(
        "https://www.independent.ie/entertainment/rss",
        BLOCKS,
        "Filter Out: Indo Entertainment",
        return_filtered_out=True
    )


# https://rss-filter-y4fa.onrender.com/indo_ent_inclusive.xml
@app.route('/indo_ent_inclusive.xml')
def indo_ent_inclusive():
    ALLOWED = f"{FI_INDO}|word1|word2"
    return process_generic_feed(
        "https://www.independent.ie/entertainment/rss",
        ALLOWED,
        "Filter In: Indo Entertainment",
        inclusive=True
    )


########################### INDO MAIN SUB-FEEDS

# So each of the three types of feeds — main, filterout, sub-feed — needs its own copy of the filter applied, because each is an independent fetch making an independent decision. Flask doesn't reuse anything computed by /indo_main.xml — it makes a fresh HTTP request to https://www.independent.ie/rss, gets the full raw feed, and starts filtering from scratch. The two routes never share state.

# https://rss-filter-y4fa.onrender.com/indo_comment.xml
@app.route('/indo_comment.xml')
def indo_comment():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_MAIN}",
        feed_title_override="Indo Main: Comment",
        comment_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_courts.xml
@app.route('/indo_courts.xml')
def indo_courts():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_MAIN}",
        feed_title_override="Indo Main: Courts",
        courts_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_county.xml
@app.route('/indo_county.xml')
def indo_county():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_MAIN}",
        feed_title_override="Indo Main: County",
        county_only=True
    )

# LEVEL 3

# https://rss-filter-y4fa.onrender.com/indo_county_antrim.xml
@app.route('/indo_county_antrim.xml')
def indo_county_antrim():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_MAIN}",
        feed_title_override="Indo Main: County: Antrim",
        county_antrim_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_county_armagh.xml
@app.route('/indo_county_armagh.xml')
def indo_county_armagh():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_MAIN}",
        feed_title_override="Indo Main: County: Armagh",
        county_armagh_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_county_carlow.xml
@app.route('/indo_county_carlow.xml')
def indo_county_carlow():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_MAIN}",
        feed_title_override="Indo Main: County: Carlow",
        county_carlow_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_county_cavan.xml
@app.route('/indo_county_cavan.xml')
def indo_county_cavan():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_MAIN}",
        feed_title_override="Indo Main: County: Cavan",
        county_cavan_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_county_clare.xml
@app.route('/indo_county_clare.xml')
def indo_county_clare():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_MAIN}",
        feed_title_override="Indo Main: County: Clare",
        county_clare_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_county_cork.xml
@app.route('/indo_county_cork.xml')
def indo_county_cork():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_MAIN}",
        feed_title_override="Indo Main: County: Cork",
        county_cork_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_county_derry.xml
@app.route('/indo_county_derry.xml')
def indo_county_derry():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_MAIN}",
        feed_title_override="Indo Main: County: Derry",
        county_derry_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_county_donegal.xml
@app.route('/indo_county_donegal.xml')
def indo_county_donegal():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_MAIN}",
        feed_title_override="Indo Main: County: Donegal",
        county_donegal_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_county_down.xml
@app.route('/indo_county_down.xml')
def indo_county_down():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_MAIN}",
        feed_title_override="Indo Main: County: Down",
        county_down_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_county_dublin.xml
@app.route('/indo_county_dublin.xml')
def indo_county_dublin():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_MAIN}",
        feed_title_override="Indo Main: County: Dublin",
        county_dublin_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_county_fermanagh.xml
@app.route('/indo_county_fermanagh.xml')
def indo_county_fermanagh():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_MAIN}",
        feed_title_override="Indo Main: County: Fermanagh",
        county_fermanagh_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_county_galway.xml
@app.route('/indo_county_galway.xml')
def indo_county_galway():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_MAIN}",
        feed_title_override="Indo Main: County: Galway",
        county_galway_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_county_kerry.xml
@app.route('/indo_county_kerry.xml')
def indo_county_kerry():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_MAIN}",
        feed_title_override="Indo Main: County: Kerry",
        county_kerry_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_county_kildare.xml
@app.route('/indo_county_kildare.xml')
def indo_county_kildare():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_MAIN}",
        feed_title_override="Indo Main: County: Kildare",
        county_kildare_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_county_kilkenny.xml
@app.route('/indo_county_kilkenny.xml')
def indo_county_kilkenny():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_MAIN}",
        feed_title_override="Indo Main: County: Kilkenny",
        county_kilkenny_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_county_laois.xml
@app.route('/indo_county_laois.xml')
def indo_county_laois():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_MAIN}",
        feed_title_override="Indo Main: County: Laois",
        county_laois_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_county_leitrim.xml
@app.route('/indo_county_leitrim.xml')
def indo_county_leitrim():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_MAIN}",
        feed_title_override="Indo Main: County: Leitrim",
        county_leitrim_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_county_limerick.xml
@app.route('/indo_county_limerick.xml')
def indo_county_limerick():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_MAIN}",
        feed_title_override="Indo Main: County: Limerick",
        county_limerick_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_county_longford.xml
@app.route('/indo_county_longford.xml')
def indo_county_longford():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_MAIN}",
        feed_title_override="Indo Main: County: Longford",
        county_longford_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_county_louth.xml
@app.route('/indo_county_louth.xml')
def indo_county_louth():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_MAIN}",
        feed_title_override="Indo Main: County: Louth",
        county_louth_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_county_mayo.xml
@app.route('/indo_county_mayo.xml')
def indo_county_mayo():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_MAIN}",
        feed_title_override="Indo Main: County: Mayo",
        county_mayo_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_county_meath.xml
@app.route('/indo_county_meath.xml')
def indo_county_meath():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_MAIN}",
        feed_title_override="Indo Main: County: Meath",
        county_meath_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_county_monaghan.xml
@app.route('/indo_county_monaghan.xml')
def indo_county_monaghan():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_MAIN}",
        feed_title_override="Indo Main: County: Monaghan",
        county_monaghan_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_county_offaly.xml
@app.route('/indo_county_offaly.xml')
def indo_county_offaly():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_MAIN}",
        feed_title_override="Indo Main: County: Offaly",
        county_offaly_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_county_roscommon.xml
@app.route('/indo_county_roscommon.xml')
def indo_county_roscommon():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_MAIN}",
        feed_title_override="Indo Main: County: Roscommon",
        county_roscommon_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_county_sligo.xml
@app.route('/indo_county_sligo.xml')
def indo_county_sligo():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_MAIN}",
        feed_title_override="Indo Main: County: Sligo",
        county_sligo_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_county_tipperary.xml
@app.route('/indo_county_tipperary.xml')
def indo_county_tipperary():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_MAIN}",
        feed_title_override="Indo Main: County: Tipperary",
        county_tipperary_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_county_tyrone.xml
@app.route('/indo_county_tyrone.xml')
def indo_county_tyrone():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_MAIN}",
        feed_title_override="Indo Main: County: Tyrone",
        county_tyrone_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_county_waterford.xml
@app.route('/indo_county_waterford.xml')
def indo_county_waterford():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_MAIN}",
        feed_title_override="Indo Main: County: Waterford",
        county_waterford_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_county_westmeath.xml
@app.route('/indo_county_westmeath.xml')
def indo_county_westmeath():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_MAIN}",
        feed_title_override="Indo Main: County: Westmeath",
        county_westmeath_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_county_wexford.xml
@app.route('/indo_county_wexford.xml')
def indo_county_wexford():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_MAIN}",
        feed_title_override="Indo Main: County: Wexford",
        county_wexford_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_county_wicklow.xml
@app.route('/indo_county_wicklow.xml')
def indo_county_wicklow():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_MAIN}",
        feed_title_override="Indo Main: County: Wicklow",
        county_wicklow_only=True
    )

#  LEVEL 2 AGAIN
# https://rss-filter-y4fa.onrender.com/indo_farming.xml
@app.route('/indo_farming.xml')
def indo_farming():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_MAIN}",
        feed_title_override="Indo Main: Farming",
        farming_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_irish_news.xml
@app.route('/indo_irish_news.xml')
def indo_irish_news():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_MAIN}",
        feed_title_override="Indo Main: Irish News",
        irish_news_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_lifestyle.xml
@app.route('/indo_lifestyle.xml')
def indo_lifestyle():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_MAIN}",
        feed_title_override="Indo Main: Lifestyle",
        lifestyle_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_podcasts.xml
@app.route('/indo_podcasts.xml')
def indo_podcasts():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_MAIN}",
        feed_title_override="Indo Main: Podcasts",
        podcasts_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_seachtain.xml
@app.route('/indo_seachtain.xml')
def indo_seachtain():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_MAIN}",
        feed_title_override="Indo Main: Seachtain",
        seachtain_only=True
    )
    
# https://rss-filter-y4fa.onrender.com/indo_politics.xml
@app.route('/indo_politics.xml')
def indo_politics():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_MAIN}",
        feed_title_override="Indo Main: Politics",
        politics_only=True 
    )

# https://rss-filter-y4fa.onrender.com/indo_weather.xml
@app.route('/indo_weather.xml')
def indo_weather():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_MAIN}",
        feed_title_override="Indo Main: Weather",
        weather_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_world_news.xml
@app.route('/indo_world_news.xml')
def indo_world_news():
    return process_generic_feed(
        source_url="https://www.independent.ie/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_MAIN}",
        feed_title_override="Indo Main: World News",
        world_news_only=True
    )


########################### INDO SPORT SUB-FEEDS

# https://rss-filter-y4fa.onrender.com/indo_sport_county.xml
@app.route('/indo_sport_county.xml')
def indo_sport_county():
    return process_generic_feed(
        source_url="https://www.independent.ie/sport/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_SPORT}",
        feed_title_override="Indo Sport: County",
        sport_county_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_soccer.xml
@app.route('/indo_soccer.xml')
def indo_soccer():
    return process_generic_feed(
        source_url="https://www.independent.ie/sport/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_SPORT}",
        feed_title_override="Indo Sport: Soccer",
        soccer_only=True
    )

# LEVEL 3
# https://rss-filter-y4fa.onrender.com/indo_soccer_loi.xml
@app.route('/indo_soccer_loi.xml')
def indo_soccer_loi():
    return process_generic_feed(
        source_url="https://www.independent.ie/sport/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_SPORT}",
        feed_title_override="Indo Sport: Football: LOI",
        soccer_loi_only=True
    )

#  LEVEL 2 AGAIN
# https://rss-filter-y4fa.onrender.com/indo_gaa.xml
@app.route('/indo_gaa.xml')
def indo_gaa():
    return process_generic_feed(
        source_url="https://www.independent.ie/sport/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_SPORT}",
        feed_title_override="Indo Sport: GAA",
        gaa_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_golf.xml
@app.route('/indo_golf.xml')
def indo_golf():
    return process_generic_feed(
        source_url="https://www.independent.ie/sport/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_SPORT}",
        feed_title_override="Indo Sport: Golf",
        golf_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_sport_irish_news.xml
@app.route('/indo_sport_irish_news.xml')
def indo_sport_irish_news():
    return process_generic_feed(
        source_url="https://www.independent.ie/sport/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_SPORT}",
        feed_title_override="Indo Sport: Irish News",
        sport_irish_news_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_other_sports.xml
@app.route('/indo_other_sports.xml')
def indo_other_sports():
    return process_generic_feed(
        source_url="https://www.independent.ie/sport/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_SPORT}",
        feed_title_override="Indo Sport: Other Sports",
        other_sports_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_sports_podcasts.xml
@app.route('/indo_sports_podcasts.xml')
def indo_sports_podcasts():
    return process_generic_feed(
        source_url="https://www.independent.ie/sport/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_SPORT}",
        feed_title_override="Indo Sport: Podcasts",
        sport_podcasts_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_rugby.xml
@app.route('/indo_rugby.xml')
def indo_rugby():
    return process_generic_feed(
        source_url="https://www.independent.ie/sport/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_SPORT}",
        feed_title_override="Indo Sport: Rugby",
        rugby_only=True
    )
    
# https://rss-filter-y4fa.onrender.com/indo_horse_racing.xml
@app.route('/indo_horse_racing.xml')
def indo_horse_racing():
    return process_generic_feed(
        source_url="https://www.independent.ie/sport/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_SPORT}",
        feed_title_override="Indo Sport: Horse Racing",
        horse_racing_only=True
    )


########################### INDO BUSINESS SUB-FEEDS

# https://rss-filter-y4fa.onrender.com/indo_commercial_property.xml
@app.route('/indo_commercial_property.xml')
def indo_commercial_property():
    return process_generic_feed(
        source_url="https://www.independent.ie/business/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_BUSINESS}",
        feed_title_override="Indo Business: Commercial Property",
        commercial_property_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_county_business.xml
@app.route('/indo_county_business.xml')
def indo_county_business():
    return process_generic_feed(
        source_url="https://www.independent.ie/business/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_BUSINESS}",
        feed_title_override="Indo Business: County",
        county_business_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_irish_business.xml
@app.route('/indo_irish_business.xml')
def indo_irish_business():
    return process_generic_feed(
        source_url="https://www.independent.ie/business/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_BUSINESS}",
        feed_title_override="Indo Business: Irish",
        irish_business_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_irish_news_business.xml
@app.route('/indo_irish_news_business.xml')
def indo_irish_news_business():
    return process_generic_feed(
        source_url="https://www.independent.ie/business/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_BUSINESS}",
        feed_title_override="Indo Business: Irish News",
        irish_news_business_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_money.xml
@app.route('/indo_money.xml')
def indo_money():
    return process_generic_feed(
        source_url="https://www.independent.ie/business/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_BUSINESS}",
        feed_title_override="Indo Business: Money",
        money_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_technology.xml
@app.route('/indo_technology.xml')
def indo_technology():
    return process_generic_feed(
        source_url="https://www.independent.ie/business/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_BUSINESS}",
        feed_title_override="Indo Business: Technology",
        technology_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_world_business.xml
@app.route('/indo_world_business.xml')
def indo_world_business():
    return process_generic_feed(
        source_url="https://www.independent.ie/business/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_BUSINESS}",
        feed_title_override="Indo Business: World",
        world_only=True
    )


########################### INDO ENTERTAINMENT SUB-FEEDS

# https://rss-filter-y4fa.onrender.com/indo_books.xml
@app.route('/indo_books.xml')
def indo_books():
    return process_generic_feed(
        source_url="https://www.independent.ie/entertainment/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_ENTERTAINMENT}",
        feed_title_override="Indo Entertainment: Books",
        books_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_celebrity.xml
@app.route('/indo_celebrity.xml')
def indo_celebrity():
    return process_generic_feed(
        source_url="https://www.independent.ie/entertainment/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_ENTERTAINMENT}",
        feed_title_override="Indo Entertainment: Celebrity",
        celebrity_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_comment_ent.xml
@app.route('/indo_comment_ent.xml')
def indo_comment_ent():
    return process_generic_feed(
        source_url="https://www.independent.ie/entertainment/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_ENTERTAINMENT}",
        feed_title_override="Indo Entertainment: Comment",
        comment_ent_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_county_ent.xml
@app.route('/indo_county_ent.xml')
def indo_county_ent():
    return process_generic_feed(
        source_url="https://www.independent.ie/entertainment/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_ENTERTAINMENT}",
        feed_title_override="Indo Entertainment: County",
        county_ent_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_horoscopes.xml
@app.route('/indo_horoscopes.xml')
def indo_horoscopes():
    return process_generic_feed(
        source_url="https://www.independent.ie/entertainment/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_ENTERTAINMENT}",
        feed_title_override="Indo Entertainment: Horoscopes",
        horoscopes_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_irish_news_ent.xml
@app.route('/indo_irish_news_ent.xml')
def indo_irish_news_ent():
    return process_generic_feed(
        source_url="https://www.independent.ie/entertainment/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_ENTERTAINMENT}",
        feed_title_override="Indo Entertainment: Irish News",
        irish_news_ent_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_lifestyle_ent.xml
@app.route('/indo_lifestyle_ent.xml')
def indo_lifestyle_ent():
    return process_generic_feed(
        source_url="https://www.independent.ie/entertainment/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_ENTERTAINMENT}",
        feed_title_override="Indo Entertainment: Lifestyle",
        lifestyle_ent_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_movies.xml
@app.route('/indo_movies.xml')
def indo_movies():
    return process_generic_feed(
        source_url="https://www.independent.ie/entertainment/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_ENTERTAINMENT}",
        feed_title_override="Indo Entertainment: Movies",
        movies_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_music.xml
@app.route('/indo_music.xml')
def indo_music():
    return process_generic_feed(
        source_url="https://www.independent.ie/entertainment/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_ENTERTAINMENT}",
        feed_title_override="Indo Entertainment: Music",
        music_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_television.xml
@app.route('/indo_television.xml')
def indo_television():
    return process_generic_feed(
        source_url="https://www.independent.ie/entertainment/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_ENTERTAINMENT}",
        feed_title_override="Indo Entertainment: Television",
        television_only=True
    )

# https://rss-filter-y4fa.onrender.com/indo_theatre_arts.xml
@app.route('/indo_theatre_arts.xml')
def indo_theatre_arts():
    return process_generic_feed(
        source_url="https://www.independent.ie/entertainment/rss",
        regex_pattern=f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_ENTERTAINMENT}",
        feed_title_override="Indo Entertainment: Theatre & Arts",
        theatre_arts_only=True
    )



########################### Business Insider Feeds

    
# https://rss-filter-y4fa.onrender.com/business_insider.xml
@app.route('/business_insider.xml')
def business_insider():
    BLOCKS = f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_BUSINESS}|word1|word2"
    return process_generic_feed(
        "https://feeds.businessinsider.com/custom/all",
        BLOCKS,
        "Business Insider"
    )

# https://rss-filter-y4fa.onrender.com/business_insider_filterout.xml
@app.route('/business_insider_filterout.xml')
def business_insider_filterout():
    BLOCKS = f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_BUSINESS}|word1|word2"
    return process_generic_feed(
        "https://feeds.businessinsider.com/custom/all",
        BLOCKS,
        "Filter Out: Business Insider",
        return_filtered_out=True
    )


# https://rss-filter-y4fa.onrender.com/business_insider_inclusive.xml
@app.route('/business_insider_inclusive.xml')
def business_insider_inclusive():
    ALLOWED = f"{FI_BUSINESS_INSIDER}|word1|word2"
    return process_generic_feed(
        source_url="https://feeds.businessinsider.com/custom/all",
        regex_pattern=ALLOWED,
        feed_title_override="Filter In: Business Insider",
        exclude_groups_of_links=True,
        inclusive=True
    )

# https://rss-filter-y4fa.onrender.com/bi_artificial_intelligence.xml
@app.route('/bi_artificial_intelligence.xml')
def bi_artificial_intelligence():
    BLOCKS = f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_BUSINESS}|word1|word2"
    return process_generic_feed(
        source_url="https://feeds.businessinsider.com/custom/all",
        regex_pattern=BLOCKS,
        feed_title_override="BI: Artificial-intelligence",
        bi_ai_only=True
    )

# https://rss-filter-y4fa.onrender.com/bi_careers.xml
@app.route('/bi_careers.xml')
def bi_careers():
    BLOCKS = f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_BUSINESS}|word1|word2"
    return process_generic_feed(
        source_url="https://feeds.businessinsider.com/custom/all",
        regex_pattern=BLOCKS,
        feed_title_override="BI: Careers",
        bi_careers_only=True
    )

# https://rss-filter-y4fa.onrender.com/bi_defense.xml
@app.route('/bi_defense.xml')
def bi_defense():
    BLOCKS = f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_BUSINESS}|word1|word2"
    return process_generic_feed(
        source_url="https://feeds.businessinsider.com/custom/all",
        regex_pattern=BLOCKS,
        feed_title_override="BI: Defense",
        bi_defense_only=True
    )

# https://rss-filter-y4fa.onrender.com/bi_economy.xml
@app.route('/bi_economy.xml')
def bi_economy():
    BLOCKS = f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_BUSINESS}|word1|word2"
    return process_generic_feed(
        source_url="https://feeds.businessinsider.com/custom/all",
        regex_pattern=BLOCKS,
        feed_title_override="BI: Economy",
        bi_economy_only=True
    )

# https://rss-filter-y4fa.onrender.com/bi_entertainment.xml
@app.route('/bi_entertainment.xml')
def bi_entertainment():
    BLOCKS = f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_BUSINESS}|word1|word2"
    return process_generic_feed(
        source_url="https://feeds.businessinsider.com/custom/all",
        regex_pattern=BLOCKS,
        feed_title_override="BI: Entertainment",
        bi_entertainment_only=True
    )

# https://rss-filter-y4fa.onrender.com/bi_finance.xml
@app.route('/bi_finance.xml')
def bi_finance():
    BLOCKS = f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_BUSINESS}|word1|word2"
    return process_generic_feed(
        source_url="https://feeds.businessinsider.com/custom/all",
        regex_pattern=BLOCKS,
        feed_title_override="BI: Finance",
        bi_finance_only=True
    )

# https://rss-filter-y4fa.onrender.com/bi_health.xml
@app.route('/bi_health.xml')
def bi_health():
    BLOCKS = f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_BUSINESS}|word1|word2"
    return process_generic_feed(
        source_url="https://feeds.businessinsider.com/custom/all",
        regex_pattern=BLOCKS,
        feed_title_override="BI: Health",
        bi_health_only=True
    )

# https://rss-filter-y4fa.onrender.com/bi_media.xml
@app.route('/bi_media.xml')
def bi_media():
    BLOCKS = f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_BUSINESS}|word1|word2"
    return process_generic_feed(
        source_url="https://feeds.businessinsider.com/custom/all",
        regex_pattern=BLOCKS,
        feed_title_override="BI: Media",
        bi_media_only=True
    )

# https://rss-filter-y4fa.onrender.com/bi_parenting.xml
@app.route('/bi_parenting.xml')
def bi_parenting():
    BLOCKS = f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_BUSINESS}|word1|word2"
    return process_generic_feed(
        source_url="https://feeds.businessinsider.com/custom/all",
        regex_pattern=BLOCKS,
        feed_title_override="BI: Parenting",
        bi_parenting_only=True
    )

# https://rss-filter-y4fa.onrender.com/bi_real_estate.xml
@app.route('/bi_real_estate.xml')
def bi_real_estate():
    BLOCKS = f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_BUSINESS}|word1|word2"
    return process_generic_feed(
        source_url="https://feeds.businessinsider.com/custom/all",
        regex_pattern=BLOCKS,
        feed_title_override="BI: Real-estate",
        bi_real_estate_only=True
    )

# https://rss-filter-y4fa.onrender.com/bi_retail.xml
@app.route('/bi_retail.xml')
def bi_retail():
    BLOCKS = f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_BUSINESS}|word1|word2"
    return process_generic_feed(
        source_url="https://feeds.businessinsider.com/custom/all",
        regex_pattern=BLOCKS,
        feed_title_override="BI: Retail",
        bi_retail_only=True
    )

# https://rss-filter-y4fa.onrender.com/bi_sports.xml
@app.route('/bi_sports.xml')
def bi_sports():
    BLOCKS = f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_BUSINESS}|word1|word2"
    return process_generic_feed(
        source_url="https://feeds.businessinsider.com/custom/all",
        regex_pattern=BLOCKS,
        feed_title_override="BI: Sports",
        bi_sports_only=True
    )

# https://rss-filter-y4fa.onrender.com/bi_tech.xml
@app.route('/bi_tech.xml')
def bi_tech():
    BLOCKS = f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_BUSINESS}|word1|word2"
    return process_generic_feed(
        source_url="https://feeds.businessinsider.com/custom/all",
        regex_pattern=BLOCKS,
        feed_title_override="BI: Technology",
        bi_tech_only=True
    )

# https://rss-filter-y4fa.onrender.com/bi_transportation.xml
@app.route('/bi_transportation.xml')
def bi_transportation():
    BLOCKS = f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_BUSINESS}|word1|word2"
    return process_generic_feed(
        source_url="https://feeds.businessinsider.com/custom/all",
        regex_pattern=BLOCKS,
        feed_title_override="BI: Transportation",
        bi_transportation_only=True
    )

# https://rss-filter-y4fa.onrender.com/bi_travel.xml
@app.route('/bi_travel.xml')
def bi_travel():
    BLOCKS = f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|{F_BUSINESS}|word1|word2"
    return process_generic_feed(
        source_url="https://feeds.businessinsider.com/custom/all",
        regex_pattern=BLOCKS,
        feed_title_override="BI: Travel",
        bi_travel_only=True
    )




########################### OTHER FEEDS

# https://rss-filter-y4fa.onrender.com/forbes.xml
@app.route('/forbes.xml')
def forbes():
    BLOCKS = f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|word1|word2"
    return process_generic_feed(
        "https://www.forbes.com/feeds/popstories.xml",
        BLOCKS,
        "Forbes"
    )

# https://rss-filter-y4fa.onrender.com/forbes_filterout.xml
@app.route('/forbes_filterout.xml')
def forbes_filterout():
    BLOCKS = f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|word1|word2"
    return process_generic_feed(
        "https://www.forbes.com/feeds/popstories.xml",
        BLOCKS,
        "Filter Out: Forbes",
        return_filtered_out=True
    )

# https://rss-filter-y4fa.onrender.com/fortune.xml
@app.route('/fortune.xml')
def fortune():
    BLOCKS = f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|word1|word2"
    return process_generic_feed(
        "https://fortune.com/rss",
        BLOCKS,
        "Fortune"
    )

# https://rss-filter-y4fa.onrender.com/fortune_filterout.xml
@app.route('/fortune_filterout.xml')
def fortune_filterout():
    BLOCKS = f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|word1|word2"
    return process_generic_feed(
        "https://fortune.com/rss",
        BLOCKS,
        "Filter Out: Fortune",
        return_filtered_out=True
    )
    
# https://rss-filter-y4fa.onrender.com/nyt_soccer.xml
@app.route('/nyt_soccer.xml')
def nyt_soccer():
    BLOCKS = f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|word1|word2"
    return process_generic_feed(
        "https://rss.nytimes.com/services/xml/rss/nyt/Soccer.xml",
        BLOCKS,
        "NYT Soccer"
    )

# https://rss-filter-y4fa.onrender.com/nyt_soccer_filterout.xml
@app.route('/nyt_soccer_filterout.xml')
def nyt_soccer_filterout():
    BLOCKS = f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|word1|word2"
    return process_generic_feed(
        "https://rss.nytimes.com/services/xml/rss/nyt/Soccer.xml",
        BLOCKS,
        "Filter Out: NYT Soccer",
        return_filtered_out=True
    )
    
# https://rss-filter-y4fa.onrender.com/wired.xml
@app.route('/wired.xml')
def wired():
    BLOCKS = f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|word1|word2"
    return process_generic_feed(
        "https://www.wired.com/feed/rss",
        BLOCKS,
        "Wired"
    )

# https://rss-filter-y4fa.onrender.com/wired_filterout.xml
@app.route('/wired_filterout.xml')
def wired_filterout():
    BLOCKS = f"{F_ALWAYS_NEGATIVE}|{F_ALWAYS_AVOID}|word1|word2"
    return process_generic_feed(
        "https://www.wired.com/feed/rss",
        BLOCKS,
        "Filter Out: Wired",
        return_filtered_out=True
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
    
