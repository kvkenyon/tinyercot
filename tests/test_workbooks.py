# XLSX timestamps are deliberately timezone-naive, as published.
# ruff: noqa: DTZ001
import json
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


@pytest.mark.parametrize(
    "sample",
    json.loads((INPUTS / "price-workbooks-evidence.json").read_text()),
    ids=lambda s: s["fixture"],
)
def test_price_adder_workbook_formats(sample):
    product, method = sample["endpoint"].split("/")
    with Client() as client:
        reader = getattr(
            getattr(client, product.replace("-", "_")), method + "_history"
        )
        rows = list(
            reader.read(
                zipped(sample["file"], (INPUTS / sample["fixture"]).read_bytes())
            )
        )
    assert Counter(r.sourceSheet for r in rows) == {
        s: min(n, 3) for s, n in sample["sheet_rows"].items() if n
    }
    for sheet, expected in sample["first_rows"].items():
        assert (
            next(r for r in rows if r.sourceSheet == sheet).model_dump(mode="json")
            == expected
        )


def test_price_adder_history_keeps_legacy_components():
    with Client() as client:
        old = next(
            client.np6_792_er.price_adders_history.read(
                zipped(
                    "old.xlsx",
                    (INPUTS / "np6-792-er-history-samples.xlsx").read_bytes(),
                )
            )
        )
        current = next(
            client.np6_792_er.price_adders_history.read(
                zipped(
                    "new.xlsx",
                    (INPUTS / "np6-792-er-history-current.xlsx").read_bytes(),
                )
            )
        )
        interval = next(
            client.np6_793_er.price_adders_history.read(
                zipped(
                    "interval.xlsx",
                    (INPUTS / "np6-793-er-history-samples.xlsx").read_bytes(),
                )
            )
        )
    assert old.batchId == 5061293
    assert old.RTORPA == Decimal(0)
    assert old.RTRDPA is None
    assert current.RTORPA is None
    assert current.RTRDPA == Decimal(0)
    assert current.RTDLL is None
    assert interval.deliveryDate == date(2017, 1, 1)
    assert interval.RTRSVPOR == Decimal("0.31")


@pytest.mark.parametrize(
    "sample",
    json.loads((INPUTS / "capacity-workbooks-evidence.json").read_text()),
    ids=lambda s: s["fixture"],
)
def test_capacity_clearing_workbook_formats(sample):
    product, method = sample["endpoint"].split("/")
    with Client() as client:
        reader = getattr(
            getattr(client, product.replace("-", "_")), method + "_history"
        )
        rows = list(
            reader.read(
                zipped(sample["file"], (INPUTS / sample["fixture"]).read_bytes())
            )
        )
    assert Counter(r.sourceSheet for r in rows) == {
        s: min(n, 3) for s, n in sample["sheet_rows"].items() if n
    }
    for sheet, expected in sample["first_rows"].items():
        assert (
            next(r for r in rows if r.sourceSheet == sheet).model_dump(mode="json")
            == expected
        )


def test_capacity_workbooks_preserve_capped_and_legacy_prices():
    with Client() as client:
        old = next(
            client.np6_795_er.clearing_prices_history.read(
                zipped(
                    "old.xlsx",
                    (INPUTS / "np6-795-er-history-samples.xlsx").read_bytes(),
                )
            )
        )
        current = next(
            client.np6_795_er.clearing_prices_history.read(
                zipped(
                    "current.xlsx",
                    (INPUTS / "np6-795-er-history-current.xlsx").read_bytes(),
                )
            )
        )
        capacity = next(
            client.np6_794_er.capability_history.read(
                zipped(
                    "capacity.xlsx",
                    (INPUTS / "np6-794-er-history-samples.xlsx").read_bytes(),
                )
            )
        )
    assert old.MCPC == Decimal("0.53")
    assert old.cappedMCPC is None
    assert current.MCPC is None
    assert current.cappedMCPC == Decimal("0.06")
    assert current.uncappedMCPC == Decimal("0.06")
    assert current.ASType == "ECRS"
    assert capacity.CapREGUPTotal == Decimal("17673.1866")
    assert capacity.CapREGUP_RRS_ECRS_NSPINTotal == Decimal("39745.3392")


@pytest.mark.parametrize(
    "sample",
    json.loads((INPUTS / "fuel-paths-evidence.json").read_text()),
    ids=lambda s: s["fixture"],
)
def test_fuel_and_path_archive_formats(sample):
    product, method = sample["endpoint"].split("/")
    with Client() as client:
        reader = getattr(
            getattr(client, product.replace("-", "_")), method + "_history"
        )
        rows = list(
            reader.read(
                zipped(sample["file"], (INPUTS / sample["fixture"]).read_bytes())
            )
        )
    assert len(rows) == 3
    assert rows[0].model_dump(mode="json") == sample["first_row"]


def test_path_adders_preserve_dates_and_signed_coefficients():
    with Client() as client:
        row = next(
            client.np7_535_sg.path_adders_history.read(
                zipped(
                    "MAY2026.CSV",
                    (INPUTS / "np7-535-sg-history-samples.csv").read_bytes(),
                )
            )
        )
    assert row.targetDate == date(2026, 4, 1)
    assert row.startDate == date(2026, 5, 1)
    assert row.source == "HHOLLW4_WND1"
    assert row.sink == "CHISMGRD_RN"
    assert row.timeOfUse == "Off-peak"
    assert row.ACI99 == Decimal("-2.9138")
    assert row.ACP == Decimal("-1.0881")


@pytest.mark.parametrize(
    "year, count, system_lambda, capacity",
    [(2019, 3, "13.8376", "3583.92"), (2023, 4, "-2.6458", "4125.85")],
)
def test_price_adder_workbooks_preserve_intermediate_capacity_fields(
    year, count, system_lambda, capacity
):
    with Client() as client:
        rows = list(
            client.np6_792_er.price_adders_history.read(
                zipped(
                    "prices.xlsx",
                    (INPUTS / f"np6-792-er-history-{year}.xlsx").read_bytes(),
                )
            )
        )
    assert len(rows) == count
    assert rows[0].SCEDTimestamp == datetime(year, 1, 1, 0, 0, 20)
    assert rows[0].systemLambda == Decimal(system_lambda)
    assert rows[0].RTCST30HSL == Decimal(capacity)
    assert rows[0].RTRUCCST30HSL == Decimal(0)
    assert rows[0].RTRDPA is None
    if year == 2019:
        assert all(row.RTNCLRNSCAP is None for row in rows)
    else:
        assert rows[-1].SCEDTimestamp == datetime(2023, 1, 4, 0, 5, 15)
        assert rows[-1].RTNCLRNSCAP == Decimal(30)
