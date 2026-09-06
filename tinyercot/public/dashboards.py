"""Anonymous fuel-mix and Daily PRC snapshots from ERCOT's public dashboards.

The source pages link these JSON routes directly. Explicit models describe the
observed payloads, not a guaranteed service schema or historical availability.
See docs/public-dashboards.md for primary sources and fixture provenance.
"""

import datetime
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Self
from zoneinfo import ZoneInfo

import httpx
from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr, field_validator

from ._http import _HTTP, Limits, Payload, Receipt, SchemaMismatchError

FUEL_MIX_URL = "https://www.ercot.com/api/1/services/read/dashboards/fuel-mix.json"
DAILY_PRC_URL = "https://www.ercot.com/api/1/services/read/dashboards/daily-prc.json"


def _source_time(value: str) -> datetime.datetime:
    """Validate an observed source timestamp against the Texas UTC offset.

    Args:
        value: Original timestamp with its explicit offset.

    Returns:
        The same instant and source offset, without interpreting DST flags.

    Raises:
        ValueError: Text or offset is outside the observed source contract.
    """
    stamp = datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S%z")
    texas = stamp.astimezone(ZoneInfo("America/Chicago"))
    if stamp.utcoffset() != texas.utcoffset():
        raise ValueError("Source offset does not match Texas time")
    return stamp


class FuelMixValues(BaseModel):
    """Eight observed fuel categories in source MW, including signed storage.

    Attributes:
        coal_and_lignite: Coal and Lignite source value.
        hydro: Hydro source value.
        nuclear: Nuclear source value.
        other: Other source value.
        power_storage: Power Storage source value; negative values are retained.
        solar: Solar source value.
        wind: Wind source value.
        natural_gas: Natural Gas source value.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)
    coal_and_lignite: Decimal = Field(alias="Coal and Lignite")
    hydro: Decimal = Field(alias="Hydro")
    nuclear: Decimal = Field(alias="Nuclear")
    other: Decimal = Field(alias="Other")
    power_storage: Decimal = Field(alias="Power Storage")
    solar: Decimal = Field(alias="Solar")
    wind: Decimal = Field(alias="Wind")
    natural_gas: Decimal = Field(alias="Natural Gas")

    @field_validator("*", mode="before")
    @classmethod
    def numeric_source(cls, value: object) -> Decimal:
        """Require finite JSON numbers without string or boolean coercion.

        Args:
            value: One source number, parsed losslessly from JSON.

        Returns:
            The exact numeric value as a Decimal.

        Raises:
            ValueError: The value is nonnumeric or nonfinite.
        """
        if type(value) not in (int, float, Decimal):
            raise ValueError("Expected a JSON number")
        result = Decimal(str(value))
        if not result.is_finite():
            raise ValueError("Expected a finite number")
        return result


@dataclass(frozen=True)
class FuelMixRow:
    """One generation observation, retaining original day and time labels.

    Attributes:
        source_day: Unchanged source day-section key.
        source_timestamp: Unchanged source time key, including its offset.
        timestamp: Validated observation instant with the source offset.
        generation: Source generation MW by fuel; no rounding or aggregation.
    """

    source_day: str
    source_timestamp: str
    timestamp: datetime.datetime
    generation: FuelMixValues


@dataclass(frozen=True)
class DashboardSnapshot:
    """Common retrieval and freshness evidence for one dashboard capture.

    Attributes:
        source_last_updated: Original source update text, including its offset.
        last_updated: Validated source update instant.
        receipt: Retrieval time, public URL, HTTP status, and response hash.
        raw: Original response bytes, preserving source fields and labels.
    """

    source_last_updated: str
    last_updated: datetime.datetime
    receipt: Receipt
    raw: bytes = field(repr=False)

    def is_stale(
        self, *, max_age: datetime.timedelta = datetime.timedelta(minutes=10)
    ) -> bool:
        """Compare source update time against this capture's retrieval time.

        Args:
            max_age: Acceptable age selected by the caller, not a source SLA.

        Returns:
            True when the source update is too old or is in the future.

        Raises:
            ValueError: max_age is negative.
        """
        if max_age < datetime.timedelta(0):
            raise ValueError("max_age must be nonnegative")
        age = self.receipt.retrieved_at - self.last_updated
        return age < datetime.timedelta(0) or age > max_age


@dataclass(frozen=True)
class FuelMixSnapshot(DashboardSnapshot):
    """One rolling fuel-mix capture with source capacity kept separate.

    Attributes:
        monthly_capacity: Source monthlyCapacity MW, not per-interval generation.
        rows: Observations in source day/time order, without history guarantees.
    """

    monthly_capacity: FuelMixValues
    rows: tuple[FuelMixRow, ...]


class GridCondition(BaseModel):
    """Unchanged source status fields from the Daily PRC dashboard.

    Strings remain source labels, not a client-defined emergency-state enum.

    Attributes:
        condition_note: Source explanatory status text.
        eea_level: Raw source EEA level integer.
        energy_level_value: Raw source energy level integer.
        state: Raw source condition state.
        title: Raw source condition title.
        prc_value: Source display value, including thousands separators.
        index: Raw source index, not a pagination cursor.
        datetime: Source epoch seconds for the condition.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)
    condition_note: StrictStr
    eea_level: StrictInt
    energy_level_value: StrictInt
    state: StrictStr
    title: StrictStr
    prc_value: StrictStr
    index: StrictInt
    datetime: StrictInt


class PrcRow(BaseModel):
    """One source Physical Responsive Capability observation in MW.

    Attributes:
        timestamp: Original source timestamp, including its UTC offset.
        epoch: Source epoch milliseconds, verified against timestamp.
        interval: Original local interval text, verified against timestamp.
        dstFlag: Raw source DST flag without inferred meaning.
        prc: Source PRC MW integer.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)
    timestamp: StrictStr
    epoch: StrictInt
    interval: StrictStr
    dstFlag: StrictStr
    prc: StrictInt


@dataclass(frozen=True)
class GridConditionsSnapshot(DashboardSnapshot):
    """One Daily PRC capture, including its current grid-condition status.

    Attributes:
        current_condition: Unmodified source condition fields.
        rows: Source-order PRC observations with verified time evidence.
    """

    current_condition: GridCondition
    rows: tuple[PrcRow, ...]


def decode_fuel_mix(payload: Payload) -> FuelMixSnapshot:
    """Decode the observed eight-fuel rolling feed without inferring history.

    Args:
        payload: Bounded public JSON bytes and retrieval receipt.

    Returns:
        Typed generation, monthly capacity, original timestamps, and raw bytes.

    Raises:
        SchemaMismatchError: Field names, types, or time evidence differ.
    """
    body = payload.json()
    try:
        if set(body) != {"lastUpdated", "monthlyCapacity", "data"}:
            raise ValueError
        updated = _source_time(body["lastUpdated"])
        capacity = FuelMixValues.model_validate(body["monthlyCapacity"])
        rows = []
        previous = None
        for day, observations in body["data"].items():
            if datetime.date.fromisoformat(day).isoformat() != day:
                raise ValueError
            for text, fuels in observations.items():
                stamp = _source_time(text)
                if stamp.date().isoformat() != day or stamp > updated:
                    raise ValueError
                if previous is not None and stamp <= previous:
                    raise ValueError
                values = {}
                for name, value in fuels.items():
                    if set(value) != {"gen"}:
                        raise ValueError
                    values[name] = value["gen"]
                rows.append(
                    FuelMixRow(day, text, stamp, FuelMixValues.model_validate(values))
                )
                previous = stamp
        return FuelMixSnapshot(
            body["lastUpdated"],
            updated,
            payload.receipt,
            payload.body,
            capacity,
            tuple(rows),
        )
    except (AttributeError, KeyError, TypeError, ValueError):
        pass
    raise SchemaMismatchError("Fuel mix differs from the observed source contract")


def decode_grid_conditions(payload: Payload) -> GridConditionsSnapshot:
    """Decode Daily PRC and preserve the current condition status verbatim.

    Args:
        payload: Bounded public JSON bytes and retrieval receipt.

    Returns:
        Typed PRC rows, source condition, time evidence, and raw response bytes.

    Raises:
        SchemaMismatchError: Field names, types, or time evidence differ.
    """
    body = payload.json()
    try:
        if set(body) != {"lastUpdated", "current_condition", "data"}:
            raise ValueError
        updated = _source_time(body["lastUpdated"])
        condition = GridCondition.model_validate(body["current_condition"])
        if condition.datetime != int(updated.timestamp()):
            raise ValueError
        if not isinstance(body["data"], list):
            raise TypeError
        rows = tuple(PrcRow.model_validate(row) for row in body["data"])
        previous = None
        for row in rows:
            stamp = _source_time(row.timestamp)
            if (
                row.epoch != int(stamp.timestamp() * 1000)
                or row.interval != stamp.strftime("%H:%M:%S")
                or stamp > updated
                or (previous is not None and row.epoch <= previous)
            ):
                raise ValueError
            previous = row.epoch
        return GridConditionsSnapshot(
            body["lastUpdated"],
            updated,
            payload.receipt,
            payload.body,
            condition,
            rows,
        )
    except (KeyError, TypeError, ValueError):
        pass
    raise SchemaMismatchError("Daily PRC differs from the observed source contract")


class DashboardClient:
    """Anonymous, bounded captures of two explicitly supported website feeds.

    Methods perform one logical capture with bounded retries. They do not poll,
    fetch historical dates, or claim the rolling rows establish retention.
    """

    def __init__(
        self,
        *,
        limits: Limits | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        """Create an anonymous dashboard client without making requests.

        Args:
            limits: Request, response-size, retry, and pacing safeguards.
            transport: Optional mocked HTTPX transport for offline validation.
        """
        self._http = _HTTP(limits or Limits(), transport)

    def __enter__(self) -> Self:
        """Enter a context that closes HTTP connections on exit.

        Returns:
            This client instance.
        """
        return self

    def __exit__(self, *exc: object) -> None:
        """Close connections when the context ends.

        Args:
            *exc: Context exception details; exceptions are not suppressed.
        """
        self.close()

    def close(self) -> None:
        """Release this instance's HTTP connections."""
        self._http.close()

    def fuel_mix(self) -> FuelMixSnapshot:
        """Capture the anonymous rolling fuel-mix feed once.

        Returns:
            Typed source values and explicit receipt and freshness evidence.

        Raises:
            PublicDataError: Transport, byte budget, or schema validation fails.
        """
        return decode_fuel_mix(self._http.request("GET", FUEL_MIX_URL))

    def grid_conditions(self) -> GridConditionsSnapshot:
        """Capture anonymous Daily PRC and its grid-condition status once.

        Returns:
            Typed PRC observations and unchanged source status fields.

        Raises:
            PublicDataError: Transport, byte budget, or schema validation fails.
        """
        return decode_grid_conditions(self._http.request("GET", DAILY_PRC_URL))
