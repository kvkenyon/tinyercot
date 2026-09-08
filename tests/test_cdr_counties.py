from collections import Counter
from decimal import Decimal
from pathlib import Path
from zipfile import ZipFile

import httpx
import pytest
import xlrd

from tinyercot import CdrCountyTable, Client, PublicFile

ROOT = Path(__file__).resolve().parents[1] / "tools/inputs/cdr"


@pytest.fixture(scope="module")
def originals():
    with ZipFile(ROOT / "county-tables.zip") as z:
        files = {name: z.read(name) for name in z.namelist()}
    with ZipFile(ROOT / "summaries.zip") as z:
        name = next(n for n in z.namelist() if "07CDR" in n)
        files[name] = z.read(name)
    return files


@pytest.fixture(scope="module")
def tables(originals):
    with Client() as client:
        return [
            table
            for name, data in originals.items()
            for table in client.cdr.read_county_tables(data, filename=name)
        ]


def test_all_county_cells_periods_labels_and_notes(tables, originals):
    assert len(tables) == 28
    for member, data in originals.items():
        actual = {t.sourceSheet: t for t in tables if t.sourceMember == member}
        with xlrd.open_workbook(file_contents=data) as book:
            expected_sheets = {s.name for s in book.sheets() if "County" in s.name}
            assert set(actual) == expected_sheets
            for name, table in actual.items():
                sheet = book.sheet_by_name(name)
                header = next(
                    r for r in range(sheet.nrows) if "County" in sheet.row_values(r)
                )
                county_col = sheet.row_values(header).index("County")
                expected = {
                    (r + 1, c + 1)
                    for r in range(header + 1, sheet.nrows)
                    if any(v != "" for v in sheet.row_values(r))
                    for c in range(county_col + 1, sheet.ncols)
                    if sheet.cell_value(header, c) != ""
                }
                assert {(v.sourceRow, v.sourceColumn) for v in table.values} == expected
                assert len(table.values) == len(expected)
                for value in table.values:
                    source = sheet.cell_value(
                        value.sourceRow - 1, value.sourceColumn - 1
                    )
                    assert value.valueMW == (
                        None if source == "" else Decimal(str(source))
                    )
                    assert value.sourceError is None
                    assert value.county == (
                        sheet.cell_value(value.sourceRow - 1, county_col) or None
                    )
                    period = sheet.cell_value(header, value.sourceColumn - 1)
                    assert value.period == (
                        str(int(period)) if isinstance(period, float) else period
                    )
                for note in table.notes:
                    assert note.text == sheet.cell_value(
                        note.sourceRow - 1, note.sourceColumn - 1
                    )


def select(tables, fragment, sheet):
    return next(
        t for t in tables if fragment in t.sourceMember and t.sourceSheet == sheet
    )


def test_load_basis_changes_and_coincident_forecasts_are_distinct(tables):
    old = select(tables, "2009_with", "SummerLoadbyCounty")
    coincident = select(tables, "2009_with", "SummerCoincidentDemandbyCounty")
    new = select(tables, "report_2012", "SummerLoadbyCounty")
    assert old.metric == new.metric == "load"
    assert old.loadBasis == "noncoincident" and new.loadBasis == "coincident"
    assert (
        coincident.metric == "coincident_demand"
        and coincident.loadBasis == "coincident"
    )
    assert old.values[0].valueMW != coincident.values[0].valueMW
    assert "Anderson" == new.values[0].county
    assert select(tables, "03CDR", "SummerLoadbyCounty").values[0].county == "ANDERSON"
    assert any("do not include self-serve" in n.text for n in new.notes)


def test_capacity_assumptions_and_illustrative_balance_signs(tables):
    early = select(tables, "03CDR", "SummerGenerationbyCounty")
    later = select(tables, "2009_with", "SummerGenerationbyCounty")
    assert early.metric == later.metric == "generation_capacity"
    assert any("100%" in n.text for n in early.notes)
    assert any("8.7%" in n.text for n in later.notes)
    balance = select(tables, "2009_with", "SummerImport-ExportbyCounty")
    load = select(tables, "2009_with", "SummerLoadbyCounty")
    assert (
        balance.metric == "generation_minus_load"
        and balance.loadBasis == "noncoincident"
    )
    assert any("example only" in n.text for n in balance.notes)
    assert balance.values[0].valueMW == -load.values[0].valueMW
    assert any(v.county == "WISE" and v.valueMW > 0 for v in balance.values)
    assert (
        select(tables, "report_2012", "SummerImport-ExportbyCounty").loadBasis
        == "coincident"
    )


def test_winter_periods_missing_cells_and_unlabelled_numeric_row(tables):
    table = select(tables, "report_2012", "WinterLoadbyCounty")
    assert table.season == "winter" and table.values[0].period == "2013/14"
    unlabelled = [(t, v) for t in tables for v in t.values if v.county is None]
    assert len(unlabelled) == 6
    assert all(
        t.sourceSheet == "WinterImport-ExportbyCounty" and "2009_with" in t.sourceMember
        for t, v in unlabelled
    )
    blanks = [v for t in tables for v in t.values if v.valueMW is None]
    assert len(blanks) == 6 and all(v.sourceError is None for v in blanks)
    assert any(v.valueMW == 0 for t in tables for v in t.values)
    assert CdrCountyTable.model_validate_json(table.model_dump_json()) == table


def test_anonymous_download_file_identity_predicate_and_absent_tables(originals):
    member = next(n for n in originals if "report_2012" in n)
    url = "https://www.ercot.com/files/docs/" + member
    title = "Capacity Demand and Reserve Report 2012"

    def handler(request):
        assert "authorization" not in request.headers
        return (
            httpx.Response(200, content=originals[member])
            if str(request.url) == url
            else httpx.Response(200, text=f'<a href="{url}">{title}</a>')
        )

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as http,
        Client(client=http) as client,
    ):
        tables = list(
            client.cdr.county_tables(
                where=lambda t: t.metric == "generation_minus_load"
            )
        )
        assert Counter(t.season for t in tables) == {"summer": 1, "winter": 1}
        assert all(t.sourceFile == PublicFile(title=title, url=url) for t in tables)
        assert all(t.sourceMember == member.rsplit("/", 1)[-1] for t in tables)
        with ZipFile(ROOT / "summaries.zip") as z:
            latest = next(n for n in z.namelist() if "December2024" in n)
            assert list(client.cdr.read_county_tables(z.read(latest))) == []
        saved = list(
            client.cdr.read_county_tables((ROOT / "county-tables.zip").read_bytes())
        )
        assert len(saved) == 20 and {t.sourceMember for t in saved} == set(
            originals
        ) - {n for n in originals if "07CDR" in n}
