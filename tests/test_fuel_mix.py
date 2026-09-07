from datetime import date, time
from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from zipfile import ZipFile

import httpx
import pytest

from tinyercot import Client
from tinyercot._fuel_mix import INDEX_URL

FIXTURE = (
    Path(__file__).resolve().parents[1] / "tools/inputs/history/fuel-mix-originals.zip"
)


@lru_cache
def sample(year):
    with ZipFile(FIXTURE) as archive:
        name = next(n for n in archive.namelist() if str(year) in n)
        return name, archive.read(name)


def rows(client, year):
    name, data = sample(year)
    return client.fuel_mix.read(data, filename=name)


@pytest.mark.parametrize(
    "year,count",
    [
        (2007, 2190),
        (2008, 2227),
        (2010, 2555),
        (2011, 2931),
        (2013, 3285),
        (2016, 3294),
        (2017, 3285),
        (2025, 3650),
        (2026, 2120),
    ],
)
def test_original_daily_counts(year, count):
    with Client() as client:
        assert sum(1 for _ in rows(client, year)) == count


def test_old_combined_label_and_precise_interval_values():
    with Client() as client:
        row = next(
            r
            for r in rows(client, 2007)
            if r.operatingDay == date(2007, 1, 1) and r.fuel == "Coal"
        )
    assert row.totalMWh == Decimal("314608.6399")
    assert row.intervals[0].energyMWh == Decimal("3376.329577")
    assert row.intervals[0].ending == time(0, 15)
    assert row.intervals[-1].ending == time(0)
    assert len(row.intervals) == 96 and row.settlementType is None
    assert row.sourceMember == "IntGenByFuel2007.xls"


def test_monthly_and_annual_totals_keep_original_units_and_labels():
    with Client() as client:
        name, data = sample(2007)
        old = list(client.fuel_mix.read_summaries(data, filename=name))
        name, data = sample(2026)
        current = list(client.fuel_mix.read_summaries(data, filename=name))
    coal = next(r for r in old if r.fuel == "Coal")
    assert (coal.year, coal.month, coal.energy, coal.unit) == (
        2007,
        None,
        Decimal("113912250.23"),
        "MWh",
    )
    biomass = [r for r in current if r.fuel == "Biomass"]
    assert len(biomass) == 13
    assert biomass[0].sourcePeriod == "Jan*" and biomass[0].energy == Decimal(
        "55.105695"
    )
    assert biomass[7].energy is None and biomass[7].month == 8
    assert biomass[-1].energy == Decimal("292.478075") and biomass[-1].unit == "GWh"


def test_unlabelled_monthly_subtotal_is_not_a_fake_daily_row():
    name, data = sample(2008)
    with Client() as client:
        unlabelled = [
            r
            for r in client.fuel_mix.read_summaries(data, filename=name)
            if r.fuel is None
        ]
    assert len(unlabelled) == 1
    assert (unlabelled[0].year, unlabelled[0].month, unlabelled[0].energy) == (
        2008,
        4,
        Decimal("22167854.158047"),
    )


def test_known_malformed_cells_preserve_original_text():
    with Client() as client:
        november = next(r for r in rows(client, 2010) if r.sourceSheet == "Nov10")
        errors = [
            (r, i) for r in rows(client, 2011) for i in r.intervals if i.sourceError
        ]
    invalid = next(i for i in november.intervals if i.sourceError)
    assert invalid.energyMWh is None and invalid.sourceError == "1/0/1900 0:00"
    assert invalid.sourceHeader == "DST1" and invalid.ending is None and invalid.dst
    assert [(r.fuel, i.sourceError, i.energyMWh) for r, i in errors] == [
        ("Sun", "1.00E", None),
        ("Sun", "6.00E", None),
    ]


def test_unlabelled_zero_columns_are_retained_with_source_positions():
    with Client() as client:
        row = next(r for r in rows(client, 2011) if r.sourceSheet == "Aug11")
    unknown = [i for i in row.intervals if not i.sourceHeader]
    assert [i.sourceColumn for i in unknown] == [100, 101, 102, 103]
    assert all(i.energyMWh == 0 and i.ending is None and not i.dst for i in unknown)


def test_dst_blanks_negative_storage_and_settlement_status():
    with Client() as client:
        wanted = {
            (date(2025, 3, 9), "Coal"),
            (date(2025, 11, 2), "Coal"),
            (date(2025, 1, 1), "WSL"),
        }
        selected = {
            (r.operatingDay, r.fuel): r
            for r in rows(client, 2025)
            if (r.operatingDay, r.fuel) in wanted
        }
        july = next(r for r in rows(client, 2026) if r.operatingDay == date(2026, 7, 1))
    spring = selected[(date(2025, 3, 9), "Coal")]
    assert len(spring.intervals) == 96
    assert [i.ending for i in spring.intervals if i.energyMWh is None] == [
        time(2, 15),
        time(2, 30),
        time(2, 45),
        time(3),
    ]
    fall = selected[(date(2025, 11, 2), "Coal")]
    assert len(fall.intervals) == 100
    assert [i.sourceHeader for i in fall.intervals[-4:]] == [
        "01:15 (DST)",
        "01:30 (DST)",
        "01:45 (DST)",
        "02:00 (DST)",
    ]
    assert all(i.dst and i.energyMWh is not None for i in fall.intervals[-4:])
    assert selected[(date(2025, 1, 1), "WSL")].totalMWh < 0
    assert spring.settlementType == "FINAL" and july.settlementType == "INITIAL"


def test_anonymous_index_discovery_and_date_filter():
    requests = []
    name, data = sample(2026)

    def handler(request):
        assert "authorization" not in request.headers
        requests.append(str(request.url))
        if str(request.url) == INDEX_URL:
            return httpx.Response(
                200,
                text=f"""
                <a href="/files/docs/old.zip">Fuel Mix Report: 2007 - 2024</a>
                <a href="/files/docs/{name}">Fuel Mix Report: 2026</a>
                <a href="/files/docs/other.xlsx">Unrelated workbook</a>
            """,
            )
        assert request.url.path.endswith(name)
        return httpx.Response(200, content=data)

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as http,
        Client(client=http) as client,
    ):
        result = list(
            client.fuel_mix.rows(date_from=date(2026, 7, 1), date_to=date(2026, 7, 1))
        )
    assert len(result) == 10 and all(r.operatingDay == date(2026, 7, 1) for r in result)
    assert len(requests) == 2


def test_summary_year_requires_original_filename_for_standalone_modern_file():
    with Client() as client, pytest.raises(ValueError, match="original filename"):
        list(client.fuel_mix.read_summaries(sample(2026)[1]))
