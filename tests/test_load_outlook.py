from decimal import Decimal
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import httpx
import pytest

from tinyercot import Client
from tinyercot._load import INDEX_URL

INPUT = (
    Path(__file__).resolve().parents[1] / "tools/inputs/history/legacy-hourly-load.zip"
)


def sample(name):
    with ZipFile(INPUT) as archive:
        return archive.read(name)


def rows(name):
    with Client() as client:
        return list(client.hourly_load.read_outlook(sample(name), filename=name))


@pytest.mark.parametrize(
    "name,count",
    [
        ("97frc714.zip", 468),
        ("ferc714.zip", 957),
        ("1999ferc714.zip", 330),
        ("2000ferc714.zip", 330),
        ("erceei97.xls", 2),
    ],
)
def test_original_outlook_tables(name, count):
    assert len(rows(name)) == count


def test_monthly_status_units_and_unlabelled_values():
    coa = [r for r in rows("97frc714.zip") if r.entity == "COA"]
    actual = [
        r
        for r in coa
        if r.month and r.measure == "peak_demand" and r.status == "actual"
    ]
    assert [r.value for r in actual] == [
        1321,
        1347,
        1219,
        1427,
        1678,
        1815,
        1815,
        1803,
        1614,
        1428,
        1203,
        1383,
    ]
    assert [r.periodLabel for r in actual] == [f"1996-{m:02}" for m in range(1, 13)]
    assert all(r.unit == "MW" and r.reportingYear == 1997 for r in actual)
    for status, year, first in [
        ("reporting_year", 1997, 1363),
        ("next_year", 1998, 1430),
    ]:
        row = next(
            r
            for r in coa
            if r.status == status and r.month == 1 and r.measure == "peak_demand"
        )
        assert (row.year, row.value) == (year, first)
    unknown = [r for r in coa if r.measure == "unlabelled"]
    assert [r.value for r in unknown] == [
        1706,
        1775,
        1847,
        1917,
        1975,
        2044,
        2100,
        2172,
        2233,
        2293,
        2357,
    ]
    assert all(r.unit is None and r.status == "unspecified" for r in unknown)


def test_word95_forecasts_and_winter_century_boundary():
    tnp = [r for r in rows("97frc714.zip") if r.entity == "TNP"]
    assert len(tnp) == 33
    assert all(r.reportingYear is None and r.sourceMember == "TNPFORE.96" for r in tnp)
    winter = next(r for r in tnp if r.periodLabel == "1999/00")
    assert (winter.year, winter.endYear, winter.season, winter.value) == (
        1999,
        2000,
        "winter",
        687,
    )
    energy = next(r for r in tnp if r.year == 1996 and r.measure == "net_energy")
    assert (energy.status, energy.value, energy.unit) == ("actual", 3890, "GWh")


def test_missing_actuals_remain_distinct_from_zero():
    actual = [
        r for r in rows("97frc714.zip") if r.entity == "PUB" and r.status == "actual"
    ]
    assert {r.season: r.value for r in actual} == {
        "summer": None,
        "winter": None,
        None: Decimal(0),
    }


def test_workbook_units_and_control_area_labels():
    outlook = rows("ferc714.zip")
    energy = next(
        r
        for r in outlook
        if r.entity == "AENX" and r.year == 1999 and r.measure == "energy"
    )
    assert (energy.value, energy.unit, energy.sourceSheet) == (
        9399000,
        "MWh",
        "ANNUAL ENERGY PROJECTION MWH",
    )
    assert {r.controlArea for r in outlook if r.entity == "TXLA"} == {"TEUT"}
    assert {r.controlArea for r in outlook if r.entity == "SESC"} == {"TUET & LCRA"}
    assert all(r.endYear is None and r.status == "projected" for r in outlook)


def test_text_matrix_preserves_source_entity_and_unknown_units():
    old = rows("1999ferc714.zip")
    total = next(
        r
        for r in old
        if r.entity == "ERCOT Total" and r.year == 2000 and r.measure == "energy"
    )
    assert total.value == 274902196
    newer = rows("2000ferc714.zip")
    summer = next(
        r
        for r in newer
        if r.entity == "ERCOTL" and r.year == 2001 and r.season == "summer"
    )
    assert summer.value == 56759
    assert all(r.unit is None for r in old + newer)


def test_composite_actual_summaries():
    peak, energy = rows("erceei97.xls")
    assert (peak.year, peak.value, peak.unit) == (1997, 50365, "MW")
    assert (energy.value, energy.unit) == (Decimal("249610.864"), "GWh")
    assert peak.status == energy.status == "actual"


def test_anonymous_discovery_filters_target_year_not_index_year():
    seen = []

    def handler(request):
        assert "authorization" not in request.headers
        seen.append(str(request.url))
        if str(request.url) == INDEX_URL:
            return httpx.Response(
                200,
                text="""
                <a href="/files/docs/ferc714.zip">1998 ERCOT Hourly Load Data</a>
                <a href="/files/docs/Native_Load_2026.zip">2026 ERCOT Hourly Load Data</a>
            """,
            )
        assert request.url.path == "/files/docs/ferc714.zip"
        return httpx.Response(200, content=sample("ferc714.zip"))

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as http,
        Client(client=http) as client,
    ):
        result = list(client.hourly_load.outlook(year_from=2009, year_to=2009))
    assert len(result) == 87 and all(r.year == 2009 for r in result)
    assert len(seen) == 2


def test_invalid_word_text_bounds_report_source_member():
    with ZipFile(BytesIO(sample("97frc714.zip"))) as archive:
        data = bytearray(archive.read("TNPFORE.96"))
    # The source WordDocument stream begins in the first sector after the header.
    data[512 + 24 : 512 + 32] = b"\xff" * 8
    with (
        Client() as client,
        pytest.raises(ValueError, match="TNPFORE.96: Invalid Word outlook text range"),
    ):
        list(client.hourly_load.read_outlook(bytes(data), filename="TNPFORE.96"))
