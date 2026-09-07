import json
from datetime import date, datetime
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import httpx
import pytest

from tinyercot import Client

INPUTS = Path(__file__).resolve().parents[1] / "tools" / "inputs" / "history"


def zipped(name, data):
    output = BytesIO()
    with ZipFile(output, "w") as archive:
        archive.writestr(name, data)
    return output.getvalue()


@pytest.mark.parametrize(
    "product,method,date_field,day,value_field,value",
    [
        (
            "np4-190-cd",
            "dam_stlmnt_pnt_prices",
            "deliveryDate",
            date(2014, 5, 2),
            "settlementPointPrice",
            Decimal("29.92"),
        ),
        (
            "np6-905-cd",
            "spp_node_zone_hub",
            "deliveryDate",
            date(2014, 4, 30),
            "settlementPointPrice",
            Decimal("30.5"),
        ),
        (
            "np4-188-cd",
            "dam_clear_price_for_cap",
            "deliveryDate",
            date(2014, 5, 2),
            "MCPC",
            Decimal("7.25"),
        ),
        (
            "np6-345-cd",
            "act_sys_load_by_wzn",
            "operatingDay",
            date(2014, 4, 30),
            "total",
            Decimal("27934.84"),
        ),
    ],
)
def test_captured_oldest_csv_in_nested_download(
    product, method, date_field, day, value_field, value
):
    data = zipped(
        "download.zip", zipped("report.csv", (INPUTS / f"{product}.csv").read_bytes())
    )
    with Client() as client:
        history = getattr(
            getattr(client, product.replace("-", "_")), method + "_history"
        )
        rows = list(history.read(data))
    assert len(rows) == 3
    assert getattr(rows[0], date_field) == day
    assert getattr(rows[0], value_field) == value
    assert isinstance(getattr(rows[0], value_field), Decimal)
    assert rows[0].DSTFlag is False


def test_history_query_paginates_and_filters_publications_and_rows():
    csv = (INPUTS / "np4-190-cd.csv").read_bytes()
    calls = []

    def handler(request):
        if "b2clogin" in request.url.host:
            return httpx.Response(200, json={"id_token": "test", "expires_in": 3600})
        if request.method == "POST":
            assert request.content == b'{"docIds":[2]}'
            return httpx.Response(200, content=zipped("report.csv", csv))
        page = int(request.url.params["page"])
        calls.append(page)
        return httpx.Response(
            200,
            json={
                "_meta": {"currentPage": page, "totalPages": 3},
                "product": {
                    "emilId": "NP4-190-CD",
                    "name": "DAM",
                    "reportTypeId": 12331,
                },
                "archives": [
                    {
                        "docId": page,
                        "friendlyName": "DAM",
                        "postDatetime": f"2014-05-0{4 - page}T12:00:00",
                    }
                ],
            },
        )

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as http,
        Client("u", "p", "k", client=http) as client,
    ):
        rows = list(
            client.np4_190_cd.dam_stlmnt_pnt_prices_history.rows(
                posted_from=datetime(2014, 5, 2),  # noqa: DTZ001 - ERCOT publication time
                posted_to=datetime(2014, 5, 2, 23, 59, 59),  # noqa: DTZ001 - ERCOT publication time
                where=lambda row: row.settlementPoint == "AMISTAD_ALL",
            )
        )
    assert calls == [1, 2, 3]
    assert len(rows) == 1
    assert rows[0].settlementPointPrice == Decimal("29.92")


@pytest.mark.parametrize(
    "content",
    [
        b"wrong,header\n1,2\n",
        (INPUTS / "np4-190-cd.csv").read_bytes().replace(b"29.92", b"invalid"),
    ],
)
def test_bad_archive_reports_file_and_does_not_silently_drop_rows(content):
    with Client() as client, pytest.raises(ValueError, match="report.csv"):
        list(
            client.np4_190_cd.dam_stlmnt_pnt_prices_history.read(
                zipped("report.csv", content)
            )
        )


def test_download_without_csv_is_not_an_empty_success():
    with Client() as client, pytest.raises(ValueError, match="no CSV"):
        list(
            client.np4_190_cd.dam_stlmnt_pnt_prices_history.read(
                zipped("report.xml", b"<report/>")
            )
        )


@pytest.mark.parametrize(
    "sample",
    [
        entry
        for entry in json.loads((INPUTS / "evidence.json").read_text())
        if entry["sample"] == "history-current"
    ],
    ids=lambda entry: entry["endpoint"],
)
def test_recent_archive_format(sample):
    product, method = sample["endpoint"].split("/")
    with Client() as client:
        reader = getattr(
            getattr(client, product.replace("-", "_")), method + "_history"
        )
        rows = list(
            reader.read(
                zipped("recent.csv", (INPUTS / f"{product}-recent.csv").read_bytes())
            )
        )
    assert len(rows) == 3
    assert rows[0].model_dump(mode="json") == sample["first_row"]


@pytest.mark.parametrize(
    "sample",
    json.loads((INPUTS / "disclosure-evidence.json").read_text()),
    ids=lambda entry: entry["fixture"],
)
def test_disclosure_tables_and_schema_epochs(sample):
    method = sample["endpoint"].split("/")[1]
    data = BytesIO()
    with ZipFile(data, "w") as archive:
        archive.writestr("unrelated.csv", b"other,columns\n1,2\n")
        archive.writestr(sample["file"], (INPUTS / sample["fixture"]).read_bytes())
    with Client() as client:
        reader = getattr(client.np3_966_er, "_" + method + "_history")
        rows = list(reader.read(zipped("disclosure.zip", data.getvalue())))
    assert len(rows) == min(3, sample["csv_rows"])
    assert rows[0].model_dump(mode="json") == sample["first_row"]


def test_legacy_rrs_is_preserved_separately_from_new_categories():
    sample = INPUTS / "60_dam_load_res_data-history-samples.csv"
    with Client() as client:
        rows = list(
            client.np3_966_er._60_dam_load_res_data_history.read(
                zipped("60d_DAM_Load_Resource_Data-01-MAY-14.csv", sample.read_bytes())
            )
        )
    assert rows[2].RRSAwarded == Decimal("1.5")
    assert rows[2].RRSPFRAwarded is None
