import os
import random

from config import SERVER_ID

# Server flag emojis
SERVER_FLAGS = {
    'us1': '🇺🇸 US1', 'us2': '🇺🇸 US2', 'us3': '🇺🇸 US3',
    'nl': '🇳🇱 NL', 'neth': '🇳🇱 NETH',
    'sg': '🇸🇬 SG', 'jp': '🇯🇵 JP',
    'de': '🇩🇪 DE', 'uk': '🇬🇧 UK', 'fr': '🇫🇷 FR',
    'id': '🇮🇩 ID', 'in': '🇮🇳 IN', 'au': '🇦🇺 AU',
    'co': '🌐 BOT',
}
SERVER_DISPLAY = SERVER_FLAGS.get(SERVER_ID, f'🌐 {SERVER_ID.upper()}')
CMD_NAME = SERVER_ID

PROXY_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "proxies.json")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Browser Profiles — TLS + UA always matched
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Each entry maps a curl_cffi TLS profile to its compatible User-Agent strings.
# This ensures the TLS fingerprint (JA3/JA4) matches the UA being sent.
BROWSER_PROFILES = [
    # ── Chrome 136 (latest stable, March 2026) ──
    {"tls": "chrome136", "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"},
    {"tls": "chrome136", "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"},
    {"tls": "chrome136", "ua": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"},
    # ── Chrome 134 ──
    {"tls": "chrome133a", "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"},
    {"tls": "chrome133a", "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"},
    {"tls": "chrome133a", "ua": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"},
    # ── Chrome 133 ──
    {"tls": "chrome133a", "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"},
    {"tls": "chrome133a", "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"},
    # ── Chrome 131 (still common) ──
    {"tls": "chrome131", "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"},
    {"tls": "chrome131", "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"},
    # ── Edge 136 (latest, Chromium-based) ──
    {"tls": "chrome136", "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0"},
    {"tls": "chrome136", "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0"},
    # ── Edge 134 ──
    {"tls": "chrome133a", "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0"},
    {"tls": "chrome133a", "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0"},
    # ── Firefox 137 (latest stable) ──
    {"tls": "firefox135", "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) Gecko/20100101 Firefox/137.0"},
    {"tls": "firefox135", "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:137.0) Gecko/20100101 Firefox/137.0"},
    {"tls": "firefox135", "ua": "Mozilla/5.0 (X11; Linux x86_64; rv:137.0) Gecko/20100101 Firefox/137.0"},
    # ── Firefox 135 ──
    {"tls": "firefox135", "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:135.0) Gecko/20100101 Firefox/135.0"},
    {"tls": "firefox135", "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:135.0) Gecko/20100101 Firefox/135.0"},
    {"tls": "firefox135", "ua": "Mozilla/5.0 (X11; Linux x86_64; rv:135.0) Gecko/20100101 Firefox/135.0"},
    # ── Safari 18.3 (macOS Sequoia, latest) ──
    {"tls": "safari18_0", "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.3 Safari/605.1.15"},
    {"tls": "safari18_0", "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.3 Safari/605.1.15"},
    # ── Safari 18.1 ──
    {"tls": "safari18_0", "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15"},
    {"tls": "safari18_0", "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15"},
    # ── Opera 117 (latest, Chrome 136 based) ──
    {"tls": "chrome136", "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 OPR/117.0.0.0"},
    {"tls": "chrome133a", "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 OPR/116.0.0.0"},
    {"tls": "chrome131", "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 OPR/116.0.0.0"},
]

# Derived lists for backward compatibility
USER_AGENTS = [p["ua"] for p in BROWSER_PROFILES]
TLS_PROFILES = list(set(p["tls"] for p in BROWSER_PROFILES))

# Stripe.js version patterns
STRIPE_JS_VERSIONS = [
    "v3", "v3.1", "v3.2", "v3.3", "v3.4", "v3.5",
]


def get_random_browser_profile() -> dict:
    """Pick a random browser profile with matched TLS + UA.
    Returns dict with 'tls' and 'ua' keys."""
    return random.choice(BROWSER_PROFILES)

# Pool of realistic billing addresses organized by country code
BILLING_ADDRESSES_BY_COUNTRY = {
    "US": [
        {"name": "James Wilson", "line1": "742 Evergreen Terrace", "city": "Springfield", "state": "IL", "zip": "62704"},
        {"name": "Sarah Johnson", "line1": "1520 Oak Street", "city": "San Francisco", "state": "CA", "zip": "94117"},
        {"name": "Michael Brown", "line1": "308 Meadow Lane", "city": "Austin", "state": "TX", "zip": "78701"},
        {"name": "Emily Davis", "line1": "2145 Birch Drive", "city": "Denver", "state": "CO", "zip": "80202"},
        {"name": "Robert Martinez", "line1": "987 Pine Avenue", "city": "Miami", "state": "FL", "zip": "33101"},
        {"name": "Jessica Taylor", "line1": "1100 Maple Road", "city": "Seattle", "state": "WA", "zip": "98101"},
        {"name": "David Anderson", "line1": "456 Cedar Boulevard", "city": "Portland", "state": "OR", "zip": "97201"},
        {"name": "Ashley Thomas", "line1": "2301 Elm Street", "city": "Chicago", "state": "IL", "zip": "60601"},
        {"name": "Christopher Lee", "line1": "789 Walnut Court", "city": "Boston", "state": "MA", "zip": "02101"},
        {"name": "Amanda White", "line1": "1435 Spruce Way", "city": "Nashville", "state": "TN", "zip": "37201"},
        {"name": "Daniel Harris", "line1": "562 Willow Lane", "city": "Phoenix", "state": "AZ", "zip": "85001"},
        {"name": "Stephanie Clark", "line1": "3200 Ash Drive", "city": "Las Vegas", "state": "NV", "zip": "89101"},
        {"name": "Matthew Lewis", "line1": "871 Poplar Street", "city": "Atlanta", "state": "GA", "zip": "30301"},
        {"name": "Jennifer Robinson", "line1": "1028 Magnolia Ave", "city": "Charlotte", "state": "NC", "zip": "28201"},
        {"name": "Andrew Walker", "line1": "445 Hickory Road", "city": "Minneapolis", "state": "MN", "zip": "55401"},
        {"name": "Lauren Hall", "line1": "1567 Chestnut Blvd", "city": "San Diego", "state": "CA", "zip": "92101"},
        {"name": "Joshua Allen", "line1": "2890 Sycamore Dr", "city": "Dallas", "state": "TX", "zip": "75201"},
        {"name": "Megan Young", "line1": "634 Dogwood Lane", "city": "Philadelphia", "state": "PA", "zip": "19101"},
        {"name": "Ryan King", "line1": "1750 Juniper Street", "city": "Columbus", "state": "OH", "zip": "43201"},
        {"name": "Brittany Wright", "line1": "903 Redwood Ave", "city": "San Antonio", "state": "TX", "zip": "78201"},
        {"name": "Tyler Scott", "line1": "2475 Magnolia Street", "city": "New Orleans", "state": "LA", "zip": "70112"},
        {"name": "Madison Green", "line1": "1890 River Road", "city": "Detroit", "state": "MI", "zip": "48201"},
        {"name": "Brandon Adams", "line1": "3421 Sunset Boulevard", "city": "Los Angeles", "state": "CA", "zip": "90028"},
        {"name": "Kayla Baker", "line1": "5678 Hillcrest Avenue", "city": "Salt Lake City", "state": "UT", "zip": "84101"},
        {"name": "Justin Nelson", "line1": "1234 Peachtree Street", "city": "Atlanta", "state": "GA", "zip": "30309"},
        {"name": "Rachel Carter", "line1": "8765 Lake Shore Drive", "city": "Milwaukee", "state": "WI", "zip": "53202"},
        {"name": "Dylan Mitchell", "line1": "4321 Central Avenue", "city": "Albuquerque", "state": "NM", "zip": "87102"},
        {"name": "Alexis Perez", "line1": "9876 Beach Boulevard", "city": "Honolulu", "state": "HI", "zip": "96815"},
        {"name": "Jordan Turner", "line1": "6543 Market Street", "city": "St. Louis", "state": "MO", "zip": "63101"},
        {"name": "Samantha Phillips", "line1": "2109 Broad Street", "city": "Richmond", "state": "VA", "zip": "23219"},
        {"name": "Cody Campbell", "line1": "7531 Forest Lane", "city": "Kansas City", "state": "MO", "zip": "64105"},
        {"name": "Victoria Parker", "line1": "1593 Main Street", "city": "Hartford", "state": "CT", "zip": "06103"},
        {"name": "Ethan Evans", "line1": "3579 University Avenue", "city": "Madison", "state": "WI", "zip": "53703"},
        {"name": "Olivia Edwards", "line1": "4862 Capitol Drive", "city": "Tallahassee", "state": "FL", "zip": "32301"},
    ],
    "GB": [
        {"name": "Oliver Smith", "line1": "42 Baker Street", "city": "London", "state": "England", "zip": "W1U 7EU"},
        {"name": "Charlotte Davies", "line1": "15 Victoria Road", "city": "Manchester", "state": "England", "zip": "M1 1AA"},
        {"name": "George Wilson", "line1": "78 Queen Street", "city": "Edinburgh", "state": "Scotland", "zip": "EH2 1JX"},
        {"name": "Emily Taylor", "line1": "23 Castle Road", "city": "Birmingham", "state": "England", "zip": "B1 1BB"},
        {"name": "Harry Brown", "line1": "9 Park Lane", "city": "Bristol", "state": "England", "zip": "BS1 5AH"},
        {"name": "Amelia Clarke", "line1": "45 High Street", "city": "Leeds", "state": "England", "zip": "LS1 4HR"},
        {"name": "Jack Thompson", "line1": "12 George Square", "city": "Glasgow", "state": "Scotland", "zip": "G2 1DY"},
        {"name": "Sophie Walker", "line1": "89 King Street", "city": "Liverpool", "state": "England", "zip": "L1 1HA"},
        {"name": "William White", "line1": "34 Royal Crescent", "city": "Bath", "state": "England", "zip": "BA1 2LX"},
        {"name": "Isabella Green", "line1": "67 Castle Street", "city": "Cardiff", "state": "Wales", "zip": "CF10 1BZ"},
        {"name": "Thomas Hall", "line1": "21 St Giles'", "city": "Oxford", "state": "England", "zip": "OX1 3PT"},
        {"name": "Olivia Lewis", "line1": "56 Trinity Street", "city": "Cambridge", "state": "England", "zip": "CB2 1TJ"},
        {"name": "James Young", "line1": "78 Princes Street", "city": "Belfast", "state": "Northern Ireland", "zip": "BT1 6EQ"},
        {"name": "Ava King", "line1": "14 The Shambles", "city": "York", "state": "England", "zip": "YO1 7LZ"},
        {"name": "Noah Wright", "line1": "33 Market Place", "city": "Nottingham", "state": "England", "zip": "NG1 6JB"},
    ],
    "CA": [
        {"name": "Liam Thompson", "line1": "450 Yonge Street", "city": "Toronto", "state": "ON", "zip": "M5B 1T8"},
        {"name": "Sophie Martin", "line1": "1200 Rue Sainte-Catherine", "city": "Montreal", "state": "QC", "zip": "H3B 1K1"},
        {"name": "Ethan Wilson", "line1": "800 Robson Street", "city": "Vancouver", "state": "BC", "zip": "V6Z 3B7"},
        {"name": "Olivia Brown", "line1": "320 Portage Avenue", "city": "Winnipeg", "state": "MB", "zip": "R3C 0C4"},
        {"name": "Noah Davis", "line1": "156 Sparks Street", "city": "Ottawa", "state": "ON", "zip": "K1P 5B9"},
        {"name": "Emma Tremblay", "line1": "650 Boulevard René-Lévesque", "city": "Quebec City", "state": "QC", "zip": "G1R 2A4"},
        {"name": "Lucas Anderson", "line1": "101 8th Avenue SW", "city": "Calgary", "state": "AB", "zip": "T2P 1B4"},
        {"name": "Chloe Johnson", "line1": "220 4th Avenue", "city": "Saskatoon", "state": "SK", "zip": "S7K 0H9"},
        {"name": "Benjamin Lee", "line1": "1090 West Georgia Street", "city": "Vancouver", "state": "BC", "zip": "V6E 3V7"},
        {"name": "Ava Gagnon", "line1": "505 Boulevard de Maisonneuve", "city": "Montreal", "state": "QC", "zip": "H3A 3C2"},
        {"name": "William Clark", "line1": "155 Wellington Street", "city": "London", "state": "ON", "zip": "N6A 3N9"},
        {"name": "Charlotte Roy", "line1": "310 Place Royale", "city": "Quebec City", "state": "QC", "zip": "G1K 4A7"},
        {"name": "Oliver Scott", "line1": "10020 101A Avenue", "city": "Edmonton", "state": "AB", "zip": "T5J 3G2"},
        {"name": "Mia Lefebvre", "line1": "450 Rue Saint-Antoine", "city": "Montreal", "state": "QC", "zip": "H2Y 1X5"},
        {"name": "James Miller", "line1": "200 King Street West", "city": "Toronto", "state": "ON", "zip": "M5H 3T4"},
    ],
    "AU": [
        {"name": "Jack Mitchell", "line1": "120 Collins Street", "city": "Melbourne", "state": "VIC", "zip": "3000"},
        {"name": "Mia Johnson", "line1": "88 George Street", "city": "Sydney", "state": "NSW", "zip": "2000"},
        {"name": "William Taylor", "line1": "45 Adelaide Street", "city": "Brisbane", "state": "QLD", "zip": "4000"},
        {"name": "Ella Brown", "line1": "200 Murray Street", "city": "Perth", "state": "WA", "zip": "6000"},
        {"name": "Oliver Wilson", "line1": "25 Martin Place", "city": "Sydney", "state": "NSW", "zip": "2000"},
        {"name": "Charlotte Anderson", "line1": "150 Lonsdale Street", "city": "Melbourne", "state": "VIC", "zip": "3000"},
        {"name": "Noah Thompson", "line1": "77 St Georges Terrace", "city": "Perth", "state": "WA", "zip": "6000"},
        {"name": "Ava White", "line1": "300 Queen Street", "city": "Brisbane", "state": "QLD", "zip": "4000"},
        {"name": "Liam Davis", "line1": "45 North Terrace", "city": "Adelaide", "state": "SA", "zip": "5000"},
        {"name": "Sophie Martin", "line1": "2 Elizabeth Street", "city": "Hobart", "state": "TAS", "zip": "7000"},
        {"name": "Benjamin Jones", "line1": "66 Smith Street", "city": "Darwin", "state": "NT", "zip": "0800"},
        {"name": "Emma Garcia", "line1": "100 Bunda Street", "city": "Canberra", "state": "ACT", "zip": "2601"},
        {"name": "Lucas Rodriguez", "line1": "50 Crown Street", "city": "Wollongong", "state": "NSW", "zip": "2500"},
        {"name": "Isabella Martinez", "line1": "75 Moorabool Street", "city": "Geelong", "state": "VIC", "zip": "3220"},
        {"name": "Henry Lee", "line1": "108 Scarborough Street", "city": "Gold Coast", "state": "QLD", "zip": "4215"},
    ],
    "DE": [
        {"name": "Lukas Mueller", "line1": "Friedrichstraße 43", "city": "Berlin", "state": "Berlin", "zip": "10117"},
        {"name": "Anna Schmidt", "line1": "Maximilianstraße 15", "city": "Munich", "state": "Bayern", "zip": "80539"},
        {"name": "Felix Weber", "line1": "Hohe Straße 78", "city": "Cologne", "state": "NRW", "zip": "50667"},
        {"name": "Sophie Fischer", "line1": "Mönckebergstraße 22", "city": "Hamburg", "state": "Hamburg", "zip": "20095"},
        {"name": "Maximilian Meyer", "line1": "Zeil 85", "city": "Frankfurt", "state": "Hessen", "zip": "60313"},
        {"name": "Emma Wagner", "line1": "Königsallee 32", "city": "Düsseldorf", "state": "NRW", "zip": "40212"},
        {"name": "Paul Becker", "line1": "Kaiserstraße 56", "city": "Stuttgart", "state": "Baden-Württemberg", "zip": "70173"},
        {"name": "Hannah Hoffmann", "line1": "Sögestraße 44", "city": "Bremen", "state": "Bremen", "zip": "28195"},
        {"name": "Leon Schulz", "line1": "Bahnhofstraße 12", "city": "Leipzig", "state": "Saxony", "zip": "04109"},
        {"name": "Mia Koch", "line1": "Georgstraße 89", "city": "Hanover", "state": "Lower Saxony", "zip": "30159"},
        {"name": "Tim Richter", "line1": "Augustusplatz 9", "city": "Dresden", "state": "Saxony", "zip": "04109"},
        {"name": "Lea Klein", "line1": "Schildergasse 95", "city": "Cologne", "state": "NRW", "zip": "50667"},
        {"name": "Jonas Schröder", "line1": "Neuhauser Straße 25", "city": "Munich", "state": "Bayern", "zip": "80331"},
        {"name": "Laura Neumann", "line1": "Leipziger Straße 108", "city": "Berlin", "state": "Berlin", "zip": "10117"},
        {"name": "Finn Zimmermann", "line1": "Königstraße 22", "city": "Nuremberg", "state": "Bayern", "zip": "90402"},
    ],
    "FR": [
        {"name": "Lucas Dubois", "line1": "25 Rue de Rivoli", "city": "Paris", "state": "Île-de-France", "zip": "75001"},
        {"name": "Emma Martin", "line1": "14 Rue de la République", "city": "Lyon", "state": "Auvergne-Rhône-Alpes", "zip": "69001"},
        {"name": "Hugo Bernard", "line1": "8 Rue Paradis", "city": "Marseille", "state": "PACA", "zip": "13001"},
        {"name": "Chloé Moreau", "line1": "32 Rue du Faubourg", "city": "Toulouse", "state": "Occitanie", "zip": "31000"},
        {"name": "Louis Petit", "line1": "15 Place de la Comédie", "city": "Montpellier", "state": "Occitanie", "zip": "34000"},
        {"name": "Camille Roux", "line1": "28 Avenue Jean Médecin", "city": "Nice", "state": "PACA", "zip": "06000"},
        {"name": "Gabriel Fournier", "line1": "50 Rue du Commerce", "city": "Bordeaux", "state": "Nouvelle-Aquitaine", "zip": "33000"},
        {"name": "Manon Lambert", "line1": "12 Rue de la République", "city": "Strasbourg", "state": "Grand Est", "zip": "67000"},
        {"name": "Raphaël Girard", "line1": "45 Cours Lafayette", "city": "Lyon", "state": "Auvergne-Rhône-Alpes", "zip": "69006"},
        {"name": "Léa Bonnet", "line1": "78 Rue Saint-Ferréol", "city": "Marseille", "state": "PACA", "zip": "13001"},
        {"name": "Jules André", "line1": "33 Rue Sainte-Catherine", "city": "Bordeaux", "state": "Nouvelle-Aquitaine", "zip": "33000"},
        {"name": "Sarah François", "line1": "19 Rue Esquermoise", "city": "Lille", "state": "Hauts-de-France", "zip": "59000"},
        {"name": "Nathan Mercier", "line1": "56 Rue de Verdun", "city": "Nantes", "state": "Pays de la Loire", "zip": "44000"},
        {"name": "Julie Blanc", "line1": "42 Avenue des Champs-Élysées", "city": "Paris", "state": "Île-de-France", "zip": "75008"},
        {"name": "Mathis Chevalier", "line1": "21 Rue de la Paix", "city": "Paris", "state": "Île-de-France", "zip": "75002"},
    ],
    "JP": [
        {"name": "Takeshi Yamamoto", "line1": "1-2-3 Shibuya", "city": "Shibuya-ku", "state": "Tokyo", "zip": "150-0002"},
        {"name": "Yuki Tanaka", "line1": "4-5-6 Umeda", "city": "Kita-ku", "state": "Osaka", "zip": "530-0001"},
        {"name": "Kenji Suzuki", "line1": "2-8-1 Nishiki", "city": "Naka-ku", "state": "Aichi", "zip": "460-0003"},
        {"name": "Sakura Watanabe", "line1": "3-1-1 Tenjin", "city": "Chuo-ku", "state": "Fukuoka", "zip": "810-0001"},
        {"name": "Hiroshi Kobayashi", "line1": "5-4-3 Ginza", "city": "Chuo-ku", "state": "Tokyo", "zip": "104-0061"},
        {"name": "Yui Sato", "line1": "7-8-9 Shinjuku", "city": "Shinjuku-ku", "state": "Tokyo", "zip": "160-0022"},
        {"name": "Ryota Nakamura", "line1": "2-3-4 Namba", "city": "Naniwa-ku", "state": "Osaka", "zip": "556-0011"},
        {"name": "Aiko Ito", "line1": "6-7-8 Susukino", "city": "Chuo-ku", "state": "Hokkaido", "zip": "064-0804"},
        {"name": "Daiki Kato", "line1": "1-9-8 Sakae", "city": "Naka-ku", "state": "Aichi", "zip": "460-0008"},
        {"name": "Mei Yoshida", "line1": "4-5-6 Hakata", "city": "Hakata-ku", "state": "Fukuoka", "zip": "812-0011"},
        {"name": "Kaito Yamada", "line1": "3-2-1 Omotesando", "city": "Shibuya-ku", "state": "Tokyo", "zip": "150-0001"},
        {"name": "Rin Shimizu", "line1": "8-9-7 Dotonbori", "city": "Chuo-ku", "state": "Osaka", "zip": "542-0071"},
        {"name": "Haruto Inoue", "line1": "5-6-4 Odaiba", "city": "Minato-ku", "state": "Tokyo", "zip": "135-0091"},
        {"name": "Yuna Kimura", "line1": "2-1-3 Asakusa", "city": "Taito-ku", "state": "Tokyo", "zip": "111-0032"},
        {"name": "Sota Hayashi", "line1": "9-8-7 Roppongi", "city": "Minato-ku", "state": "Tokyo", "zip": "106-0032"},
    ],
    "SG": [
        {"name": "Wei Ming Tan", "line1": "1 Raffles Place", "city": "Singapore", "state": "Singapore", "zip": "048616"},
        {"name": "Li Hua Lim", "line1": "391 Orchard Road", "city": "Singapore", "state": "Singapore", "zip": "238872"},
        {"name": "Jun Jie Wong", "line1": "80 Marine Parade Road", "city": "Singapore", "state": "Singapore", "zip": "449269"},
        {"name": "Shu Fen Lee", "line1": "2 Bayfront Avenue", "city": "Singapore", "state": "Singapore", "zip": "018972"},
        {"name": "Jia Hao Chen", "line1": "68 Orchard Road", "city": "Singapore", "state": "Singapore", "zip": "238839"},
        {"name": "Xin Yi Ng", "line1": "10 Bayfront Avenue", "city": "Singapore", "state": "Singapore", "zip": "018956"},
        {"name": "Kai Wen Lim", "line1": "8 Sentosa Gateway", "city": "Sentosa", "state": "Singapore", "zip": "098269"},
        {"name": "Hui Min Ong", "line1": "3 Temasek Boulevard", "city": "Singapore", "state": "Singapore", "zip": "038983"},
        {"name": "Yong Jie Goh", "line1": "1 Kim Seng Promenade", "city": "Singapore", "state": "Singapore", "zip": "237994"},
        {"name": "Mei Ling Chua", "line1": "2 Tampines Central 5", "city": "Tampines", "state": "Singapore", "zip": "529509"},
        {"name": "Chee Keong Tan", "line1": "1 Woodlands Square", "city": "Woodlands", "state": "Singapore", "zip": "738099"},
        {"name": "Siew Leng Koh", "line1": "63 Jurong West Central 3", "city": "Jurong", "state": "Singapore", "zip": "648331"},
    ],
    "NL": [
        {"name": "Daan de Vries", "line1": "Kalverstraat 92", "city": "Amsterdam", "state": "Noord-Holland", "zip": "1012 PH"},
        {"name": "Emma Jansen", "line1": "Lijnbaan 45", "city": "Rotterdam", "state": "Zuid-Holland", "zip": "3012 EL"},
        {"name": "Sem Bakker", "line1": "Lange Viestraat 12", "city": "Utrecht", "state": "Utrecht", "zip": "3511 BK"},
        {"name": "Luuk van Dijk", "line1": "Grote Markt 8", "city": "Groningen", "state": "Groningen", "zip": "9711 VH"},
        {"name": "Sophie Mulder", "line1": "Gelderlandplein 120", "city": "Amsterdam", "state": "Noord-Holland", "zip": "1082 LX"},
        {"name": "Bram Peters", "line1": "Spui 12", "city": "The Hague", "state": "Zuid-Holland", "zip": "2511 BP"},
        {"name": "Evi Smit", "line1": "Kerkplein 5", "city": "Eindhoven", "state": "North Brabant", "zip": "5611 GH"},
        {"name": "Noud Meijer", "line1": "Neude 25", "city": "Utrecht", "state": "Utrecht", "zip": "3512 AD"},
        {"name": "Zoë Janssen", "line1": "Vrijthof 40", "city": "Maastricht", "state": "Limburg", "zip": "6211 LE"},
        {"name": "Mees van den Berg", "line1": "Potterstraat 1", "city": "Utrecht", "state": "Utrecht", "zip": "3511 BB"},
        {"name": "Noor Bos", "line1": "Markthal Verlengde Nieuwstraat", "city": "Rotterdam", "state": "Zuid-Holland", "zip": "3011 GM"},
        {"name": "Thomas Willems", "line1": "Nieuwezijds Voorburgwal 150", "city": "Amsterdam", "state": "Noord-Holland", "zip": "1012 SJ"},
    ],
    "IN": [
        {"name": "Rahul Sharma", "line1": "45 MG Road", "city": "Mumbai", "state": "Maharashtra", "zip": "400001"},
        {"name": "Priya Patel", "line1": "12 Brigade Road", "city": "Bangalore", "state": "Karnataka", "zip": "560001"},
        {"name": "Amit Kumar", "line1": "78 Park Street", "city": "Kolkata", "state": "West Bengal", "zip": "700016"},
        {"name": "Sneha Gupta", "line1": "23 Connaught Place", "city": "New Delhi", "state": "Delhi", "zip": "110001"},
        {"name": "Vikram Singh", "line1": "150 Anna Salai", "city": "Chennai", "state": "Tamil Nadu", "zip": "600002"},
        {"name": "Neha Reddy", "line1": "89 Jubilee Hills", "city": "Hyderabad", "state": "Telangana", "zip": "500033"},
        {"name": "Arun Nair", "line1": "34 MG Road", "city": "Pune", "state": "Maharashtra", "zip": "411001"},
        {"name": "Deepa Iyer", "line1": "56 Sardar Patel Road", "city": "Ahmedabad", "state": "Gujarat", "zip": "380001"},
        {"name": "Rajesh Khanna", "line1": "101 FC Road", "city": "Pune", "state": "Maharashtra", "zip": "411004"},
        {"name": "Anjali Desai", "line1": "77 Lavelle Road", "city": "Bangalore", "state": "Karnataka", "zip": "560001"},
        {"name": "Suresh Menon", "line1": "22 Marine Drive", "city": "Mumbai", "state": "Maharashtra", "zip": "400020"},
        {"name": "Pooja Malhotra", "line1": "88 Nehru Place", "city": "New Delhi", "state": "Delhi", "zip": "110019"},
        {"name": "Karthik Venkatesh", "line1": "5 Residency Road", "city": "Bangalore", "state": "Karnataka", "zip": "560025"},
        {"name": "Lakshmi Rao", "line1": "42 Banjara Hills", "city": "Hyderabad", "state": "Telangana", "zip": "500034"},
        {"name": "Manish Tiwari", "line1": "67 Hazratganj", "city": "Lucknow", "state": "Uttar Pradesh", "zip": "226001"},
    ],
    "BR": [
        {"name": "Lucas Silva", "line1": "Av. Paulista 1578", "city": "São Paulo", "state": "SP", "zip": "01310-200"},
        {"name": "Ana Oliveira", "line1": "Rua Visconde de Pirajá 330", "city": "Rio de Janeiro", "state": "RJ", "zip": "22410-002"},
        {"name": "Pedro Santos", "line1": "SQS 308 Bloco A", "city": "Brasília", "state": "DF", "zip": "70356-010"},
        {"name": "Julia Costa", "line1": "Av. Beira Mar 2200", "city": "Fortaleza", "state": "CE", "zip": "60165-121"},
        {"name": "Matheus Lima", "line1": "Rua da Consolação 345", "city": "São Paulo", "state": "SP", "zip": "01301-000"},
        {"name": "Isabela Souza", "line1": "Av. Rio Branco 185", "city": "Rio de Janeiro", "state": "RJ", "zip": "20040-007"},
        {"name": "Gabriel Ferreira", "line1": "Av. Afonso Pena 1200", "city": "Belo Horizonte", "state": "MG", "zip": "30130-005"},
        {"name": "Mariana Almeida", "line1": "Rua XV de Novembro 800", "city": "Curitiba", "state": "PR", "zip": "80020-310"},
        {"name": "Rafael Rodrigues", "line1": "Av. Salvador 800", "city": "Salvador", "state": "BA", "zip": "40050-000"},
        {"name": "Larissa Carvalho", "line1": "Rua 24 Horas 150", "city": "Curitiba", "state": "PR", "zip": "80420-060"},
        {"name": "Felipe Gomes", "line1": "Av. Boa Viagem 4000", "city": "Recife", "state": "PE", "zip": "51020-000"},
        {"name": "Amanda Barbosa", "line1": "Av. das Américas 5000", "city": "Rio de Janeiro", "state": "RJ", "zip": "22640-102"},
    ],
    "IT": [
        {"name": "Marco Rossi", "line1": "Via del Corso 112", "city": "Rome", "state": "Lazio", "zip": "00186"},
        {"name": "Giulia Bianchi", "line1": "Via Montenapoleone 8", "city": "Milan", "state": "Lombardia", "zip": "20121"},
        {"name": "Alessandro Ferrari", "line1": "Via Roma 45", "city": "Florence", "state": "Toscana", "zip": "50123"},
        {"name": "Francesca Romano", "line1": "Via Toledo 200", "city": "Naples", "state": "Campania", "zip": "80132"},
        {"name": "Matteo Ricci", "line1": "Via Garibaldi 88", "city": "Turin", "state": "Piemonte", "zip": "10122"},
        {"name": "Chiara Marino", "line1": "Via Etnea 250", "city": "Catania", "state": "Sicily", "zip": "95124"},
        {"name": "Davide Greco", "line1": "Via XX Settembre 45", "city": "Genoa", "state": "Liguria", "zip": "16121"},
        {"name": "Valentina Bruno", "line1": "Via Maqueda 250", "city": "Palermo", "state": "Sicily", "zip": "90133"},
        {"name": "Simone Gallo", "line1": "Via dell'Indipendenza 60", "city": "Bologna", "state": "Emilia-Romagna", "zip": "40121"},
        {"name": "Martina Conti", "line1": "Via San Lorenzo 120", "city": "Florence", "state": "Toscana", "zip": "50123"},
        {"name": "Andrea Mancini", "line1": "Via San Marco 75", "city": "Venice", "state": "Veneto", "zip": "30124"},
        {"name": "Sara Costa", "line1": "Via Nazionale 180", "city": "Rome", "state": "Lazio", "zip": "00184"},
    ],
    "ES": [
        {"name": "Carlos García", "line1": "Calle Gran Vía 32", "city": "Madrid", "state": "Madrid", "zip": "28013"},
        {"name": "María López", "line1": "Passeig de Gràcia 55", "city": "Barcelona", "state": "Cataluña", "zip": "08007"},
        {"name": "Pablo Martínez", "line1": "Calle Sierpes 70", "city": "Seville", "state": "Andalucía", "zip": "41004"},
        {"name": "Ana Fernández", "line1": "Calle Larios 15", "city": "Malaga", "state": "Andalucía", "zip": "29005"},
        {"name": "David Ruiz", "line1": "Calle Colón 28", "city": "Valencia", "state": "Valencia", "zip": "46004"},
        {"name": "Laura Sánchez", "line1": "Calle Preciados 30", "city": "Madrid", "state": "Madrid", "zip": "28013"},
        {"name": "Javier Rodríguez", "line1": "Avenida de la Constitución 18", "city": "Seville", "state": "Andalucía", "zip": "41004"},
        {"name": "Carmen Torres", "line1": "Calle de Fuencarral 120", "city": "Madrid", "state": "Madrid", "zip": "28010"},
        {"name": "Miguel Gómez", "line1": "Rambla de Catalunya 89", "city": "Barcelona", "state": "Cataluña", "zip": "08008"},
        {"name": "Elena Vázquez", "line1": "Calle Mayor 45", "city": "Madrid", "state": "Madrid", "zip": "28013"},
        {"name": "Antonio Morales", "line1": "Paseo del Prado 14", "city": "Madrid", "state": "Madrid", "zip": "28014"},
        {"name": "Isabel Ortiz", "line1": "Calle Arenal 18", "city": "Madrid", "state": "Madrid", "zip": "28013"},
    ],
    "IE": [
        {"name": "Sean Murphy", "line1": "45 Grafton Street", "city": "Dublin", "state": "Dublin", "zip": "D02 VK60"},
        {"name": "Aoife O'Brien", "line1": "12 Patrick Street", "city": "Cork", "state": "Cork", "zip": "T12 X70A"},
        {"name": "Conor Kelly", "line1": "8 Shop Street", "city": "Galway", "state": "Galway", "zip": "H91 XR85"},
        {"name": "Ciara Ryan", "line1": "98 O'Connell Street", "city": "Dublin", "state": "Dublin", "zip": "D01 F5P2"},
        {"name": "Fionn Walsh", "line1": "34 Henry Street", "city": "Dublin", "state": "Dublin", "zip": "D01 T3K6"},
        {"name": "Niamh Byrne", "line1": "21 St Patrick's Street", "city": "Cork", "state": "Cork", "zip": "T12 F5W7"},
        {"name": "Darragh Doyle", "line1": "56 Eyre Square", "city": "Galway", "state": "Galway", "zip": "H91 P7C4"},
        {"name": "Saoirse Kennedy", "line1": "18 Oliver Plunkett Street", "city": "Cork", "state": "Cork", "zip": "T12 T6C9"},
        {"name": "Liam Fitzgerald", "line1": "72 Dame Street", "city": "Dublin", "state": "Dublin", "zip": "D02 K7C1"},
        {"name": "Maeve O'Connor", "line1": "33 William Street South", "city": "Dublin", "state": "Dublin", "zip": "D02 K7X0"},
    ],
    "SE": [
        {"name": "Erik Lindberg", "line1": "Drottninggatan 53", "city": "Stockholm", "state": "Stockholm", "zip": "111 21"},
        {"name": "Astrid Johansson", "line1": "Vallgatan 12", "city": "Gothenburg", "state": "Västra Götaland", "zip": "411 16"},
        {"name": "Oscar Andersson", "line1": "Södra Förstadsgatan 24", "city": "Malmö", "state": "Skåne", "zip": "211 43"},
        {"name": "Freja Karlsson", "line1": "Hamngatan 18", "city": "Stockholm", "state": "Stockholm", "zip": "111 47"},
        {"name": "Liam Eriksson", "line1": "Avenyn 42", "city": "Gothenburg", "state": "Västra Götaland", "zip": "411 36"},
        {"name": "Maja Nilsson", "line1": "Södergatan 30", "city": "Malmö", "state": "Skåne", "zip": "211 34"},
        {"name": "William Larsson", "line1": "Kungsgatan 55", "city": "Uppsala", "state": "Uppsala", "zip": "753 21"},
        {"name": "Elsa Olsson", "line1": "Storgatan 88", "city": "Stockholm", "state": "Stockholm", "zip": "111 29"},
        {"name": "Hugo Persson", "line1": "Östra Hamngatan 18", "city": "Gothenburg", "state": "Västra Götaland", "zip": "411 10"},
        {"name": "Alice Svensson", "line1": "Sveavägen 120", "city": "Stockholm", "state": "Stockholm", "zip": "113 50"},
    ],
    "CH": [
        {"name": "Thomas Müller", "line1": "Bahnhofstrasse 21", "city": "Zurich", "state": "Zürich", "zip": "8001"},
        {"name": "Laura Weber", "line1": "Rue du Rhône 48", "city": "Geneva", "state": "Genève", "zip": "1204"},
        {"name": "Marc Schneider", "line1": "Marktgasse 15", "city": "Bern", "state": "Bern", "zip": "3011"},
        {"name": "Sophie Meier", "line1": "Storchengasse 12", "city": "Basel", "state": "Basel-Stadt", "zip": "4051"},
        {"name": "Lucas Fischer", "line1": "Via Nassa 50", "city": "Lugano", "state": "Ticino", "zip": "6900"},
        {"name": "Emma Huber", "line1": "Gutenbergstrasse 5", "city": "Lausanne", "state": "Vaud", "zip": "1003"},
        {"name": "Noah Keller", "line1": "Rennweg 42", "city": "Zurich", "state": "Zürich", "zip": "8001"},
        {"name": "Mia Lehmann", "line1": "Quai du Mont-Blanc 19", "city": "Geneva", "state": "Genève", "zip": "1201"},
        {"name": "Benjamin Schmid", "line1": "Spitalgasse 38", "city": "Bern", "state": "Bern", "zip": "3011"},
        {"name": "Olivia Brunner", "line1": "Freie Strasse 75", "city": "Basel", "state": "Basel-Stadt", "zip": "4051"},
    ],
    "NZ": [
        {"name": "James Taylor", "line1": "125 Queen Street", "city": "Auckland", "state": "Auckland", "zip": "1010"},
        {"name": "Sophie Williams", "line1": "88 Lambton Quay", "city": "Wellington", "state": "Wellington", "zip": "6011"},
        {"name": "Ben Martin", "line1": "45 Colombo Street", "city": "Christchurch", "state": "Canterbury", "zip": "8013"},
        {"name": "Emma Thompson", "line1": "789 Victoria Street", "city": "Auckland", "state": "Auckland", "zip": "1010"},
        {"name": "Oliver Wilson", "line1": "256 Cuba Street", "city": "Wellington", "state": "Wellington", "zip": "6011"},
        {"name": "Charlotte Brown", "line1": "34 Cashel Street", "city": "Christchurch", "state": "Canterbury", "zip": "8011"},
        {"name": "Liam Anderson", "line1": "178 George Street", "city": "Dunedin", "state": "Otago", "zip": "9016"},
        {"name": "Isabella Jones", "line1": "56 Maunganui Road", "city": "Tauranga", "state": "Bay of Plenty", "zip": "3110"},
        {"name": "Noah Davis", "line1": "345 Trafalgar Street", "city": "Nelson", "state": "Nelson", "zip": "7010"},
        {"name": "Mia Johnson", "line1": "88 The Strand", "city": "Tauranga", "state": "Bay of Plenty", "zip": "3110"},
    ],
    "HK": [
        {"name": "Kevin Chan", "line1": "1 Queen's Road Central", "city": "Central", "state": "Hong Kong", "zip": "999077"},
        {"name": "Amy Wong", "line1": "100 Nathan Road", "city": "Tsim Sha Tsui", "state": "Kowloon", "zip": "999077"},
        {"name": "David Lau", "line1": "68 Hennessy Road", "city": "Wan Chai", "state": "Hong Kong", "zip": "999077"},
        {"name": "Siu Ming Lee", "line1": "5 Canton Road", "city": "Tsim Sha Tsui", "state": "Kowloon", "zip": "999077"},
        {"name": "Wai Ying Cheung", "line1": "20 Des Voeux Road Central", "city": "Central", "state": "Hong Kong", "zip": "999077"},
        {"name": "Chi Ho Ng", "line1": "80 Granville Road", "city": "Tsim Sha Tsui", "state": "Kowloon", "zip": "999077"},
        {"name": "Mei Lin Tang", "line1": "12 Percival Street", "city": "Causeway Bay", "state": "Hong Kong", "zip": "999077"},
        {"name": "Ka Fai Ho", "line1": "45 Argyle Street", "city": "Mong Kok", "state": "Kowloon", "zip": "999077"},
        {"name": "Yan Yan Chow", "line1": "3 Connaught Road", "city": "Central", "state": "Hong Kong", "zip": "999077"},
        {"name": "Chun Kit Yuen", "line1": "150 Sai Yeung Choi Street", "city": "Mong Kok", "state": "Kowloon", "zip": "999077"},
    ],
    "MY": [
        {"name": "Ahmad bin Ibrahim", "line1": "Lot 10, Jalan Bukit Bintang", "city": "Kuala Lumpur", "state": "WP KL", "zip": "55100"},
        {"name": "Siti Nurhaliza", "line1": "22 Jalan Sultan Ismail", "city": "Kuala Lumpur", "state": "WP KL", "zip": "50250"},
        {"name": "Tan Wei Ming", "line1": "Gurney Drive 88", "city": "George Town", "state": "Penang", "zip": "10250"},
        {"name": "Nurul Huda", "line1": "35 Jalan Wong Ah Fook", "city": "Johor Bahru", "state": "Johor", "zip": "80000"},
        {"name": "Mohd Faizal", "line1": "12 Jalan Tunku Abdul Rahman", "city": "Kuala Lumpur", "state": "WP KL", "zip": "50100"},
        {"name": "Lee Mei Ling", "line1": "88 Jalan Universiti", "city": "Petaling Jaya", "state": "Selangor", "zip": "46200"},
        {"name": "Rajesh Kumar", "line1": "56 Jalan Ipoh", "city": "Kuala Lumpur", "state": "WP KL", "zip": "51200"},
        {"name": "Faridah Abdullah", "line1": "27 Jalan Raja", "city": "Shah Alam", "state": "Selangor", "zip": "40000"},
        {"name": "Chong Wai Kit", "line1": "123 Jalan Burma", "city": "George Town", "state": "Penang", "zip": "10050"},
        {"name": "Aisyah Mohd", "line1": "8 Jalan Melaka Raya", "city": "Malacca City", "state": "Malacca", "zip": "75000"},
    ],
    "MX": [
        {"name": "Carlos Hernández", "line1": "Av. Reforma 222", "city": "Mexico City", "state": "CDMX", "zip": "06600"},
        {"name": "María González", "line1": "Calle Morelos 45", "city": "Guadalajara", "state": "Jalisco", "zip": "44100"},
        {"name": "Juan López", "line1": "Av. Constitución 800", "city": "Monterrey", "state": "Nuevo León", "zip": "64000"},
        {"name": "Ana Martínez", "line1": "Av. Insurgentes Sur 1000", "city": "Mexico City", "state": "CDMX", "zip": "03100"},
        {"name": "Pedro Sánchez", "line1": "Calle 5 de Mayo 300", "city": "Puebla", "state": "Puebla", "zip": "72000"},
        {"name": "Sofía Ramírez", "line1": "Av. Revolución 1500", "city": "Tijuana", "state": "Baja California", "zip": "22000"},
        {"name": "Diego Torres", "line1": "Av. Vallarta 5000", "city": "Guadalajara", "state": "Jalisco", "zip": "45000"},
        {"name": "Fernanda Ruiz", "line1": "Calle Madero 100", "city": "León", "state": "Guanajuato", "zip": "37000"},
        {"name": "Luis Flores", "line1": "Av. Juárez 600", "city": "Chihuahua", "state": "Chihuahua", "zip": "31000"},
        {"name": "Gabriela Ortiz", "line1": "Calle Francisco I. Madero 250", "city": "Mérida", "state": "Yucatán", "zip": "97000"},
    ],
    "MO": [
        {"name": "Wong Ka Ming", "line1": "Rua de S. Paulo No. 45", "city": "Macau", "state": "Macau", "zip": "999078"},
        {"name": "Chan Mei Ling", "line1": "Av. de Almeida Ribeiro 128", "city": "Macau", "state": "Macau", "zip": "999078"},
        {"name": "Ho Siu Wai", "line1": "Rua do Campo No. 78", "city": "Macau", "state": "Macau", "zip": "999078"},
        {"name": "Leong Chi Keong", "line1": "Estrada do Repouso 32", "city": "Taipa", "state": "Macau", "zip": "999078"},
        {"name": "Lam Pui San", "line1": "Rua de Pedro Coutinho 56", "city": "Macau", "state": "Macau", "zip": "999078"},
        {"name": "Choi Man Cheong", "line1": "Avenida da Praia Grande 100", "city": "Macau", "state": "Macau", "zip": "999078"},
        {"name": "Fong Wai Han", "line1": "Rua de S. Domingos 28", "city": "Macau", "state": "Macau", "zip": "999078"},
        {"name": "Kou Chi Fong", "line1": "Estrada do Istmo 300", "city": "Cotai", "state": "Macau", "zip": "999078"},
        {"name": "Sou Ka Lai", "line1": "Rua Nova do Guimarães 15", "city": "Macau", "state": "Macau", "zip": "999078"},
        {"name": "Iao Chi Man", "line1": "Av. da Amizade 50", "city": "Macau", "state": "Macau", "zip": "999078"},
    ],
    "DK": [
        {"name": "Magnus Nielsen", "line1": "Strøget 28", "city": "Copenhagen", "state": "Hovedstaden", "zip": "1050"},
        {"name": "Freja Hansen", "line1": "Søndergade 14", "city": "Aarhus", "state": "Midtjylland", "zip": "8000"},
        {"name": "Lucas Pedersen", "line1": "Østergade 42", "city": "Copenhagen", "state": "Hovedstaden", "zip": "1100"},
        {"name": "Emma Andersen", "line1": "Vesterbrogade 100", "city": "Copenhagen", "state": "Hovedstaden", "zip": "1620"},
        {"name": "Oliver Christensen", "line1": "Bispensgade 20", "city": "Aarhus", "state": "Midtjylland", "zip": "8000"},
        {"name": "Sofie Larsen", "line1": "Kongens Nytorv 15", "city": "Copenhagen", "state": "Hovedstaden", "zip": "1050"},
        {"name": "William Rasmussen", "line1": "Søndre Boulevard 50", "city": "Odense", "state": "Syddanmark", "zip": "5000"},
        {"name": "Clara Sørensen", "line1": "Algade 75", "city": "Roskilde", "state": "Region Zealand", "zip": "4000"},
        {"name": "Noah Petersen", "line1": "Købmagergade 33", "city": "Copenhagen", "state": "Hovedstaden", "zip": "1150"},
        {"name": "Ida Madsen", "line1": "Frederiksgade 28", "city": "Aarhus", "state": "Midtjylland", "zip": "8000"},
    ],
    "NO": [
        {"name": "Lars Eriksen", "line1": "Karl Johans gate 22", "city": "Oslo", "state": "Oslo", "zip": "0159"},
        {"name": "Nora Larsen", "line1": "Torgallmenningen 8", "city": "Bergen", "state": "Vestland", "zip": "5014"},
        {"name": "Emma Johansen", "line1": "Bogstadveien 45", "city": "Oslo", "state": "Oslo", "zip": "0355"},
        {"name": "Olav Olsen", "line1": "Øvre Slottsgate 18", "city": "Oslo", "state": "Oslo", "zip": "0157"},
        {"name": "Sofia Halvorsen", "line1": "Bryggen 10", "city": "Bergen", "state": "Vestland", "zip": "5003"},
        {"name": "Lucas Nilsen", "line1": "Kongens gate 30", "city": "Trondheim", "state": "Trøndelag", "zip": "7012"},
        {"name": "Maja Kristiansen", "line1": "Nedre Slottsgate 5", "city": "Oslo", "state": "Oslo", "zip": "0157"},
        {"name": "William Solberg", "line1": "Marken 25", "city": "Bergen", "state": "Vestland", "zip": "5017"},
        {"name": "Frida Berg", "line1": "Nordre gate 42", "city": "Trondheim", "state": "Trøndelag", "zip": "7011"},
        {"name": "Theo Henriksen", "line1": "Stortingsgata 12", "city": "Oslo", "state": "Oslo", "zip": "0161"},
    ],
    "FI": [
        {"name": "Mikko Virtanen", "line1": "Aleksanterinkatu 17", "city": "Helsinki", "state": "Uusimaa", "zip": "00100"},
        {"name": "Aino Korhonen", "line1": "Hämeenkatu 12", "city": "Tampere", "state": "Pirkanmaa", "zip": "33100"},
        {"name": "Juuso Mäkinen", "line1": "Mannerheimintie 50", "city": "Helsinki", "state": "Uusimaa", "zip": "00100"},
        {"name": "Emma Nieminen", "line1": "Kauppakatu 25", "city": "Kuopio", "state": "North Savo", "zip": "70100"},
        {"name": "Lauri Järvinen", "line1": "Eerikinkatu 8", "city": "Turku", "state": "Southwest Finland", "zip": "20100"},
        {"name": "Sofia Heikkinen", "line1": "Kirkkokatu 15", "city": "Oulu", "state": "North Ostrobothnia", "zip": "90100"},
        {"name": "Onni Koskinen", "line1": "Pohjoisesplanadi 35", "city": "Helsinki", "state": "Uusimaa", "zip": "00100"},
        {"name": "Olivia Laine", "line1": "Kuninkaankatu 22", "city": "Tampere", "state": "Pirkanmaa", "zip": "33210"},
        {"name": "Elias Rantanen", "line1": "Aurakatu 12", "city": "Turku", "state": "Southwest Finland", "zip": "20100"},
        {"name": "Venla Salminen", "line1": "Iso Roobertinkatu 28", "city": "Helsinki", "state": "Uusimaa", "zip": "00120"},
    ],
    "AT": [
        {"name": "Maximilian Gruber", "line1": "Kärntner Straße 38", "city": "Vienna", "state": "Wien", "zip": "1010"},
        {"name": "Anna Huber", "line1": "Getreidegasse 9", "city": "Salzburg", "state": "Salzburg", "zip": "5020"},
        {"name": "Lukas Bauer", "line1": "Mariahilfer Straße 70", "city": "Vienna", "state": "Wien", "zip": "1070"},
        {"name": "Sophia Wagner", "line1": "Herrengasse 15", "city": "Graz", "state": "Styria", "zip": "8010"},
        {"name": "Tobias Pichler", "line1": "Landstraße 50", "city": "Linz", "state": "Upper Austria", "zip": "4020"},
        {"name": "Emma Schmid", "line1": "Stephansplatz 10", "city": "Vienna", "state": "Wien", "zip": "1010"},
        {"name": "David Fischer", "line1": "Universitätsstraße 25", "city": "Innsbruck", "state": "Tyrol", "zip": "6020"},
        {"name": "Leonie Weber", "line1": "Sporgasse 30", "city": "Graz", "state": "Styria", "zip": "8010"},
        {"name": "Felix Maier", "line1": "Graben 12", "city": "Vienna", "state": "Wien", "zip": "1010"},
        {"name": "Hannah Schulz", "line1": "Makartplatz 5", "city": "Salzburg", "state": "Salzburg", "zip": "5020"},
    ],
    "BE": [
        {"name": "Lucas Peeters", "line1": "Meir 47", "city": "Antwerp", "state": "Antwerpen", "zip": "2000"},
        {"name": "Emma Dubois", "line1": "Rue Neuve 123", "city": "Brussels", "state": "Bruxelles", "zip": "1000"},
        {"name": "Louis Janssens", "line1": "Avenue Louise 250", "city": "Brussels", "state": "Bruxelles", "zip": "1050"},
        {"name": "Marie Leroy", "line1": "Groenplaats 15", "city": "Antwerp", "state": "Antwerpen", "zip": "2000"},
        {"name": "Noah Maes", "line1": "Veldstraat 40", "city": "Ghent", "state": "East Flanders", "zip": "9000"},
        {"name": "Lina De Smet", "line1": "Rue des Bouchers 30", "city": "Brussels", "state": "Bruxelles", "zip": "1000"},
        {"name": "Thomas Vermeulen", "line1": "Steenstraat 22", "city": "Bruges", "state": "West Flanders", "zip": "8000"},
        {"name": "Julie Wouters", "line1": "Place Saint-Lambert 18", "city": "Liège", "state": "Liège", "zip": "4000"},
        {"name": "Victor Jacobs", "line1": "Bondgenotenlaan 100", "city": "Leuven", "state": "Flemish Brabant", "zip": "3000"},
        {"name": "Charlotte Mertens", "line1": "Rue du Marché aux Herbes 75", "city": "Brussels", "state": "Bruxelles", "zip": "1000"},
    ],
    "PT": [
        {"name": "Miguel Santos", "line1": "Rua Augusta 274", "city": "Lisbon", "state": "Lisboa", "zip": "1100-053"},
        {"name": "Ana Ferreira", "line1": "Rua de Santa Catarina 112", "city": "Porto", "state": "Porto", "zip": "4000-442"},
        {"name": "Tiago Costa", "line1": "Avenida da Liberdade 180", "city": "Lisbon", "state": "Lisboa", "zip": "1250-146"},
        {"name": "Sofia Oliveira", "line1": "Rua das Flores 45", "city": "Porto", "state": "Porto", "zip": "4050-265"},
        {"name": "Diogo Pereira", "line1": "Avenida dos Aliados 80", "city": "Porto", "state": "Porto", "zip": "4000-064"},
        {"name": "Mariana Rodrigues", "line1": "Rua Garrett 25", "city": "Lisbon", "state": "Lisboa", "zip": "1200-203"},
        {"name": "Pedro Almeida", "line1": "Rua Dom João IV 60", "city": "Porto", "state": "Porto", "zip": "4000-295"},
        {"name": "Beatriz Martins", "line1": "Praça do Comércio 15", "city": "Lisbon", "state": "Lisboa", "zip": "1100-148"},
        {"name": "João Silva", "line1": "Rua do Carmo 90", "city": "Lisbon", "state": "Lisboa", "zip": "1200-093"},
        {"name": "Carolina Gonçalves", "line1": "Avenida da Boavista 500", "city": "Porto", "state": "Porto", "zip": "4100-135"},
    ],
    "PL": [
        {"name": "Jakub Kowalski", "line1": "Nowy Świat 46", "city": "Warsaw", "state": "Mazowieckie", "zip": "00-363"},
        {"name": "Zofia Nowak", "line1": "Floriańska 14", "city": "Kraków", "state": "Małopolskie", "zip": "31-021"},
        {"name": "Jan Wiśniewski", "line1": "Ulica Piotrkowska 80", "city": "Łódź", "state": "Łódzkie", "zip": "90-001"},
        {"name": "Anna Wójcik", "line1": "Aleja Niepodległości 150", "city": "Warsaw", "state": "Mazowieckie", "zip": "02-626"},
        {"name": "Michał Kowalczyk", "line1": "Ulica Grodzka 25", "city": "Kraków", "state": "Małopolskie", "zip": "31-001"},
        {"name": "Katarzyna Kamińska", "line1": "Ulica Świdnicka 40", "city": "Wrocław", "state": "Dolnośląskie", "zip": "50-068"},
        {"name": "Mateusz Lewandowski", "line1": "Ulica Długa 60", "city": "Gdańsk", "state": "Pomorskie", "zip": "80-831"},
        {"name": "Magdalena Zielińska", "line1": "Aleja Marcinkowskiego 20", "city": "Poznań", "state": "Wielkopolskie", "zip": "61-745"},
        {"name": "Piotr Szymański", "line1": "Ulica Marszałkowska 100", "city": "Warsaw", "state": "Mazowieckie", "zip": "00-017"},
        {"name": "Agnieszka Dąbrowska", "line1": "Ulica Floriańska 50", "city": "Kraków", "state": "Małopolskie", "zip": "31-019"},
    ],
    "TH": [
        {"name": "Somchai Prasert", "line1": "123 Sukhumvit Road", "city": "Bangkok", "state": "Bangkok", "zip": "10110"},
        {"name": "Ploy Srisai", "line1": "45 Nimman Road", "city": "Chiang Mai", "state": "Chiang Mai", "zip": "50200"},
        {"name": "Kritsada Wongsawat", "line1": "88 Silom Road", "city": "Bangkok", "state": "Bangkok", "zip": "10500"},
        {"name": "Nattaya Chaiyaporn", "line1": "150 Ratchadamri Road", "city": "Bangkok", "state": "Bangkok", "zip": "10330"},
        {"name": "Thanakorn Meesuk", "line1": "22 Thanon Tha Phae", "city": "Chiang Mai", "state": "Chiang Mai", "zip": "50100"},
        {"name": "Siriporn Jaidee", "line1": "77 Khao San Road", "city": "Bangkok", "state": "Bangkok", "zip": "10200"},
        {"name": "Pongsak Rattanaporn", "line1": "55 Beach Road", "city": "Pattaya", "state": "Chonburi", "zip": "20150"},
        {"name": "Wanida Suksabai", "line1": "33 Phuket Road", "city": "Phuket", "state": "Phuket", "zip": "83000"},
        {"name": "Surachai Khunpha", "line1": "100 Rama I Road", "city": "Bangkok", "state": "Bangkok", "zip": "10330"},
        {"name": "Achara Phongsri", "line1": "18 Thanon Yaowarat", "city": "Bangkok", "state": "Bangkok", "zip": "10100"},
    ],
    "PH": [
        {"name": "Juan dela Cruz", "line1": "123 Ayala Avenue", "city": "Makati", "state": "Metro Manila", "zip": "1226"},
        {"name": "Maria Santos", "line1": "45 Osmeña Boulevard", "city": "Cebu City", "state": "Cebu", "zip": "6000"},
        {"name": "Jose Reyes", "line1": "88 Session Road", "city": "Baguio City", "state": "Benguet", "zip": "2600"},
        {"name": "Ana Villanueva", "line1": "250 Roxas Boulevard", "city": "Pasay", "state": "Metro Manila", "zip": "1300"},
        {"name": "Miguel Bautista", "line1": "55 Bonifacio High Street", "city": "Taguig", "state": "Metro Manila", "zip": "1634"},
        {"name": "Carmen Lim", "line1": "12 Escario Street", "city": "Cebu City", "state": "Cebu", "zip": "6000"},
        {"name": "Ricardo Tan", "line1": "76 Tomas Morato Avenue", "city": "Quezon City", "state": "Metro Manila", "zip": "1103"},
        {"name": "Dolores Garcia", "line1": "200 Ortigas Avenue", "city": "Pasig", "state": "Metro Manila", "zip": "1605"},
        {"name": "Antonio Ramos", "line1": "34 P. Burgos Street", "city": "Makati", "state": "Metro Manila", "zip": "1210"},
        {"name": "Elena Cruz", "line1": "150 CM Recto Avenue", "city": "Manila", "state": "Metro Manila", "zip": "1008"},
    ],
    "ID": [
        {"name": "Budi Santoso", "line1": "Jl. Sudirman Kav. 52", "city": "Jakarta", "state": "DKI Jakarta", "zip": "12190"},
        {"name": "Siti Rahayu", "line1": "Jl. Malioboro 56", "city": "Yogyakarta", "state": "DIY", "zip": "55271"},
        {"name": "Ahmad Fauzi", "line1": "Jl. Thamrin Kav. 10", "city": "Jakarta", "state": "DKI Jakarta", "zip": "10230"},
        {"name": "Dewi Kusuma", "line1": "Jl. Asia Afrika 100", "city": "Bandung", "state": "West Java", "zip": "40111"},
        {"name": "Rudi Hartono", "line1": "Jl. Pemuda 50", "city": "Surabaya", "state": "East Java", "zip": "60271"},
        {"name": "Maya Indriani", "line1": "Jl. Gatot Subroto Kav. 89", "city": "Jakarta", "state": "DKI Jakarta", "zip": "12930"},
        {"name": "Agus Wijaya", "line1": "Jl. Ir. H. Juanda 25", "city": "Bandung", "state": "West Java", "zip": "40132"},
        {"name": "Rina Susanti", "line1": "Jl. Raya Seminyak 80", "city": "Bali", "state": "Bali", "zip": "80361"},
        {"name": "Dedi Kurniawan", "line1": "Jl. A. Yani 150", "city": "Surabaya", "state": "East Java", "zip": "60241"},
        {"name": "Lestari Wulandari", "line1": "Jl. Diponegoro 45", "city": "Medan", "state": "North Sumatra", "zip": "20152"},
    ],
    "AE": [
        {"name": "Ahmed Al Maktoum", "line1": "Sheikh Zayed Road Tower 1", "city": "Dubai", "state": "Dubai", "zip": "00000"},
        {"name": "Fatima Al Nahyan", "line1": "Corniche Road Villa 23", "city": "Abu Dhabi", "state": "Abu Dhabi", "zip": "00000"},
        {"name": "Mohammed Al Falasi", "line1": "Jumeirah Beach Road Villa 15", "city": "Dubai", "state": "Dubai", "zip": "00000"},
        {"name": "Aisha Al Suwaidi", "line1": "Al Maryah Island Tower 3", "city": "Abu Dhabi", "state": "Abu Dhabi", "zip": "00000"},
        {"name": "Rashid Al Qasimi", "line1": "Al Rigga Street Building 50", "city": "Dubai", "state": "Dubai", "zip": "00000"},
        {"name": "Layla Al Ameri", "line1": "Saadiyat Island Residence 8", "city": "Abu Dhabi", "state": "Abu Dhabi", "zip": "00000"},
        {"name": "Khalid Al Mansouri", "line1": "Downtown Dubai Boulevard 25", "city": "Dubai", "state": "Dubai", "zip": "00000"},
        {"name": "Noora Al Zaabi", "line1": "Al Wahda Mall Street 12", "city": "Abu Dhabi", "state": "Abu Dhabi", "zip": "00000"},
        {"name": "Saeed Al Hammadi", "line1": "Dubai Marina Tower 40", "city": "Dubai", "state": "Dubai", "zip": "00000"},
        {"name": "Mariam Al Hashimi", "line1": "Yas Island Boulevard 6", "city": "Abu Dhabi", "state": "Abu Dhabi", "zip": "00000"},
    ],
}

# Flat list for backward compatibility
BILLING_ADDRESSES = []
for _country, _addrs in BILLING_ADDRESSES_BY_COUNTRY.items():
    for _a in _addrs:
        BILLING_ADDRESSES.append({**_a, "country": _country})

CARD_SEPARATOR = "━ ━ ━ ━ ━ ━━━ ━ ━ ━ ━ ━"
STATUS_EMOJIS = {
    'CHARGED': '😎', 'LIVE': '✅', 'DECLINED': '🥲', '3DS': '😡',
    'ERROR': '💀', 'FAILED': '💀', 'UNKNOWN': '❓'
}

# Decline codes that mean the card is LIVE (valid number, wrong details)
LIVE_DECLINE_CODES = {
    'incorrect_cvc', 'incorrect_zip', 'insufficient_funds',
    'invalid_cvc', 'card_velocity_exceeded', 'do_not_honor',
    'try_again_later', 'not_permitted', 'withdrawal_count_limit_exceeded',
}


def get_random_billing(country: str = None) -> dict:
    """Get a random billing address, matched to country if available.
    
    Priority:
    1. If country is provided and we have addresses for it → use that country
    2. If country not found → fallback to MO (Macau)
    """
    if country:
        country = country.upper().strip()
        if country in BILLING_ADDRESSES_BY_COUNTRY:
            addr = random.choice(BILLING_ADDRESSES_BY_COUNTRY[country])
            return {**addr, "country": country}
    # Fallback to Macau
    addr = random.choice(BILLING_ADDRESSES_BY_COUNTRY["MO"])
    return {**addr, "country": "MO"}


def get_currency_symbol(currency: str) -> str:
    symbols = {
        "USD": "$", "EUR": "€", "GBP": "£", "INR": "₹", "JPY": "¥",
        "CNY": "¥", "KRW": "₩", "RUB": "₽", "BRL": "R$", "CAD": "C$",
        "AUD": "A$", "MXN": "MX$", "SGD": "S$", "HKD": "HK$", "THB": "฿",
        "VND": "₫", "PHP": "₱", "IDR": "Rp", "MYR": "RM", "ZAR": "R",
        "CHF": "CHF", "SEK": "kr", "NOK": "kr", "DKK": "kr", "PLN": "zł",
        "TRY": "₺", "AED": "د.إ", "SAR": "﷼", "ILS": "₪", "TWD": "NT$"
    }
    return symbols.get(currency, "")


# Currency to Country mapping for billing address
def get_country_from_currency(currency: str) -> str:
    """Map currency code to country code for billing address selection."""
    mapping = {
        "USD": "US",  # United States
        "EUR": "DE",  # Germany (largest Euro economy)
        "GBP": "GB",  # United Kingdom
        "INR": "IN",  # India
        "JPY": "JP",  # Japan
        "CNY": "JP",  # China -> Fallback to JP (nearest major)
        "KRW": "JP",  # South Korea -> Fallback to JP
        "RUB": "DE",  # Russia -> Fallback to DE
        "BRL": "BR",  # Brazil
        "CAD": "CA",  # Canada
        "AUD": "AU",  # Australia
        "MXN": "MX",  # Mexico
        "SGD": "SG",  # Singapore
        "HKD": "HK",  # Hong Kong
        "THB": "TH",  # Thailand
        "VND": "SG",  # Vietnam -> Fallback to SG
        "PHP": "PH",  # Philippines
        "IDR": "ID",  # Indonesia
        "MYR": "MY",  # Malaysia
        "ZAR": "GB",  # South Africa -> Fallback to GB
        "CHF": "CH",  # Switzerland
        "SEK": "SE",  # Sweden
        "NOK": "NO",  # Norway
        "DKK": "DK",  # Denmark
        "PLN": "PL",  # Poland
        "TRY": "GB",  # Turkey -> Fallback to GB
        "AED": "AE",  # UAE
        "SAR": "AE",  # Saudi Arabia -> Fallback to AE
        "ILS": "GB",  # Israel -> Fallback to GB
        "TWD": "JP",  # Taiwan -> Fallback to JP
        "NZD": "NZ",  # New Zealand
    }
    return mapping.get(currency.upper(), "US")  # Default to US


def format_time(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.2f}s"
    mins = int(seconds // 60)
    secs = seconds % 60
    return f"{mins}m {secs:.2f}s"
