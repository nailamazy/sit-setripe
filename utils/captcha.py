import asyncio
import aiohttp

from config import NOPECHA_KEY


# NopeCHA v1 Token API — proper endpoint for hCaptcha token generation
NOPECHA_SUBMIT_URL = "https://api.nopecha.com/v1/token/hcaptcha"
NOPECHA_TIMEOUT = 120  # Max waktu tunggu solve (detik)
NOPECHA_POLL_INTERVAL = 3  # Interval poll status (detik)


# NopeCHA error codes
_NOPECHA_ERRORS = {
    1: "Invalid request — bad parameters",
    2: "Not enough credit balance",
    3: "Invalid API key size",
    4: "Unrecognized CAPTCHA type",
    5: "Server too busy, try again",
    6: "Internal server error",
    7: "Invalid sitekey",
    9: "Rate limited — too many requests",
    10: "Invalid request — check proxy format or API key",
    11: "Unsupported captcha type",
    12: "Proxy error",
    14: "Banned — contact NopeCHA support",
}


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


async def solve_hcaptcha(site_key: str, url: str, rqdata: str = None, proxy: str = None, user_agent: str = None) -> dict | None:
    """Solve hCaptcha menggunakan NopeCHA v1 Token API.
    
    Uses the proper v1 endpoint: POST /v1/token/hcaptcha
    Auth via Authorization header, not body key field.
    
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
            # Step 1: Submit captcha task
            async with session.post(
                NOPECHA_SUBMIT_URL,
                json=body,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                raw_text = await resp.text()
                print(f"[DEBUG] 📡 NopeCHA HTTP {resp.status}")
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
                
                if resp.status != 200:
                    err_code = data.get("error", "unknown") if isinstance(data, dict) else "unknown"
                    err_msg = data.get("message", "") if isinstance(data, dict) else ""
                    err_type = data.get("type", "") if isinstance(data, dict) else ""
                    known = _NOPECHA_ERRORS.get(err_code, "") if isinstance(err_code, int) else ""
                    print(f"[DEBUG] ❌ NopeCHA HTTP {resp.status} — error={err_code}, message={err_msg}, type={err_type}")
                    if known:
                        print(f"[DEBUG]    Known: {known}")
                    print(f"[DEBUG]    Full response: {data}")
                    return None
                
                # Check if token returned immediately (string response)
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
                    elif data.get("error") == "Incomplete":
                        print(f"[DEBUG] ⏳ NopeCHA processing... polling for result")
                        job_id = None
                    else:
                        print(f"[DEBUG] ⚠️ Unexpected response: {str(data)[:100]}")
                        job_id = None
                
            # Step 2: Poll for result
            elapsed = 0
            while elapsed < NOPECHA_TIMEOUT:
                await asyncio.sleep(NOPECHA_POLL_INTERVAL)
                elapsed += NOPECHA_POLL_INTERVAL
                
                # Poll via GET with job ID, or re-POST without ID
                if job_id:
                    poll_url = f"{NOPECHA_SUBMIT_URL}?id={job_id}"
                    async with session.get(
                        poll_url,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=30),
                    ) as poll_resp:
                        poll_raw = await poll_resp.text()
                        print(f"[DEBUG] ⏳ Poll HTTP {poll_resp.status}, len={len(poll_raw)}")
                        try:
                            import json as _j2
                            poll_data = _j2.loads(poll_raw)
                        except Exception:
                            print(f"[DEBUG] ⚠️ Poll response not JSON: {poll_raw[:100]}")
                            continue
                else:
                    # Legacy fallback: re-POST with same body
                    async with session.post(
                        NOPECHA_SUBMIT_URL,
                        json=body,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=30),
                    ) as poll_resp:
                        poll_raw = await poll_resp.text()
                        print(f"[DEBUG] ⏳ Poll (POST) HTTP {poll_resp.status}, len={len(poll_raw)}")
                        try:
                            import json as _j3
                            poll_data = _j3.loads(poll_raw)
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
                    
                    # Still processing — check both string and integer error codes
                    error = poll_data.get("error", "")
                    error_msg = str(poll_data.get("message", "")).lower()
                    
                    # Error 14 = BANNED per NopeCHA docs — DO NOT treat as "incomplete"
                    # Even if message says "incomplete job", error 14 is terminal
                    if isinstance(error, int) and error == 14:
                        print(f"[DEBUG] ❌ NopeCHA error 14: Banned/blocked — cannot solve this captcha")
                        print(f"[DEBUG]    Message: {error_msg}")
                        print(f"[DEBUG]    This usually means:")
                        print(f"[DEBUG]    - Your NopeCHA account is banned/restricted")
                        print(f"[DEBUG]    - The captcha type (Enterprise + rqdata) is not supported")
                        print(f"[DEBUG]    - Consider using a different solver (CapSolver, 2Captcha)")
                        return None
                    
                    # NopeCHA can indicate "still processing" in these ways:
                    # - {"error": "Incomplete"}
                    # - HTTP 409 with non-14 error codes
                    is_incomplete = (
                        error == "Incomplete"
                        or ("incomplete" in error_msg and not isinstance(error, int))
                    )
                    
                    if is_incomplete:
                        print(f"[DEBUG] ⏳ Still solving... ({elapsed}s/{NOPECHA_TIMEOUT}s) [error={error}, msg={error_msg}]")
                        continue
                    
                    # Real error — not retryable
                    if error:
                        known = _NOPECHA_ERRORS.get(error, "") if isinstance(error, int) else ""
                        print(f"[DEBUG] ❌ NopeCHA error during poll: {error}")
                        if known:
                            print(f"[DEBUG]    Known: {known}")
                        print(f"[DEBUG]    Full poll response: {str(poll_data)[:200]}")
                        return None
                
                print(f"[DEBUG] ⏳ Polling... ({elapsed}s/{NOPECHA_TIMEOUT}s)")
            
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
