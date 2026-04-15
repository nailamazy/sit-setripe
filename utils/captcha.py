import asyncio
import aiohttp

from config import NOPECHA_KEY


# NopeCHA v1 Token API — proper endpoint for hCaptcha token generation
NOPECHA_SUBMIT_URL = "https://api.nopecha.com/v1/token/hcaptcha"
NOPECHA_TIMEOUT = 120  # Max waktu tunggu solve (detik)
NOPECHA_POLL_INTERVAL = 1  # Interval poll status (detik) — docs recommend 500ms min


def _validate_hcaptcha_token(token: str):
    """Validate and log hCaptcha token format details."""
    print(f"[DEBUG] 🔍 Token analysis:")
    print(f"[DEBUG]    Length: {len(token)} chars")
    print(f"[DEBUG]    First 10: {token[:10]}")
    print(f"[DEBUG]    Last 10: ...{token[-10:]}")
    
    # hCaptcha tokens biasanya format P0_eyJ... atau P1_eyJ...
    if token.startswith("P0_") or token.startswith("P1_"):
        print(f"[DEBUG]    Format: ✅ Valid hCaptcha prefix ({token[:3]})")
    elif token.startswith("10000000-aaaa"):
        print(f"[DEBUG]    Format: ⚠️ Looks like DUMMY/test token!")
    else:
        print(f"[DEBUG]    Format: ⚠️ Non-standard prefix ({token[:10]})")
    
    # Check if it looks like a JWT (base64 encoded)
    if "eyJ" in token[:20]:
        print(f"[DEBUG]    JWT: ✅ Contains JWT payload")
        # Try to decode header to check expiry info
        try:
            import base64
            # Extract the base64 part after prefix
            b64_part = token.split("_", 1)[1] if "_" in token else token
            # Add padding
            padded = b64_part.split(".")[0] + "===" 
            decoded = base64.b64decode(padded)
            print(f"[DEBUG]    JWT header: {decoded[:100]}")
        except Exception:
            pass
    else:
        print(f"[DEBUG]    JWT: ❌ No JWT payload detected")


def _is_real_hcaptcha_token(token: str) -> bool:
    """Check if a string is a real hCaptcha token vs a job/task ID.
    
    Real hCaptcha tokens:
    - Length: 2000+ characters (typically 2500-4000)
    - Start with P0_ or P1_ prefix
    - Contain JWT payload (eyJ...)
    
    Job/task IDs:
    - Length: 30-100 characters  
    - Random alphanumeric strings
    - No JWT structure
    """
    if not token or not isinstance(token, str):
        return False
    
    # Real tokens are MUCH longer than job IDs
    # Minimum 500 chars to be safe (real ones are 2000+)
    if len(token) < 500:
        return False
    
    # Valid prefix check (P0_ or P1_ are standard hCaptcha prefixes)
    # Some tokens may not have prefix but are still valid if very long
    if token.startswith(("P0_", "P1_")):
        return True
    
    # If very long (1000+) but no standard prefix, still likely a token
    if len(token) >= 1000:
        return True
    
    return False


def _get_http_error_description(status: int) -> str:
    """Map NopeCHA HTTP status codes to human-readable descriptions.
    
    Based on NopeCHA v1 API docs:
    https://nopecha.com/api-reference
    """
    return {
        400: "Invalid Request — bad parameters or update required",
        401: "Invalid API Key — check your NOPECHA_KEY",
        402: "Unavailable Feature — plan upgrade required",
        403: "Out of Credit or Free Tier Ineligible",
        409: "Incomplete Job — still solving (poll again)",
        429: "Rate Limited — slow down requests",
        500: "Internal Server Error — try again later",
    }.get(status, f"Unknown HTTP error {status}")


async def solve_hcaptcha(site_key: str, url: str, rqdata: str = None, proxy: str = None, user_agent: str = None) -> dict | None:
    """Solve hCaptcha menggunakan NopeCHA v1 Token API.
    
    Uses the proper v1 endpoint: POST /v1/token/hcaptcha
    Auth via Authorization header, not body key field.
    
    Flow:
    1. POST /v1/token/hcaptcha → returns job ID in {"data": "job_id"}
    2. GET /v1/token/hcaptcha?id=JOB_ID → poll until {"data": "P0_eyJ...token"}
    
    HTTP status codes:
    - 200: Success (token or job ID)
    - 409: Incomplete job (keep polling)
    - 403: Out of credit
    - 429: Rate limited
    
    Args:
        site_key: hCaptcha sitekey dari Stripe response
        url: URL halaman checkout (dimana hCaptcha muncul)
        rqdata: Optional rqdata dari Stripe hCaptcha Enterprise
        proxy: Optional proxy string (format: host:port:user:pass or http://user:pass@host:port)
        user_agent: Optional user agent string
        
    Returns:
        Dict {"token": str, "ekey": str|None} jika berhasil, None jika gagal/timeout.
    """
    if not NOPECHA_KEY:
        print("[DEBUG] ❌ NOPECHA_KEY not configured — skipping captcha solve")
        print("[DEBUG]    Get your key at: https://nopecha.com/manage")
        return None
    
    if not site_key:
        print("[DEBUG] ❌ No site_key provided — cannot solve captcha")
        return None
    
    print(f"[DEBUG] 🔄 Solving hCaptcha via NopeCHA v1 API...")
    print(f"[DEBUG]    site_key: {site_key[:20]}...")
    print(f"[DEBUG]    url: {url[:60]}...")
    if rqdata:
        print(f"[DEBUG]    rqdata: {rqdata[:30]}... (Enterprise)")
    
    # Build request body — v1 API format
    # No "key" or "type" in body — auth via header, type via URL path
    body = {
        "sitekey": site_key,
        "url": url,
    }
    
    # Add rqdata for hCaptcha Enterprise (Stripe uses this)
    if rqdata:
        body["data"] = {"rqdata": rqdata}
    
    # Add optional proxy (NopeCHA format)
    if proxy:
        proxy_parts = _parse_proxy_for_nopecha(proxy)
        if proxy_parts:
            body["proxy"] = proxy_parts
            print(f"[DEBUG]    proxy: {proxy_parts}")
        else:
            print(f"[DEBUG]    ⚠️ Could not parse proxy: {proxy[:40]}...")
    
    # Add optional user agent
    if user_agent:
        body["useragent"] = user_agent
    
    # Headers with Authorization
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {NOPECHA_KEY}",
    }
    
    # Debug: show body (sans sensitive data)
    debug_body = dict(body)
    if "proxy" in debug_body:
        debug_body["proxy"] = "***"
    print(f"[DEBUG]    NopeCHA v1 body: {debug_body}")
    
    try:
        async with aiohttp.ClientSession() as session:
            # ━━━ Step 1: Submit captcha task ━━━
            async with session.post(
                NOPECHA_SUBMIT_URL,
                json=body,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                raw_text = await resp.text()
                print(f"[DEBUG] 📡 NopeCHA Submit — HTTP {resp.status}")
                print(f"[DEBUG]    Content-Type: {resp.content_type}")
                print(f"[DEBUG]    Response-Length: {len(raw_text)} chars")
                
                # Log relevant response headers
                for hdr in ['x-ratelimit-remaining', 'x-credits-remaining', 'x-request-id', 'cf-ray']:
                    val = resp.headers.get(hdr)
                    if val:
                        print(f"[DEBUG]    Header {hdr}: {val}")
                
                try:
                    import json as _j
                    data = _j.loads(raw_text)
                except Exception:
                    print(f"[DEBUG] ❌ NopeCHA response not JSON: {raw_text[:200]}")
                    return None
                
                # ━━━ Handle HTTP errors on submit ━━━
                if resp.status == 401:
                    print(f"[DEBUG] ❌ Invalid API Key — check NOPECHA_KEY")
                    return None
                elif resp.status == 402:
                    print(f"[DEBUG] ❌ Feature unavailable — plan upgrade needed")
                    return None
                elif resp.status == 403:
                    msg = data.get("message", "") if isinstance(data, dict) else ""
                    print(f"[DEBUG] ❌ Out of credit or IP banned: {msg}")
                    return None
                elif resp.status == 429:
                    print(f"[DEBUG] ❌ Rate limited — too many requests")
                    return None
                elif resp.status == 500:
                    print(f"[DEBUG] ❌ NopeCHA internal server error")
                    return None
                elif resp.status == 400:
                    msg = data.get("message", "") if isinstance(data, dict) else ""
                    err_type = data.get("type", "") if isinstance(data, dict) else ""
                    print(f"[DEBUG] ❌ Invalid request: type={err_type}, msg={msg}")
                    return None
                elif resp.status != 200 and resp.status != 409:
                    desc = _get_http_error_description(resp.status)
                    print(f"[DEBUG] ❌ NopeCHA HTTP {resp.status}: {desc}")
                    print(f"[DEBUG]    Full response: {data}")
                    return None
                
                # ━━━ Parse successful submit response ━━━
                job_id = None
                
                # Token returned immediately (string response)
                if isinstance(data, str) and _is_real_hcaptcha_token(data):
                    _validate_hcaptcha_token(data)
                    print(f"[DEBUG] ✅ hCaptcha solved instantly! Token: {data[:30]}...")
                    return {"token": data, "ekey": None}
                elif isinstance(data, str) and len(data) > 10:
                    # Short string = job ID, not a token
                    print(f"[DEBUG] ⏳ Got job ID (string): {data[:40]}... ({len(data)} chars) — will poll")
                    job_id = data
                
                if isinstance(data, dict):
                    print(f"[DEBUG]    Response keys: {list(data.keys())}")
                    # Token in data field — v1 format: {"data": "P0_eyJ..."}
                    data_val = data.get("data", "")
                    if isinstance(data_val, str) and _is_real_hcaptcha_token(data_val):
                        token = data_val
                        ekey = data.get("ekey")
                        _validate_hcaptcha_token(token)
                        print(f"[DEBUG] ✅ hCaptcha solved instantly! Token: {token[:30]}...")
                        if ekey:
                            print(f"[DEBUG]    ekey: {ekey[:30]}...")
                        return {"token": token, "ekey": ekey}
                    
                    # Job ID returned — need to poll
                    job_id = data.get("data")
                    if job_id and isinstance(job_id, str) and len(job_id) > 0:
                        print(f"[DEBUG] ⏳ Job ID submitted: {job_id[:40]}... ({len(job_id)} chars) — polling for real token")
                    else:
                        # Check for error in response body (legacy compat)
                        error = data.get("error", "")
                        msg = data.get("message", "")
                        if error or msg:
                            print(f"[DEBUG] ❌ NopeCHA error in body: error={error}, message={msg}")
                            return None
                        print(f"[DEBUG] ⚠️ Unexpected response (no job ID): {str(data)[:100]}")
                        return None
                
                # Safety check: must have job_id to poll
                if not job_id:
                    print(f"[DEBUG] ❌ No job ID received — cannot poll")
                    return None
                
            # ━━━ Step 2: Poll for result ━━━
            elapsed = 0
            consecutive_errors = 0
            max_consecutive_errors = 5
            
            while elapsed < NOPECHA_TIMEOUT:
                await asyncio.sleep(NOPECHA_POLL_INTERVAL)
                elapsed += NOPECHA_POLL_INTERVAL
                
                poll_url = f"{NOPECHA_SUBMIT_URL}?id={job_id}"
                try:
                    async with session.get(
                        poll_url,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=30),
                    ) as poll_resp:
                        poll_raw = await poll_resp.text()
                        
                        # ━━━ Handle HTTP status codes during poll ━━━
                        if poll_resp.status == 409:
                            # Incomplete — still solving, keep polling
                            print(f"[DEBUG] ⏳ Still solving... ({elapsed}s/{NOPECHA_TIMEOUT}s) [HTTP 409 Incomplete]")
                            consecutive_errors = 0
                            continue
                        elif poll_resp.status == 403:
                            print(f"[DEBUG] ❌ Out of credit during poll")
                            return None
                        elif poll_resp.status == 429:
                            print(f"[DEBUG] ⚠️ Rate limited during poll — waiting 2s...")
                            await asyncio.sleep(2)
                            elapsed += 2
                            consecutive_errors += 1
                            if consecutive_errors >= max_consecutive_errors:
                                print(f"[DEBUG] ❌ Too many consecutive errors during poll")
                                return None
                            continue
                        elif poll_resp.status == 401:
                            print(f"[DEBUG] ❌ Invalid API key during poll")
                            return None
                        elif poll_resp.status >= 500:
                            print(f"[DEBUG] ⚠️ Server error during poll (HTTP {poll_resp.status}) — retrying...")
                            consecutive_errors += 1
                            if consecutive_errors >= max_consecutive_errors:
                                print(f"[DEBUG] ❌ Too many server errors during poll")
                                return None
                            continue
                        elif poll_resp.status != 200:
                            desc = _get_http_error_description(poll_resp.status)
                            print(f"[DEBUG] ⚠️ Unexpected HTTP {poll_resp.status} during poll: {desc}")
                            consecutive_errors += 1
                            if consecutive_errors >= max_consecutive_errors:
                                print(f"[DEBUG] ❌ Too many errors during poll")
                                return None
                            continue
                        
                        # HTTP 200 — parse response
                        consecutive_errors = 0
                        print(f"[DEBUG] ⏳ Poll HTTP {poll_resp.status}, len={len(poll_raw)}")
                        
                        try:
                            import json as _j2
                            poll_data = _j2.loads(poll_raw)
                        except Exception:
                            print(f"[DEBUG] ⚠️ Poll response not JSON: {poll_raw[:100]}")
                            continue
                        
                        # Token returned as string
                        if isinstance(poll_data, str) and _is_real_hcaptcha_token(poll_data):
                            _validate_hcaptcha_token(poll_data)
                            print(f"[DEBUG] ✅ hCaptcha solved! ({elapsed}s) Token: {poll_data[:30]}...")
                            return {"token": poll_data, "ekey": None}
                        
                        if isinstance(poll_data, dict):
                            # Token in data field
                            poll_val = poll_data.get("data", "")
                            if isinstance(poll_val, str) and _is_real_hcaptcha_token(poll_val):
                                token = poll_val
                                ekey = poll_data.get("ekey")
                                _validate_hcaptcha_token(token)
                                print(f"[DEBUG] ✅ hCaptcha solved! ({elapsed}s) Token: {token[:30]}...")
                                if ekey:
                                    print(f"[DEBUG]    ekey: {ekey[:30]}...")
                                return {"token": token, "ekey": ekey}
                            
                            # Check for error in response body (compat with both old/new format)
                            error = poll_data.get("error", "")
                            error_msg = str(poll_data.get("message", "")).lower()
                            
                            # "Incomplete" in body = still solving (same as HTTP 409)
                            if error == "Incomplete" or "incomplete" in error_msg:
                                print(f"[DEBUG] ⏳ Still solving... ({elapsed}s/{NOPECHA_TIMEOUT}s) [body: Incomplete]")
                                continue
                            
                            # Any other error in body = terminal
                            if error:
                                print(f"[DEBUG] ❌ NopeCHA error during poll: error={error}, msg={error_msg}")
                                print(f"[DEBUG]    Full poll response: {str(poll_data)[:200]}")
                                return None
                        
                        print(f"[DEBUG] ⏳ Polling... ({elapsed}s/{NOPECHA_TIMEOUT}s)")
                        
                except aiohttp.ClientError as ce:
                    print(f"[DEBUG] ⚠️ Network error during poll: {str(ce)[:60]}")
                    consecutive_errors += 1
                    if consecutive_errors >= max_consecutive_errors:
                        print(f"[DEBUG] ❌ Too many network errors during poll")
                        return None
                    continue
            
            print(f"[DEBUG] ❌ NopeCHA timeout after {NOPECHA_TIMEOUT}s")
            return None
            
    except asyncio.TimeoutError:
        print(f"[DEBUG] ❌ NopeCHA request timeout")
        return None
    except Exception as e:
        print(f"[DEBUG] ❌ NopeCHA error: {str(e)[:80]}")
        return None


def _parse_proxy_for_nopecha(proxy_str: str) -> dict | None:
    """Convert proxy string ke format NopeCHA API v1.
    
    Supports formats:
        http://user:pass@host:port  (from get_proxy_url())
        http://host:port
        host:port:user:pass
        user:pass@host:port
        host:port
    
    Returns dict: {"scheme": "http", "host": ..., "port": ..., "username": ..., "password": ...}
    """
    try:
        scheme = "http"
        username = None
        password = None
        
        # Strip scheme prefix (http://, https://, socks5://)
        clean = proxy_str
        if "://" in clean:
            scheme_part, clean = clean.split("://", 1)
            if scheme_part in ("http", "https", "socks5", "socks4"):
                scheme = scheme_part
        
        if "@" in clean:
            # user:pass@host:port
            auth, hostport = clean.rsplit("@", 1)
            parts = auth.split(":", 1)
            username = parts[0]
            password = parts[1] if len(parts) > 1 else None
            hp = hostport.split(":")
            host = hp[0]
            port = int(hp[1]) if len(hp) > 1 else 8080
        else:
            parts = clean.split(":")
            if len(parts) == 4:
                # host:port:user:pass
                host, port, username, password = parts[0], int(parts[1]), parts[2], parts[3]
            elif len(parts) == 2:
                # host:port
                host, port = parts[0], int(parts[1])
            else:
                return None
        
        result = {
            "scheme": scheme,
            "host": host,
            "port": port,
        }
        if username:
            result["username"] = username
        if password:
            result["password"] = password
        
        return result
        
    except Exception:
        return None
