"""Typed observations of the public rolling ESR dashboard feed."""

import datetime
from dataclasses import dataclass, field
from decimal import Decimal
from zoneinfo import ZoneInfo

from pydantic import (
    BaseModel,
    ConfigDict,
    StrictInt,
    StrictStr,
    field_validator,
    model_validator,
)

from ._http import Payload, Receipt, SchemaMismatchError


class EsrRow(BaseModel):
    """One observed storage aggregate, with source time evidence retained.

    Attributes:
        tagCLastTime: Source local timestamp text, not a publication timestamp.
        dstFlag: Raw source flag with no inferred repeated-hour meaning.
        totalCharging: Source charging MW, preserving the source sign convention.
        totalDischarging: Source discharging MW.
        netOutput: Source net MW; no new calculation or rounding is applied.
        timestamp: Source timestamp with its explicit UTC offset.
        epoch: Source epoch milliseconds, checked against timestamp.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)
    tagCLastTime: StrictStr
    dstFlag: StrictStr
    totalCharging: Decimal
    totalDischarging: Decimal
    netOutput: Decimal
    timestamp: datetime.datetime
    epoch: StrictInt

    @field_validator("timestamp", mode="before")
    @classmethod
    def source_time(cls, value: str) -> datetime.datetime:
        """Parse the observed offset-bearing source format.

        Args:
            value: Timestamp text in the public feed's documented observation.

        Returns:
            Offset-aware datetime without replacing the source offset.

        Raises:
            ValueError: The source text does not match the observed format.
        """
        return datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S%z")

    @model_validator(mode="after")
    def check_time_evidence(self):
        """Require epoch, local text, and Texas offset to describe one instant.

        Returns:
            This row after time and finite-number checks.

        Raises:
            ValueError: Source timestamps conflict or a power value is nonfinite.
        """
        local = datetime.datetime.fromisoformat(self.tagCLastTime)
        texas = self.timestamp.astimezone(ZoneInfo("America/Chicago"))
        if (
            int(self.timestamp.timestamp() * 1000) != self.epoch
            or self.timestamp.replace(tzinfo=None) != local
            or texas.replace(tzinfo=None) != local
            or texas.utcoffset() != self.timestamp.utcoffset()
        ):
            raise ValueError("Conflicting timestamp evidence")
        if not all(
            x.is_finite()
            for x in (self.totalCharging, self.totalDischarging, self.netOutput)
        ):
            raise ValueError("Nonfinite power value")
        return self

    @property
    def utc(self) -> datetime.datetime:
        """The UTC instant established by the source offset and epoch.

        Returns:
            The same instant in UTC; DST flags do not change its meaning.
        """
        return self.timestamp.astimezone(datetime.UTC)


class EsrDay(BaseModel):
    """One source day section, without inventing a history window.

    Attributes:
        dayDate: Original source day marker, including its offset and time.
        data: Typed, ordered storage aggregate observations.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)
    dayDate: StrictStr
    data: tuple[EsrRow, ...]


@dataclass(frozen=True)
class EsrSnapshot:
    """A single rolling feed capture with explicit freshness evidence.

    Attributes:
        last_updated: Source update timestamp with its UTC offset.
        previous_day: Source previous-day section.
        current_day: Source current-day section.
        receipt: Retrieval time and full response hash.
        raw: Original JSON bytes, including all source labels.
    """

    last_updated: datetime.datetime
    previous_day: EsrDay
    current_day: EsrDay
    receipt: Receipt
    raw: bytes = field(repr=False)

    def is_stale(
        self, *, max_age: datetime.timedelta = datetime.timedelta(minutes=10)
    ) -> bool:
        """Compare source update time with this capture's retrieval time.

        Args:
            max_age: Caller-selected acceptable age, not a source SLA.

        Returns:
            True for old data or a source update time in the future.

        Raises:
            ValueError: max_age is negative.
        """
        if max_age.total_seconds() < 0:
            raise ValueError("max_age must be nonnegative")
        age = self.receipt.retrieved_at - self.last_updated
        return age < datetime.timedelta(0) or age > max_age


def decode_esr(payload: Payload) -> EsrSnapshot:
    """Decode the observed rolling feed and validate its time evidence.

    Args:
        payload: Bounded public JSON response and receipt.

    Returns:
        An ESR snapshot with source and retrieval times kept separate.

    Raises:
        SchemaMismatchError: Shape, field values, or timestamp evidence changes.
    """
    body = payload.json()
    try:
        if set(body) != {"lastUpdated", "previousDay", "currentDay"}:
            raise ValueError
        updated = datetime.datetime.strptime(body["lastUpdated"], "%Y-%m-%d %H:%M:%S%z")
        days = []
        for name in ("previousDay", "currentDay"):
            day = EsrDay.model_validate(body[name])
            stamps = [row.epoch for row in day.data]
            if stamps != sorted(set(stamps)):
                raise ValueError
            days.append(day)
        return EsrSnapshot(updated, *days, payload.receipt, payload.body)
    except (KeyError, TypeError, ValueError):
        pass
    raise SchemaMismatchError(
        "ESR feed differs from the observed shape or time contract"
    )
