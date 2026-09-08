from collections import Counter
from datetime import date
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import httpx
import openpyxl
import pytest

from tinyercot import Client, MoraPercentile

FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "tools/inputs/public-tables/mora-percentiles.zip"
)


@pytest.fixture(scope="module")
def percentiles():
    with Client() as client:
        return list(client.resource_outlook.read_percentiles(FIXTURE.read_bytes()))


def test_all_original_fixture_values_quantiles_and_hour_labels(percentiles):
    actual = iter(percentiles)
    with ZipFile(FIXTURE) as archive:
        for member in archive.namelist():
            book = openpyxl.load_workbook(
                BytesIO(archive.read(member)), read_only=True, data_only=True
            )
            try:
                label = next(
                    v
                    for cells in book["Cover"].values
                    for v in cells
                    if isinstance(v, str) and v.startswith("Reporting Month:")
                )
                sheet = book["PRRM Percentile Results"]
                sheet.reset_dimensions()
                source = list(sheet.values)
                notes = [
                    v
                    for cells in source
                    for v in cells
                    if isinstance(v, str) and v.startswith("* ")
                ]
                heading = None
                columns = []
                for cells in source:
                    q = cells[1] if len(cells) > 1 else None
                    if (
                        isinstance(q, (int, float))
                        or isinstance(q, str)
                        and q.endswith("%")
                    ):
                        for col, hour in columns:
                            row = next(actual)
                            value = cells[col] if col < len(cells) else None
                            assert row.value == (
                                None if value is None else Decimal(str(value))
                            )
                            assert row.percentile == Decimal(
                                str(q).removesuffix("%")
                            ) / (100 if isinstance(q, str) else 1)
                            assert row.sourcePercentile == str(q)
                            assert row.hour == (
                                int(hour) if isinstance(hour, (int, float)) else None
                            )
                            assert row.sourcePeriodLabel == str(hour)
                            assert (
                                row.sourceMetric == heading
                                and row.sourceReportLabel == label
                            )
                            assert (
                                row.sourceMember == member
                                and row.sourceSheet == sheet.title
                            )
                            assert row.sourceNotes == notes
                    elif q == "Percentiles":
                        columns = [
                            (i, v)
                            for i, v in enumerate(cells)
                            if i >= 2 and v is not None
                        ]
                    else:
                        title = next((v for v in cells[:2] if isinstance(v, str)), None)
                        if title:
                            heading = title
            finally:
                book.close()
    assert next(actual, None) is None
    assert (
        MoraPercentile.model_validate_json(percentiles[0].model_dump_json())
        == percentiles[0]
    )


def test_earliest_hours_and_missing_metrics_are_not_filled(percentiles):
    early = [r for r in percentiles if r.sourceMember == "MORA_December2023.xlsx"]
    assert len(early) == 308
    assert {r.metric for r in early} == {
        "solar_generation",
        "wind_generation",
        "thermal_outages",
    }
    assert {r.hour for r in early if r.metric == "solar_generation"} == set(
        range(8, 19)
    )
    assert {r.hour for r in early if r.metric == "wind_generation"} == set(range(7, 23))
    outages = [r for r in early if r.metric == "thermal_outages"]
    assert len(outages) == 11
    assert all(r.hour is None and r.sourceUnit is None for r in outages)
    assert all(r.reportMonth == date(2023, 12, 1) for r in early)


def test_weather_outage_regimes_and_percent_strings_remain_distinct(percentiles):
    winter = [
        r
        for r in percentiles
        if r.sourceMember == "MORA_February2026.xlsx" and r.hour is None
    ]
    assert Counter(r.metric for r in winter) == {
        "non_extreme_weather_outages": 11,
        "extreme_weather_outages": 11,
    }
    extreme = next(
        r
        for r in winter
        if r.metric == "extreme_weather_outages" and r.percentile == Decimal("0.5")
    )
    assert extreme.sourcePercentile == "50%"
    assert extreme.value == Decimal("282.8754129683155")
    assert extreme.sourceNotes and extreme.sourceUnit == "MW"


def test_revisions_and_changed_demand_definitions_are_retained(percentiles):
    early = [r for r in percentiles if r.reportMonth == date(2023, 12, 1)]
    assert len(early) == 616
    assert {r.sourceMember for r in early} == {
        "MORA_December2023.xlsx",
        "MORA_December2023_v2.xlsx",
    }
    revised = {
        r.sourceReportLabel
        for r in percentiles
        if "Revised" in r.sourceReportLabel or "REVISED" in r.sourceReportLabel
    }
    assert revised == {
        "Reporting Month: August 2026, Revised",
        "Reporting Month: March 2025 REVISED",
    }
    assert len({r.sourceMetric for r in percentiles if r.metric == "gross_demand"}) == 2


def test_discovery_follows_actual_year_links_and_ignores_pdf_duplicates():
    current = "https://www.ercot.com/files/docs/2026/09/03/MORA_November2026.xlsx"
    older = "https://www.ercot.com/files/docs/2023/10/02/MORA_December2023.xlsx"
    requested = []

    def handler(request):
        requested.append(str(request.url))
        assert "authorization" not in request.headers
        if str(request.url) in (current, older):
            with ZipFile(FIXTURE) as z:
                return httpx.Response(
                    200, content=z.read(str(request.url).rsplit("/", 1)[-1])
                )
        if request.url.path == "/gridinfo/resource":
            return httpx.Response(
                200,
                text=f'<a href="/gridinfo/resource/2023">2023</a><a href="{current}">Monthly Outlook for Resource Adequacy (MORA) November 2026</a><a href="{current.replace("xlsx", "pdf")}">Monthly Outlook for Resource Adequacy (MORA) November 2026</a>',
            )
        assert request.url.path == "/gridinfo/resource/2023"
        return httpx.Response(
            200,
            text=f'<a href="{older}">Monthly Outlook for Resource Adequacy (MORA) December 2023</a>',
        )

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as http,
        Client(client=http) as client,
    ):
        rows = list(
            client.resource_outlook.percentiles(
                where=lambda r: r.reportMonth == date(2023, 12, 1)
            )
        )
    assert len(rows) == 308
    assert requested == [
        "https://www.ercot.com/gridinfo/resource",
        "https://www.ercot.com/gridinfo/resource/2023",
        older,
        current,
    ]


def test_saved_file_month_comes_from_cover_with_typed_filter():
    with ZipFile(FIXTURE) as archive:
        data = archive.read("MORA_August2026.xlsx")
    with Client() as client:
        rows = list(
            client.resource_outlook.read_percentiles(
                data,
                filename="old-2023.xlsx",
                where=lambda r: (
                    r.metric == "gross_demand" and r.percentile == Decimal("0.5")
                ),
            )
        )
    assert len(rows) == 24
    assert all(
        r.reportMonth == date(2026, 8, 1) and r.sourceMember == "old-2023.xlsx"
        for r in rows
    )


def test_unknown_metric_cannot_reuse_previous_table_identity():
    with ZipFile(FIXTURE) as archive:
        book = openpyxl.load_workbook(BytesIO(archive.read("MORA_November2026.xlsx")))
    book["PRRM Percentile Results"]["A18"] = "New generation quantity, MW"
    data = BytesIO()
    book.save(data)
    book.close()
    with (
        Client() as client,
        pytest.raises(ValueError, match="Unknown percentile metric"),
    ):
        list(client.resource_outlook.read_percentiles(data.getvalue()))
