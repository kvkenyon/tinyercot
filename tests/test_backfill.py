"""Combined-source backfills preserve publications and avoid repeated downloads."""

# ERCOT publication timestamps are local and carry no UTC offset.
# ruff: noqa: DTZ001

import json
from datetime import date, datetime
from io import BytesIO
from pathlib import Path
from zipfile import BadZipFile, ZipFile

import httpx
import pytest

from examples.price_history import export_price_history
from tinyercot import Client

INPUTS = Path(__file__).resolve().parents[1] / "tools/inputs/history"


def zipped(members):
    out = BytesIO()
    with ZipFile(out, "w") as archive:
        for name, content in members.items():
            archive.writestr(name, content)
    return out.getvalue()


def document(doc_id, posted="2018-01-01T12:00:00", name="report"):
    return {"docId": doc_id, "friendlyName": name, "postDatetime": posted}


class Source:
    """One listing entry per page exercises both source paginators."""

    def __init__(self, archives, bundles, payloads):
        self.archives = archives
        self.bundles = bundles
        self.payloads = payloads
        self.downloads = []
        self.listings = []

    def __call__(self, request):
        if "b2clogin" in request.url.host:
            return httpx.Response(200, json={"id_token": "test", "expires_in": 3600})
        kind = "bundle" if "/bundle/" in request.url.path else "archive"
        if request.method == "POST":
            ids = json.loads(request.content)["docIds"]
            self.downloads.append((kind, ids))
            return httpx.Response(200, content=self.payloads[kind, tuple(ids)])
        if "/archive/" not in request.url.path and "/bundle/" not in request.url.path:
            return httpx.Response(
                200,
                json={
                    "emilId": "NP4-190-CD",
                    "name": "Report",
                    "reportTypeId": 1,
                    "downloadLimit": 2,
                    "status": "Active",
                },
            )
        page = int(request.url.params["page"])
        self.listings.append((kind, page))
        docs = self.bundles if kind == "bundle" else self.archives
        return httpx.Response(
            200,
            json={
                "_meta": {"currentPage": page, "totalPages": max(1, len(docs))},
                "product": {
                    "emilId": "NP4-190-CD",
                    "name": "Report",
                    "reportTypeId": 1,
                },
                "bundles" if kind == "bundle" else "archives": docs[page - 1 : page],
            },
        )


def run(source, product="np4_190_cd", method="dam_stlmnt_pnt_prices_history", **kwargs):
    with (
        httpx.Client(transport=httpx.MockTransport(source)) as http,
        Client("u", "p", "k", client=http) as client,
    ):
        return list(getattr(getattr(client, product), method).backfill(**kwargs))


def price_report():
    return zipped({"report.csv": (INPUTS / "np4-190-cd.csv").read_bytes()})


def test_overlap_missing_months_and_distinct_corrections_preserve_rows():
    report = price_report()
    # Same rows in two distinct publications remain distinct. Overlapping bundle
    # copies of publication 2 must not add another set of rows.
    source = Source(
        [document(i) for i in range(1, 6)],
        [document(-1), document(-2)],
        {
            ("bundle", (-1,)): zipped(
                {"2.cdr.report.zip": report, "3.cdr.report.zip": report}
            ),
            ("bundle", (-2,)): zipped({"2.cdr.report.zip": report}),
            ("archive", (1, 4)): zipped({"1.zip": report, "4.zip": report}),
            ("archive", (5,)): report,
        },
    )
    rows = run(source, batch_size=25)
    assert len(rows) == 15
    assert rows[:3] == rows[3:6] == rows[6:9] == rows[9:12] == rows[12:]
    assert source.downloads == [
        ("bundle", [-1]),
        ("bundle", [-2]),
        ("archive", [1, 4]),
        ("archive", [5]),
    ]
    assert source.listings == [("bundle", 1), ("bundle", 2)] + [
        ("archive", i) for i in range(1, 6)
    ]


@pytest.mark.parametrize("bounded", [False, True])
def test_bundle_only_reports_and_original_publication_bounds(bounded):
    source = Source(
        [document(1), document(2, "2018-02-01T12:00:00")],
        [document(-1, "2018-01-31T23:59:59")],
        {
            ("bundle", (-1,)): zipped(
                {f"{i}.cdr.20990101.report.zip": price_report() for i in (1, 2, 3)}
            )
        },
    )
    kwargs = (
        {
            "posted_from": datetime(2018, 1, 1),
            "posted_to": datetime(2018, 1, 1, 23, 59, 59),
        }
        if bounded
        else {}
    )
    rows = run(source, **kwargs, where=lambda row: row.settlementPoint == "AMISTAD_ALL")
    assert len(rows) == (1 if bounded else 3)
    assert source.downloads == [("bundle", [-1])]


def test_bundle_month_optimization_never_loses_selected_archive():
    source = Source(
        [document(1)],
        [document(-1, "2018-02-28T23:59:59")],
        {("archive", (1,)): price_report()},
    )
    assert len(run(source, posted_to=datetime(2018, 1, 31))) == 3
    assert source.downloads == [("archive", [1])]


def test_empty_bounded_archive_listing_does_not_infer_bundle_member_posting_time():
    source = Source([], [document(-1)], {})
    assert run(source, posted_from=datetime(2018, 1, 1)) == []
    assert source.listings == [("archive", 1)] and not source.downloads


def test_unbounded_bundle_only_history_with_no_archive_listing():
    source = Source(
        [],
        [document(-1)],
        {("bundle", (-1,)): zipped({"1.cdr.report.zip": price_report()})},
    )
    assert len(run(source)) == 3


@pytest.mark.parametrize(
    "product,method,fixture,extension,count",
    [
        ("np4_190_cd", "dam_stlmnt_pnt_prices_history", "np4-190-cd.csv", "csv", 3),
        ("np1_346_er", "outages_history", "np1-346-er-history-samples.xlsx", "xlsx", 3),
        ("np4_765_er", "daily_values_history", "np4-765-er-old.pdf", "pdf", 1),
    ],
)
def test_direct_bundle_members_use_inherited_typed_readers(
    product, method, fixture, extension, count
):
    source = Source(
        [document(1)],
        [document(-1)],
        {
            ("bundle", (-1,)): zipped(
                {"1.rpt.report." + extension: (INPUTS / fixture).read_bytes()}
            )
        },
    )
    assert len(run(source, product, method)) == count
    assert source.downloads == [("bundle", [-1])]


def test_mixed_correction_subtypes_and_repeated_rows():
    csv = (INPUTS / "np4-196-m-spp-current.csv").read_bytes()
    # Deliberately repeat every data row within a publication; backfill must
    # only deduplicate document IDs, never row values.
    repeated = csv + b"\n" + csv.split(b"\n", 1)[1]
    report = zipped({"pricecorrection_DAM_SPP_2026.csv": repeated})
    other = zipped({"pricecorrection_DAM_MCPC_2026.csv": csv})
    source = Source(
        [
            document(1, name="pricecorrection_DAM_SPP_first"),
            document(2, name="pricecorrection_DAM_MCPC_other"),
            document(3, name="pricecorrection_DAM_SPP_corrected"),
        ],
        [document(-1)],
        {
            ("bundle", (-1,)): zipped(
                {"1.cdr.report.zip": report, "2.cdr.report.zip": other}
            ),
            ("archive", (3,)): report,
        },
    )
    rows = run(source, "np4_196_m", "dam_price_corrections_spp_history")
    assert len(rows) == 12
    assert source.downloads == [("bundle", [-1]), ("archive", [3])]


@pytest.mark.parametrize(
    "name,content,match",
    [
        ("report.zip", price_report(), "missing original document ID"),
        ("1.cdr.report.zip", b"bad zip", "File is not a zip file"),
        ("1.cdr.report.csv", b"wrong,header\n1,2\n", "unexpected CSV columns"),
    ],
)
def test_unsupported_bundle_identity_or_payload_is_not_silent_success(
    name, content, match
):
    source = Source(
        [document(1)], [document(-1)], {("bundle", (-1,)): zipped({name: content})}
    )
    with pytest.raises(Exception, match=match):
        run(source)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"batch_size": 0},
        {"posted_from": datetime(2018, 2, 1), "posted_to": datetime(2018, 1, 1)},
    ],
)
def test_invalid_selection_fails_before_network(kwargs):
    source = Source([], [], {})
    with pytest.raises(ValueError):
        run(source, **kwargs)
    assert not source.listings and not source.downloads


def disclosure_reports():
    old = zipped(
        {
            "60d_SCED_SMNE_GEN_RES-01-MAY-14.csv": (
                INPUTS / "np3-965-er--60_sced_smne_gen_res-history-samples.csv"
            ).read_bytes()
        }
    )
    current = zipped(
        {
            "60d_ESR_Data_in_SCED-06-SEP-26.csv": (
                INPUTS / "np3-965-er--60d_sced_esr_data-history-current.csv"
            ).read_bytes()
        }
    )
    return old, current


@pytest.mark.parametrize(
    "bundled,batch_size", [(False, 1), (False, 25), (True, 1), (True, 25)]
)
def test_disclosure_backfill_crosses_absent_tables_in_both_sources(bundled, batch_size):
    old, current = disclosure_reports()
    if bundled:
        bundles = [document(-1)]
        payloads = {
            ("bundle", (-1,)): zipped(
                {"1.ext.disclosure.zip": old, "3.ext.disclosure.zip": current}
            )
        }
        remaining = [2, 4]
    else:
        bundles, payloads, remaining = [], {}, [1, 2, 3, 4]
    reports = {1: old, 2: old, 3: current, 4: current}
    limit = min(batch_size, 2)
    batches = [remaining[i : i + limit] for i in range(0, len(remaining), limit)]
    payloads.update(
        {
            ("archive", tuple(batch)): zipped({f"{i}.zip": reports[i] for i in batch})
            for batch in batches
        }
    )
    source = Source([document(i) for i in reports], bundles, payloads)
    rows = run(
        source, "np3_965_er", "_60d_sced_esr_data_history", batch_size=batch_size
    )
    with Client() as client:
        expected = list(client.np3_965_er._60d_sced_esr_data_history.read(current))
    assert rows == expected * 2 and expected
    assert source.downloads == ([("bundle", [-1])] if bundled else []) + [
        ("archive", batch) for batch in batches
    ]


@pytest.mark.parametrize("bundled", [False, True])
def test_named_table_absent_from_all_selected_disclosures_returns_no_rows(bundled):
    old, _ = disclosure_reports()
    kind, doc_id = ("bundle", -1) if bundled else ("archive", 1)
    source = Source(
        [document(1)],
        [document(-1)] if bundled else [],
        {(kind, (doc_id,)): zipped({"1.ext.report.zip": old})},
    )
    assert run(source, "np3_965_er", "_60d_sced_esr_data_history") == []
    assert source.downloads == [(kind, [doc_id])]


@pytest.mark.parametrize(
    "bad",
    [
        zipped({}),
        zipped({"report.xml": b"<report/>"}),
        zipped({"nested.zip": b"corrupt"}),
        zipped({"60d_ESR_Data_in_SCED-06-SEP-26.csv": b"wrong,columns\n1,2\n"}),
    ],
)
def test_missing_table_handling_does_not_swallow_bad_downloads(bad):
    source = Source([document(1)], [], {("archive", (1,)): bad})
    with pytest.raises((ValueError, BadZipFile)):
        run(source, "np3_965_er", "_60d_sced_esr_data_history")


def test_explicit_disclosure_read_and_download_remain_strict():
    old, _ = disclosure_reports()
    source = Source([], [], {("archive", (1,)): old})
    with (
        httpx.Client(transport=httpx.MockTransport(source)) as http,
        Client("u", "p", "k", client=http) as client,
    ):
        history = client.np3_965_er._60d_sced_esr_data_history
        with pytest.raises(ValueError, match="no CSV files matching"):
            list(history.read(old))
        with pytest.raises(ValueError, match="no CSV files matching"):
            list(history.download([1]))


def test_generic_uppercase_csv_reader_does_not_treat_missing_report_as_sparse_table():
    source = Source(
        [document(1)], [], {("archive", (1,)): zipped({"other.csv": b"a,b\n1,2\n"})}
    )
    with pytest.raises(ValueError, match="no CSV files matching"):
        run(source, "np7_535_sg", "path_adders_history")


@pytest.mark.parametrize("bounded", [False, True])
@pytest.mark.parametrize(
    ("market", "product", "delivery_day", "price"),
    [
        ("dam", "np4-190-cd", date(2014, 5, 2), "29.92"),
        ("rt", "np6-905-cd", date(2014, 4, 30), "30.5"),
    ],
)
def test_price_history_export_uses_delivery_dates_and_both_sources(
    tmp_path, market, product, delivery_day, price, bounded
):
    report = zipped({"report.csv": (INPUTS / f"{product}.csv").read_bytes()})
    source = Source(
        [document(1, "2014-05-01T12:00:00"), document(2)],
        [document(-1)],
        {
            ("bundle", (-1,)): zipped({"2.report.zip": report, "3.report.zip": report}),
            ("archive", (1,)): report,
        },
    )

    def handle(request):
        if "b2clogin" not in request.url.host:
            assert product in request.url.path
            if "postDatetimeFrom" in request.url.params:
                assert bounded
                assert request.url.params["postDatetimeFrom"] == "2014-05-01T00:00:00"
                assert request.url.params["postDatetimeTo"] == "2014-05-02T00:00:00"
            else:
                assert "postDatetimeTo" not in request.url.params
        return source(request)

    path = tmp_path / "history" / "prices.jsonl"
    with (
        httpx.Client(transport=httpx.MockTransport(handle)) as http,
        Client("u", "p", "k", client=http) as client,
    ):
        count = export_price_history(
            client,
            market,
            "AMISTAD_ALL",
            path,
            date_from=delivery_day,
            date_to=delivery_day,
            posted_from=datetime(2014, 5, 1) if bounded else None,
            posted_to=datetime(2014, 5, 2) if bounded else None,
        )
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        assert count == len(rows) == (1 if bounded else 3)
        assert all(r["deliveryDate"] == delivery_day.isoformat() for r in rows)
        assert all(r["settlementPoint"] == "AMISTAD_ALL" for r in rows)
        assert all(r["settlementPointPrice"] == price for r in rows)
        assert all(r["DSTFlag"] is False for r in rows)
        assert source.downloads == (
            [("archive", [1])] if bounded else [("bundle", [-1]), ("archive", [1])]
        )
        assert (
            export_price_history(
                client, market, "AMISTAD_ALL", path, date_from=date(2020, 1, 1)
            )
            == 0
        )
        assert path.read_text() == ""


@pytest.mark.parametrize(
    ("start", "end", "message"),
    [
        ("2014-05-02", "2014-05-01", "posted_from must not exceed posted_to"),
        ("2014-05-01T00:00:00Z", "2014-05-02", "without an offset"),
    ],
)
def test_price_history_invalid_publication_bounds_preserve_output(
    tmp_path, start, end, message
):
    path = tmp_path / "prices.jsonl"
    path.write_text("existing export\n")
    with Client() as client, pytest.raises(ValueError, match=message):
        export_price_history(
            client,
            "dam",
            "HB_HOUSTON",
            path,
            posted_from=datetime.fromisoformat(start),
            posted_to=datetime.fromisoformat(end),
        )
    assert path.read_text() == "existing export\n"


@pytest.mark.parametrize("bundled", [False, True])
def test_unbounded_first_rows_do_not_wait_for_later_archive_pages(bundled):
    report = price_report()
    source = Source(
        [document(1), document(1), document(2)],
        [document(-1)] if bundled else [],
        {
            ("bundle", (-1,)): zipped({"1.report.zip": report}),
            ("archive", (1,)): report,
            ("archive", (2,)): report,
        },
    )
    with (
        httpx.Client(transport=httpx.MockTransport(source)) as http,
        Client("u", "p", "k", client=http) as client,
    ):
        history = client.np4_190_cd.dam_stlmnt_pnt_prices_history
        expected = list(history.read(report))
        rows = history.backfill()
        assert next(rows) == expected[0]
        assert source.listings == (
            [("bundle", 1)] if bundled else [("bundle", 1), ("archive", 1)]
        )
        assert list(rows) == expected[1:] + expected
    assert source.downloads == [
        ("bundle", [-1]) if bundled else ("archive", [1]),
        ("archive", [2]),
    ]
