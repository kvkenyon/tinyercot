"""Keep archive publication identity with lazily decoded market rows."""

import json
from datetime import date, datetime
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import httpx
import pytest

from tinyercot import Client, Publication

INPUTS = Path(__file__).resolve().parents[1] / "tools/inputs/history"


def zipped(name, data):
    out = BytesIO()
    with ZipFile(out, "w") as z:
        z.writestr(name, data)
    return out.getvalue()


def test_publications_are_lazy_and_keep_identity_when_consumed_out_of_order():
    downloads = []

    def handler(request):
        if "b2clogin" in request.url.host:
            return httpx.Response(200, json={"id_token": "test", "expires_in": 3600})
        if request.method == "POST":
            downloads.extend(json.loads(request.content)["docIds"])
            return httpx.Response(
                200,
                content=zipped(
                    "forecast.csv",
                    (INPUTS / "np3-561-cd-history-samples.csv").read_bytes(),
                ),
            )
        assert request.url.params["postDatetimeFrom"] == "2014-05-01T00:00:00"
        page = int(request.url.params["page"])
        return httpx.Response(
            200,
            json={
                "_meta": {"currentPage": page, "totalPages": 2},
                "product": {
                    "emilId": "NP3-561-CD",
                    "name": "Forecast",
                    "reportTypeId": 1,
                },
                "archives": [
                    {
                        "docId": page,
                        "friendlyName": "forecast",
                        "postDatetime": f"2014-05-01T0{page}:01:23",
                    }
                ],
            },
        )

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as http,
        Client("u", "p", "k", client=http) as client,
    ):
        reports = list(
            client.np3_561_cd._7d_load_fcast_by_wzn_history.publications(
                posted_from=datetime(2014, 5, 1, tzinfo=None)  # noqa: DTZ001
            )
        )
        assert len(reports) == 2 and not downloads
        assert all(isinstance(p, Publication) and p.kind == "archive" for p in reports)
        second = list(reports[1].rows)
        first = list(reports[0].rows)
    assert downloads == [2, 1]
    assert reports[0].document.docId == 1 and reports[1].document.docId == 2
    assert reports[0].document.postDatetime != reports[1].document.postDatetime
    assert first == second and first  # identical rows retain distinct publications
    assert all(
        r.postedDatetime is None for r in first
    )  # no invented embedded timestamp


@pytest.mark.parametrize(
    "product,method,fixture,extension,count",
    [
        ("np4_190_cd", "dam_stlmnt_pnt_prices_history", "np4-190-cd.csv", "csv", 3),
        ("np1_346_er", "outages_history", "np1-346-er-history-samples.xlsx", "xlsx", 3),
        ("np4_765_er", "daily_values_history", "np4-765-er-old.pdf", "pdf", 1),
    ],
)
def test_bundle_metadata_stays_distinct_and_all_reader_formats_work(
    product, method, fixture, extension, count
):
    def handler(request):
        if "b2clogin" in request.url.host:
            return httpx.Response(200, json={"id_token": "test", "expires_in": 3600})
        assert "/bundle/" in request.url.path
        if request.method == "POST":
            assert json.loads(request.content)["docIds"] == [-1]
            return httpx.Response(
                200,
                content=zipped(
                    "inner.zip",
                    zipped("report." + extension, (INPUTS / fixture).read_bytes()),
                ),
            )
        return httpx.Response(
            200,
            json={
                "_meta": {"currentPage": 1, "totalPages": 1},
                "product": {"emilId": product, "name": "Report", "reportTypeId": 1},
                "bundles": [
                    {
                        "docId": -1,
                        "friendlyName": "monthly",
                        "postDatetime": "2026-08-31T23:59:59",
                    }
                ],
            },
        )

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as http,
        Client("u", "p", "k", client=http) as client,
    ):
        report = next(
            getattr(getattr(client, product), method).publications(kind="bundle")
        )
        rows = list(report.rows)
    assert report.kind == "bundle" and report.document.postDatetime.date() == date(
        2026, 8, 31
    )
    assert len(rows) == count
    if extension == "csv":
        assert rows[0].deliveryDate == date(2014, 5, 2)


def test_correction_publications_filter_before_download():
    names = [
        "pricecorrection_DAM_SPP_other",
        "pricecorrection_DAM_EBLMP_first",
        "PRICECORRECTION_DAM_EBLMP_SECOND",
    ]

    def handler(request):
        if "b2clogin" in request.url.host:
            return httpx.Response(200, json={"id_token": "test", "expires_in": 3600})
        assert request.method == "GET"  # listing alone must not fetch any payload
        return httpx.Response(
            200,
            json={
                "_meta": {"currentPage": 1, "totalPages": 1},
                "product": {
                    "emilId": "NP4-196-M",
                    "name": "Corrections",
                    "reportTypeId": 1,
                },
                "archives": [
                    {
                        "docId": i,
                        "friendlyName": name,
                        "postDatetime": "2025-12-08T22:41:53",
                    }
                    for i, name in enumerate(names)
                ],
            },
        )

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as http,
        Client("u", "p", "k", client=http) as client,
    ):
        reports = list(
            client.np4_196_m.dam_price_corrections_eblmp_history.publications()
        )
    assert [r.document.docId for r in reports] == [1, 2]
