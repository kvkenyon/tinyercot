from collections import Counter
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import httpx
import openpyxl
import pytest
import xlrd

from tinyercot import CdrSummary, Client, PublicFile

FIXTURE = Path(__file__).resolve().parents[1] / "tools/inputs/cdr/summaries.zip"


@pytest.fixture(scope="module")
def reports():
    with Client() as client:
        return list(client.cdr.read_summaries(FIXTURE.read_bytes()))


@pytest.fixture(scope="module")
def originals():
    result = {}
    with ZipFile(FIXTURE) as archive:
        for name in archive.namelist():
            data = archive.read(name)
            if name.endswith(".xls"):
                with xlrd.open_workbook(file_contents=data) as book:
                    for s in book.sheets():
                        result[name, s.name] = [
                            [
                                xlrd.error_text_from_code[int(c.value)]
                                if c.ctype == 5
                                else c.value
                                for c in s.row(r)
                            ]
                            for r in range(s.nrows)
                        ]
            else:
                book = openpyxl.load_workbook(
                    BytesIO(data), read_only=True, data_only=True
                )
                try:
                    for s in book:
                        s.reset_dimensions()
                        result[name, s.title] = list(s.values)
                finally:
                    book.close()
    return result


def test_every_returned_value_and_note_matches_original_cells(reports, originals):
    assert len(reports) == 9
    for report in reports:
        keys = set()
        for value in report.values:
            key = value.sourceSheet, value.sourceRow, value.sourceColumn
            assert key not in keys
            keys.add(key)
            source_row = originals[report.sourceMember, value.sourceSheet][
                value.sourceRow - 1
            ]
            source = (
                source_row[value.sourceColumn - 1]
                if value.sourceColumn <= len(source_row)
                else None
            )
            if value.sourceError:
                assert value.sourceError == source and value.value is None
            else:
                assert value.value == (
                    None if source in (None, "") else Decimal(str(source))
                )
        for note in report.notes:
            assert (
                note.text
                == originals[report.sourceMember, note.sourceSheet][note.sourceRow - 1][
                    note.sourceColumn - 1
                ]
            )


def find(reports, fragment):
    return next(r for r in reports if fragment in r.sourceMember)


def test_all_2000_lse_control_area_forecasts(reports, originals):
    report = find(reports, "02082000")
    rows = originals[report.sourceMember, "Summer Summary"]
    actual = {(v.sourceRow, v.sourceColumn): v for v in report.values}
    expected = set()
    for n, row in enumerate(rows, 1):
        if n == 1 or row[2].endswith("Year"):
            continue
        for c in range(3, 9):
            expected.add((n, c + 1))
            v = actual[n, c + 1]
            assert v.loadServingEntity == row[0] and v.controlArea == row[1]
            assert v.reportingGroup is None and v.period == str(1997 + c)
            assert v.season == "summer"
            assert v.unit == ("fraction" if "Margin" in row[2] else "MW")
    assert set(actual) == expected


def test_tdsp_group_and_multiple_reserve_bases(reports):
    report = find(reports, "082001")
    values = {(v.sourceSheet, v.sourceRow, v.sourceColumn): v for v in report.values}
    aep = values["Summer Summary", 6, 3]
    assert aep.reportingGroup == "AEP" and aep.period == "2002"
    assert values["Summer Summary", 11, 3].reportingGroup == "AUSTIN ENERGY"
    first = values["Summer Summary", 189, 3]
    second = values["Summer Summary", 193, 3]
    assert first.metric == second.metric and first.reserveBasis != second.reserveBasis
    assert first.unit == second.unit == "fraction"
    assert first.value == Decimal("0.32417092161286487")
    assert (
        values["Summer Summary", 203, 3].reportingGroup
        == "MARGINS (based on System Planning forecast)"
    )


def test_short_winter_spans_source_errors_and_signed_adjustments(reports):
    early = (
        find(reports, "may2013")
        if any("may2013" in r.sourceMember for r in reports)
        else find(reports, "report_2013")
    )
    winter = next(v for v in early.values if v.sourceSheet == "WinterSummary")
    assert winter.period == "2014/15"
    errors = [v for r in reports for v in r.values if v.sourceError]
    assert errors and all(v.sourceError == "#REF!" and v.value is None for v in errors)
    positive = next(
        v for v in early.values if v.sourceSheet == "SummerSummary" and v.sourceRow == 7
    )
    negative = next(
        v
        for v in find(reports, "May2024").values
        if v.sourceSheet == "SummerSummary"
        and v.sourceRow == 9
        and v.kind == "forecast"
    )
    assert positive.value > 0 and negative.value < 0


def test_installed_ratings_retain_future_cumulative_basis(reports):
    report = find(reports, "May2024")
    installed = [v for v in report.values if v.kind == "installed_capacity"]
    assert len(installed) == 46
    assert all(v.period is None and "by 2029" in v.sourceColumnLabel for v in installed)
    current = next(
        v for v in installed if v.sourceSheet == "SummerSummary" and v.sourceRow == 19
    )
    forecast = next(
        v
        for v in report.values
        if v.sourceSheet == "SummerSummary"
        and v.sourceRow == 19
        and v.kind == "forecast"
    )
    assert current.value == Decimal("74288.58000000002")
    assert current.value != forecast.value and forecast.period == "2025"


def test_modern_peak_hours_difference_columns_and_all_seasons(reports):
    report = find(reports, "May2025")
    assert Counter(v.season for v in report.values) == dict.fromkeys(
        ["summer", "winter", "spring", "fall"], 600
    )
    row = {v.sourceColumn: v for v in report.values if v.sourceRow == 8}
    assert row[4].hourBasis == "peak_load" and row[4].hour == 17
    assert row[5].hourBasis == "peak_net_load" and row[5].hour == 21
    assert row[6].hourBasis == "difference" and row[6].hour is None
    assert row[4].period == row[5].period == row[6].period == "2026"
    assert row[19].season == "winter" and row[19].period == "2026/2027"
    assert row[34].season == "spring" and row[49].season == "fall"
    assert CdrSummary.model_validate_json(report.model_dump_json()) == report
    old = find(reports, "December2024")
    assert {v.period for v in old.values if v.season == "winter"} == {
        "2025/26",
        "2026/27",
        "2027/28",
        "2028/29",
        "2029/30",
    }


def test_anonymous_discovery_and_original_file_identity(reports):
    report = find(reports, "May2025")
    url = "https://www.ercot.com/files/docs/" + report.sourceMember
    title = "Capacity Demand and Reserves Report May 2025 Revised"
    with ZipFile(FIXTURE) as archive:
        data = archive.read(report.sourceMember)

    def handler(request):
        assert "authorization" not in request.headers
        return (
            httpx.Response(200, content=data)
            if str(request.url) == url
            else httpx.Response(200, text=f'<a href="{url}">{title}</a>')
        )

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as http,
        Client(client=http) as client,
    ):
        actual = next(client.cdr.summaries(where=lambda d: bool(d.values)))
        assert actual.sourceFile == PublicFile(title=title, url=url)
        assert actual.sourceMember == url.rsplit("/", 1)[-1]
        assert actual.values == report.values
        assert not list(client.cdr.read_summaries(data, where=lambda d: False))
