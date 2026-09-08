"""Combined-source backfills preserve publications and avoid repeated downloads."""

# ERCOT publication timestamps are local and carry no UTC offset.
# ruff: noqa: DTZ001

import json
from datetime import datetime
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import httpx
import pytest

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
    assert source.listings == [("archive", i) for i in range(1, 6)] + [
        ("bundle", 1),
        ("bundle", 2),
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
