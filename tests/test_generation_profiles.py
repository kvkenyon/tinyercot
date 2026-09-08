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


def test_older_wind_clock_alias_and_archive_boundaries():
    data = (FIXTURES / "formats/2015_Wind_Profiles.zip").read_bytes()
    with Client() as client:
        row = next(client.generation_profiles.read(data, filename="2015.zip"))
        sites = list(client.generation_profiles.sites(data, filename="2015.zip"))
    assert row.profileDate == date(2014, 12, 31)
    assert row.sourceTimeColumn == "HHMM(CST)"
    assert row.timeHHMM == 1800
    assert row.sourceMember == "2015.zip/ERCOT_offshore_2015.CSV"
    assert sites[0].capacityMW == Decimal("500.0")
    assert row.generationMW[sites[0].column] == Decimal("452.3")


def test_side_by_side_original_tables_keep_their_own_dates():
    from collections import Counter
    from itertools import chain

    data = (FIXTURES / "formats/legacy-compound.zip").read_bytes()
    with Client() as client:
        sites = list(client.generation_profiles.sites(data))
        rows = client.generation_profiles.read(data)
        onshore, offshore = next(rows), next(rows)
        assert onshore.profileDate == date(2011, 1, 1)
        assert offshore.profileDate == date(2013, 1, 1)
        assert onshore.sourceBlock == 1 and offshore.sourceBlock == 2
        counts = Counter()
        for row in chain([onshore, offshore], rows):
            assert row.profileDate.year == {1: 2011, 2: 2013}[row.sourceBlock]
            assert len(row.generationMW) == {1: 225, 2: 3}[row.sourceBlock]
            assert "YYYYMMDD" not in row.generationMW
            assert "HHMM(CST)" not in row.generationMW
            counts[row.sourceBlock] += 1
    # Six short trailing rows have an entirely empty offshore block.
    assert counts == {1: 8760, 2: 8754}
    assert Counter(site.sourceBlock for site in sites) == {1: 225, 2: 3}


def test_hypothetical_solar_tracking_metadata():
    name = "ERCOT-Hypothetical-DualAxis-SolarPVProfiles-2020-2021-CST-CDT.xlsx"
    data = (FIXTURES / "formats" / name).read_bytes()
    with Client() as client:
        sites = list(client.generation_profiles.sites(data, filename=name))
        row = next(client.generation_profiles.read(data, filename=name))
    assert len(sites) == 149
    assert all(site.tracking == "DUAL" for site in sites)
    assert all(site.plantStatus == "Hypothetical" for site in sites)
    assert all(site.capacityMW == 50 for site in sites)
    assert sites[0].commonName == "NA"
    assert sites[0].siteId == sites[0].column == "SITE_00004"
    assert sites[0].county == "Presidio"
    assert sites[0].sourceBlock == row.sourceBlock == 1


@pytest.mark.parametrize("index", [0, 1])
def test_legacy_workbook_source_row_excerpts(index, monkeypatch):
    from tinyercot import _generation_profiles

    source = json.loads((FIXTURES / "legacy-workbooks/rows.json").read_text())[index]
    hypothetical = source["member"].startswith("Hypotherical")
    start, stop, date_column = (6, 139, 1) if hypothetical else (2, 95, 0)
    calendar_columns = (3, 4, 5) if hypothetical else (95, 96, 97)
    metadata = [tuple(row) for row in source["metadata"]]
    # The XLSX header has only six stored cells despite a 139-column data table.
    if hypothetical:
        metadata[-1] = metadata[-1][:6]
    data_rows = [tuple(row) for _, row in source["sampleRows"]]
    ids = metadata[2 if hypothetical else 6]

    def tables(data, filename):
        yield filename, "Sheet1", iter([*metadata, *data_rows, (None,)])
        for sheet in source["emptySheets"]:
            yield filename, sheet, iter([(None,)])

    # Feed exact source cell values through the table-reading boundary. Complete
    # original XLSX parsing and all rows are checked by the recorded source audit.
    monkeypatch.setattr(_generation_profiles, "_tables", tables)
    with Client() as client:
        sites = list(client.generation_profiles.sites(b"", filename=source["member"]))
        rows = list(client.generation_profiles.read(b"", filename=source["member"]))
    assert len(sites) == stop - start
    assert len(rows) == len(data_rows)
    for parsed, raw in zip(rows, data_rows, strict=True):
        assert parsed.profileDate == date.fromisoformat(str(raw[date_column]))
        assert parsed.sourceTime == str(raw[date_column + 1])
        assert parsed.calendarDate == date(*(raw[i] for i in calendar_columns))
        assert parsed.sourceYear == (int(raw[0]) if hypothetical else None)
        assert parsed.generationMW == {
            str(ids[i]): Decimal(str(raw[i])) if raw[i] is not None else None
            for i in range(start, stop)
        }
        assert parsed.sourceMember == source["member"]
    for i, site in enumerate(sites, start):
        assert site.siteId == site.column == str(ids[i])
        assert site.capacityMW == Decimal(str(metadata[4 if hypothetical else 2][i]))
        if hypothetical:
            assert site.county == metadata[0][i]
            assert site.sourceSum == Decimal(str(metadata[5][i]))
            assert site.sourceCount == metadata[6][i]
            assert site.sourceCapacityFactor == Decimal(str(metadata[7][i]))
        else:
            assert site.commonName == metadata[0][i]
            assert site.awsName == metadata[1][i]
            assert site.annualEnergyMWh == {
                2006: Decimal(str(metadata[3][i])),
                2011: Decimal(str(metadata[4][i])),
            }
            assert site.annualCapacityFactor == {2011: Decimal(str(metadata[5][i]))}
        assert GenerationProfileSite.model_validate_json(site.model_dump_json()) == site
