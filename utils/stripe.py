import re
import random
import string
import uuid
import asyncio

from curl_cffi.requests import AsyncSession as CurlSession

from utils.constants import USER_AGENTS, TLS_PROFILES, get_random_browser_profile


# Fingerprints are now generated fresh per attempt (rotation)


def _is_mobile_ua(ua: str) -> bool:
    """Check if a User-Agent string is from a mobile device."""
    return any(k in ua for k in ("Mobile", "Android", "iPhone", "iPad", "iPod"))


def _detect_browser_info(ua: str) -> dict:
    """Extract browser name, version, platform, and mobile flag from user agent string."""
    info = {"browser": "Chrome", "version": "131", "platform": "Windows", "mobile": False}

    # Detect mobile
    info["mobile"] = _is_mobile_ua(ua)

    # Detect platform
    if "iPhone" in ua or "iPad" in ua or "iPod" in ua:
        info["platform"] = "iOS"
    elif "Macintosh" in ua or "Mac OS X" in ua:
        info["platform"] = "macOS"
    elif "Android" in ua:
        info["platform"] = "Android"
    elif "Linux" in ua:
        info["platform"] = "Linux"
    else:
        info["platform"] = "Windows"

    # Detect browser + version
    if "Edg/" in ua:
        info["browser"] = "Edge"
        m = re.search(r'Edg/(\d+)', ua)
        if m: info["version"] = m.group(1)
    elif "OPR/" in ua:
        info["browser"] = "Opera"
        m = re.search(r'Chrome/(\d+)', ua)
        if m: info["version"] = m.group(1)
    elif "CriOS/" in ua:
        # Chrome on iOS
        info["browser"] = "CriOS"
        m = re.search(r'CriOS/(\d+)', ua)
        if m: info["version"] = m.group(1)
    elif "Firefox/" in ua:
        info["browser"] = "Firefox"
        m = re.search(r'Firefox/(\d+)', ua)
        if m: info["version"] = m.group(1)
    elif "Safari/" in ua and "Chrome" not in ua:
        info["browser"] = "Safari"
        m = re.search(r'Version/(\d+)', ua)
        if m: info["version"] = m.group(1)
    else:
        info["browser"] = "Chrome"
        m = re.search(r'Chrome/(\d+)', ua)
        if m: info["version"] = m.group(1)

    return info


def _get_grease_brand(major: str) -> tuple:
    """Get deterministic GREASE brand based on Chrome major version.
    Real Chrome picks GREASE brand deterministically, not randomly."""
    grease_options = [
        ("Not_A Brand", "8"),
        ("Not A(Brand", "99"),
        ("Not)A;Brand", "99"),
        ("Not/A)Brand", "8"),
    ]
    idx = int(major) % len(grease_options)
    return grease_options[idx]


def get_stripe_headers(user_agent: str = None) -> dict:
    """Stripe-specific headers for use with curl_cffi impersonate.
    When user_agent is provided, sets correct sec-ch-ua headers
    (critical for Edge/Opera where curl_cffi defaults don't match UA)."""
    headers = {
        "accept": "application/json",
        "accept-language": random.choice([
            "en-US,en;q=0.9",
            "en-GB,en;q=0.9,en-US;q=0.8",
            "en-US,en;q=0.9,en-GB;q=0.8",
            "en,en-US;q=0.9",
            "en-US,en;q=0.8",
            "en-GB,en-US;q=0.9,en;q=0.8",
            "en-US,en-GB;q=0.9,en;q=0.8",
        ]),
        "content-type": "application/x-www-form-urlencoded",
        "origin": "https://checkout.stripe.com",
        "referer": "https://checkout.stripe.com/",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
    }
    if user_agent:
        headers["user-agent"] = user_agent
        browser = _detect_browser_info(user_agent)
        v = browser["version"]
        platform = browser["platform"]
        is_mobile = browser["mobile"]
        if browser["browser"] in ("Chrome", "Edge", "Opera"):
            g_brand, g_ver = _get_grease_brand(v)
            if browser["browser"] == "Edge":
                headers["sec-ch-ua"] = f'"Chromium";v="{v}", "{g_brand}";v="{g_ver}", "Microsoft Edge";v="{v}"'
            elif browser["browser"] == "Opera":
                headers["sec-ch-ua"] = f'"Chromium";v="{v}", "{g_brand}";v="{g_ver}", "Opera";v="{v}"'
            else:
                headers["sec-ch-ua"] = f'"Chromium";v="{v}", "{g_brand}";v="{g_ver}", "Google Chrome";v="{v}"'
            headers["sec-ch-ua-mobile"] = "?1" if is_mobile else "?0"
            # Platform header: Android for Android phones, etc.
            if platform == "Android":
                headers["sec-ch-ua-platform"] = '"Android"'
            elif platform == "iOS":
                headers["sec-ch-ua-platform"] = '"iOS"'
            else:
                headers["sec-ch-ua-platform"] = f'"{platform}"'
    return headers


def get_headers(stripe_js: bool = False) -> dict:
    """Return headers mimicking Stripe.js browser requests."""
    ua = random.choice(USER_AGENTS)
    headers = {
        "accept": "application/json",
        "content-type": "application/x-www-form-urlencoded",
        "origin": "https://checkout.stripe.com",
        "referer": "https://checkout.stripe.com/",
        "user-agent": ua
    }
    if stripe_js:
        browser = _detect_browser_info(ua)
        v = browser["version"]
        platform = browser["platform"]

        headers["accept-language"] = random.choice([
            "en-US,en;q=0.9",
            "en-GB,en;q=0.9,en-US;q=0.8",
            "en-US,en;q=0.9,en-GB;q=0.8",
            "en,en-US;q=0.9",
            "en-US,en;q=0.8",
            "en-GB,en-US;q=0.9,en;q=0.8",
            "en-US,en-GB;q=0.9,en;q=0.8",
        ])
        headers["sec-fetch-dest"] = "empty"
        headers["sec-fetch-mode"] = "cors"
        headers["sec-fetch-site"] = "same-site"

        # Dynamic sec-ch-ua based on actual browser (deterministic GREASE brand)
        if browser["browser"] in ("Chrome", "Edge", "Opera"):
            g_brand, g_ver = _get_grease_brand(v)
            if browser["browser"] == "Edge":
                headers["sec-ch-ua"] = f'"Chromium";v="{v}", "{g_brand}";v="{g_ver}", "Microsoft Edge";v="{v}"'
            elif browser["browser"] == "Opera":
                headers["sec-ch-ua"] = f'"Chromium";v="{v}", "{g_brand}";v="{g_ver}", "Opera";v="{v}"'
            else:
                headers["sec-ch-ua"] = f'"Chromium";v="{v}", "{g_brand}";v="{g_ver}", "Google Chrome";v="{v}"'
            headers["sec-ch-ua-mobile"] = "?1" if browser.get("mobile") else "?0"
            if platform == "Android":
                headers["sec-ch-ua-platform"] = '"Android"'
            elif platform == "iOS":
                headers["sec-ch-ua-platform"] = '"iOS"'
            else:
                headers["sec-ch-ua-platform"] = f'"{platform}"'
        # Firefox/Safari don't send sec-ch-ua

    return headers

import hashlib
import json as _json
import aiohttp
import time as _time


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  X-Stripe-Telemetry tracking
#  Real Stripe.js sends this on every request after the first
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_last_request_metrics = {}


def record_stripe_request(request_id: str, duration_ms: int):
    """Record metrics from a Stripe API response for telemetry header.
    
    Call this after every Stripe API request with:
    - request_id: from response header 'Request-Id' (e.g. 'req_xxx')
    - duration_ms: how long the request took in ms
    """
    global _last_request_metrics
    _last_request_metrics = {
        "request_id": request_id,
        "request_duration_ms": duration_ms,
    }


def get_stripe_telemetry_header() -> str | None:
    """Get X-Stripe-Telemetry header value if we have previous request metrics.
    
    Returns None on first request (real Stripe.js doesn't send it on first request).
    """
    if not _last_request_metrics:
        return None
    return _json.dumps({"last_request_metrics": _last_request_metrics})

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Real Stripe.js hash scraping from CDN
#  Auto-refreshes every 3 hours (TTL)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_STRIPE_HASH_TTL = 3 * 60 * 60  # 3 jam dalam detik

_cached_stripe_hashes = {
    "core": None,     # stripe.js main bundle hash
    "v3": None,       # stripe-js-v3 module hash
    "fetched_at": 0,  # timestamp terakhir fetch (epoch seconds)
}
_stripe_hash_lock = None  # asyncio.Lock, lazy init


def _is_hash_stale() -> bool:
    """Check apakah hash sudah expired (lebih dari 3 jam)."""
    if not _cached_stripe_hashes["core"]:
        return True  # Belum pernah fetch
    elapsed = _time.time() - _cached_stripe_hashes["fetched_at"]
    return elapsed >= _STRIPE_HASH_TTL


async def _get_hash_lock():
    """Lazy init asyncio.Lock (harus di dalam event loop)."""
    global _stripe_hash_lock
    if _stripe_hash_lock is None:
        _stripe_hash_lock = asyncio.Lock()
    return _stripe_hash_lock


async def fetch_stripe_js_hashes(force: bool = False):
    """Fetch real Stripe.js from CDN and extract build hashes.
    
    Auto-refreshes setiap 3 jam. Bisa dipanggil berkali-kali — 
    hanya fetch ulang jika TTL expired atau force=True.
    
    Extracts fingerprint hashes from the webpack bundle's 
    'fingerprinted/js/' asset paths, which are the same hashes 
    Stripe uses to identify legitimate JS clients.
    """
    global _cached_stripe_hashes
    
    # Skip jika hash masih fresh (belum expired)
    if not force and not _is_hash_stale():
        return
    
    # Prevent concurrent fetches
    lock = await _get_hash_lock()
    async with lock:
        # Double-check setelah acquire lock
        if not force and not _is_hash_stale():
            return
        
        old_core = _cached_stripe_hashes.get("core")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://js.stripe.com/v3/",
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                        "Accept": "*/*",
                    },
                    timeout=aiohttp.ClientTimeout(total=15),
                    ssl=False,
                ) as resp:
                    if resp.status != 200:
                        print(f"[DEBUG] Stripe.js fetch failed: HTTP {resp.status}")
                        # Jangan reset fetched_at agar retry lagi nanti
                        return
                    
                    content = await resp.text()
                    
                    # Extract fingerprint hashes from the webpack bundle
                    # Real Stripe.js contains paths like: fingerprinted/js/MODULE-HASH.js
                    js_hashes = re.findall(
                        r'fingerprinted/js/[a-zA-Z0-9_-]+-([a-f0-9]{20,40})\.js',
                        content
                    )
                    
                    if js_hashes:
                        # Use first two distinct hashes for core and v3
                        unique_hashes = list(dict.fromkeys(js_hashes))
                        _cached_stripe_hashes["core"] = unique_hashes[0][:10]
                        if len(unique_hashes) > 1:
                            _cached_stripe_hashes["v3"] = unique_hashes[1][:10]
                        else:
                            _cached_stripe_hashes["v3"] = unique_hashes[0][:10]
                        _cached_stripe_hashes["fetched_at"] = _time.time()
                        
                        changed = old_core != _cached_stripe_hashes["core"]
                        status = "🔄 UPDATED" if (old_core and changed) else "✅ Fetched"
                        print(f"[DEBUG] {status} Stripe.js hashes: "
                              f"core={_cached_stripe_hashes['core']}, "
                              f"v3={_cached_stripe_hashes['v3']} "
                              f"(from {len(unique_hashes)} unique hashes, "
                              f"TTL={_STRIPE_HASH_TTL//3600}h)")
                    else:
                        # Fallback: derive hash from content itself
                        content_hash = hashlib.sha256(content.encode()).hexdigest()
                        _cached_stripe_hashes["core"] = content_hash[:10]
                        _cached_stripe_hashes["v3"] = content_hash[10:20]
                        _cached_stripe_hashes["fetched_at"] = _time.time()
                        print(f"[DEBUG] ⚠️ No fingerprint paths found, using content hash: "
                              f"core={_cached_stripe_hashes['core']}, "
                              f"v3={_cached_stripe_hashes['v3']}")
                        
        except Exception as e:
            print(f"[DEBUG] ❌ Stripe.js hash fetch error: {str(e)[:80]}")
            # Jika sudah punya hash lama, tetap pakai — jangan kosongkan
            # Hanya set fetched_at mundur sedikit agar retry lebih cepat (30 menit)
            if _cached_stripe_hashes["core"]:
                _cached_stripe_hashes["fetched_at"] = _time.time() - _STRIPE_HASH_TTL + 1800
                print(f"[DEBUG] ⚠️ Keeping old hashes, retry in ~30min")


def get_random_stripe_js_agent() -> str:
    """Get Stripe.js payment_user_agent using real CDN hashes when available.
    
    Jika hash sudah stale, akan trigger background refresh pada call berikutnya.
    """
    core = _cached_stripe_hashes.get("core")
    v3 = _cached_stripe_hashes.get("v3")
    
    # Schedule background refresh jika stale (non-blocking)
    if _is_hash_stale():
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(fetch_stripe_js_hashes())
            print(f"[DEBUG] 🔄 Stripe.js hash refresh scheduled (TTL expired)")
        except RuntimeError:
            pass  # No event loop — will be refreshed on next async call
    
    if not core or not v3:
        # Last resort fallback — should rarely happen if fetch_stripe_js_hashes() was called
        core = hashlib.sha256(f"stripe-core-{random.randint(0,9999)}".encode()).hexdigest()[:10]
        v3 = hashlib.sha256(f"stripe-v3-{random.randint(0,9999)}".encode()).hexdigest()[:10]
        print(f"[DEBUG] ⚠️ Using generated hashes (CDN not fetched yet)")
    
    return f"stripe.js%2F{core}%3B+stripe-js-v3%2F{v3}%3B+checkout"


def get_stripe_js_version() -> str:
    """Get Stripe.js build version hash (e.g. 'd50036e08e').
    
    This is sent as 'version' field in confirm payload.
    Real browser sends this same hash in both r.stripe.com events
    and the confirm request body.
    """
    core = _cached_stripe_hashes.get("core")
    if not core:
        core = hashlib.sha256(f"stripe-core-{random.randint(0,9999)}".encode()).hexdigest()[:10]
    return core


def _rand_hex(length: int) -> str:
    return ''.join(random.choices(string.hexdigits[:16], k=length))


def _uuid_format() -> str:
    return f"{_rand_hex(8)}-{_rand_hex(4)}-4{_rand_hex(3)}-{random.choice('89ab')}{_rand_hex(3)}-{_rand_hex(12)}"


def _extended_uuid() -> str:
    """Generate Stripe-style extended UUID.
    
    Real Stripe muid/guid/sid have 5-6 extra hex chars appended
    to the last segment of a UUID v4, making them 41-42 chars.
    Example from DevTools: b9107d56-3767-4c38-bc00-c1ba177abb6dcde98
    Standard UUID would be: b9107d56-3767-4c38-bc00-c1ba177abb6d (36 chars)
    Extended:               b9107d56-3767-4c38-bc00-c1ba177abb6dcde98 (41 chars)
    """
    base = _uuid_format()
    extra_len = random.choice([5, 5, 5, 6])  # Usually 5, sometimes 6
    extra = _rand_hex(extra_len)
    return base + extra


def generate_stripe_mid() -> str:
    """Generate realistic __stripe_mid cookie value (extended UUID format)."""
    return _extended_uuid()


def generate_stripe_sid() -> str:
    """Generate realistic __stripe_sid cookie value (extended UUID format)."""
    return _extended_uuid()


def generate_stripe_fingerprints(user_id: int = None) -> dict:
    """Generate fresh Stripe.js fingerprint identifiers per attempt.
    Uses extended UUID format matching real Stripe (41-42 chars, not standard 36)."""
    muid = _extended_uuid()
    guid = _extended_uuid()
    sid = _extended_uuid()
    return {"muid": muid, "guid": guid, "sid": sid}


def generate_eid() -> str:
    """Generate a valid UUID v4 for the eid parameter."""
    return str(uuid.uuid4())


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Canvas/WebGL Device Fingerprint
#  Simulates what Stripe Radar collects from real browsers
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Real GPU renderers seen on common hardware
_WEBGL_RENDERERS = [
    # ━━━ Windows — NVIDIA (D3D11) ━━━
    {"vendor": "Google Inc. (NVIDIA)", "renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 4090 Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (NVIDIA)", "renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 4080 SUPER Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (NVIDIA)", "renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 4070 Ti SUPER Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (NVIDIA)", "renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 4070 Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (NVIDIA)", "renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 4060 Ti Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (NVIDIA)", "renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 4060 Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (NVIDIA)", "renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 3090 Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (NVIDIA)", "renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 3080 Ti Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (NVIDIA)", "renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 3080 Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (NVIDIA)", "renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 3070 Ti Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (NVIDIA)", "renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 3070 Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (NVIDIA)", "renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Ti Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (NVIDIA)", "renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (NVIDIA)", "renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 3050 Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (NVIDIA)", "renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 2080 Ti Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (NVIDIA)", "renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 2080 SUPER Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (NVIDIA)", "renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 2070 SUPER Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (NVIDIA)", "renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 2060 SUPER Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (NVIDIA)", "renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 2060 Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (NVIDIA)", "renderer": "ANGLE (NVIDIA, NVIDIA GeForce GTX 1080 Ti Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (NVIDIA)", "renderer": "ANGLE (NVIDIA, NVIDIA GeForce GTX 1080 Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (NVIDIA)", "renderer": "ANGLE (NVIDIA, NVIDIA GeForce GTX 1070 Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (NVIDIA)", "renderer": "ANGLE (NVIDIA, NVIDIA GeForce GTX 1660 SUPER Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (NVIDIA)", "renderer": "ANGLE (NVIDIA, NVIDIA GeForce GTX 1660 Ti Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (NVIDIA)", "renderer": "ANGLE (NVIDIA, NVIDIA GeForce GTX 1650 SUPER Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (NVIDIA)", "renderer": "ANGLE (NVIDIA, NVIDIA GeForce GTX 1650 Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (NVIDIA)", "renderer": "ANGLE (NVIDIA, NVIDIA GeForce GTX 1060 6GB Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (NVIDIA)", "renderer": "ANGLE (NVIDIA, NVIDIA GeForce GTX 1050 Ti Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    # ━━━ Windows — AMD (D3D11) ━━━
    {"vendor": "Google Inc. (AMD)", "renderer": "ANGLE (AMD, AMD Radeon RX 7900 XTX Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (AMD)", "renderer": "ANGLE (AMD, AMD Radeon RX 7900 XT Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (AMD)", "renderer": "ANGLE (AMD, AMD Radeon RX 7800 XT Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (AMD)", "renderer": "ANGLE (AMD, AMD Radeon RX 7700 XT Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (AMD)", "renderer": "ANGLE (AMD, AMD Radeon RX 7600 Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (AMD)", "renderer": "ANGLE (AMD, AMD Radeon RX 6900 XT Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (AMD)", "renderer": "ANGLE (AMD, AMD Radeon RX 6800 XT Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (AMD)", "renderer": "ANGLE (AMD, AMD Radeon RX 6700 XT Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (AMD)", "renderer": "ANGLE (AMD, AMD Radeon RX 6600 XT Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (AMD)", "renderer": "ANGLE (AMD, AMD Radeon RX 5700 XT Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (AMD)", "renderer": "ANGLE (AMD, AMD Radeon RX 5600 XT Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (AMD)", "renderer": "ANGLE (AMD, AMD Radeon RX 580 Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (AMD)", "renderer": "ANGLE (AMD, AMD Radeon RX 570 Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    # ━━━ Windows — Intel (D3D11) ━━━
    {"vendor": "Google Inc. (Intel)", "renderer": "ANGLE (Intel, Intel(R) UHD Graphics 770 Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (Intel)", "renderer": "ANGLE (Intel, Intel(R) UHD Graphics 730 Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (Intel)", "renderer": "ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (Intel)", "renderer": "ANGLE (Intel, Intel(R) UHD Graphics 620 Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (Intel)", "renderer": "ANGLE (Intel, Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (Intel)", "renderer": "ANGLE (Intel, Intel(R) Iris(R) Plus Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (Intel)", "renderer": "ANGLE (Intel, Intel(R) Arc(TM) A770 Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (Intel)", "renderer": "ANGLE (Intel, Intel(R) Arc(TM) A750 Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    # ━━━ macOS — Apple Silicon (OpenGL 4.1) ━━━
    {"vendor": "Google Inc. (Apple)", "renderer": "ANGLE (Apple, Apple M1, OpenGL 4.1)"},
    {"vendor": "Google Inc. (Apple)", "renderer": "ANGLE (Apple, Apple M1 Pro, OpenGL 4.1)"},
    {"vendor": "Google Inc. (Apple)", "renderer": "ANGLE (Apple, Apple M1 Max, OpenGL 4.1)"},
    {"vendor": "Google Inc. (Apple)", "renderer": "ANGLE (Apple, Apple M2, OpenGL 4.1)"},
    {"vendor": "Google Inc. (Apple)", "renderer": "ANGLE (Apple, Apple M2 Pro, OpenGL 4.1)"},
    {"vendor": "Google Inc. (Apple)", "renderer": "ANGLE (Apple, Apple M2 Max, OpenGL 4.1)"},
    {"vendor": "Google Inc. (Apple)", "renderer": "ANGLE (Apple, Apple M3, OpenGL 4.1)"},
    {"vendor": "Google Inc. (Apple)", "renderer": "ANGLE (Apple, Apple M3 Pro, OpenGL 4.1)"},
    {"vendor": "Google Inc. (Apple)", "renderer": "ANGLE (Apple, Apple M3 Max, OpenGL 4.1)"},
    {"vendor": "Google Inc. (Apple)", "renderer": "ANGLE (Apple, Apple M4, OpenGL 4.1)"},
    {"vendor": "Google Inc. (Apple)", "renderer": "ANGLE (Apple, Apple M4 Pro, OpenGL 4.1)"},
    {"vendor": "Google Inc. (AMD)", "renderer": "ANGLE (AMD, AMD Radeon Pro 5500M, OpenGL 4.1)"},
    {"vendor": "Google Inc. (AMD)", "renderer": "ANGLE (AMD, AMD Radeon Pro 580, OpenGL 4.1)"},
    # ━━━ Linux — Mesa/OpenGL 4.5 ━━━
    {"vendor": "Google Inc. (Intel)", "renderer": "ANGLE (Intel, Mesa Intel(R) UHD Graphics 630 (CFL GT2), OpenGL 4.5)"},
    {"vendor": "Google Inc. (Intel)", "renderer": "ANGLE (Intel, Mesa Intel(R) UHD Graphics 770 (ADL-S GT1), OpenGL 4.5)"},
    {"vendor": "Google Inc. (Intel)", "renderer": "ANGLE (Intel, Mesa Intel(R) Iris(R) Xe Graphics (TGL GT2), OpenGL 4.5)"},
    {"vendor": "Google Inc. (NVIDIA)", "renderer": "ANGLE (NVIDIA, NVIDIA GeForce GTX 1650/PCIe/SSE2, OpenGL 4.5)"},
    {"vendor": "Google Inc. (NVIDIA)", "renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060/PCIe/SSE2, OpenGL 4.5)"},
    {"vendor": "Google Inc. (NVIDIA)", "renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 3070/PCIe/SSE2, OpenGL 4.5)"},
    {"vendor": "Google Inc. (NVIDIA)", "renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 4070/PCIe/SSE2, OpenGL 4.5)"},
    {"vendor": "Google Inc. (AMD)", "renderer": "ANGLE (AMD, AMD Radeon RX 580, OpenGL 4.5)"},
    {"vendor": "Google Inc. (AMD)", "renderer": "ANGLE (AMD, AMD Radeon RX 6700 XT, OpenGL 4.5)"},
    {"vendor": "Google Inc. (AMD)", "renderer": "ANGLE (AMD, AMD Radeon RX 7800 XT, OpenGL 4.5)"},
]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Mobile GPU Renderers — Real device WebGL fingerprints
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_MOBILE_WEBGL_RENDERERS = [
    # ━━━ Qualcomm Adreno — Samsung, OnePlus, Xiaomi, Sony, OPPO, Vivo, etc. ━━━
    {"vendor": "Qualcomm", "renderer": "Adreno (TM) 750"},           # Snapdragon 8 Gen 3 — Galaxy S24, OnePlus 12
    {"vendor": "Qualcomm", "renderer": "Adreno (TM) 740"},           # Snapdragon 8 Gen 2 — Galaxy S23, Xiaomi 13
    {"vendor": "Qualcomm", "renderer": "Adreno (TM) 730"},           # Snapdragon 8 Gen 1 — Galaxy S22, OnePlus 10
    {"vendor": "Qualcomm", "renderer": "Adreno (TM) 725"},           # Snapdragon 8+ Gen 1
    {"vendor": "Qualcomm", "renderer": "Adreno (TM) 660"},           # Snapdragon 888 — Galaxy S21, Mi 11
    {"vendor": "Qualcomm", "renderer": "Adreno (TM) 650"},           # Snapdragon 865 — Galaxy S20, OnePlus 8
    {"vendor": "Qualcomm", "renderer": "Adreno (TM) 642L"},          # Snapdragon 778G — Galaxy A52s, Nothing Phone 1
    {"vendor": "Qualcomm", "renderer": "Adreno (TM) 619"},           # Snapdragon 695 — Galaxy A54, Redmi Note 12 Pro
    {"vendor": "Qualcomm", "renderer": "Adreno (TM) 618"},           # Snapdragon 730G — Galaxy A72, Pixel 4a
    {"vendor": "Qualcomm", "renderer": "Adreno (TM) 616"},           # Snapdragon 720G — Galaxy A52
    {"vendor": "Qualcomm", "renderer": "Adreno (TM) 612"},           # Snapdragon 680 — Galaxy A34, Redmi Note 12
    {"vendor": "Qualcomm", "renderer": "Adreno (TM) 610"},           # Snapdragon 665 — Galaxy A30
    {"vendor": "Qualcomm", "renderer": "Adreno (TM) 512"},           # Snapdragon 636 — Nokia X30
    # ━━━ ARM Mali — Samsung Exynos, Huawei Kirin, MediaTek Dimensity ━━━
    {"vendor": "ARM", "renderer": "Mali-G720-Immortalis MC12"},      # Exynos 2400 — Galaxy S24 (global)
    {"vendor": "ARM", "renderer": "Mali-G715-Immortalis MC11"},      # Exynos 2200 — Galaxy S22 (global)
    {"vendor": "ARM", "renderer": "Mali-G710 MC10"},                 # Dimensity 9200 — Vivo X90
    {"vendor": "ARM", "renderer": "Mali-G78 MC14"},                  # Exynos 2100 — Galaxy S21 (global)
    {"vendor": "ARM", "renderer": "Mali-G77 MC9"},                   # Kirin 9000 — Huawei Mate 40 Pro
    {"vendor": "ARM", "renderer": "Mali-G76 MC4"},                   # Kirin 990 — Huawei P40 Pro
    {"vendor": "ARM", "renderer": "Mali-G72 MC12"},                  # Kirin 970 — Huawei P20 Pro
    {"vendor": "ARM", "renderer": "Mali-G68 MC4"},                   # Dimensity 1080 — Redmi Note 12 Pro
    {"vendor": "ARM", "renderer": "Mali-G57 MC3"},                   # Dimensity 920 — OPPO Reno 7
    {"vendor": "ARM", "renderer": "Mali-G57 MC2"},                   # Dimensity 810 — Realme Narzo 50
    {"vendor": "ARM", "renderer": "Mali-G52 MC2"},                   # MediaTek Helio G99 — Infinix, Tecno
    {"vendor": "ARM", "renderer": "Mali-G52"},                       # Helio G85 — Redmi Note 10
    {"vendor": "ARM", "renderer": "Mali-G51 MP4"},                   # Helio P90 — OPPO Reno
    # ━━━ Apple GPU — iPhone & iPad ━━━
    {"vendor": "Apple Inc.", "renderer": "Apple GPU"},               # Generic Apple label (all iPhones)
    {"vendor": "Apple Inc.", "renderer": "Apple A17 Pro GPU"},       # iPhone 15 Pro
    {"vendor": "Apple Inc.", "renderer": "Apple A16 GPU"},           # iPhone 14 Pro
    {"vendor": "Apple Inc.", "renderer": "Apple A15 GPU"},           # iPhone 13 / 14
    {"vendor": "Apple Inc.", "renderer": "Apple A14 GPU"},           # iPhone 12
    {"vendor": "Apple Inc.", "renderer": "Apple M2 GPU"},            # iPad Pro M2
    {"vendor": "Apple Inc.", "renderer": "Apple M1 GPU"},            # iPad Pro M1 / iPad Air M1
    # ━━━ Google Tensor (Pixel phones) ━━━
    {"vendor": "ARM", "renderer": "Mali-G715-Immortalis MC10"},      # Tensor G4 — Pixel 9
    {"vendor": "ARM", "renderer": "Mali-G710 MC10"},                 # Tensor G3 — Pixel 8
    {"vendor": "ARM", "renderer": "Mali-G78 MP20"},                  # Tensor G2 — Pixel 7
    {"vendor": "ARM", "renderer": "Mali-G78"},                       # Tensor — Pixel 6
    # ━━━ PowerVR (some budget phones) ━━━
    {"vendor": "Imagination Technologies", "renderer": "PowerVR Rogue GE8320"},  # MediaTek MT6769
    {"vendor": "Imagination Technologies", "renderer": "PowerVR Rogue GE8322"},  # MediaTek MT6768
]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Mobile Screen Resolutions — All Major Brands
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_MOBILE_SCREEN_RESOLUTIONS = [
    # ━━━ iPhone ━━━
    {"w": 393, "h": 852, "avail_w": 393, "avail_h": 852, "dpr": 3},    # iPhone 15 Pro / 14 Pro
    {"w": 430, "h": 932, "avail_w": 430, "avail_h": 932, "dpr": 3},    # iPhone 15 Pro Max / 14 Pro Max
    {"w": 390, "h": 844, "avail_w": 390, "avail_h": 844, "dpr": 3},    # iPhone 13 / 14
    {"w": 428, "h": 926, "avail_w": 428, "avail_h": 926, "dpr": 3},    # iPhone 13 Pro Max / 14 Plus
    {"w": 375, "h": 812, "avail_w": 375, "avail_h": 812, "dpr": 3},    # iPhone X / 11 Pro / 12 Mini
    {"w": 414, "h": 896, "avail_w": 414, "avail_h": 896, "dpr": 3},    # iPhone 11 Pro Max
    {"w": 375, "h": 667, "avail_w": 375, "avail_h": 667, "dpr": 2},    # iPhone SE / 8 / 7 / 6s
    # ━━━ iPad ━━━
    {"w": 1024, "h": 1366, "avail_w": 1024, "avail_h": 1366, "dpr": 2},  # iPad Pro 12.9"
    {"w": 834, "h": 1194, "avail_w": 834, "avail_h": 1194, "dpr": 2},    # iPad Pro 11"
    {"w": 820, "h": 1180, "avail_w": 820, "avail_h": 1180, "dpr": 2},    # iPad Air (M1)
    {"w": 810, "h": 1080, "avail_w": 810, "avail_h": 1080, "dpr": 2},    # iPad 10th gen
    # ━━━ Samsung Galaxy S24/S23/S22 (QHD+ Dynamic AMOLED) ━━━
    {"w": 360, "h": 780, "avail_w": 360, "avail_h": 780, "dpr": 3},     # Galaxy S24
    {"w": 384, "h": 854, "avail_w": 384, "avail_h": 854, "dpr": 2.8125},# Galaxy S24+
    {"w": 412, "h": 915, "avail_w": 412, "avail_h": 915, "dpr": 3.5},   # Galaxy S24 Ultra
    {"w": 360, "h": 780, "avail_w": 360, "avail_h": 780, "dpr": 3},     # Galaxy S23
    {"w": 384, "h": 854, "avail_w": 384, "avail_h": 854, "dpr": 2.8125},# Galaxy S23+
    {"w": 412, "h": 915, "avail_w": 412, "avail_h": 915, "dpr": 3.5},   # Galaxy S23 Ultra
    # ━━━ Samsung Galaxy A Series ━━━
    {"w": 412, "h": 915, "avail_w": 412, "avail_h": 915, "dpr": 2.625}, # Galaxy A55
    {"w": 412, "h": 883, "avail_w": 412, "avail_h": 883, "dpr": 2.625}, # Galaxy A54
    {"w": 393, "h": 851, "avail_w": 393, "avail_h": 851, "dpr": 2.75},  # Galaxy A35
    {"w": 384, "h": 854, "avail_w": 384, "avail_h": 854, "dpr": 2.0},   # Galaxy A25
    # ━━━ Samsung Galaxy Z Fold/Flip ━━━
    {"w": 360, "h": 816, "avail_w": 360, "avail_h": 816, "dpr": 3},     # Galaxy Z Fold 5 (cover)
    {"w": 412, "h": 914, "avail_w": 412, "avail_h": 914, "dpr": 2.625}, # Galaxy Z Fold 5 (inner)
    {"w": 360, "h": 748, "avail_w": 360, "avail_h": 748, "dpr": 3},     # Galaxy Z Flip 5
    # ━━━ Google Pixel ━━━
    {"w": 412, "h": 915, "avail_w": 412, "avail_h": 883, "dpr": 2.625}, # Pixel 9 Pro XL
    {"w": 412, "h": 915, "avail_w": 412, "avail_h": 883, "dpr": 2.625}, # Pixel 8 Pro
    {"w": 393, "h": 851, "avail_w": 393, "avail_h": 819, "dpr": 2.75},  # Pixel 8
    {"w": 412, "h": 892, "avail_w": 412, "avail_h": 860, "dpr": 2.625}, # Pixel 7 Pro
    {"w": 393, "h": 851, "avail_w": 393, "avail_h": 819, "dpr": 2.75},  # Pixel 7
    # ━━━ Xiaomi / Redmi ━━━
    {"w": 393, "h": 873, "avail_w": 393, "avail_h": 873, "dpr": 2.75},  # Xiaomi 14
    {"w": 412, "h": 915, "avail_w": 412, "avail_h": 915, "dpr": 3.5},   # Xiaomi 14 Ultra
    {"w": 393, "h": 873, "avail_w": 393, "avail_h": 873, "dpr": 2.75},  # Xiaomi 13
    {"w": 360, "h": 800, "avail_w": 360, "avail_h": 800, "dpr": 3},     # Redmi Note 13 Pro
    {"w": 393, "h": 873, "avail_w": 393, "avail_h": 873, "dpr": 2.75},  # Redmi Note 12 Pro+
    {"w": 360, "h": 800, "avail_w": 360, "avail_h": 800, "dpr": 2},     # Redmi Note 12
    # ━━━ OnePlus ━━━
    {"w": 412, "h": 915, "avail_w": 412, "avail_h": 883, "dpr": 3.5},   # OnePlus 12
    {"w": 412, "h": 915, "avail_w": 412, "avail_h": 883, "dpr": 2.625}, # OnePlus 11
    {"w": 412, "h": 915, "avail_w": 412, "avail_h": 883, "dpr": 2.625}, # OnePlus 10 Pro
    # ━━━ OPPO / Realme / Vivo ━━━
    {"w": 412, "h": 915, "avail_w": 412, "avail_h": 915, "dpr": 2.625}, # OPPO Find X7 Ultra
    {"w": 360, "h": 800, "avail_w": 360, "avail_h": 800, "dpr": 3},     # OPPO Reno 11
    {"w": 393, "h": 873, "avail_w": 393, "avail_h": 873, "dpr": 2.75},  # Realme GT 5 Pro
    {"w": 360, "h": 800, "avail_w": 360, "avail_h": 800, "dpr": 2},     # Realme 12 Pro
    {"w": 412, "h": 915, "avail_w": 412, "avail_h": 915, "dpr": 2.625}, # vivo X100 Pro
    {"w": 360, "h": 800, "avail_w": 360, "avail_h": 800, "dpr": 2.75},  # vivo V30
    # ━━━ Huawei / Honor ━━━
    {"w": 360, "h": 780, "avail_w": 360, "avail_h": 780, "dpr": 3},     # Huawei Mate 50 Pro
    {"w": 360, "h": 800, "avail_w": 360, "avail_h": 800, "dpr": 3},     # Honor Magic6 Pro
    {"w": 360, "h": 780, "avail_w": 360, "avail_h": 780, "dpr": 2.75},  # Honor 90
    # ━━━ Sony Xperia ━━━
    {"w": 360, "h": 840, "avail_w": 360, "avail_h": 840, "dpr": 3},     # Xperia 1 V (21:9)
    {"w": 360, "h": 780, "avail_w": 360, "avail_h": 780, "dpr": 2.5},   # Xperia 5 V
    # ━━━ Motorola ━━━
    {"w": 412, "h": 915, "avail_w": 412, "avail_h": 883, "dpr": 2.625}, # Motorola Edge 50 Ultra
    {"w": 360, "h": 800, "avail_w": 360, "avail_h": 800, "dpr": 2.75},  # moto g84
    # ━━━ Nothing Phone ━━━
    {"w": 412, "h": 915, "avail_w": 412, "avail_h": 883, "dpr": 2.625}, # Nothing Phone 2
    {"w": 393, "h": 873, "avail_w": 393, "avail_h": 873, "dpr": 2.75},  # Nothing Phone 1
    # ━━━ Budget phones (Infinix, Tecno, Blackview, etc.) ━━━
    {"w": 360, "h": 800, "avail_w": 360, "avail_h": 800, "dpr": 2},
    {"w": 360, "h": 780, "avail_w": 360, "avail_h": 780, "dpr": 2},
    {"w": 412, "h": 892, "avail_w": 412, "avail_h": 892, "dpr": 1.75},
    # ━━━ Samsung Galaxy Tab ━━━
    {"w": 800, "h": 1280, "avail_w": 800, "avail_h": 1280, "dpr": 2},   # Galaxy Tab S9+
    {"w": 753, "h": 1205, "avail_w": 753, "avail_h": 1205, "dpr": 2},   # Galaxy Tab S9
]

_SCREEN_RESOLUTIONS = [
    # ━━━ Desktop monitors ━━━
    {"w": 1920, "h": 1080, "avail_w": 1920, "avail_h": 1040, "dpr": 1},
    {"w": 1920, "h": 1080, "avail_w": 1920, "avail_h": 1032, "dpr": 1},
    {"w": 2560, "h": 1440, "avail_w": 2560, "avail_h": 1400, "dpr": 1},
    {"w": 3840, "h": 2160, "avail_w": 3840, "avail_h": 2120, "dpr": 1},
    {"w": 1920, "h": 1200, "avail_w": 1920, "avail_h": 1160, "dpr": 1},
    {"w": 2560, "h": 1080, "avail_w": 2560, "avail_h": 1040, "dpr": 1},   # Ultrawide
    {"w": 3440, "h": 1440, "avail_w": 3440, "avail_h": 1400, "dpr": 1},   # Ultrawide QHD
    {"w": 1280, "h": 1024, "avail_w": 1280, "avail_h": 984, "dpr": 1},    # 5:4 monitor
    # ━━━ Laptops (Windows scaling) ━━━
    {"w": 1920, "h": 1080, "avail_w": 1920, "avail_h": 1032, "dpr": 1.25},
    {"w": 1536, "h": 864, "avail_w": 1536, "avail_h": 824, "dpr": 1.25},
    {"w": 1366, "h": 768, "avail_w": 1366, "avail_h": 728, "dpr": 1},     # Common laptop
    {"w": 1600, "h": 900, "avail_w": 1600, "avail_h": 860, "dpr": 1},     # HD+ laptop
    {"w": 1280, "h": 720, "avail_w": 1280, "avail_h": 680, "dpr": 1},     # HD laptop
    {"w": 3840, "h": 2160, "avail_w": 3840, "avail_h": 2120, "dpr": 1.5}, # 4K laptop scaled
    # ━━━ macOS / Retina displays ━━━
    {"w": 1440, "h": 900, "avail_w": 1440, "avail_h": 875, "dpr": 2},     # MacBook Air 13"
    {"w": 2560, "h": 1600, "avail_w": 2560, "avail_h": 1575, "dpr": 2},   # MacBook Pro 13"
    {"w": 1680, "h": 1050, "avail_w": 1680, "avail_h": 1025, "dpr": 2},   # MacBook Pro 15"
    {"w": 1512, "h": 982, "avail_w": 1512, "avail_h": 957, "dpr": 2},     # MacBook Pro 14" M-series
    {"w": 1728, "h": 1117, "avail_w": 1728, "avail_h": 1092, "dpr": 2},   # MacBook Pro 16" M-series
    {"w": 2880, "h": 1800, "avail_w": 2880, "avail_h": 1775, "dpr": 2},   # MacBook Pro 15" Retina
    {"w": 3024, "h": 1964, "avail_w": 3024, "avail_h": 1939, "dpr": 2},   # MacBook Pro 14" native
    {"w": 3456, "h": 2234, "avail_w": 3456, "avail_h": 2209, "dpr": 2},   # MacBook Pro 16" native
    {"w": 5120, "h": 2880, "avail_w": 5120, "avail_h": 2855, "dpr": 2},   # iMac 5K
]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Device Fingerprint - Rotation per Attempt
#  Hanya metode yang diperlukan:
#  - Navigator (UA, Platform, Hardware Concurrency, Device Memory, Language)
#  - User-Agent Data (Client Hints: brands, platformVersion, architecture)
#  - Canvas (Position-based deterministic noise)
#  - WebGL (GPU vendor/renderer - Intel/NVIDIA/AMD)
#  - AudioContext (Imperceptible noise ~-80dB)
#  - Screen (Resolution, colorDepth, pixelRatio)
#  - Plugins/MimeTypes (PDF viewer consistency)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# AudioContext noise generator - imperceptible ~-80dB
def _generate_audio_noise() -> float:
    """Generate imperceptible audio noise (~-80dB) for AudioContext fingerprint."""
    # -80dB = 10^(-80/20) = 0.0001
    base_noise = 0.0001
    # Add small variation ±20%
    variation = random.uniform(0.8, 1.2)
    return base_noise * variation


def _generate_canvas_noise() -> str:
    """Generate deterministic position-based canvas noise."""
    # Position-based noise: slight pixel offsets that are deterministic per session
    offset_x = random.randint(-2, 2)
    offset_y = random.randint(-2, 2)
    return hashlib.sha256(f"canvas-{offset_x}-{offset_y}".encode()).hexdigest()[:32]


def _get_pdf_viewer_consistency() -> dict:
    """Generate consistent PDF plugin/MIME type data."""
    # Real browsers have consistent PDF viewer settings
    return {
        "has_pdf_viewer": True,
        "pdf_mime_type": "application/pdf",
        "pdf_plugin_enabled": random.choice([True, True, True, False]),  # 75% enabled
    }


def _get_client_hints(ua: str, platform: str) -> dict:
    """Generate User-Agent Client Hints (brands, platformVersion, architecture)."""
    browser = _detect_browser_info(ua)
    v = browser["version"]
    is_mobile = browser["mobile"]
    
    # Determine architecture based on platform
    if platform == "Linux armv81" or platform == "Linux armv8l":
        # Android mobile
        architecture = "arm"
        arch_bitness = "64"
        # Android version from UA → "14.0.0" style
        android_match = re.search(r'Android (\d+)', ua)
        android_ver = android_match.group(1) if android_match else "14"
        platform_version = f"{android_ver}.0.0"
    elif platform in ("iPhone", "iPad"):
        architecture = "arm"
        arch_bitness = "64"
        platform_version = "18.4.0"
    elif platform == "Win32":
        architecture = "x86"
        arch_bitness = "64"
        platform_version = "15.0.0"  # Windows 11
    elif platform == "MacIntel":
        architecture = "arm" if "Apple" in ua and random.random() > 0.3 else "x86"
        arch_bitness = "64"
        platform_version = "14.0.0"  # macOS Sonoma
    else:  # Linux desktop
        architecture = "x86"
        arch_bitness = "64"
        platform_version = "6.8.0"  # Linux kernel version
    
    # Extract device model from UA for Android phones
    model = ""
    if is_mobile and "Android" in ua:
        # Extract model: "Android 14; SM-S928B)" → "SM-S928B"
        model_match = re.search(r'Android [^;]+;\s*([^)]+)', ua)
        if model_match:
            model = model_match.group(1).strip()
    
    # GREASE brand handling
    g_brand, g_ver = _get_grease_brand(v)
    
    if browser["browser"] == "Edge":
        brands = [
            {"brand": "Chromium", "version": v},
            {"brand": g_brand, "version": g_ver},
            {"brand": "Microsoft Edge", "version": v}
        ]
    elif browser["browser"] == "Opera":
        brands = [
            {"brand": "Chromium", "version": v},
            {"brand": g_brand, "version": g_ver},
            {"brand": "Opera", "version": v}
        ]
    elif browser["browser"] in ("Firefox",):
        # Firefox doesn't send brands
        brands = []
    elif browser["browser"] in ("Safari", "CriOS"):
        # Safari / CriOS sends limited brands (iOS WebKit)
        brands = [{"brand": "Safari", "version": v}]
    else:  # Chrome (desktop + Android)
        brands = [
            {"brand": "Chromium", "version": v},
            {"brand": g_brand, "version": g_ver},
            {"brand": "Google Chrome", "version": v}
        ]
    
    return {
        "brands": brands,
        "platform_version": platform_version,
        "architecture": architecture,
        "arch_bitness": arch_bitness,
        "model": model,
        "mobile": is_mobile,
    }


def generate_device_fingerprint(user_agent: str, user_id: int = None) -> dict:
    """Generate a fresh device fingerprint per attempt (rotation).
    
    Setiap panggilan menghasilkan fingerprint baru - tidak ada caching per user.
    Supports BOTH desktop AND mobile devices:
    - Desktop: Windows/macOS/Linux with discrete GPU (NVIDIA/AMD/Intel)
    - Mobile: Android/iOS with mobile GPU (Adreno/Mali/Apple GPU)
    
    Fingerprinting methods:
    - Navigator: UA, Platform, Hardware Concurrency, Device Memory, Language
    - User-Agent Data: Client Hints API (brands, platformVersion, architecture, model)
    - Canvas: Position-based deterministic noise
    - WebGL: GPU vendor/renderer (Desktop: Intel/NVIDIA/AMD, Mobile: Adreno/Mali/Apple)
    - AudioContext: Imperceptible noise (~-80dB)
    - Screen: Resolution, colorDepth, pixelRatio
    - Plugins/MimeTypes: PDF viewer consistency
    """
    # Detect device type from UA
    is_mobile = _is_mobile_ua(user_agent)
    is_iphone = "iPhone" in user_agent
    is_ipad = "iPad" in user_agent
    is_ios = is_iphone or is_ipad
    is_android = "Android" in user_agent
    is_mac = "Macintosh" in user_agent or ("Mac OS X" in user_agent and not is_ios)
    is_linux = "Linux" in user_agent and not is_android
    
    if is_mobile:
        # ━━━ Mobile device fingerprint ━━━
        if is_ios:
            # iPhone/iPad — Apple GPU
            gpu_pool = [g for g in _MOBILE_WEBGL_RENDERERS if "Apple" in g["vendor"]]
            if is_ipad:
                screen_pool = [s for s in _MOBILE_SCREEN_RESOLUTIONS if s["w"] >= 750]  # Tablet size
            else:
                screen_pool = [s for s in _MOBILE_SCREEN_RESOLUTIONS if 370 <= s["w"] <= 440 and s["h"] < 960]  # Phone size
        else:
            # Android — Adreno or Mali GPU
            gpu_pool = [g for g in _MOBILE_WEBGL_RENDERERS if g["vendor"] in ("Qualcomm", "ARM", "Imagination Technologies")]
            screen_pool = [s for s in _MOBILE_SCREEN_RESOLUTIONS if s["w"] <= 450 and s["h"] < 960]  # Phone size
        
        gpu = random.choice(gpu_pool) if gpu_pool else random.choice(_MOBILE_WEBGL_RENDERERS)
        screen = random.choice(screen_pool) if screen_pool else random.choice(_MOBILE_SCREEN_RESOLUTIONS)
        
        # Platform string
        if is_ios:
            plat = "iPhone" if is_iphone else "iPad"
        else:
            plat = "Linux armv81"  # Standard Android platform string
        
        # Mobile hardware — realistic specs
        if is_ios:
            hw_concurrency = random.choice([6, 6, 6, 8])  # A15=6, A16=6, A17Pro=6
            device_memory = random.choice([4, 6, 8])       # iPhone RAM
            color_depth = 24
        else:
            # Android — varies by tier
            hw_concurrency = random.choice([4, 6, 8, 8, 8])  # Most flagships = 8
            device_memory = random.choice([4, 6, 8, 8, 12])   # Android RAM
            color_depth = 24
    else:
        # ━━━ Desktop device fingerprint ━━━
        if is_mac:
            gpu_pool = [g for g in _WEBGL_RENDERERS if "Apple" in g["renderer"] or "Apple" in g["vendor"]]
            screen_pool = [s for s in _SCREEN_RESOLUTIONS if s["dpr"] == 2]
        elif is_linux:
            gpu_pool = [g for g in _WEBGL_RENDERERS if "OpenGL 4.5" in g["renderer"]]
            screen_pool = [s for s in _SCREEN_RESOLUTIONS if s["dpr"] <= 1]
        else:
            gpu_pool = [g for g in _WEBGL_RENDERERS if "Direct3D11" in g["renderer"]]
            screen_pool = [s for s in _SCREEN_RESOLUTIONS if s["dpr"] <= 1.5]
        
        gpu = random.choice(gpu_pool) if gpu_pool else random.choice(_WEBGL_RENDERERS)
        screen = random.choice(screen_pool) if screen_pool else random.choice(_SCREEN_RESOLUTIONS)
        
        # Platform string must match UA
        if is_mac:
            plat = "MacIntel"
        elif is_linux:
            plat = "Linux x86_64"
        else:
            plat = "Win32"
        
        hw_concurrency = random.choice([4, 6, 8, 10, 12, 16])
        device_memory = random.choice([4, 8, 16, 32])
        color_depth = 30 if is_mac else 24
    
    # Generate fresh fingerprints per attempt (NO CACHING)
    profile = {
        # ━━━ Navigator ━━━
        "user_agent": user_agent,
        "platform": plat,
        "hardware_concurrency": hw_concurrency,
        "device_memory": device_memory,
        "language": "en-US",
        "languages": ["en-US", "en"],
        "mobile": is_mobile,
        
        # ━━━ User-Agent Data (Client Hints) ━━━
        "client_hints": _get_client_hints(user_agent, plat),
        
        # ━━━ Canvas (Position-based deterministic noise) ━━━
        "canvas_hash": _generate_canvas_noise(),
        
        # ━━━ WebGL (GPU vendor/renderer) ━━━
        "webgl_vendor": gpu["vendor"],
        "webgl_renderer": gpu["renderer"],
        "webgl_hash": hashlib.md5(gpu["renderer"].encode()).hexdigest()[:16],
        
        # ━━━ AudioContext (Imperceptible noise ~-80dB) ━━━
        "audio_noise": _generate_audio_noise(),
        
        # ━━━ Screen ━━━
        "screen_width": screen["w"],
        "screen_height": screen["h"],
        "avail_width": screen["avail_w"],
        "avail_height": screen["avail_h"],
        "device_pixel_ratio": screen["dpr"],
        "color_depth": color_depth,
        
        # ━━━ Plugins/MimeTypes (PDF viewer consistency) ━━━
        "pdf_viewer": _get_pdf_viewer_consistency(),
    }
    
    # TANPA CACHING - setiap attempt menghasilkan fingerprint baru
    return profile


def get_stripe_cookies(fp: dict, real_cookies: dict = None) -> str:
    """Generate Stripe cookie header — uses real cookies from warm session if available.
    
    Fallback cookies use extended UUID format matching real Stripe:
    __stripe_mid and __stripe_sid are NOT standard UUIDs — they have
    5-6 extra hex chars appended to the last segment.
    """
    # Use real cookies if available, otherwise use fingerprint values
    # (which are already in extended UUID format)
    mid = real_cookies.get("__stripe_mid", fp['muid']) if real_cookies else fp['muid']
    sid = real_cookies.get("__stripe_sid", fp['sid']) if real_cookies else fp['sid']
    
    cookie_str = f"__stripe_mid={mid}; __stripe_sid={sid}"
    
    # Include any extra cookies from warm session
    if real_cookies:
        for k, v in real_cookies.items():
            if k not in ("__stripe_mid", "__stripe_sid"):
                cookie_str += f"; {k}={v}"
    
    return cookie_str


async def warm_checkout_session(checkout_url: str, tls_profile: str, user_agent: str, proxy: str = None) -> dict:
    """Fetch checkout page to collect real Stripe cookies and establish session.
    
    Real browsers always load the checkout page first before making API calls.
    This step gets real __stripe_mid/__stripe_sid cookies from Stripe's servers.
    
    Returns dict with:
        - cookies: dict of cookie name -> value from Set-Cookie headers
        - success: whether the page was loaded successfully
    """
    result = {"cookies": {}, "success": False}
    
    try:
        async with CurlSession(impersonate=tls_profile) as s:
            r = await s.get(
                checkout_url,
                headers={
                    "user-agent": user_agent,
                    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                    "accept-language": "en-US,en;q=0.9",
                    "sec-fetch-dest": "document",
                    "sec-fetch-mode": "navigate",
                    "sec-fetch-site": "none",
                    "sec-fetch-user": "?1",
                    "upgrade-insecure-requests": "1",
                },
                timeout=15,
                allow_redirects=True,
                proxy=proxy,
            )
            
            # Debug: show raw Set-Cookie headers
            print(f"[DEBUG] Warm response status: {r.status_code}")
            try:
                all_headers = dict(r.headers) if hasattr(r.headers, '__iter__') else {}
                set_cookie_raw = [v for k, v in all_headers.items() if k.lower() == 'set-cookie']
                print(f"[DEBUG] Raw Set-Cookie: {set_cookie_raw[:3]}")
            except Exception:
                pass
            
            # Strategy 1: Extract from cookies jar
            try:
                if hasattr(r, 'cookies') and r.cookies:
                    for name in r.cookies.keys():
                        result["cookies"][name] = r.cookies.get(name, "")
            except Exception:
                pass
            
            # Strategy 2: Extract from session cookies
            try:
                if hasattr(s, 'cookies') and s.cookies:
                    for name in s.cookies.keys():
                        result["cookies"][name] = s.cookies.get(name, "")
            except Exception:
                pass
            
            # Strategy 3: Parse Set-Cookie from raw headers
            try:
                raw_headers = str(r.headers) if hasattr(r, 'headers') else ""
                # curl_cffi headers — try multiple methods
                if hasattr(r.headers, 'multi_items'):
                    for name, value in r.headers.multi_items():
                        if name.lower() == "set-cookie":
                            parts = value.split(";")[0].strip()
                            if "=" in parts:
                                k, v = parts.split("=", 1)
                                result["cookies"][k.strip()] = v.strip()
                elif hasattr(r.headers, 'items'):
                    for name, value in r.headers.items():
                        if name.lower() == "set-cookie":
                            parts = value.split(";")[0].strip()
                            if "=" in parts:
                                k, v = parts.split("=", 1)
                                result["cookies"][k.strip()] = v.strip()
            except Exception:
                pass
            
            # Strategy 4: Look for stripe cookies in response body (JS sets them)
            if not result["cookies"] and r.status_code == 200:
                try:
                    body = r.text
                    import re
                    # Find __stripe_mid and __stripe_sid in the HTML/JS
                    for cookie_name in ["__stripe_mid", "__stripe_sid"]:
                        match = re.search(rf'{cookie_name}["\s]*[=:]["\s]*([a-f0-9-]+)', body)
                        if match:
                            result["cookies"][cookie_name] = match.group(1)
                except Exception:
                    pass
            
            if r.status_code == 200:
                result["success"] = True
                print(f"[DEBUG] ✅ Warm session OK — got {len(result['cookies'])} cookies: {list(result['cookies'].keys())}")
            else:
                print(f"[DEBUG] ⚠️ Warm session HTTP {r.status_code}")
                result["success"] = True  # Still usable
                
    except Exception as e:
        print(f"[DEBUG] ❌ Warm session error: {str(e)[:60]}")
    
    return result


async def send_m_stripe_beacon(fp: dict, checkout_url: str, tls_profile: str, user_agent: str, cookies_str: str, proxy: str = None, device_fp: dict = None) -> bool:
    """Send single telemetry beacon to m.stripe.com/6.
    
    DevTools analysis shows real Stripe Checkout sends only 1 request to m.stripe.com,
    NOT 5-6 like we were doing before. The response returns muid/guid/sid identifiers.
    Sending too many beacons actually makes us MORE detectable.
    
    Args:
        device_fp: Pre-generated device fingerprint for session consistency.
    
    Returns:
        Tuple of (success: bool, collected_cookies: dict, identifiers: dict)
    """
    import json
    import time
    
    beacon_headers = {
        "user-agent": user_agent,
        "content-type": "application/json",
        "origin": "https://checkout.stripe.com",
        "referer": "https://checkout.stripe.com/",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
    }
    # Only include cookie header if we have cookies
    if cookies_str:
        beacon_headers["cookie"] = cookies_str
    
    # Add sec-ch-ua for Chrome-based browsers (must match UA)
    browser = _detect_browser_info(user_agent)
    if browser["browser"] in ("Chrome", "Edge", "Opera"):
        v = browser["version"]
        g_brand, g_ver = _get_grease_brand(v)
        if browser["browser"] == "Edge":
            beacon_headers["sec-ch-ua"] = f'"Chromium";v="{v}", "{g_brand}";v="{g_ver}", "Microsoft Edge";v="{v}"'
        elif browser["browser"] == "Opera":
            beacon_headers["sec-ch-ua"] = f'"Chromium";v="{v}", "{g_brand}";v="{g_ver}", "Opera";v="{v}"'
        else:
            beacon_headers["sec-ch-ua"] = f'"Chromium";v="{v}", "{g_brand}";v="{g_ver}", "Google Chrome";v="{v}"'
        beacon_headers["sec-ch-ua-mobile"] = "?1" if browser.get("mobile") else "?0"
        if browser["platform"] == "Android":
            beacon_headers["sec-ch-ua-platform"] = '"Android"'
        elif browser["platform"] == "iOS":
            beacon_headers["sec-ch-ua-platform"] = '"iOS"'
        else:
            beacon_headers["sec-ch-ua-platform"] = f'"{browser["platform"]}"'
    
    now = int(time.time() * 1000)
    
    # Use provided device_fp for session consistency, or generate new one
    if device_fp is None:
        device_fp = generate_device_fingerprint(user_agent)
    
    # Single beacon — real Stripe Checkout only sends 1 m.stripe.com request
    beacon = {
        "v": 2,
        "tag": "checkout_init_pageload",
        "src": "checkout-js",
        "pid": fp["guid"],
        "data": {
            "url": checkout_url,
            "muid": fp["muid"],
            "sid": fp["sid"],
            "pageloadTimestamp": now,
            "livemode": True,
            "userAgent": user_agent,
            "screenWidth": device_fp["screen_width"],
            "screenHeight": device_fp["screen_height"],
            "devicePixelRatio": device_fp["device_pixel_ratio"],
            "colorDepth": device_fp["color_depth"],
            "platform": device_fp["platform"],
            "languages": device_fp["languages"],
            "hardwareConcurrency": device_fp["hardware_concurrency"],
            "deviceMemory": device_fp["device_memory"],
        }
    }
    
    collected_cookies = {}
    identifiers = {}
    try:
        async with CurlSession(impersonate=tls_profile) as s:
            r = await s.post(
                "https://m.stripe.com/6",
                headers=beacon_headers,
                data=json.dumps(beacon),
                timeout=8,
                proxy=proxy,
            )
            
            # Extract identifiers from response (m.stripe.com returns muid/guid/sid)
            try:
                resp_data = r.json()
                if isinstance(resp_data, dict):
                    if "muid" in resp_data:
                        identifiers["muid"] = resp_data["muid"]
                    if "guid" in resp_data:
                        identifiers["guid"] = resp_data["guid"]
                    if "sid" in resp_data:
                        identifiers["sid"] = resp_data["sid"]
                    if identifiers:
                        print(f"[DEBUG] ✅ m.stripe.com identifiers: muid={identifiers.get('muid', 'N/A')[:16]}...")
            except Exception:
                pass
            
            # Extract cookies from response
            try:
                if hasattr(r, 'cookies') and r.cookies:
                    for name in r.cookies.keys():
                        collected_cookies[name] = r.cookies.get(name, "")
            except Exception:
                pass
            
            # Check session cookies
            try:
                if hasattr(s, 'cookies') and s.cookies:
                    for name in s.cookies.keys():
                        collected_cookies[name] = s.cookies.get(name, "")
            except Exception:
                pass
        
        if collected_cookies:
            print(f"[DEBUG] ✅ Beacon cookies: {list(collected_cookies.keys())}")
        print(f"[DEBUG] ✅ m.stripe.com beacon sent (1 request)")
        return True, collected_cookies, identifiers
            
    except Exception as e:
        print(f"[DEBUG] ⚠️ Beacon error (non-fatal): {str(e)[:50]}")
        return False, {}, {}


async def send_r_stripe_events(
    fp: dict,
    checkout_url: str,
    tls_profile: str,
    user_agent: str,
    cookies_str: str,
    device_fp: dict = None,
    proxy: str = None,
    payment_user_agent: str = None,
):
    """Send r.stripe.com/0 Radar telemetry — real Stripe.js lifecycle events.

    Real Stripe Checkout sends individual JSON events to r.stripe.com/0.
    Format is same as m.stripe.com: v2 envelope with tag/src/pid/data.

    Key events a real checkout sends:
      1. checkout-js pageload (on page load)
      2. checkout-js element interaction (before submit)

    This is NON-BLOCKING / best-effort — failures don't stop checkout.
    """
    import json
    import time as _t

    if device_fp is None:
        device_fp = generate_device_fingerprint(user_agent)

    now_ms = int(_t.time() * 1000)

    # Headers — same origin as Stripe Checkout
    hdr = {
        "user-agent": user_agent,
        "content-type": "application/json",
        "origin": "https://checkout.stripe.com",
        "referer": "https://checkout.stripe.com/",
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
    }
    if cookies_str:
        hdr["cookie"] = cookies_str

    browser = _detect_browser_info(user_agent)
    if browser["browser"] in ("Chrome", "Edge", "Opera"):
        v = browser["version"]
        g_brand, g_ver = _get_grease_brand(v)
        if browser["browser"] == "Edge":
            hdr["sec-ch-ua"] = f'"Chromium";v="{v}", "{g_brand}";v="{g_ver}", "Microsoft Edge";v="{v}"'
        elif browser["browser"] == "Opera":
            hdr["sec-ch-ua"] = f'"Chromium";v="{v}", "{g_brand}";v="{g_ver}", "Opera";v="{v}"'
        else:
            hdr["sec-ch-ua"] = f'"Chromium";v="{v}", "{g_brand}";v="{g_ver}", "Google Chrome";v="{v}"'
        hdr["sec-ch-ua-mobile"] = "?1" if browser.get("mobile") else "?0"
        plat = browser["platform"]
        if plat == "Android":
            hdr["sec-ch-ua-platform"] = '"Android"'
        elif plat == "iOS":
            hdr["sec-ch-ua-platform"] = '"iOS"'
        else:
            hdr["sec-ch-ua-platform"] = f'"{plat}"'

    pua = payment_user_agent or get_random_stripe_js_agent()

    # Build v2 event — same format as m.stripe.com/6
    event = {
        "v": 2,
        "tag": "checkout-elements-inner-card-element-render-complete",
        "src": "checkout-js",
        "pid": fp["guid"],
        "data": {
            "url": checkout_url,
            "muid": fp["muid"],
            "sid": fp["sid"],
            "paymentUserAgent": pua,
            "timeSincePageLoad": random.randint(2000, 8000),
            "livemode": True,
            "userAgent": user_agent,
            "screenWidth": device_fp.get("screen_width", 1920),
            "screenHeight": device_fp.get("screen_height", 1080),
            "windowWidth": device_fp.get("avail_width", 1920),
            "windowHeight": device_fp.get("avail_height", 1040),
            "devicePixelRatio": device_fp.get("device_pixel_ratio", 1),
            "colorDepth": device_fp.get("color_depth", 24),
            "platform": device_fp.get("platform", "Win32"),
            "language": "en-US",
            "hardwareConcurrency": device_fp.get("hardware_concurrency", 8),
            "deviceMemory": device_fp.get("device_memory", 8),
            "pageloadTimestamp": now_ms - random.randint(3000, 10000),
            "canvasHash": device_fp.get("canvas_hash", ""),
            "webglVendor": device_fp.get("webgl_vendor", ""),
            "webglRenderer": device_fp.get("webgl_renderer", ""),
        },
    }

    sent = 0
    try:
        async with CurlSession(impersonate=tls_profile) as s:
            # Send main event
            r = await s.post(
                "https://r.stripe.com/0",
                headers=hdr,
                data=json.dumps(event),
                timeout=8,
                proxy=proxy,
            )
            sent += 1

            # Send a second event (element focus) after short gap
            event2 = {
                "v": 2,
                "tag": "checkout-elements-inner-payment-element-rendered",
                "src": "checkout-js",
                "pid": fp["guid"],
                "data": {
                    "url": checkout_url,
                    "muid": fp["muid"],
                    "sid": fp["sid"],
                    "paymentUserAgent": pua,
                    "timeSincePageLoad": random.randint(4000, 12000),
                    "livemode": True,
                    "userAgent": user_agent,
                    "pageloadTimestamp": now_ms - random.randint(3000, 10000),
                },
            }
            r2 = await s.post(
                "https://r.stripe.com/0",
                headers=hdr,
                data=json.dumps(event2),
                timeout=8,
                proxy=proxy,
            )
            sent += 1

        print(f"[DEBUG] ✅ r.stripe.com sent {sent} events (HTTP {r.status_code}, {r2.status_code})")
        return True
    except Exception as e:
        print(f"[DEBUG] ⚠️ r.stripe.com error (non-fatal): {str(e)[:60]}")
        return False


def generate_realistic_email(name: str) -> str:
    """Generate a realistic email address that matches the billing name.

    Avoids the suspicious 'john@example.com' fallback.  Produces patterns
    commonly seen in real customers (first.last, firstlast99, etc.)
    """
    parts = name.strip().split()
    first = parts[0].lower() if parts else "user"
    last = parts[-1].lower() if len(parts) > 1 else ""

    domains = [
        "gmail.com", "yahoo.com", "outlook.com", "hotmail.com",
        "icloud.com", "protonmail.com", "live.com", "aol.com",
        "mail.com", "yandex.com",
    ]

    if last:
        patterns = [
            f"{first}.{last}",
            f"{first}{last}",
            f"{first}.{last}{random.randint(1, 99)}",
            f"{first}{last}{random.randint(1, 999)}",
            f"{first[0]}{last}",
            f"{first[0]}.{last}",
            f"{first}_{last}",
            f"{first}{random.randint(10, 99)}",
        ]
    else:
        patterns = [
            f"{first}{random.randint(10, 9999)}",
            f"{first}.{random.randint(1, 99)}",
        ]

    return f"{random.choice(patterns)}@{random.choice(domains)}"


def generate_session_context(user_id: int = None, rotation_per_attempt: bool = True, country: str = None) -> dict:
    """Generate a complete session context for one checkout session.
    
    Args:
        user_id: User ID (kept for compatibility, tidak mempengaruhi fingerprint)
        rotation_per_attempt: Jika True, setiap panggilan menghasilkan fingerprint baru
        country: Country code untuk billing address (e.g., 'US', 'GB', 'MO')
    
    Returns dict with:
        - tls_profile: browser TLS profile
        - fingerprints: muid/guid/sid (fresh per attempt jika rotation=True)
        - cookies: stripe cookie header
        - payment_user_agent: stripe.js agent string
        - pasted_fields: which fields were pasted
        - time_on_page_base: base time user spent on page
        - device_fp: Device fingerprint dengan metode terbatas (Navigator, Client Hints, 
                     Canvas, WebGL, AudioContext, Screen, Plugins/MimeTypes)
        - billing: Billing address yang sama untuk semua kartu dalam session
    """
    from utils.constants import get_random_billing
    
    # Pick ONE browser for the entire session — TLS + UA always matched
    browser = get_random_browser_profile()
    tls_profile = browser["tls"]
    user_agent = browser["ua"]

    # Generate fingerprints - ROTATION PER ATTEMPT (tidak di-cache)
    fp = generate_stripe_fingerprints(user_id)

    # Cookies - fresh per attempt jika rotation enabled
    cookies = get_stripe_cookies(fp)

    # Payment user agent - fresh per attempt
    payment_user_agent = get_random_stripe_js_agent()

    # Device fingerprint - FRESH PER ATTEMPT (rotasi, tidak ada caching)
    # Menggunakan hanya metode: Navigator, Client Hints, Canvas, WebGL, 
    # AudioContext, Screen, Plugins/MimeTypes
    device_fp = generate_device_fingerprint(user_agent, user_id=None if rotation_per_attempt else user_id)

    # Randomize pasted_fields
    pasted_fields = random.choice(["number", "number|cvc", "number|cvc|exp", ""])

    # Base time on page
    time_on_page_base = random.randint(20000, 60000)
    
    # Billing address - SAMA untuk semua kartu dalam session ini
    billing = get_random_billing(country)

    return {
        "tls_profile": tls_profile,
        "user_agent": user_agent,
        "fingerprints": fp,
        "cookies": cookies,
        "payment_user_agent": payment_user_agent,
        "device_fp": device_fp,
        "pasted_fields": pasted_fields,
        "time_on_page_base": time_on_page_base,
        "allow_redisplay": "unspecified",
        "rotation_enabled": rotation_per_attempt,  # Flag untuk tracking
        "billing": billing,  # Same billing for all cards in this session
    }
