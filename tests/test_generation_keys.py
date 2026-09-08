from collections import Counter
from datetime import date
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import httpx
import openpyxl
import pytest

from tinyercot import Client, GenerationProfileKey

ROOT = Path(__file__).resolve().parents[1] / "tools/inputs/generation-profiles/keys"
WIND20 = "ERCOT_WindProfiles_1980-2020_Key-public.xlsx"
WIND21 = "ERCOT-WindProfiles-1980-2021-Key-public.xlsx"
SOLAR20 = "ERCOT_SolarPVProfiles_1980-2020_Key-public.xlsx"
SOLAR21 = "ERCOT-SolarPVProfiles-1980-2021-Key-public.xlsx"

# Original worksheet data extents, including both repeated-header solar sections.
TABLES = [
    (
        WIND20,
        "Op&Planned_Wind-Summary",
        range(2, 157),
        ("siteNumber", "commonName", "county", "newFor"),
    ),
    (
        WIND20,
        "Op&Planned_Wind-Unit_Codes",
        range(2, 229),
        ("commonName", "unitCode", "siteNumber", "newFor"),
    ),
    (
        WIND20,
        "Hypo_Wind-Summary",
        range(2, 150),
        (
            "siteNumber",
            "capacityMW",
            "xCoordinate",
            "yCoordinate",
            "county",
            "distanceToOperationalOrQueued",
            "newFor",
            "iecClass",
        ),
    ),
    (
        WIND21,
        "Op&Planned_Wind-Summary",
        range(2, 215),
        (
            "siteNumber",
            "commonName",
            "county",
            "cdrZone",
            "newFor",
            "capacityMW",
            "plantStatus",
        ),
    ),
    (
        WIND21,
        "Op&Planned_Wind-Unit_Codes",
        range(2, 354),
        ("commonName", "unitCode", "siteNumber", "newFor"),
    ),
    (
        SOLAR20,
        "Utility_Operational&Planned",
        [*range(3, 29), *range(33, 60)],
        (
            "unitCode",
            "latitude",
            "longitude",
            "county",
            "cdrZone",
            "capacityMW",
            "trackingSystem",
            "trackingType",
            "tilt",
            "azimuth",
            "dcAcRatio",
            "inverters",
            "modules",
            "modeledIn",
        ),
    ),
    (
        SOLAR20,
        "Utility_Hypothetical",
        range(2, 141),
        (
            "siteNumber",
            "typeCode",
            "capacityMW",
            "latitude",
            "longitude",
            "county",
            "cdrZone",
        ),
    ),
    (
        SOLAR20,
        "DGPV_metro",
        range(2, 14),
        ("siteNumber", "metroArea", "developmentIntensity", "capacityMW"),
    ),
    (
        SOLAR20,
        "DGPV_rural",
        range(2, 218),
        ("siteNumber", "capacityMW", "county", "cdrZone"),
    ),
    (
        SOLAR21,
        "Utility_Operational&Planned",
        [*range(3, 43), *range(47, 171)],
        ("unitCode", "commonName", "county", "cdrZone", "capacityMW", "newFor"),
    ),
    (
        SOLAR21,
        "Utility_Hypothetical",
        range(2, 151),
        ("siteNumber", "typeCode", "capacityMW", "county", "cdrZone", "newFor"),
    ),
]


def read(name):
    with Client() as client:
        return next(
            client.generation_profiles.read_keys(
                (ROOT / name).read_bytes(), filename=name
            )
        )


@pytest.mark.parametrize("name,sheet,source_rows,fields", TABLES)
def test_every_original_site_table_cell(name, sheet, source_rows, fields):
    key = read(name)
    records = [row for row in key.sites if row.sourceSheet == sheet]
    assert [row.sourceRow for row in records] == list(source_rows)
    workbook = openpyxl.load_workbook(ROOT / name, read_only=True, data_only=True)
    try:
        source = list(workbook[sheet].values)
        for row in records:
            for field, value in zip(fields, source[row.sourceRow - 1], strict=False):
                expected = (
                    Decimal(str(value)) if isinstance(value, (float, int)) else value
                )
                assert getattr(row, field) == expected, (row.sourceRow, field)
    finally:
        workbook.close()
    assert key.sourceMember == name
    assert GenerationProfileKey.model_validate_json(key.model_dump_json()) == key


@pytest.mark.parametrize("name,expected", [(SOLAR20, 22), (SOLAR21, 10)])
def test_every_original_summary_number_and_label(name, expected):
    key = read(name)
    workbook = openpyxl.load_workbook(ROOT / name, read_only=True, data_only=True)
    try:
        source = list(workbook["SUMMARY"].values)
        numeric_rows = {
            i
            for i, row in enumerate(source, 1)
            if any(isinstance(v, (int, float)) for v in row)
        }
        assert {r.sourceRow for r in key.summaries} == numeric_rows
        assert len(key.summaries) == expected
        for row in key.summaries:
            cells = source[row.sourceRow - 1]
            if row.typeCode is not None:
                assert (
                    row.typeCode,
                    row.label,
                    row.profileCount,
                    row.trackingScenarioCount,
                    row.trackingType,
                    row.totalProfileCount,
                ) == cells[1:7]
            elif row.totalProfileCount is not None:
                assert row.label == cells[1]
                assert row.totalProfileCount == cells[6]
            else:
                assert row.label == cells[2]
                assert row.profileCount == cells[3]
                assert row.capacityMW == (
                    Decimal(str(cells[4])) if cells[4] is not None else None
                )
        assert key.sourceTitle == source[0][1]
        assert key.sourceDate == source[1][1].date()
    finally:
        workbook.close()


def test_source_labels_notes_and_inconsistent_published_total():
    key = read(SOLAR20)
    assert key.sourceDate == date(2021, 6, 25)
    by_unit = {row.unitCode: row for row in key.sites if row.unitCode}
    assert by_unit["ECLIPSE_UNIT1"].tilt == "Lat"
    assert by_unit["HELIOS_UNIT1"].tilt == "NA"
    assert by_unit["ACACIA_UNIT_1"].modeledInLabel == "Modeled in 2020"
    assert any("OXYSOLAR_SOLAR_1" in note for note in key.sourceNotes.values())
    assert key.summaries[0].profileCount == 313
    assert (
        sum(
            row.totalProfileCount or 0
            for row in key.summaries
            if row.label.strip() == "Total"
        )
        == 331
    )
    wind = read(WIND20)
    assert wind.sites[0].newForLabel == "New for 2021"
    assert next(row for row in wind.sites if row.unitCode).newForLabel == "New for 2020"


def test_color_legend_flags_and_multiple_units_per_site():
    key = read(WIND20)
    marked = [row for row in key.sites if row.queuedModelFlag]
    assert {row.siteNumber for row in marked} == {4000, 4001, 4004, 4007}
    assert Counter(row.sourceSheet for row in marked) == {
        "Op&Planned_Wind-Summary": 4,
        "Op&Planned_Wind-Unit_Codes": 12,
    }
    # The legend is beside Falvez Astra's row; it must not mark that site's ID.
    assert (
        next(row for row in key.sites if row.siteNumber == 2).queuedModelFlag is False
    )
    assert all(row.queuedModelFlag is None for row in read(WIND21).sites)
    high_lonesome = [
        row.unitCode for row in marked if row.siteNumber == 4007 and row.unitCode
    ]
    assert len(high_lonesome) == 7


def test_key_discovery_download_and_nested_original_workbooks():
    url = "https://www.ercot.com/files/docs/2022/12/19/solar-key.xlsx"
    calls = []

    def serve(request):
        calls.append(request.url.path)
        assert "Authorization" not in request.headers
        if request.url.path == "/gridinfo/resource":
            return httpx.Response(
                200, text='<a href="/gridinfo/resource/2022">2022</a>'
            )
        if request.url.path.endswith("/2022"):
            return httpx.Response(
                200, text=f'<a href="{url}">ERCOT Solar PV Profiles 1980-2021 Key</a>'
            )
        return httpx.Response(200, content=(ROOT / SOLAR21).read_bytes())

    with (
        httpx.Client(transport=httpx.MockTransport(serve)) as http,
        Client(client=http) as client,
    ):
        files = client.generation_profiles.key_files()
        assert len(files) == 1
        key = next(
            client.generation_profiles.read_keys(
                client.generation_profiles.download(files[0])
            )
        )
        assert len(key.sites) == 313
    assert len(calls) == 3
    inner = BytesIO()
    with ZipFile(inner, "w") as archive:
        archive.writestr(SOLAR21, (ROOT / SOLAR21).read_bytes())
        archive.writestr(WIND21, (ROOT / WIND21).read_bytes())
    outer = BytesIO()
    with ZipFile(outer, "w") as archive:
        archive.writestr("keys.zip", inner.getvalue())
    with Client() as client:
        keys = list(client.generation_profiles.read_keys(outer.getvalue()))
    assert [key.sourceMember for key in keys] == [SOLAR21, WIND21]
    assert [len(key.sites) for key in keys] == [313, 565]


def test_same_vintage_unit_code_mismatch_is_not_silently_normalized():
    key = read(SOLAR21)
    with ZipFile(ROOT.parent / "profiles.zip") as archive:
        data = archive.read(
            "ERCOT-OperationalPlanned-SolarPVProfiles-2020-2021-CST-CDT.xlsx"
        )
    with Client() as client:
        columns = {site.column for site in client.generation_profiles.sites(data)}
    units = {site.unitCode for site in key.sites if site.unitCode}
    assert len(columns & units) == 163
    assert columns - units == {"TREBA_UNIT1"}
    assert units - columns == {"TREBA_UNIT 1"}
