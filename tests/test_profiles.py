import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from zipfile import ZipFile

import httpx
import pytest

from tinyercot import Client, ProfileArchive, ProfileHour
from tinyercot._profiles import INDEX_URL

INPUTS = Path(__file__).resolve().parents[1] / "tools/inputs"
FIXTURE = INPUTS / "history/generation-profiles.zip"
METRO = "ERCOT_SolarPVProfiles_Metro-Distributed_1980-2020_CST.csv"
WIND = "ERCOT-OperationalPlanned-WindProfiles-2020-2021-CST-CDT.xlsx"


def sample(name):
    with ZipFile(FIXTURE) as archive:
        return archive.read(name)


with ZipFile(FIXTURE) as archive:
    MEMBERS = archive.namelist()
COUNTS = {
    item["filename"]: item["sampleHours"]
    for item in json.loads((INPUTS / "public-profile-fixtures.json").read_text())
}


@pytest.mark.parametrize("name", MEMBERS)
def test_captured_profile_formats(name):
    with Client() as client:
        rows = list(client.generation_profiles.read(sample(name), filename=name))
        series = client.generation_profiles.read_series(sample(name))
    assert rows and series and all(isinstance(r, ProfileHour) for r in rows)
    assert len(rows) == COUNTS[name]
    assert all(r.sourceMember == name for r in rows)
    assert all([v.series for v in r.outputs] == series for r in rows)
    assert all(r.timestamp.tzinfo is None for r in rows)
    assert all(isinstance(v.generationMW, Decimal) for r in rows for v in r.outputs)


def test_index_discovery_and_study_selection():
    def handler(request):
        assert str(request.url) == INDEX_URL
        assert "authorization" not in request.headers
        return httpx.Response(
            200, content=(INPUTS / "public-profile-index.html").read_bytes()
        )

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as http,
        Client(client=http) as client,
    ):
        archives = client.generation_profiles.archives()
        old = client.generation_profiles.archives(study_year=2021)
        metro = client.generation_profiles.archives(scenario="metro-distributed")
    assert len(archives) == 42 and len(old) == 23
    assert len({a.url for a in archives}) == 42
    assert all(a.timeBasis == "CST" for a in old)
    assert len(metro) == 1 and metro[0].yearFrom == 1980 and metro[0].yearTo == 2020
    # The 2022 index does not link a 2000–2009 wind workbook. Do not invent it.
    assert not any(
        a.studyYear == 2022 and a.fuel == "wind" and a.yearFrom == 2000
        for a in archives
    )


def test_query_dates_and_series_anonymously():
    archive = ProfileArchive(
        studyYear=2021,
        yearFrom=1980,
        yearTo=2020,
        fuel="solar",
        scenario="metro-distributed",
        timeBasis="CST",
        title="Metro",
        url=f"https://www.ercot.com/files/{METRO}",
    )

    def handler(request):
        assert (
            str(request.url) == archive.url and "authorization" not in request.headers
        )
        return httpx.Response(200, content=sample(METRO))

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as http,
        Client(client=http) as client,
    ):
        rows = list(
            client.generation_profiles.rows(
                archive,
                date_from=date(1980, 1, 1),
                date_to=date(1980, 1, 1),
                series=["SITE_01022"],
            )
        )
    assert len(rows) == 24
    assert all(
        len(r.outputs) == 1 and r.outputs[0].series.label == "SITE_01022" for r in rows
    )
    assert rows[0].timestamp == datetime.fromisoformat("1980-01-01T00:00:00")
    assert rows[0].sourceTime == "0000" and rows[0].sourceYear is None
    assert rows[12].outputs[0].generationMW == Decimal("212.534")


def test_workbook_metadata_and_daylight_saving_rows():
    with Client() as client:
        profiles = client.generation_profiles
        metadata = profiles.read_series(sample(WIND))
        rows = list(
            profiles.read(
                sample(WIND),
                date_from=date(2020, 11, 1),
                date_to=date(2020, 11, 1),
                series=["ANACACHO_ANA"],
            )
        )
        spring = list(
            profiles.read(
                sample(WIND),
                date_from=date(2020, 3, 8),
                date_to=date(2020, 3, 8),
                series=[],
            )
        )
    assert metadata[0].siteId == "SITE_00001"
    assert metadata[0].capacityMW == Decimal("99.83")
    assert metadata[0].commonName == "Anacacho" and metadata[0].county == "Kinney"
    assert metadata[0].cdrZone == "South" and metadata[0].plantStatus == "Operational"
    assert metadata[0].newForStudy == "NO"
    repeated = [r for r in rows if r.timestamp.hour == 1]
    assert len(rows) == 25 and len(repeated) == 2
    assert repeated[0].sourceRow != repeated[1].sourceRow
    assert repeated[0].timestamp == repeated[1].timestamp
    assert len(spring) == 23 and all(r.timestamp.hour != 2 for r in spring)


def test_csv_capacity_and_unlabelled_year_column():
    with Client() as client:
        profiles = client.generation_profiles
        wind = profiles.read_series(
            sample("ERCOT_WindProfiles_Hypothetical_2020_CST.csv")
        )
        dual = next(
            profiles.read(
                sample("ERCOT_SolarPVProfiles_Hypothetical-DualAxis_2020_CST.csv")
            )
        )
    assert wind[0].label == "SITE00003" and wind[0].capacityMW == 281
    assert wind[0].sourceHeader == "SITE00003:capacity=281"
    assert dual.sourceYear == 2020 and dual.outputs[0].series.sourceColumn == 4


def test_missing_zero_and_duplicate_columns_remain_distinct():
    data = b"DATE,TIME,X,X\n19800101,0,,0\n19800101,0,-1,2\n"
    with Client() as client:
        rows = list(client.generation_profiles.read(data))
    assert len(rows) == 2 and rows[0].timestamp == rows[1].timestamp
    assert [v.generationMW for v in rows[0].outputs] == [None, Decimal(0)]
    assert [v.series.sourceColumn for v in rows[0].outputs] == [3, 4]
    assert rows[1].outputs[0].generationMW == -1


def test_unexpected_source_column_is_not_dropped():
    with Client() as client, pytest.raises(ValueError, match="column count"):
        list(client.generation_profiles.read(b"DATE,TIME,X\n19800101,0,1,2\n"))
