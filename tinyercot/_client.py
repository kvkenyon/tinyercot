import asyncio
import os
from typing import ClassVar, Generic, TypeVar

import httpx
from aiolimiter import AsyncLimiter
from cachetools import TTLCache, cached
from httpx_retries import Retry, RetryTransport
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T", bound=BaseModel)

BASE_URL = "https://api.ercot.com/api/public-reports"
CLIENT_ID = "fec253ea-0d06-4272-a5e6-b478baeecd70"
SCOPE = f"openid+{CLIENT_ID}+offline_access"

_username: str | None = None
_password: str | None = None
_subscription_key: str | None = None

_tok_cache: TTLCache = TTLCache(maxsize=1, ttl=3600)
_client = httpx.Client(
    transport=RetryTransport(retry=Retry(total=3, backoff_factor=2)),
    timeout=30.0,
)


def configure(
    *,
    username: str | None = None,
    password: str | None = None,
    subscription_key: str | None = None,
) -> None:
    """Set ERCOT API credentials directly, instead of using environment variables.

    Any value left as None will fall back to the corresponding environment variable
    (ERCOT_USERNAME, ERCOT_PASSWORD, ERCOT_SUBSCRIPTION_KEY).

    Calling this clears any cached auth token so new credentials take effect immediately.
    """
    global _username, _password, _subscription_key
    _username = username
    _password = password
    _subscription_key = subscription_key
    _tok_cache.clear()


def _resolve_creds() -> tuple[str, str, str]:
    username = _username or os.environ["ERCOT_USERNAME"]
    password = _password or os.environ["ERCOT_PASSWORD"]
    sub_key = _subscription_key or os.environ["ERCOT_SUBSCRIPTION_KEY"]
    return username, password, sub_key


def _auth_url() -> str:
    username, password, _ = _resolve_creds()
    return (
        f"https://ercotb2c.b2clogin.com/ercotb2c.onmicrosoft.com/"
        f"B2C_1_PUBAPI-ROPC-FLOW/oauth2/v2.0/token"
        f"?username={username}&password={password}"
        f"&grant_type=password&scope={SCOPE}&client_id={CLIENT_ID}&response_type=id_token"
    )

_rate_limiter = AsyncLimiter(20, 60)
_async_client: httpx.AsyncClient | None = None

_MAX_RETRIES = 5
_BASE_DELAY = 2.0  # seconds


def _get_async_client() -> httpx.AsyncClient:
    global _async_client
    if _async_client is None:
        _async_client = httpx.AsyncClient(timeout=30.0)
    return _async_client


@cached(_tok_cache)
def _token() -> str:
    return _client.post(_auth_url()).json().get("id_token")


def _get(path: str, schema: dict | None = None, **params) -> dict:  # pyright: ignore
    """Fetch data from API, optionally converting list-of-lists to list-of-dicts."""
    _, _, sub_key = _resolve_creds()
    response = _client.get(
        f"{BASE_URL}/{path.lstrip('/')}",
        headers={
            "Ocp-Apim-Subscription-Key": sub_key,
            "Authorization": f"Bearer {_token()}",
        },
        params={k: v for k, v in params.items() if v is not None},
    ).json()

    if schema and "data" in response and response["data"]:
        keys = list(schema.keys())
        response["data"] = [dict(zip(keys, row)) for row in response["data"]]

    return response


async def _aget(path: str, schema: dict | None = None, **params) -> dict:  # pyright: ignore
    """Async fetch with rate limiting and retry on 429."""
    _, _, sub_key = _resolve_creds()
    client = _get_async_client()
    url = f"{BASE_URL}/{path.lstrip('/')}"
    headers = {
        "Ocp-Apim-Subscription-Key": sub_key,
        "Authorization": f"Bearer {_token()}",
    }
    filtered_params = {k: v for k, v in params.items() if v is not None}

    for attempt in range(_MAX_RETRIES):
        async with _rate_limiter:
            resp = await client.get(
                url, headers=headers, params=filtered_params
            )

            if resp.status_code == 429:
                # Exponential backoff: 2s, 4s, 8s, 16s, 32s
                delay = _BASE_DELAY * (2**attempt)
                await asyncio.sleep(delay)
                continue

            response = resp.json()
            break
    else:
        # All retries exhausted
        raise httpx.HTTPStatusError(
            f"Rate limited after {_MAX_RETRIES} retries",
            request=resp.request,
            response=resp,
        )

    # Convert list-of-lists to list-of-dicts if schema provided
    if schema and "data" in response and response["data"]:
        keys = list(schema.keys())
        response["data"] = [dict(zip(keys, row)) for row in response["data"]]

    return response


class ErcotResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(populate_by_name=True, extra="allow")
    meta: dict = Field(default_factory=dict, alias="_meta")
    report: dict = Field(default_factory=dict)
    fields: list[dict] = Field(default_factory=list)
    data: list[T] = Field(default_factory=list)
    links: list[dict] | dict = Field(default_factory=dict, alias="_links")
    _schema: ClassVar[dict] = {}

    def to_df(self):
        import pandas as pd

        df = pd.DataFrame([r.model_dump() for r in self.data])
        for col, dtype in self._schema.items():
            if col not in df.columns:
                continue
            match dtype:
                case "DATE":
                    df[col] = pd.to_datetime(df[col]).dt.date
                case "DATETIME":
                    df[col] = pd.to_datetime(df[col])
                case "DOUBLE":
                    df[col] = pd.to_numeric(df[col], errors="coerce")
                case "INTEGER":
                    df[col] = pd.to_numeric(df[col], errors="coerce").astype(
                        "Int64"
                    )
                case "BOOLEAN":
                    df[col] = df[col].astype(bool)
        return df
