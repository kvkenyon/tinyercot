import os
from typing import ClassVar, Generic, TypeVar

import httpx
from cachetools import TTLCache, cached
from httpx_retries import Retry, RetryTransport
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T", bound=BaseModel)

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


class ErcotResponse(BaseModel, Generic[T]):
    """Base response model with to_df() support."""

    model_config = ConfigDict(populate_by_name=True)
    meta: dict = Field(alias="_meta")
    links: dict = Field(alias="_links")
    data: list[T]
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
