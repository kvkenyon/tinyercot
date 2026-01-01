import os

import httpx
from cachetools import TTLCache, cached
from httpx_retries import Retry, RetryTransport

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
_client = httpx.Client(
    transport=RetryTransport(retry=Retry(total=3, backoff_factor=2))
)


@cached(_tok_cache)
def _token() -> str:
    return _client.post(AUTH_URL).json().get("id_token")


def _get(path: str, schema: dict | None = None, **params) -> dict:  # pyright: ignore
    """Fetch data from API, optionally converting list-of-lists to list-of-dicts."""
    response = _client.get(
        f"{BASE_URL}/{path.lstrip('/')}",
        headers={
            "Ocp-Apim-Subscription-Key": os.environ["ERCOT_SUBSCRIPTION_KEY"],
            "Authorization": f"Bearer {_token()}",
        },
        params={k: v for k, v in params.items() if v is not None},
    ).json()

    # Convert list-of-lists to list-of-dicts if schema provided
    if schema and "data" in response and response["data"]:
        keys = list(schema.keys())
        response["data"] = [dict(zip(keys, row)) for row in response["data"]]

    return response


def _to_df(response: dict, schema: dict):  # pyright: ignore[reportUnusedFunction]
    """Convert API response to DataFrame with proper types."""
    import pandas as pd

    df = pd.DataFrame(response["data"], columns=list(schema.keys()))
    for col, dtype in schema.items():
        if col not in df.columns:
            continue
        if dtype == "DATE":
            df[col] = pd.to_datetime(df[col]).dt.date
        elif dtype == "DATETIME":
            df[col] = pd.to_datetime(df[col])
        elif dtype == "DOUBLE":
            df[col] = pd.to_numeric(df[col], errors="coerce")
        elif dtype == "INTEGER":
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
        elif dtype == "BOOLEAN":
            df[col] = df[col].astype(bool)
    return df
