import csv
from collections import Counter
from datetime import date
from decimal import Decimal
from io import BytesIO, StringIO
from pathlib import Path
from zipfile import ZipFile

import httpx
import openpyxl
import pytest
import xlrd

from tinyercot import Client, LoadShedShare, PublicFile, TransmissionLossCoefficient

INPUTS = Path(__file__).resolve().parents[1] / "tools/inputs"
MANIFEST = list(
    csv.DictReader(
        StringIO((INPUTS / "public-seasonal-tables-sources.csv").read_text())
    )
)


@pytest.fixture(scope="module")
def coefficients():
    with Client() as client:
        return list(
            client.transmission_loss_coefficients.read(
                (
                    INPUTS / "public-tables/transmission-loss-coefficients.zip"
                ).read_bytes()
            )
        )


def test_every_original_coefficient_and_input_cell(coefficients):
    with ZipFile(INPUTS / "public-tables/transmission-loss-coefficients.zip") as z:
        for filename in z.namelist():
            data = z.read(filename)
            if filename.endswith(".xls"):
                with xlrd.open_workbook(file_contents=data) as book:
                    sources = {
                        s.name: [s.row_values(i) for i in range(s.nrows)]
                        for s in book.sheets()
                    }
            else:
                book = openpyxl.load_workbook(
                    BytesIO(data), read_only=True, data_only=True
                )
                sources = {s.title: list(s.values) for s in book}
                book.close()
            expected = {}
            for sheet, rows in sources.items():
                if len(rows) < 49:
                    continue
                for row in (43, 45, 47, 49):
                    for column, header in enumerate(rows[41]):
                        if header != "SSC":
                            continue
                        area = rows[40][column].split()[0]
                        basis = next(
                            i
                            for i, name in enumerate(rows[28])
                            if isinstance(name, str) and name.startswith(area + " ")
                        )
                        expected[(sheet, row, area)] = (
                            rows[row - 1][column : column + 2]
                            + rows[row - 13][basis : basis + 4]
                        )
            actual = [r for r in coefficients if r.sourceMember == filename]
            assert len(actual) == len(expected)
            for r in actual:
                values = expected.pop((r.sourceSheet, r.sourceRow, r.area))
                assert [
                    r.slopePercentPerMW,
                    r.interceptPercent,
                    r.onPeakLoadMW,
                    r.offPeakLoadMW,
                    r.onPeakLossFactor,
                    r.offPeakLossFactor,
                ] == [None if v in (None, "") else Decimal(str(v)) for v in values]
                rows = sources[r.sourceSheet]
                assert r.sourceInputRow == r.sourceRow - 12
                assert r.sourceHeading == rows[0][0]
                assert r.sourceFile is None
            assert not expected
    assert len(coefficients) == 948
    assert {r.year for r in coefficients} == set(range(2001, 2027))


def test_original_periods_missing_values_and_shifted_area_columns(coefficients):
    lookup = {(r.year, r.season, r.area): r for r in coefficients}
    shifted = lookup[2002, "spring", "COCS"]
    assert shifted.onPeakLoadMW == Decimal("101.9")
    assert shifted.offPeakLoadMW == Decimal("86.5")
    assert shifted.slopePercentPerMW == Decimal("0.0003661768367650714")
    assert shifted.interceptPercent == Decimal("0.060725796019913715")
    assert shifted.asOf == date(2002, 2, 21)
    assert "Version 3" in shifted.sourceHeading
    assert {r.area for r in coefficients if r.year == 2002} >= {
        "PUB",
        "Rayburn",
        "TEXLA",
    }
    blank = lookup[2021, "spring", "LPL"]
    assert blank.onPeakLoadMW is None and blank.onPeakLossFactor is None
    assert blank.slopePercentPerMW is None and blank.interceptPercent is None
    assert blank.effectiveFrom == date(2021, 3, 1)
    assert all(
        r.effectiveFrom is None and r.sourceEffectivePeriod is None
        for r in coefficients
        if r.year < 2011
    )
    for year, label in [
        (2020, "12/01/2021 - 02/28/2021"),
        (2026, "12/01/2027 - 02/28/2027"),
    ]:
        winter = lookup[year, "winter", "ERCOT"]
        assert winter.sourceEffectivePeriod == label
        assert winter.effectiveFrom is None and winter.effectiveThrough is None
    assert lookup[2011, "summer", "ERCOT"].effectiveThrough == date(2011, 8, 31)
    assert lookup[2012, "summer", "ERCOT"].effectiveThrough == date(2012, 9, 30)
    assert lookup[2023, "winter", "ERCOT"].effectiveThrough == date(2024, 2, 29)
    assert (
        lookup[2026, "spring", "ERCOT"].sourceArea
        != lookup[2026, "spring", "ERCOT"].sourceInputArea
    )
    assert Counter(r.effectiveFrom is None for r in coefficients) == {
        True: 367,
        False: 581,
    }
    assert (
        TransmissionLossCoefficient.model_validate_json(shifted.model_dump_json())
        == shifted
    )
    assert (
        TransmissionLossCoefficient.model_validate_json(blank.model_dump_json())
        == blank
    )


def test_actual_annual_index_links_and_typed_coefficient_query():
    with ZipFile(INPUTS / "loss-factors/indexes.zip") as z:
        pages = {n.removesuffix(".html"): z.read(n) for n in z.namelist()}
    with ZipFile(INPUTS / "public-tables/transmission-loss-coefficients.zip") as z:
        files = {
            f["url"]: z.read(f["file"]) for f in MANIFEST if f["kind"] == "coefficients"
        }
    requested = []

    def handler(request):
        assert "authorization" not in request.headers
        url = str(request.url)
        requested.append(url)
        return httpx.Response(
            200,
            content=files[url]
            if url in files
            else pages[request.url.path.rsplit("/", 1)[-1]],
        )

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as http,
        Client(client=http) as client,
    ):
        discovered = client.transmission_loss_coefficients.files()
        assert {(f.title, f.url) for f in discovered} == {
            (f["title"], f["url"]) for f in MANIFEST if f["kind"] == "coefficients"
        }
        requested.clear()
        rows = list(
            client.transmission_loss_coefficients.rows(
                where=lambda r: r.year == 2026 and r.area == "ERCOT"
            )
        )
    assert len(rows) == 4
    assert all(
        isinstance(r.sourceFile, PublicFile)
        and r.sourceFile.url.endswith("2026_Transmission_Loss_Factors_Final.xlsx")
        for r in rows
    )
    assert len(requested) == 26 + 26


def test_saved_coefficient_revisions_remain_separate():
    with ZipFile(INPUTS / "public-tables/transmission-loss-coefficients.zip") as z:
        data = z.read("2026_Transmission_Loss_Factors_Final.xlsx")
    bundle = BytesIO()
    with ZipFile(bundle, "w") as z:
        z.writestr("original.xlsx", data)
        z.writestr("revision.xlsx", data)
    with Client() as client:
        rows = list(
            client.transmission_loss_coefficients.read(
                bundle.getvalue(), where=lambda r: r.season == "winter"
            )
        )
    assert len(rows) == 20
    assert {r.sourceMember for r in rows} == {"original.xlsx", "revision.xlsx"}


def test_all_original_operator_shares_and_effective_notes():
    with ZipFile(INPUTS / "public-tables/load-shed.zip") as z, Client() as client:
        for filename in z.namelist():
            data = z.read(filename)
            actual = list(client.load_shed.read(data, filename=filename))
            book = openpyxl.load_workbook(BytesIO(data), read_only=True, data_only=True)
            source = list(book.active.values)
            expected = source[1:22]
            notes = [
                r[0]
                for r in source
                if isinstance(r[0], str) and r[0].startswith(("*", "Note:"))
            ]
            book.close()
            assert len(actual) == 21
            for r, cells in zip(actual, expected, strict=True):
                assert r.transmissionOperator == cells[0]
                assert r.loadSharePercent == Decimal(str(cells[1]))
                assert r.sourceHeader == source[0][1] and r.sourceNotes == notes
                assert r.sourceMember == filename
                assert r.effectiveFrom == (
                    date(2026, 4, 1) if r.season == "summer" else date(2026, 9, 1)
                )
            assert (
                LoadShedShare.model_validate_json(actual[0].model_dump_json())
                == actual[0]
            )


def test_anonymous_load_share_discovery_and_typed_filter():
    with ZipFile(INPUTS / "public-tables/load-shed.zip") as z:
        sources = {
            f["url"]: z.read(f["file"]) for f in MANIFEST if f["kind"] == "loadShares"
        }
    html = "".join(
        f'<a href="{f["url"]}">{f["title"]}</a>'
        for f in MANIFEST
        if f["kind"] == "loadShares"
    )

    def handler(request):
        assert "authorization" not in request.headers
        return (
            httpx.Response(200, content=sources[str(request.url)])
            if str(request.url) in sources
            else httpx.Response(200, text=html)
        )

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as http,
        Client(client=http) as client,
    ):
        rows = list(
            client.load_shed.rows(
                where=lambda r: (
                    r.season == "winter"
                    and r.transmissionOperator.startswith("CenterPoint")
                )
            )
        )
    assert len(rows) == 1 and rows[0].loadSharePercent == Decimal("20.08")
    assert rows[0].effectiveFrom == date(2026, 9, 1)
