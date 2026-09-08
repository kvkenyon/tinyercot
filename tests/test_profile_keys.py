from collections import Counter
from datetime import date
from decimal import Decimal
from pathlib import Path
from zipfile import ZipFile

import httpx
import pytest

from tinyercot import Client, ProfileKey, ProfileSite, ProfileUnitMapping
from tinyercot._profiles import INDEX_URL

INPUTS = Path(__file__).resolve().parents[1] / "tools/inputs"
FIXTURE = INPUTS / "history/generation-profile-keys.zip"
SOLAR21 = "ERCOT_SolarPVProfiles_1980-2020_Key-public.xlsx"
SOLAR22 = "ERCOT-SolarPVProfiles-1980-2021-Key-public.xlsx"
WIND21 = "ERCOT_WindProfiles_1980-2020_Key-public.xlsx"
WIND22 = "ERCOT-WindProfiles-1980-2021-Key-public.xlsx"


def sample(name):
    with ZipFile(FIXTURE) as archive:
        return archive.read(name)


def read(name):
    with Client() as client:
        return client.generation_profiles.read_key(sample(name), filename=name)


@pytest.mark.parametrize(
    "name,sites,units,summaries,notes",
    [
        (SOLAR21, 420, 0, 22, 8),
        (SOLAR22, 313, 0, 10, 0),
        (WIND21, 303, 227, 0, 4),
        (WIND22, 213, 352, 0, 0),
    ],
)
def test_complete_original_key_counts(name, sites, units, summaries, notes):
    key = read(name)
    assert isinstance(key, ProfileKey) and key.sourceMember == name
    assert len(key.sites) == sites and all(
        isinstance(s, ProfileSite) for s in key.sites
    )
    assert len(key.units) == units and all(
        isinstance(u, ProfileUnitMapping) for u in key.units
    )
    assert len(key.summaries) == summaries and len(key.notes) == notes
    assert len({(s.sourceSheet, s.sourceRow) for s in key.sites}) == sites


def test_solar_equipment_sections_and_modeling_notes():
    key = read(SOLAR21)
    assert key.revisionDate == date(2021, 6, 25)
    assert key.title.endswith(
        "2021 V2- CONFIDENTIAL"
    )  # Literal heading in the public file.
    assert key.authors == "A. Gothandaraman, M. Shakarjian"
    solar = [s for s in key.sites if s.kind == "solar-operational-planned"]
    assert Counter(s.sourceSection for s in solar) == {1: 26, 2: 27}
    first = solar[0]
    assert first.unitCode == "ACACIA_UNIT_1" and first.capacityMW == 10
    assert first.latitude == Decimal("29.592953") and first.longitude == Decimal(
        "-104.334441"
    )
    assert first.trackingSystem == "SINGLE" and first.trackingType == "N-S"
    assert first.tilt == 0 and first.dcAcRatio == Decimal("1.2")
    assert first.inverters == "SMA SC500CP, SMA SC800CP"
    assert first.modules == "SunEdison MEMC-P285AMC"
    assert first.modeledInYear == 2020 and first.modeledInYearFlag == "YES"
    assert {s.tilt for s in solar} == {Decimal(0), "Lat", "NA"}
    assert all(s.developmentStatus is None for s in solar)
    assert any(
        n.sourceCell == "A68" and "omitted this year" in n.text for n in key.notes
    )


def test_distributed_solar_sites_and_published_totals_are_separate():
    key = read(SOLAR21)
    metro = [s for s in key.sites if s.kind == "solar-metro"]
    rural = [s for s in key.sites if s.kind == "solar-rural"]
    assert len(metro) == 12 and len(rural) == 216
    assert metro[0].siteId == 1022 and metro[0].metroArea == "Austin"
    assert metro[0].developmentIntensity == "Low" and metro[0].capacityMW == 374
    assert rural[0].siteId == 3001 and rural[0].county == "Anderson"
    assert rural[0].cdrZone == "North" and rural[0].capacityMW == Decimal("30.13")
    assert Counter(s.cdrZone for s in rural) == {
        "Coastal": 10,
        "Houston": 6,
        "North": 59,
        "Panhandle": 33,
        "South": 53,
        "West": 55,
    }
    # Retain the printed overview and precise cached total; do not recompute them.
    assert key.summaries[0].profileCount == 313
    assert key.summaries[-1].capacityMW == Decimal("5975.9800000000005")
    assert key.summaries[-1].profileCount == 216


def test_version_specific_precision_and_missing_fields():
    wind = read(WIND22)
    first = wind.sites[0]
    assert first.siteId == 1 and first.commonName == "Anacacho"
    assert first.capacityMW == Decimal(
        "99.825"
    )  # Hourly workbook separately prints 99.83.
    assert first.developmentStatus == "Operational" and first.cdrZone == "South"
    assert first.newForYear == 2022 and first.newForYearFlag == "NO"
    assert first.markedAsQueued is None and first.latitude is None
    solar = read(SOLAR22)
    assert Counter(
        s.sourceSection for s in solar.sites if s.kind == "solar-operational-planned"
    ) == {1: 40, 2: 124}
    assert solar.summaries[0].profileCount == 462
    assert (
        solar.summaries[-1].label == "Total  "
        and solar.summaries[-1].totalProfileCount == 298
    )


def test_queued_shading_and_many_to_one_wind_units():
    key = read(WIND21)
    assert [s.siteId for s in key.sites if s.markedAsQueued] == [4000, 4001, 4004, 4007]
    assert len([u for u in key.units if u.markedAsQueued]) == 12
    assert key.sites[0].markedAsQueued is False
    assert all(
        s.markedAsQueued is None for s in key.sites if s.kind == "wind-hypothetical"
    )
    units = [u for u in key.units if u.siteId == 3]
    assert [u.unitCode for u in units] == ["BAFFIN_UNIT1", "BAFFIN_UNIT2"]
    assert key.units[0].newForYear == 2020  # Header says 2020 even in this 2021 key.
    assert key.sites[0].newForYear == 2021
    first = next(s for s in key.sites if s.kind == "wind-hypothetical")
    assert first.siteId == 440 and first.longitude == Decimal("-102.21398")
    assert first.latitude == Decimal("32.14663") and first.capacityMW == 121
    assert first.distanceToExistingOrQueued == ">= 10 km" and first.iecClass == 3
    assert any(n.sourceCell == "K1" and "IEC class" in n.text for n in key.notes)


def test_matching_key_discovery_and_anonymous_download():
    requested = []

    def handler(request):
        requested.append(str(request.url))
        assert "authorization" not in request.headers
        if str(request.url) == INDEX_URL:
            return httpx.Response(
                200, content=(INPUTS / "public-profile-index.html").read_bytes()
            )
        assert str(request.url).endswith(WIND22)
        return httpx.Response(200, content=sample(WIND22))

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as http,
        Client(client=http) as client,
    ):
        profiles = client.generation_profiles
        assert len(profiles.keys()) == 4
        selected = profiles.keys(study_year=2022, fuel="wind")
        assert len(selected) == 1 and selected[0].yearTo == 2021
        archive = profiles.archives(study_year=2022, fuel="wind")[0]
        assert profiles.key(archive).sites[0].capacityMW == Decimal("99.825")
        before = len(requested)
        assert profiles.key(selected[0]).sites[0].siteId == 1
        assert (
            len(requested) == before + 1
        )  # Direct key does not fetch the index again.
