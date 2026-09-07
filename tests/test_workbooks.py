# XLSX timestamps are deliberately timezone-naive, as published.
# ruff: noqa: DTZ001
from collections import Counter
from datetime import date, datetime, time
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pytest
from openpyxl import load_workbook

from tinyercot import Client

INPUTS = Path(__file__).resolve().parents[1] / "tools/inputs/history"


def zipped(name, data):
    output = BytesIO()
    with ZipFile(output, "w") as archive:
        archive.writestr(name, data)
    return output.getvalue()


@pytest.mark.parametrize("period", ["samples", "current"])
def test_workbook_schema_generations(period):
    def read(reader, product):
        return list(
            reader.read(
                zipped(
                    "report.xlsx",
                    (INPUTS / f"{product}-history-{period}.xlsx").read_bytes(),
                )
            )
        )

    with Client() as client:
        outages = read(client.np1_346_er.outages_history, "np1-346-er")
        assert len(outages) == 3
        row = outages[0]
        if period == "samples":
            assert row.returnToServiceDate == datetime(
                2022, 12, 30, 23, 59, tzinfo=None
            )
            assert row.plannedEndDate is None
            assert row.availableMWMaximum == Decimal(18)
        else:
            assert row.returnToServiceDate is None
            assert row.plannedEndDate == datetime(2026, 9, 15, 23, 59, tzinfo=None)
            assert row.actualEndDate is None
        demand = read(client.np3_108.demand_response_history, "np3-108")
        assert Counter(r.sourceSheet for r in demand) == (
            {"Report Data": 3}
            if period == "samples"
            else {"CLR Report Data": 3, "NCLR Report Data": 3}
        )
        assert demand[0].month == (
            date(2017, 12, 1) if period == "samples" else date(2026, 8, 1)
        )
        factors = read(client.np5_520_er.deployment_factors_history, "np5-520-er")
        assert len(factors) == 3
        assert factors[0].minimum == (
            Decimal("0.038") if period == "samples" else Decimal("0.05")
        )


def test_bad_dimensions_and_report_footers():
    book = load_workbook(INPUTS / "np3-108-history-samples.xlsx")
    sheet = book["Report Data"]
    sheet.append(["ERCOT Confidential"])
    sheet.append(["Jan 4, 2018                    - 2 -                    8:00:25 AM"])
    sheet.append([datetime(2018, 1, 4, tzinfo=None), None, 2, None, time(8, 0, 25)])
    output = BytesIO()
    book.save(output)
    # The original December 2017 workbook declares A1 although its table is larger.
    modified = BytesIO()
    import re

    with ZipFile(output) as original, ZipFile(modified, "w") as archive:
        for name in original.namelist():
            data = original.read(name)
            if name.startswith("xl/worksheets/"):
                data = re.sub(rb'<dimension ref="[^"]+"', b'<dimension ref="A1"', data)
            archive.writestr(name, data)
    with Client() as client:
        rows = list(
            client.np3_108.demand_response_history.read(
                zipped("nested.zip", zipped("report.xlsx", modified.getvalue()))
            )
        )
    assert len(rows) == 3
    assert rows[0].houston == Decimal(626)


def test_missing_optional_dependency(monkeypatch):
    import sys

    monkeypatch.setitem(sys.modules, "openpyxl", None)
    with Client() as client, pytest.raises(ImportError, match=r"tinyercot\[files\]"):
        list(client.np1_346_er.outages_history.read(b""))
