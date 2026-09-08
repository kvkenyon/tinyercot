import csv
import json
from datetime import date
from decimal import Decimal
from io import BytesIO, StringIO
from itertools import islice
from pathlib import Path
from zipfile import ZipFile

import httpx
import openpyxl
import pytest

from tinyercot import Client, GenerationProfileHour, GenerationProfileSite

FIXTURES = Path(__file__).resolve().parents[1] / "tools/inputs/generation-profiles"
SOLAR = "ERCOT-OperationalPlanned-SolarPVProfiles-2020-2021-CST-CDT.xlsx"
WIND = "ERCOT_WindProfiles_Operational-Planned_2020_CST.csv"
DUAL = "ERCOT_SolarPVProfiles_Hypothetical-DualAxis_2020_CST.csv"


def original(name):
    with ZipFile(FIXTURES / "profiles.zip") as archive:
        return archive.read(name)


def csv_bytes(rows):
    stream = StringIO(newline="")
    csv.writer(stream, lineterminator="\n").writerows(rows)
    return stream.getvalue().encode()


def test_every_published_csv_header_sample_and_original_values():
    samples = json.loads((FIXTURES / "csv-header-samples.json").read_text())
    assert len(samples) == 25
    with Client() as client:
        for sample in samples:
            data = csv_bytes([sample["header"], *sample["sample"]])
            rows = list(client.generation_profiles.read(data))
            header = sample["header"]
            start = header.index("DATE") + 2
            assert len(rows) == 2
            for row, raw in zip(rows, sample["sample"], strict=True):
                assert row.profileDate == date.fromisoformat(raw[start - 2])
                assert row.sourceTime == raw[start - 1]
                assert row.sourceTimeColumn == header[start - 1]
                assert row.generationMW == {
                    key: Decimal(value)
                    for key, value in zip(header[start:], raw[start:], strict=True)
                }
            assert (
                GenerationProfileHour.model_validate_json(rows[0].model_dump_json())
                == rows[0]
            )


def test_original_wind_capacity_headers():
    with Client() as client:
        sites = list(client.generation_profiles.sites(original(WIND), filename=WIND))
        row = next(client.generation_profiles.read(original(WIND), filename=WIND))
    assert len(sites) == 155
    assert sites[0].column == "SITE_00001:capacity=99.825"
    assert sites[0].siteId == "SITE_00001"
    assert sites[0].capacityMW == Decimal("99.825")
    assert sites[0].commonName is None
    assert row.generationMW[sites[0].column] == Decimal("24.103")
    assert row.sourceMember == sites[0].sourceMember == WIND
    assert (
        GenerationProfileSite.model_validate_json(sites[0].model_dump_json())
        == sites[0]
    )


def test_original_workbook_embedded_metadata_and_first_day():
    data = original(SOLAR)
    with Client() as client:
        sites = list(client.generation_profiles.sites(data, filename=SOLAR))
        rows = list(islice(client.generation_profiles.read(data, filename=SOLAR), 24))
    assert len(sites) == 164
    site = sites[0]
    assert site.column == "ACACIA_UNIT_1" and site.siteId == "SITE_00001"
    assert site.capacityMW == Decimal(10)
    assert (site.commonName, site.county, site.cdrZone) == (
        "ACACIA SOLAR",
        "Presidio",
        "West",
    )
    assert (site.plantStatus, site.newFor, site.newForLabel) == (
        "Operational",
        "N",
        "New for 2022",
    )
    workbook = openpyxl.load_workbook(BytesIO(data), read_only=True, data_only=True)
    try:
        source = workbook.active.values
        metadata = list(islice(source, 8))
        columns = metadata[-1][2:]
        for row, cells in zip(rows, islice(source, 24), strict=True):
            assert row.profileDate == date(2020, 1, 1)
            assert row.timeHHMM == cells[1]
            assert row.generationMW == {
                key: Decimal(str(value))
                for key, value in zip(columns, cells[2:], strict=True)
            }
            assert row.sourceSheet == site.sourceSheet == "Sheet1"
    finally:
        workbook.close()


def test_full_original_leap_year_and_extra_year_column():
    with Client() as client:
        rows = client.generation_profiles.read(original(DUAL))
        count = 0
        for row in rows:
            assert row.sourceYear == row.profileDate.year == 2020
            assert len(row.generationMW) == 139
            count += 1
        assert count == 8784
        assert row.profileDate == date(2020, 12, 31)
        assert row.timeHHMM == 2300


def test_nested_zip_filter_retains_repeated_clocks_and_missing_values():
    data = csv_bytes(
        [
            ["DATE", "TIME_CST", "plant"],
            ["20201101", "0100", "0"],
            ["20201101", "0100", ""],
            ["20201102", "0100", "2.125"],
        ]
    )
    inner = BytesIO()
    with ZipFile(inner, "w") as archive:
        archive.writestr("hourly.csv", data)
    outer = BytesIO()
    with ZipFile(outer, "w") as archive:
        archive.writestr("profiles.zip", inner.getvalue())
    with Client() as client:
        rows = list(
            client.generation_profiles.read(
                outer.getvalue(),
                filename="bundle.zip",
                where=lambda r: r.profileDate == date(2020, 11, 1),
            )
        )
    assert [r.generationMW["plant"] for r in rows] == [Decimal(0), None]
    assert [r.sourceTime for r in rows] == ["0100", "0100"]
    assert all(r.sourceMember == "bundle.zip/profiles.zip/hourly.csv" for r in rows)


def test_direct_file_discovery_and_download_without_credentials():
    url = "https://www.ercot.com/files/docs/2021/12/07/profiles.csv"
    requests = []

    def serve(request):
        requests.append(str(request.url))
        assert "Authorization" not in request.headers
        if request.url.path == "/gridinfo/resource":
            return httpx.Response(
                200, text='<a href="/gridinfo/resource/2021">2021</a>'
            )
        if request.url.path == "/gridinfo/resource/2021":
            return httpx.Response(
                200,
                text=f'<a href="{url}">ERCOT Wind Operational and Planned 2020</a><a href="/files/docs/key.xlsx">ERCOT Wind Profile 1980-2020 Key</a>',
            )
        assert str(request.url) == url
        return httpx.Response(200, content=original(WIND))

    with (
        httpx.Client(transport=httpx.MockTransport(serve)) as http,
        Client(client=http) as client,
    ):
        files = client.generation_profiles.files()
        assert len(files) == 1 and files[0].url == url
        data = client.generation_profiles.download(files[0])
        assert next(client.generation_profiles.read(data)).profileDate == date(
            2020, 1, 1
        )
    assert len(requests) == 3


@pytest.mark.parametrize(
    "data",
    [
        b"DATE,TIME,A,A\n20200101,0,1,2\n",
        b"DATE,TIME,A\n20200101,0,1,2\n",
        b"unrecognized\n",
    ],
)
def test_unrecognized_or_lossy_layout_raises(data):
    with Client() as client, pytest.raises(ValueError):
        list(client.generation_profiles.read(data))
