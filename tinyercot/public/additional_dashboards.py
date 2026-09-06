"""Public price and supply/demand snapshots with source sections kept distinct.

Published forecasts are decoded as source data; no forecast is calculated.
See docs/additional-dashboards.md for the observed contracts and provenance.
"""

import datetime
from dataclasses import dataclass
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, StrictInt, StrictStr

from ._http import Payload, SchemaMismatchError
from .dashboards import DashboardClient, DashboardSnapshot, _source_time

SYSTEM_PRICES_URL = (
    "https://www.ercot.com/api/1/services/read/dashboards/system-wide-prices.json"
)
SUPPLY_DEMAND_URL = (
    "https://www.ercot.com/api/1/services/read/dashboards/supply-demand.json"
)


def _number(value: object) -> Decimal:
    """Keep finite source numbers exact without string or boolean coercion.

    Args:
        value: A JSON numeric value.

    Returns:
        Exact Decimal representation of the source value.

    Raises:
        ValueError: The value is nonnumeric or nonfinite.
    """
    if type(value) not in (int, float, Decimal):
        raise ValueError("Expected a JSON number")
    result = Decimal(str(value))
    if not result.is_finite():
        raise ValueError("Expected a finite number")
    return result


_Number = Annotated[Decimal, BeforeValidator(_number)]


class DashboardPrices(BaseModel):
    """Source hub and load-zone price columns without averaging or rounding.

    Attributes:
        hbBusAvg: Source hub bus average price.
        hbHubAvg: Source hub average price.
        hbHouston: Source Houston hub price.
        hbNorth: Source North hub price.
        hbPan: Source Panhandle hub price.
        hbSouth: Source South hub price.
        hbWest: Source West hub price.
        lzAen: Source AEN load-zone price.
        lzCps: Source CPS load-zone price.
        lzHouston: Source Houston load-zone price.
        lzLcra: Source LCRA load-zone price.
        lzNorth: Source North load-zone price.
        lzRaybn: Source RAYBN load-zone price.
        lzSouth: Source South load-zone price.
        lzWest: Source West load-zone price.
        dstFlag: Raw source DST label with no inferred meaning.
        timestamp: Original interval timestamp with its offset.
        interval: Source epoch milliseconds, checked against timestamp.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)
    hbBusAvg: _Number
    hbHubAvg: _Number
    hbHouston: _Number
    hbNorth: _Number
    hbPan: _Number
    hbSouth: _Number
    hbWest: _Number
    lzAen: _Number
    lzCps: _Number
    lzHouston: _Number
    lzLcra: _Number
    lzNorth: _Number
    lzRaybn: _Number
    lzSouth: _Number
    lzWest: _Number
    dstFlag: StrictStr
    timestamp: StrictStr
    interval: StrictInt


class RealTimeDashboardPrice(DashboardPrices):
    """One source real-time price observation.

    Attributes:
        intervalEnding: Original source HH:MM interval-ending label.
    """

    intervalEnding: StrictStr


class DayAheadDashboardPrice(DashboardPrices):
    """One published day-ahead price, which can describe a future interval.

    Attributes:
        hourEnding: Original source hour-ending integer, including 24.
    """

    hourEnding: StrictInt


@dataclass(frozen=True)
class SystemPricesSnapshot(DashboardSnapshot):
    """One website price capture with real-time and day-ahead sections separate.

    Attributes:
        real_time: Ordered rtSppData observations, preserving all source prices.
        day_ahead: Ordered damSppData rows, including published future intervals.
    """

    real_time: tuple[RealTimeDashboardPrice, ...]
    day_ahead: tuple[DayAheadDashboardPrice, ...]


class SupplyObservation(BaseModel):
    """Common fields of the source supply/demand data section in MW.

    Attributes:
        capacity: Original source capacity MW, without inferred availability.
        demand: Original source demand MW.
        dstFlag: Original integer flag; distinct from the outlook's string flag.
        interval: Original minute label.
        hourEnding: Original hour label, including source 0 and 24.
        timestamp: Original source timestamp and offset.
        epoch: Source epoch milliseconds, checked against timestamp.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)
    capacity: StrictInt
    demand: StrictInt
    dstFlag: StrictInt
    interval: StrictInt
    hourEnding: StrictInt
    timestamp: StrictStr
    epoch: StrictInt


class SupplyActualRow(SupplyObservation):
    """A source actual observation without an invented available value.

    Attributes:
        forecast: Source integer discriminator 0, preserved explicitly.
    """

    forecast: Literal[0]


class SupplyForecastRow(SupplyObservation):
    """A published same-day forecast observation, not a client prediction.

    Attributes:
        forecast: Source integer discriminator 1, preserved explicitly.
        available: Source forecast-only available MW, required when forecast is 1.
    """

    forecast: Literal[1]
    available: StrictInt


class SupplyOutlookRow(BaseModel):
    """One published multi-day hourly outlook, preserving original date labels.

    Attributes:
        deliveryDate: Source operating-day text.
        dstFlag: Original source string flag, without inferred meaning.
        hourEnding: Original integer hour-ending label, including 24.
        deliveryDateHrBegin: Original local interval-begin text with no offset.
        deliveryDateHrEnd: Original local interval-end text with no offset.
        availCapGen: Published source available-generation capacity MW.
        forecastedDemand: Published source forecast demand MW.
        timestamp: Source offset-bearing interval-end timestamp.
        epoch: Source interval-end epoch milliseconds.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)
    deliveryDate: StrictStr
    dstFlag: StrictStr
    hourEnding: StrictInt
    deliveryDateHrBegin: StrictStr
    deliveryDateHrEnd: StrictStr
    availCapGen: StrictInt
    forecastedDemand: StrictInt
    timestamp: StrictStr
    epoch: StrictInt


@dataclass(frozen=True)
class SupplyDemandSnapshot(DashboardSnapshot):
    """One source supply/demand capture with observed and forecast rows distinct.

    Attributes:
        data: Source-order rows; forecast-only available is never fabricated.
        forecast: Original multi-day published outlook section.
    """

    data: tuple[SupplyActualRow | SupplyForecastRow, ...]
    forecast: tuple[SupplyOutlookRow, ...]


def _instant(text: str, epoch: int, previous: int | None) -> datetime.datetime:
    """Validate exact source epoch, Texas offset, and ascending order.

    Args:
        text: Original source timestamp.
        epoch: Original epoch milliseconds.
        previous: Prior section epoch or None for its first row.

    Returns:
        Source instant with its original offset.

    Raises:
        ValueError: Source time evidence conflicts or order repeats/reverses.
    """
    stamp = _source_time(text)
    if int(stamp.timestamp() * 1000) != epoch or (
        previous is not None and epoch <= previous
    ):
        raise ValueError("Conflicting source interval evidence")
    return stamp


def decode_system_prices(payload: Payload) -> SystemPricesSnapshot:
    """Decode observed website prices without conflating them with API reports.

    Args:
        payload: One bounded anonymous response and receipt.

    Returns:
        Source-order real-time and published day-ahead prices with provenance.

    Raises:
        SchemaMismatchError: Types, shape, interval labels, or time evidence differ.
    """
    body = payload.json()
    try:
        if set(body) != {"lastUpdated", "rtSppData", "damSppData"}:
            raise ValueError
        updated = _source_time(body["lastUpdated"])
        if not isinstance(body["rtSppData"], list) or not isinstance(
            body["damSppData"], list
        ):
            raise TypeError
        rt = tuple(RealTimeDashboardPrice.model_validate(r) for r in body["rtSppData"])
        dam = tuple(
            DayAheadDashboardPrice.model_validate(r) for r in body["damSppData"]
        )
        previous = None
        for row in rt:
            stamp = _instant(row.timestamp, row.interval, previous)
            labels = {stamp.strftime("%H:%M")}
            if stamp.hour == stamp.minute == 0:
                labels.add("24:00")
            if row.intervalEnding not in labels or stamp > updated:
                raise ValueError
            previous = row.interval
        previous = None
        for day_row in dam:
            stamp = _instant(day_row.timestamp, day_row.interval, previous)
            if day_row.hourEnding != (stamp.hour or 24) or stamp.minute != 0:
                raise ValueError
            previous = day_row.interval
        return SystemPricesSnapshot(
            body["lastUpdated"], updated, payload.receipt, payload.body, rt, dam
        )
    except (KeyError, TypeError, ValueError):
        pass
    raise SchemaMismatchError("System prices differ from the observed contract")


def decode_supply_demand(payload: Payload) -> SupplyDemandSnapshot:
    """Decode published supply/demand without computing or filling forecasts.

    Args:
        payload: One bounded anonymous response and receipt.

    Returns:
        Distinct actual, same-day forecast, and outlook rows in source order.

    Raises:
        SchemaMismatchError: Source types, discriminators, or time evidence differ.
    """
    body = payload.json()
    try:
        if set(body) != {"lastUpdated", "data", "forecast"}:
            raise ValueError
        updated = _source_time(body["lastUpdated"])
        if not isinstance(body["data"], list) or not isinstance(body["forecast"], list):
            raise TypeError
        data: list[SupplyActualRow | SupplyForecastRow] = []
        previous = None
        for value in body["data"]:
            if type(value["forecast"]) is not int or value["forecast"] not in (0, 1):
                raise ValueError
            row = (
                SupplyActualRow.model_validate(value)
                if value["forecast"] == 0
                else SupplyForecastRow.model_validate(value)
            )
            stamp = _instant(row.timestamp, row.epoch, previous)
            if row.interval != stamp.minute or row.hourEnding not in (
                {0, 24} if stamp.hour == 0 else {stamp.hour}
            ):
                raise ValueError
            if row.forecast == 0 and stamp > updated:
                raise ValueError
            data.append(row)
            previous = row.epoch
        outlook = tuple(SupplyOutlookRow.model_validate(r) for r in body["forecast"])
        previous = None
        for future in outlook:
            stamp = _instant(future.timestamp, future.epoch, previous)
            begin = datetime.datetime.fromisoformat(future.deliveryDateHrBegin)
            end = datetime.datetime.fromisoformat(future.deliveryDateHrEnd)
            if (
                begin.tzinfo is not None
                or end.tzinfo is not None
                or begin > end
                or end != stamp.replace(tzinfo=None)
                or future.deliveryDate != begin.date().isoformat()
                or future.hourEnding != (end.hour or 24)
                or end.minute != 0
                or begin.minute != 0
            ):
                raise ValueError
            previous = future.epoch
        return SupplyDemandSnapshot(
            body["lastUpdated"],
            updated,
            payload.receipt,
            payload.body,
            tuple(data),
            outlook,
        )
    except (KeyError, TypeError, ValueError):
        pass
    raise SchemaMismatchError("Supply/demand differs from the observed contract")


class AdditionalDashboardClient(DashboardClient):
    """Anonymous price and supply/demand captures with existing request budgets."""

    def system_prices(self) -> SystemPricesSnapshot:
        """Capture the public system-wide price display once.

        Returns:
            Typed source prices with separate real-time/day-ahead sections.

        Raises:
            PublicDataError: Bounded transport or schema checks fail.
        """
        return decode_system_prices(self._http.request("GET", SYSTEM_PRICES_URL))

    def supply_demand(self) -> SupplyDemandSnapshot:
        """Capture public supply/demand and published forecasts once.

        Returns:
            Source rows, labels, freshness evidence, and original bytes.

        Raises:
            PublicDataError: Bounded transport or schema checks fail.
        """
        return decode_supply_demand(self._http.request("GET", SUPPLY_DEMAND_URL))
