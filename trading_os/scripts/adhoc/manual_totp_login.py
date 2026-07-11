"""One-shot Kite login using a manually supplied 6-digit TOTP code.

Same flow as tradingos.data.auth.KiteAuth.totp_login, but takes the code
as argv[1] instead of generating it from TOS_KITE_TOTP_SECRET.
"""

import sys

import requests

from tradingos.config.settings import get_settings
from tradingos.data.auth import (
    _KITE_LOGIN_API,
    _KITE_TWOFA_API,
    KiteAuth,
    _extract_request_token,
)

code = sys.argv[1]
settings = get_settings()
auth = KiteAuth(settings)
session = requests.Session()

login_resp = session.post(
    _KITE_LOGIN_API,
    data={"user_id": settings.kite_user_id, "password": settings.kite_password},
    timeout=15,
)
login_resp.raise_for_status()
request_id = login_resp.json()["data"]["request_id"]

twofa_resp = session.post(
    _KITE_TWOFA_API,
    data={
        "user_id": settings.kite_user_id,
        "request_id": request_id,
        "twofa_value": code,
        "twofa_type": "totp",
    },
    timeout=15,
)
if twofa_resp.status_code != 200:
    print(f"TWOFA FAILED ({twofa_resp.status_code}): {twofa_resp.text[:200]}")
    sys.exit(2)

location = ""
next_url = auth.login_url()
for _ in range(5):
    r = session.get(next_url, timeout=15, allow_redirects=False)
    location = r.headers.get("Location", "")
    if "request_token" in location or not location:
        break
    next_url = location

token = _extract_request_token(location)
if not token:
    print(f"NO REQUEST TOKEN in redirect chain (last location: {location[:120]})")
    sys.exit(3)

access = auth.exchange_request_token(token)
print(f"LOGIN OK - access token cached ({len(access)} chars)")
