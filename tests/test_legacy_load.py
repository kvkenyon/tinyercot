from collections import Counter
from datetime import date
from decimal import Decimal
from io import BytesIO
from itertools import islice
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


@pytest.mark.parametrize(
    "filename,count",
    [
        ("erceei95.txt", 8760),
        ("96load.txt", 9685),
        ("erceei97.txt", 8760),
        ("erceei97.xls", 8760),
        ("97frc714.zip", 96624),
        ("ferc714.zip", 236520),
        ("1999ferc714.zip", 96371),
        ("2000ferc714.zip", 96635),
    ],
)
def test_all_original_file_counts(filename, count):
    with Client() as client:
        assert (
            sum(
                1
                for _ in client.hourly_load.read_legacy(
                    sample(filename), filename=filename
                )
            )
            == count
        )


def test_eei_card_boundaries_and_raw_headers():
    with Client() as client:
        rows = list(
            islice(
                client.hourly_load.read_legacy(
                    sample("erceei95.txt"), filename="erceei95.txt"
                ),
                24,
            )
        )
    assert [r.hourEnding for r in rows] == list(range(1, 25))
    assert all(r.operatingDay == date(1995, 1, 1) for r in rows)
    assert [rows[i].demand for i in [0, 11, 12, 23]] == [19732, 23825, 23677, 24101]
    assert all(r.unit == "MW" and r.entityType == "system" for r in rows)
    assert (
        rows[0].sourceCardHeader == sample("erceei95.txt").decode().splitlines()[0][:20]
    )
    assert (
        rows[12].sourceCardHeader
        == sample("erceei95.txt").decode().splitlines()[1][:20]
    )


def test_1997_raw_and_xls_are_identical():
    with Client() as client:
        raw = [
            (r.operatingDay, r.hourEnding, r.demand, r.unit)
            for r in client.hourly_load.read_legacy(
                sample("erceei97.txt"), filename="erceei97.txt"
            )
        ]
        workbook = [
            (r.operatingDay, r.hourEnding, r.demand, r.unit)
            for r in client.hourly_load.read_legacy(sample("erceei97.xls"))
        ]
    assert raw == workbook
    assert max(r[2] for r in raw) == 50365
    # Independently published workbook summary is 249610.864 GWh.
    assert sum(r[2] for r in raw) / 1000 == Decimal("249610.864")


def test_control_area_identity_from_eei_member():
    with Client() as client:
        rows = list(islice(client.hourly_load.read_legacy(sample("97frc714.zip")), 12))
    assert all(r.operatingDay == date(1996, 1, 1) for r in rows)
    assert all(r.entity == r.controlArea == "COA" for r in rows)
    assert all(r.entityType == "control_area" for r in rows)
    assert rows[0].sourceMember == "COA96LD.EEI"
    assert [r.demand for r in rows] == [
        644,
        624,
        606,
        598,
        593,
        597,
        616,
        628,
        634,
        672,
        723,
        752,
    ]


def test_lse_and_control_area_mapping_and_kw_units():
    with Client() as client:
        rows = list(islice(client.hourly_load.read_legacy(sample("ferc714.zip")), 27))
    assert all(r.operatingDay == date(1998, 1, 1) and r.hourEnding == 1 for r in rows)
    assert all(r.unit == "kW" for r in rows)
    indexed = {r.entity: r for r in rows}
    assert indexed["BEPC"].controlArea == "TMPP"
    assert indexed["BEPC"].demand == 658000
    assert indexed["HUCO & COFV"].controlArea == "TNMP"
    assert indexed["HUCO & COFV"].demand == 8
    assert indexed["AENX"].demand == 846000
    assert indexed["TOTAL"].demand == 24167171
    assert indexed["TOTAL"].entityType == "system"
    assert indexed["TOTAL"].controlArea == "ERCOT"


def test_source_errors_and_unlabelled_units():
    with Client() as client:
        rows = list(client.hourly_load.read_legacy(sample("1999ferc714.zip")))
    errors = [r for r in rows if r.sourceError]
    assert {(r.operatingDay, r.hourEnding, r.entity) for r in errors} == {
        (date(1999, 3, 21), 24, "TMPP"),
        (date(1999, 3, 21), 24, "ERCOT TOTAL"),
        (date(1999, 4, 4), 3, "TMPP"),
        (date(1999, 4, 4), 3, "ERCOT TOTAL"),
    }
    assert all(r.demand is None and r.sourceError == "#VALUE!" for r in errors)
    assert all(r.unit is None for r in rows)
    assert rows[10].demand == 22055255  # Original magnitude; no inferred MW conversion.
    assert rows[0].entity == "AENX"
    assert rows[0].demand == 820000


def test_repeated_hour_is_not_deduplicated():
    with Client() as client:
        rows = [
            r
            for r in client.hourly_load.read_legacy(sample("2000ferc714.zip"))
            if r.operatingDay == date(2000, 10, 29) and r.entity == "ERCOT TOTAL"
        ]
    assert len(rows) == 25
    assert [r.demand for r in rows if r.hourEnding == 3] == [24286898, 23340354]


def test_filter_uses_contained_dates_and_preserves_publication_overlap():
    names = ["96load.txt", "erceei97.txt", "erceei97.xls", "97frc714.zip"]
    years = [1996, 1997, 1997, 1997]
    urls = {"https://www.ercot.com/files/docs/2004/07/26/" + n: n for n in names}
    html = "".join(
        f'<a href="{url}">{year} ERCOT Hourly Load Data</a>'
        for url, year in zip(urls, years, strict=True)
    )
    requests = []

    def handle(request):
        assert "authorization" not in request.headers
        assert "ocp-apim-subscription-key" not in request.headers
        if str(request.url) == INDEX_URL:
            return httpx.Response(200, text=html)
        requests.append(urls[str(request.url)])
        return httpx.Response(200, content=sample(requests[-1]))

    with (
        httpx.Client(transport=httpx.MockTransport(handle)) as http,
        Client(client=http) as client,
    ):
        rows = list(
            client.hourly_load.legacy(
                date_from=date(1997, 1, 1), date_to=date(1997, 1, 1)
            )
        )
    assert len(rows) == 72
    assert Counter(r.sourceMember for r in rows) == {
        "96load.txt": 24,
        "erceei97.txt": 24,
        "erceei97.xls": 24,
    }
    assert set(requests) == set(names)


def test_eei_filename_required_and_truncated_cards_fail():
    with Client() as client:
        with pytest.raises(ValueError, match="original filename"):
            list(client.hourly_load.read_legacy(sample("erceei95.txt")))
        with pytest.raises(ValueError, match="unsupported EEI card"):
            list(
                client.hourly_load.read_legacy(
                    sample("erceei95.txt")[:79], filename="erceei95.txt"
                )
            )
        with pytest.raises(ValueError, match="Unrecognized EEI entity"):
            list(
                client.hourly_load.read_legacy(
                    sample("erceei95.txt"), filename="UNKNOWNLD.EEI"
                )
            )


def test_unknown_tokens_are_not_treated_as_missing():
    with ZipFile(BytesIO(sample("1999ferc714.zip"))) as archive:
        data = archive.read("ERCOT99HRLD.txt").replace(b"#VALUE!", b"UNKNOWN")
    with Client() as client, pytest.raises(ValueError, match="Invalid source demand"):
        list(client.hourly_load.read_legacy(data, filename="ERCOT99HRLD.txt"))
