"""The direct historical archive of interim indicative ORDC results."""

from __future__ import annotations

import csv
from collections.abc import Iterator
from datetime import datetime
from decimal import Decimal
from io import StringIO
from typing import Literal

from pydantic import BaseModel, ConfigDict

from ._history import _csv_files
from ._legacy_load import _number
from ._public_tables import _PublicTable

_HEADER = (
    "SCED_TIMESTAMP",
    "REPEATED_HOUR_FLAG",
    "SYSTEM_LAMBDA",
    "RTOLCAP",
    "RTOFFCAP",
    "RTORPA",
    "RTOFFPA",
)


class IndicativeOrdcPrice(BaseModel):
    """One interim indicative result, not a realized settlement price.

    Reserve/input names retain the source abbreviations. The parsed timestamp
    has no inferred timezone; its original text and repeat-hour flag remain.
    """

    model_config = ConfigDict(extra="forbid")
    indicative: Literal[True] = True
    scedTimestamp: datetime
    sourceTimestamp: str
    repeatedHourFlag: Literal["N", "Y"]
    systemLambda: Decimal | None
    rtolcap: Decimal | None
    rtoffcap: Decimal | None
    rtorpa: Decimal | None
    rtoffpa: Decimal | None
    sourceMember: str


class IndicativeOrdcHistory(_PublicTable[IndicativeOrdcPrice]):
    """Anonymous interim ORDC history; CSV decoding needs no optional packages."""

    index_url = "https://www.ercot.com/mktinfo/rtm"
    title_pattern = r"Indicative Real-Time Reserve ORDC Price Adder"

    def _read(self, data: bytes, filename: str) -> Iterator[IndicativeOrdcPrice]:
        files = (
            _csv_files(data, "*.[cC][sS][vV]")
            if data.startswith(b"PK")
            else iter([(filename, data)])
        )
        found = False
        for member, content in files:
            rows = csv.reader(StringIO(content.decode("utf-8-sig")))
            if tuple(next(rows, ())) != _HEADER:
                raise ValueError(f"{member}: Unexpected indicative ORDC header")
            found = True
            for cells in rows:
                if not cells:
                    continue
                if len(cells) != len(_HEADER):
                    raise ValueError(f"{member}: Unexpected indicative ORDC row width")
                # The source writes midnight as 00:xx AM in a 12-hour clock.
                stamp = cells[0].replace(" 00:", " 12:")
                parsed = datetime.strptime(stamp, "%m/%d/%Y %I:%M:%S %p")  # noqa: DTZ007
                yield IndicativeOrdcPrice.model_validate(
                    {
                        "scedTimestamp": parsed,
                        "sourceTimestamp": cells[0],
                        "repeatedHourFlag": cells[1],
                        "systemLambda": _number(cells[2]),
                        "rtolcap": _number(cells[3]),
                        "rtoffcap": _number(cells[4]),
                        "rtorpa": _number(cells[5]),
                        "rtoffpa": _number(cells[6]),
                        "sourceMember": member,
                    }
                )
        if not found:
            raise ValueError("Download contains no indicative ORDC tables")
