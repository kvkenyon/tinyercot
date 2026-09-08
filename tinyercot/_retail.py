"""Public retail transaction counts, retaining source categories and totals."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date
from decimal import Decimal
from time import strptime

from pydantic import BaseModel, ConfigDict

from ._legacy_load import _number
from ._load import _sheets, _workbooks
from ._public_tables import _PublicTable


class RetailTransactionDay(BaseModel):
    """One daily count from a published transaction/category row."""

    model_config = ConfigDict(extra="forbid")
    operatingDay: date
    count: int | None


class RetailTransactionMonth(BaseModel):
    """One transaction code or category total for a source month.

    transactionCode=None identifies the source's Grand Total row. Categories
    overlap: sourceSheet retains the original grouping, including unnamed ones.
    Reported totals and averages are retained rather than recalculated.
    """

    model_config = ConfigDict(extra="forbid")
    month: date
    transactionCode: str | None
    days: list[RetailTransactionDay]
    reportedTotal: int | None
    reportedAveragePerDay: Decimal | None
    sourceMember: str
    sourceSheet: str


class RetailTransactions(_PublicTable[RetailTransactionMonth]):
    """Discover retail transaction histories; decoding uses tinyercot[files]."""

    index_url = "https://www.ercot.com/mktinfo/retail"
    title_pattern = r"Retail Monthly Transaction Totals"

    def _read(self, data: bytes, filename: str) -> Iterator[RetailTransactionMonth]:
        found = False
        for member, content in _workbooks(data):
            member = filename if member in {"workbook.xls", "workbook.xlsx"} else member
            for sheet, rows in _sheets(content, date_columns=()):
                header = next(rows, ())
                if (
                    len(header) < 4
                    or header[0] not in (None, "")
                    or header[-2:] != ("Grand Total", "Average/day")
                ):
                    raise ValueError(
                        f"{member}/{sheet}: Unexpected retail count header"
                    )
                dates = [date(*strptime(str(v), "%m/%d/%Y")[:3]) for v in header[1:-2]]
                month = dates[0].replace(day=1)
                if any(d.replace(day=1) != month for d in dates):
                    raise ValueError(f"{member}/{sheet}: Mixed months in retail table")
                found = True
                for cells in rows:
                    if all(c in (None, "") for c in cells):
                        continue
                    if len(cells) != len(header) or not isinstance(cells[0], str):
                        raise ValueError(
                            f"{member}/{sheet}: Unexpected retail count row"
                        )
                    yield RetailTransactionMonth.model_validate(
                        {
                            "month": month,
                            "transactionCode": None
                            if cells[0] == "Grand Total"
                            else cells[0],
                            "days": [
                                {"operatingDay": day, "count": _number(value)}
                                for day, value in zip(dates, cells[1:-2], strict=True)
                            ],
                            "reportedTotal": _number(cells[-2]),
                            "reportedAveragePerDay": _number(cells[-1]),
                            "sourceMember": member,
                            "sourceSheet": sheet,
                        }
                    )
        if not found:
            raise ValueError("Download contains no retail transaction tables")
