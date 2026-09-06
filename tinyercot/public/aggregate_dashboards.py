"""Anonymous generation-outage and DC-tie aggregate dashboard captures.

These models cover observed public website payloads only. Rolling prior rows
are part of one capture and do not provide a historical retrieval contract.
Primary routes and source limitations are recorded in docs/public-aggregates.md.
"""

import datetime
from dataclasses import dataclass
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr, field_validator

from ._http import Payload, SchemaMismatchError
from .dashboards import DashboardClient, DashboardSnapshot, _source_time

GENERATION_OUTAGES_URL = (
    "https://www.ercot.com/api/1/services/read/dashboards/generation-outages.json"
)
DC_TIE_FLOWS_URL = (
    "https://www.ercot.com/api/1/services/read/dashboards/dc-tie-flows.json"
)


class OutageAmounts(BaseModel):
    """Source outage capability reductions in MW without recalculated totals.

    Attributes:
        unplanned: Source unplanned outage MW.
        planned: Source planned outage MW.
        total: Source total outage MW.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)
    unplanned: StrictInt
    planned: StrictInt
    total: StrictInt


class GenerationOutageRow(BaseModel):
    """One source outage observation with resource categories kept separate.

    Attributes:
        deliveryTime: Unchanged source local time and UTC offset.
        dstFlag: Source DST label, without inferred meaning.
        combined: Source Combined outage values.
        dispatchable: Source Dispatchable outage values.
        renewable: Source Renewable outage values.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)
    deliveryTime: StrictStr
    dstFlag: StrictStr
    combined: OutageAmounts = Field(alias="Combined")
    dispatchable: OutageAmounts = Field(alias="Dispatchable")
    renewable: OutageAmounts = Field(alias="Renewable")


@dataclass(frozen=True)
class OutageObservation:
    """One row plus its original epoch key and verified observation instant.

    Attributes:
        source_epoch: Unchanged object key containing source epoch milliseconds.
        timestamp: Instant and offset established by deliveryTime and epoch.
        row: Original time labels and typed source outage values.
    """

    source_epoch: str
    timestamp: datetime.datetime
    row: GenerationOutageRow


class OutageDays(BaseModel):
    """Source day labels, which describe this capture's sections only.

    Attributes:
        previous: Ordered source labels for the previous section.
        current: Ordered source labels for the current section.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)
    previous: tuple[StrictStr, ...]
    current: tuple[StrictStr, ...]


@dataclass(frozen=True)
class GenerationOutagesSnapshot(DashboardSnapshot):
    """One rolling public outage capture with all returned sections retained.

    Attributes:
        current_outages: Source currentOutages MW, not a recomputed aggregate.
        days: Source section date labels, without a retention guarantee.
        resource_types: Original source type labels and order.
        current: Ordered observations from the source current section.
        previous: Ordered observations from the source previous section.
    """

    current_outages: int
    days: OutageDays
    resource_types: tuple[str, ...]
    current: tuple[OutageObservation, ...]
    previous: tuple[OutageObservation, ...]


class DcTieRow(BaseModel):
    """One public aggregate DC-tie observation with the source sign convention.

    Attributes:
        currentFrequency: Source system frequency in Hz, preserved as Decimal.
        currentSystemInertia: Source aggregate inertia integer, without conversion.
        dcE: Source east DC-tie MW; negative is import and positive is export.
        dcN: Source north DC-tie MW with the same sign convention.
        dcL: Source Laredo DC-tie MW with the same sign convention.
        dcR: Source Railroad DC-tie MW with the same sign convention.
        timestamp: Original source local timestamp with explicit offset.
        epoch: Source epoch milliseconds, checked against timestamp.
        interval: Original source interval text, checked against timestamp.
        dstFlag: Raw source DST label, without inferred meaning.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)
    currentFrequency: Decimal
    currentSystemInertia: StrictInt
    dcE: StrictInt
    dcN: StrictInt
    dcL: StrictInt
    dcR: StrictInt
    timestamp: StrictStr
    epoch: StrictInt
    interval: StrictStr
    dstFlag: StrictStr

    @field_validator("currentFrequency", mode="before")
    @classmethod
    def finite_frequency(cls, value: object) -> Decimal:
        """Require finite JSON numbers without boolean or string coercion.

        Args:
            value: Original numeric source value, parsed losslessly from JSON.

        Returns:
            The exact source frequency as a Decimal.

        Raises:
            ValueError: The source type is unknown or its value is nonfinite.
        """
        if type(value) not in (int, float, Decimal):
            raise ValueError("Expected a JSON number")
        result = Decimal(str(value))
        if not result.is_finite():
            raise ValueError("Expected finite frequency")
        return result


@dataclass(frozen=True)
class DcTieSnapshot(DashboardSnapshot):
    """One public DC-tie capture without schedules or historical availability.

    Attributes:
        rows: All returned aggregate observations in original source order.
    """

    rows: tuple[DcTieRow, ...]


def decode_generation_outages(payload: Payload) -> GenerationOutagesSnapshot:
    """Decode one rolling outage payload and validate section/time evidence.

    Args:
        payload: Bounded public source bytes and retrieval receipt.

    Returns:
        Typed current and previous observations with original labels and bytes.

    Raises:
        SchemaMismatchError: Shape, source type, section, or time evidence differs.
    """
    body = payload.json()
    try:
        if set(body) != {
            "lastUpdated",
            "currentOutages",
            "days",
            "types",
            "current",
            "previous",
        }:
            raise ValueError
        updated = _source_time(body["lastUpdated"])
        if type(body["currentOutages"]) is not int:
            raise TypeError
        if not isinstance(body["types"], list) or sorted(body["types"]) != [
            "Dispatchable",
            "Renewable",
        ]:
            raise ValueError
        days = OutageDays.model_validate(body["days"])
        labels = days.previous + days.current
        if len(labels) != len(set(labels)):
            raise ValueError
        for label in labels:
            if datetime.date.fromisoformat(label).isoformat() != label:
                raise ValueError
        sections = []
        for name in ("current", "previous"):
            observations = []
            previous_epoch = None
            for key, value in body[name].items():
                if not isinstance(key, str) or not key.isascii() or not key.isdecimal():
                    raise ValueError
                row = GenerationOutageRow.model_validate(value)
                stamp = _source_time(row.deliveryTime)
                epoch = int(key)
                if (
                    epoch != int(stamp.timestamp() * 1000)
                    or stamp > updated
                    or stamp.date().isoformat() not in getattr(days, name)
                    or (previous_epoch is not None and epoch <= previous_epoch)
                ):
                    raise ValueError
                observations.append(OutageObservation(key, stamp, row))
                previous_epoch = epoch
            sections.append(tuple(observations))
        return GenerationOutagesSnapshot(
            body["lastUpdated"],
            updated,
            payload.receipt,
            payload.body,
            body["currentOutages"],
            days,
            tuple(body["types"]),
            *sections,
        )
    except (AttributeError, KeyError, TypeError, ValueError):
        pass
    raise SchemaMismatchError("Generation outages differ from the observed contract")


def decode_dc_tie_flows(payload: Payload) -> DcTieSnapshot:
    """Decode one aggregate DC-tie capture with its signed source values.

    Args:
        payload: Bounded public source bytes and retrieval receipt.

    Returns:
        Typed aggregate rows, original time labels and bytes, and receipt.

    Raises:
        SchemaMismatchError: Fields, types, ordering, or time evidence differs.
    """
    body = payload.json()
    try:
        if set(body) != {"lastUpdated", "data"}:
            raise ValueError
        updated = _source_time(body["lastUpdated"])
        if not isinstance(body["data"], list):
            raise TypeError
        rows = tuple(DcTieRow.model_validate(value) for value in body["data"])
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
        return DcTieSnapshot(
            body["lastUpdated"],
            updated,
            payload.receipt,
            payload.body,
            rows,
        )
    except (KeyError, TypeError, ValueError):
        pass
    raise SchemaMismatchError("DC-tie flows differ from the observed contract")


class AggregateDashboardClient(DashboardClient):
    """Anonymous outage and DC-tie captures using existing dashboard safeguards.

    Inherits connection lifetime, limits, and the two existing capture methods.
    No credentials, private telemetry, schedule data, or historical date queries
    are used. Returned prior rows belong to the source's single rolling capture.
    """

    def generation_outages(self) -> GenerationOutagesSnapshot:
        """Capture current and rolling previous public generation outages once.

        Returns:
            Typed resource aggregates, source time evidence, and raw receipt.

        Raises:
            PublicDataError: Bounded transport or observed schema checks fail.
        """
        return decode_generation_outages(
            self._http.request("GET", GENERATION_OUTAGES_URL)
        )

    def dc_tie_flows(self) -> DcTieSnapshot:
        """Capture public DC-tie aggregate flows once without polling.

        Returns:
            Typed signed flows, frequency, inertia, time evidence, and receipt.

        Raises:
            PublicDataError: Bounded transport or observed schema checks fail.
        """
        return decode_dc_tie_flows(self._http.request("GET", DC_TIE_FLOWS_URL))
