import csv
from collections import Counter
from datetime import date
from decimal import Decimal
from io import BytesIO, StringIO
from pathlib import Path
from zipfile import ZipFile

import httpx
import msoffcrypto
import openpyxl
import pytest
import xlrd

from tinyercot import Client, DistributionLossCoefficient, PublicFile

INPUTS = Path(__file__).resolve().parents[1] / "tools/inputs"
MANIFEST = list(
    csv.DictReader(
        StringIO((INPUTS / "public-distribution-coefficients-sources.csv").read_text())
    )
)
FIXTURE = INPUTS / "public-tables/distribution-loss-coefficients.zip"


@pytest.fixture(scope="module")
def coefficients():
    with Client() as client:
        return list(client.distribution_loss_coefficients.read(FIXTURE.read_bytes()))


def test_all_original_parameters_and_baselines(coefficients):
    with ZipFile(FIXTURE) as z:
        for file in MANIFEST:
            data = z.read(file["member"])
            if file["defaultProtection"] == "True":
                office = msoffcrypto.OfficeFile(BytesIO(data))
                office.load_key(password="VelvetSweatshop")
                output = BytesIO()
                office.decrypt(output)
                data = output.getvalue()
            if file["member"].endswith(".xls"):
                with xlrd.open_workbook(file_contents=data) as book:
                    sheet = book.sheet_by_name("TDSP and ERCOT Variables")
                    raw = [sheet.row_values(i) for i in range(sheet.nrows)]
            else:
                book = openpyxl.load_workbook(
                    BytesIO(data), read_only=True, data_only=True
                )
                raw = list(book["TDSP and ERCOT Variables"].values)
                book.close()
            records = [r for r in coefficients if r.sourceMember == file["member"]]
            assert len(records) == int(file["rows"])
            header = raw[0].index("DSP =")
            columns = [
                i for i in range(header + 1, len(raw[0])) if raw[0][i] not in (None, "")
            ]
            assert len(records) == len(columns)
            baseline = raw[0].index("ERCOT")
            for r, column in zip(records, columns, strict=True):
                assert (r.tdsp, r.lossCode) == (raw[0][column], raw[1][column])
                legacy = raw[2][header] != "F1 ="
                assert r.formula == ("k_adlf" if legacy else "f1_f2_f3")
                modern_values = (r.f1, r.f2, r.f3)
                legacy_values = (
                    r.tdspAverageIntervalLoadMWh,
                    r.kFactor,
                    r.annualDistributionLossFactor,
                )
                assert (legacy_values if legacy else modern_values) == tuple(
                    Decimal(str(raw[i][column])) for i in (2, 3, 4)
                )
                assert (modern_values if legacy else legacy_values) == (
                    None,
                    None,
                    None,
                )
                assert r.ercotAnnualEnergyMWh == Decimal(str(raw[2][baseline + 1]))
                assert r.ercotIntervalCount == raw[3][baseline + 1]
                assert r.ercotAverageIntervalLoadMWh == Decimal(
                    str(raw[4][baseline + 1])
                )
                assert r.sourceBaselinePeriod == raw[1][baseline]
                assert r.sourceColumn == column + 1
                assert r.sourceSheet == "TDSP and ERCOT Variables"
                assert (
                    DistributionLossCoefficient.model_validate_json(r.model_dump_json())
                    == r
                )
    assert len(coefficients) == 466
    assert Counter(r.formula for r in coefficients) == {"k_adlf": 114, "f1_f2_f3": 352}
    assert {r.year for r in coefficients} == set(range(2001, 2027))


def test_source_year_conflict_baseline_and_period_variants(coefficients):
    latest = next(r for r in coefficients if r.year == 2026)
    assert "2025" in latest.sourceWorkbookTitle
    assert latest.baselineFrom == date(2024, 9, 1)
    assert latest.baselineThrough == date(2025, 8, 31)
    assert latest.ercotAverageIntervalLoadMWh == Decimal(13668)
    assert latest.ercotPeakLoadMW == Decimal(83941)
    earliest = next(r for r in coefficients if r.year == 2001)
    assert earliest.baselineFrom == date(2000, 1, 1)
    assert earliest.baselineThrough == date(2000, 12, 31)
    assert earliest.ercotPeakLoadMW is None
    assert any(r.tdsp.endswith(" ") for r in coefficients)
    assert any(r.f2 is not None and r.f2 < 0 for r in coefficients)
    assert len({r.sourceMember for r in coefficients if r.year == 2024}) == 2
    assert {r.formula for r in coefficients if r.year == 2007} == {"k_adlf", "f1_f2_f3"}
    assert len({r.ercotAnnualEnergyMWh for r in coefficients if r.year == 2007}) == 2


def test_original_discovery_and_anonymous_typed_query():
    index = (INPUTS / "public-tables/distribution-loss-index.html").read_bytes()
    with ZipFile(FIXTURE) as z:
        files = {}
        for f in MANIFEST:
            bundle = BytesIO()
            with ZipFile(bundle, "w") as archive:
                archive.writestr(f["member"], z.read(f["member"]))
                archive.writestr("provider-methodology.xlsx", b"unrelated attachment")
            files[f["url"]] = bundle.getvalue()
    requested = []

    def handler(request):
        assert "authorization" not in request.headers
        requested.append(str(request.url))
        return httpx.Response(200, content=files.get(str(request.url), index))

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as http,
        Client(client=http) as client,
    ):
        discovered = client.distribution_loss_coefficients.files()
        assert {(f.title, f.url) for f in discovered} == {
            (f["title"], f["url"]) for f in MANIFEST
        }
        requested.clear()
        records = list(
            client.distribution_loss_coefficients.rows(where=lambda r: r.year == 2024)
        )
    assert len(records) == 32
    assert len(requested) == 29
    assert len({r.sourceFile.url for r in records}) == 2
    assert all(isinstance(r.sourceFile, PublicFile) for r in records)


def test_saved_summary_filename_and_missing_table():
    with ZipFile(FIXTURE) as z:
        member = MANIFEST[0]["member"]
        data = z.read(member)
    with Client() as client:
        unnamed = next(client.distribution_loss_coefficients.read(data))
        assert unnamed.year is None
        named = next(client.distribution_loss_coefficients.read(data, filename=member))
        assert named.year == 2026 and named.sourceMember == member
        empty = BytesIO()
        with ZipFile(empty, "w") as z:
            z.writestr("methodology.txt", "No numerical summary")
        with pytest.raises(ValueError, match="no distribution-loss summary"):
            list(client.distribution_loss_coefficients.read(empty.getvalue()))
