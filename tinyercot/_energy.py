"""Source interval energy quantities shared by public workbook readers."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class EnergyInterval(BaseModel):
    """One original interval column in MWh, with its position and source label.

    Labels can be clock endings (including 24:00) or numbered intervals. Neither
    establishes a UTC timestamp. Missing source values remain None. A missing label means the source row
    extends beyond its interval headers; no clock is inferred.
    """

    model_config = ConfigDict(extra="forbid")
    interval: int
    energyMWh: Decimal | None
    sourceLabel: str | None
