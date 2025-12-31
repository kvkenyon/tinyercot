import os

import httpx
from cachetools import TTLCache, cached

BASE_URL = "https://api.ercot.com/api/public-reports"
CLIENT_ID = "fec253ea-0d06-4272-a5e6-b478baeecd70"
SCOPE = f"openid+{CLIENT_ID}+offline_access"
AUTH_URL = (
    f"https://ercotb2c.b2clogin.com/ercotb2c.onmicrosoft.com/"
    f"B2C_1_PUBAPI-ROPC-FLOW/oauth2/v2.0/token"
    f"?username={os.getenv('ERCOT_USERNAME')}&password={os.getenv('ERCOT_PASSWORD')}"
    f"&grant_type=password&scope={SCOPE}&client_id={CLIENT_ID}&response_type=id_token"
)

_tok_cache: TTLCache = TTLCache(maxsize=1, ttl=3600)


@cached(_tok_cache)
def _token() -> str:
    return httpx.post(AUTH_URL).json().get("id_token")


def _get(path: str, **params) -> dict:  # pyright: ignore
    return httpx.get(
        f"{BASE_URL}/{path.lstrip('/')}",
        headers={
            "Ocp-Apim-Subscription-Key": os.environ["ERCOT_SUBSCRIPTION_KEY"],
            "Authorization": f"Bearer {_token()}",
        },
        params={k: v for k, v in params.items() if v is not None},
    ).json()
