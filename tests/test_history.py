import csv
import json
from datetime import UTC, date, datetime
from decimal import Decimal
from io import BytesIO, StringIO
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
        assert request.url.params["postDatetimeFrom"] == "2014-05-02T00:00:00"
        assert request.url.params["postDatetimeTo"] == "2014-05-02T23:59:59"
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


@pytest.mark.parametrize(
    "sample",
    json.loads((INPUTS / "additional-evidence.json").read_text()),
    ids=lambda entry: entry["fixture"],
)
def test_additional_price_and_load_archives(sample):
    product, method = sample["endpoint"].split("/")
    with Client() as client:
        reader = getattr(
            getattr(client, product.replace("-", "_")), method + "_history"
        )
        rows = list(
            reader.read(
                zipped(sample["file"], (INPUTS / sample["fixture"]).read_bytes())
            )
        )
    assert len(rows) == min(3, sample["csv_rows"])
    assert rows[0].model_dump(mode="json") == sample["first_row"]


@pytest.mark.parametrize(
    "sample",
    json.loads((INPUTS / "archive-only-evidence.json").read_text()),
    ids=lambda entry: entry["fixture"],
)
def test_archive_only_product_rows(sample):
    product, method = sample["endpoint"].split("/")
    with Client() as client:
        namespace = getattr(client, product.replace("-", "_"))
        assert not hasattr(namespace, method)  # No fictitious API endpoint.
        reader = getattr(namespace, method + "_history")
        rows = list(
            reader.read(
                zipped(sample["file"], (INPUTS / sample["fixture"]).read_bytes())
            )
        )
    assert len(rows) == min(3, sample["csv_rows"])
    assert rows[0].model_dump(mode="json") == sample["first_row"]


def test_resource_identifiers_preserve_leading_zeroes():
    with Client() as client:
        rows = list(
            client.np3_988_er.resources_history.read(
                zipped(
                    "resources.csv",
                    (INPUTS / "np3-988-er-history-samples.csv").read_bytes(),
                )
            )
        )
    assert rows[0].DMEDuns == "0815527087000"
    assert rows[0].RMR is False


def test_meter_load_keeps_decimal_precision_and_unused_intervals():
    with Client() as client:
        rows = list(
            client.np1_300.adjusted_meter_load_history.read(
                zipped("aml.csv", (INPUTS / "np1-300-history-samples.csv").read_bytes())
            )
        )
    assert rows[0].INT096 == Decimal("65.9150589999")
    assert rows[0].INT100 is None
    assert rows[0].startTime == date(2025, 11, 30)
    assert rows[0].LSTime == date(2026, 5, 26)


@pytest.mark.parametrize(
    "sample",
    json.loads((INPUTS / "eia-evidence.json").read_text()),
    ids=lambda entry: entry["fixture"],
)
def test_eia_daily_mixed_hour_types(sample):
    with Client() as client:
        rows = list(
            client.eia_930_er.daily_operations_history.read(
                zipped(sample["file"], (INPUTS / sample["fixture"]).read_bytes())
            )
        )
    assert len(rows) == sample["csv_rows"]
    for row in rows:
        for hour in range(1, 26):
            value = getattr(row, f"HR{hour}")
            if value is not None:
                assert isinstance(
                    value, datetime if row.dataType.startswith("UTC") else Decimal
                )
                if isinstance(value, datetime):
                    assert value.tzinfo is not None
    if "samples" in sample["fixture"]:
        assert rows[0].HR18 == datetime(2015, 2, 9, tzinfo=UTC)
        assert rows[0].postedDate == date(2015, 2, 8)
        assert rows[0].dataDate is None
        assert rows[1].HR1 == Decimal(28241)
    else:
        assert rows[0].HR19 == datetime(2026, 9, 7, tzinfo=UTC)
        assert rows[0].dataDate == date(2026, 9, 6)
        assert rows[0].postedDate is None
        assert rows[1].HR1 == Decimal(64271)
    assert rows[0].HR25 is None


@pytest.mark.parametrize("invalid", [b"2026-09-06T24:01:00.000Z", b"not-a-number"])
def test_eia_invalid_hour_reports_the_csv_member(invalid):
    source = (INPUTS / "eia-930-er-history-current.csv").read_bytes()
    content = source.replace(b"2026-09-06T06:00:00.000Z", invalid)
    with Client() as client, pytest.raises(ValueError, match="eia.csv:2"):
        list(
            client.eia_930_er.daily_operations_history.read(zipped("eia.csv", content))
        )


def test_download_batches_respect_product_limit_and_stay_lazy():
    downloads = []
    data = (INPUTS / "np4-190-cd.csv").read_bytes()

    def handler(request):
        if "b2clogin" in request.url.host:
            return httpx.Response(200, json={"id_token": "test", "expires_in": 3600})
        if request.method == "GET":
            return httpx.Response(
                200,
                json={
                    "emilId": "NP4-190-CD",
                    "name": "DAM",
                    "status": "Active",
                    "reportTypeId": 12331,
                    "downloadLimit": 2,
                },
            )
        ids = json.loads(request.content)["docIds"]
        downloads.append(ids)
        body = BytesIO()
        with ZipFile(body, "w") as archive:
            for doc_id in ids:
                archive.writestr(f"{doc_id}.zip", zipped("prices.csv", data))
        return httpx.Response(200, content=body.getvalue())

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as http,
        Client("u", "p", "k", client=http) as client,
    ):
        rows = client.np4_190_cd.dam_stlmnt_pnt_prices_history.download(
            iter([1, 2, 3, 4, 5]), batch_size=3
        )
        assert downloads == []
        first = next(rows)
        assert downloads == [[1, 2]]
        assert len([first, *rows]) == 15
    assert downloads == [[1, 2], [3, 4], [5]]


def test_empty_batch_needs_no_credentials():
    with Client() as client:
        assert (
            list(
                client.np4_190_cd.dam_stlmnt_pnt_prices_history.download(
                    [], batch_size=100
                )
            )
            == []
        )


@pytest.mark.parametrize("size", [0, -1])
def test_invalid_batch_size_fails_before_retrieval(size):
    with Client() as client, pytest.raises(ValueError, match="batch_size"):
        list(client.np4_190_cd.dam_stlmnt_pnt_prices_history.rows(batch_size=size))


def test_intermediate_disclosure_layout_accepts_known_optional_columns():
    source = list(
        csv.DictReader(
            StringIO((INPUTS / "60_dam_load_res_data-history-samples.csv").read_text())
        )
    )
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=[*source[0], "ECRSSD Awarded"])
    writer.writeheader()
    writer.writerow({**source[2], "ECRSSD Awarded": "2.5"})
    with Client() as client:
        rows = list(
            client.np3_966_er._60_dam_load_res_data_history.read(
                zipped(
                    "60d_DAM_Load_Resource_Data-intermediate.csv",
                    output.getvalue().encode(),
                )
            )
        )
    assert rows[0].RRSAwarded == Decimal("1.5")
    assert rows[0].ECRSSDAwarded == Decimal("2.5")
    assert rows[0].RRSPFRAwarded is None


def test_missing_shared_column_still_fails():
    content = (INPUTS / "np4-190-cd.csv").read_bytes()
    lines = content.decode().splitlines()
    content = "\n".join(line.split(",", 1)[1] for line in lines).encode()
    with Client() as client, pytest.raises(ValueError, match="deliveryDate"):
        list(
            client.np4_190_cd.dam_stlmnt_pnt_prices_history.read(
                zipped("missing.csv", content)
            )
        )


def test_duplicate_aliases_do_not_overwrite_a_source_cell():
    content = (INPUTS / "eia-930-er-history-current.csv").read_bytes()
    content = content.replace(b'"Product_Name"', b'"Product_Name","Survey Name"', 1)
    with Client() as client, pytest.raises(ValueError, match="duplicate"):
        list(
            client.eia_930_er.daily_operations_history.read(
                zipped("duplicate.csv", content)
            )
        )


@pytest.mark.parametrize(
    "sample",
    json.loads((INPUTS / "next-evidence.json").read_text()),
    ids=lambda entry: entry["fixture"],
)
def test_next_historical_report_formats(sample):
    product, method = sample["endpoint"].split("/")
    with Client() as client:
        reader = getattr(
            getattr(client, product.replace("-", "_")), method + "_history"
        )
        rows = list(
            reader.read(
                zipped(sample["file"], (INPUTS / sample["fixture"]).read_bytes())
            )
        )
    assert len(rows) == min(3, sample["csv_rows"])
    assert rows[0].model_dump(mode="json") == sample["first_row"]


def test_whitespace_trailer_is_not_a_data_row():
    source = (INPUTS / "np4-192-cd-history-samples.csv").read_bytes()
    with Client() as client:
        rows = list(
            client.np4_192_cd.dam_total_energy_purchased_history.read(
                zipped("energy.csv", source + b"  \n")
            )
        )
    assert len(rows) == 3


def test_wind_layout_keeps_old_timestamp_and_combined_region():
    with Client() as client:
        old = next(
            client.np4_732_cd.wpp_hrly_avrg_actl_fcast_history.read(
                zipped(
                    "wind.csv", (INPUTS / "np4-732-cd-history-samples.csv").read_bytes()
                )
            )
        )
        recent = next(
            client.np4_732_cd.wpp_hrly_avrg_actl_fcast_history.read(
                zipped(
                    "wind.csv", (INPUTS / "np4-732-cd-history-current.csv").read_bytes()
                )
            )
        )
    assert old.hourEndingTimestamp.isoformat() == "2014-04-29T01:00:00"
    assert old.hourEnding is None
    assert old.actualWestNorth == Decimal("3262.13")
    assert old.genLoadZoneWest is None
    assert recent.hourEnding == 11
    assert recent.hourEndingTimestamp is None
    assert recent.postedDatetime is None


def test_ambiguous_header_mapping_is_rejected():
    source = (INPUTS / "np4-732-cd-history-samples.csv").read_bytes()
    source = source.replace(b"HOUR_ENDING,", b"HOUR_ENDING,DELIVERY_DATE,", 1)
    with Client() as client, pytest.raises(ValueError, match="ambiguous"):
        list(
            client.np4_732_cd.wpp_hrly_avrg_actl_fcast_history.read(
                zipped("wind.csv", source)
            )
        )


@pytest.mark.parametrize(
    "sample",
    json.loads((INPUTS / "renewables-evidence.json").read_text()),
    ids=lambda entry: entry["fixture"],
)
def test_renewable_and_demand_historical_formats(sample):
    product, method = sample["endpoint"].split("/")
    with Client() as client:
        reader = getattr(
            getattr(client, product.replace("-", "_")), method + "_history"
        )
        rows = list(
            reader.read(
                zipped(sample["file"], (INPUTS / sample["fixture"]).read_bytes())
            )
        )
    assert len(rows) == min(3, sample["csv_rows"])
    assert rows[0].model_dump(mode="json") == sample["first_row"]


def test_legacy_wind_region_and_solar_timestamp_are_preserved():
    with Client() as client:
        wind = next(
            client.np4_733_cd.wpp_actual_5min_avg_values_history.read(
                zipped(
                    "wind.csv", (INPUTS / "np4-733-cd-history-samples.csv").read_bytes()
                )
            )
        )
        assert wind.LZWestNorth == Decimal("645.12")
        assert wind.LZWest is None and wind.LZNorth is None
        solar = next(
            client.np4_737_cd.spp_hrly_avrg_actl_fcast_history.read(
                zipped(
                    "solar.csv",
                    (INPUTS / "np4-737-cd-history-samples.csv").read_bytes(),
                )
            )
        )
        assert solar.hourEndingTimestamp.isoformat() == "2016-02-08T00:00:00"
        assert solar.deliveryDate is None and solar.hourEnding is None
        assert solar.postedDatetime is None


@pytest.mark.parametrize(
    "sample",
    json.loads((INPUTS / "operations-evidence.json").read_text()),
    ids=lambda entry: entry["fixture"],
)
def test_operation_historical_formats(sample):
    product, method = sample["endpoint"].split("/")
    with Client() as client:
        reader = getattr(
            getattr(client, product.replace("-", "_")), method + "_history"
        )
        rows = list(
            reader.read(
                zipped(sample["file"], (INPUTS / sample["fixture"]).read_bytes())
            )
        )
    assert len(rows) == min(3, sample["csv_rows"])
    assert rows[0].model_dump(mode="json") == sample["first_row"]


def test_legacy_lambda_and_ordc_fields_remain_distinct():
    with Client() as client:
        price = next(
            client.np6_322_cd.sced_system_lambda_history.read(
                zipped(
                    "lambda.csv",
                    (INPUTS / "np6-322-cd-history-samples.csv").read_bytes(),
                )
            )
        )
        assert price.systemLambda == Decimal("28.8797130584717")
        assert price.cappedSystemLambda is None
        assert price.uncappedSystemLambda is None
        adder = next(
            client.np6_323_cd.rt_price_adder_sced_history.read(
                zipped(
                    "adder.csv",
                    (INPUTS / "np6-323-cd-history-samples.csv").read_bytes(),
                )
            )
        )
        assert adder.RTORPA == Decimal("0.0033")
        assert adder.RTOFFPA == Decimal("0.0005")
        assert adder.RTRDPA is None


@pytest.mark.parametrize(
    "sample",
    json.loads((INPUTS / "forecasts-evidence.json").read_text()),
    ids=lambda entry: entry["fixture"],
)
def test_forecast_historical_formats(sample):
    product, method = sample["endpoint"].split("/")
    with Client() as client:
        reader = getattr(
            getattr(client, product.replace("-", "_")),
            ("_" if method[0].isdigit() else "") + method + "_history",
        )
        rows = list(
            reader.read(
                zipped(sample["file"], (INPUTS / sample["fixture"]).read_bytes())
            )
        )
    assert len(rows) == min(3, sample["csv_rows"])
    assert rows[0].model_dump(mode="json") == sample["first_row"]


def test_forecast_publication_time_is_not_inferred_from_delivery():
    with Client() as client:
        forecast = next(
            client.np3_560_cd._7d_load_fcast_by_fzn_history.read(
                zipped(
                    "forecast.csv",
                    (INPUTS / "np3-560-cd-history-current.csv").read_bytes(),
                )
            )
        )
        assert forecast.postedDatetime is None
        assert forecast.hourEnding == "1:00"
        assert forecast.north == Decimal("22122.619443518067837")
        interval = next(
            client.np3_562_cd.ih_load_fcast_by_wzn_history.read(
                zipped(
                    "interval.csv",
                    (INPUTS / "np3-562-cd-history-current.csv").read_bytes(),
                )
            )
        )
        assert interval.model == "A6"
        assert interval.inUseFlag is False
        assert interval.postedDatetime is None


@pytest.mark.parametrize(
    "sample",
    json.loads((INPUTS / "adequacy-evidence.json").read_text()),
    ids=lambda entry: entry["fixture"],
)
def test_adequacy_historical_formats(sample):
    product, method = sample["endpoint"].split("/")
    with Client() as client:
        reader = getattr(
            getattr(client, product.replace("-", "_")),
            ("_" if method[0].isdigit() else "") + method + "_history",
        )
        rows = list(
            reader.read(
                zipped(sample["file"], (INPUTS / sample["fixture"]).read_bytes())
            )
        )
    assert len(rows) == min(3, sample["csv_rows"])
    assert rows[0].model_dump(mode="json") == sample["first_row"]


def test_legacy_outage_and_ruc_totals_are_not_assigned_to_regions():
    with Client() as client:
        outage = next(
            client.np3_233_cd.hourly_res_outage_cap_history.read(
                zipped(
                    "outages.csv",
                    (INPUTS / "np3-233-cd-history-samples.csv").read_bytes(),
                )
            )
        )
        assert outage.totalResourceMW == 18542
        assert outage.totalIRRMW == 685
        assert outage.totalResourceMWZoneSouth is None
        ruc = next(
            client.np3_764_cd.hrly_ruc_online_sced_offline_cop_history.read(
                zipped(
                    "ruc.csv", (INPUTS / "np3-764-cd-history-samples.csv").read_bytes()
                )
            )
        )
        assert ruc.sumSCEDTotal == Decimal(0)
        assert ruc.sumSCEDSouth is None
        assert ruc.RUCTimestamp.isoformat() == "2018-10-25T17:03:01"


@pytest.mark.parametrize(
    "sample",
    json.loads((INPUTS / "summaries-evidence.json").read_text()),
    ids=lambda entry: entry["fixture"],
)
def test_summary_historical_formats(sample):
    product, method = sample["endpoint"].split("/")
    with Client() as client:
        reader = getattr(
            getattr(client, product.replace("-", "_")),
            ("_" if method[0].isdigit() else "") + method + "_history",
        )
        rows = list(
            reader.read(
                zipped(sample["file"], (INPUTS / sample["fixture"]).read_bytes())
            )
        )
    assert len(rows) == min(3, sample["csv_rows"])
    assert rows[0].model_dump(mode="json") == sample["first_row"]


def test_legacy_rrs_and_offer_cap_fields_are_preserved():
    with Client() as client:
        offers = next(
            client.np4_179_cd.total_as_service_offers_history.read(
                zipped(
                    "offers.csv",
                    (INPUTS / "np4-179-cd-history-samples.csv").read_bytes(),
                )
            )
        )
        assert offers.RRS == Decimal(4378)
        assert offers.RRSPFR is None
        cap = next(
            client.np4_791_cd.da_sw_offer_caps_history.read(
                zipped(
                    "caps.csv", (INPUTS / "np4-791-cd-history-samples.csv").read_bytes()
                )
            )
        )
        assert cap.SWCAP == Decimal(5000)
        assert cap.DASWCAP is None and cap.RTSWCAP is None


def test_nonempty_extra_csv_cell_is_not_discarded():
    source = (INPUTS / "np4-791-cd-history-samples.csv").read_bytes()
    source = source.replace(b"AS,5000,", b"AS,5000,unexpected")
    with Client() as client, pytest.raises(ValueError, match="wrong number of cells"):
        list(
            client.np4_791_cd.da_sw_offer_caps_history.read(zipped("caps.csv", source))
        )


@pytest.mark.parametrize(
    "sample",
    json.loads((INPUTS / "regional-evidence.json").read_text()),
    ids=lambda entry: entry["fixture"],
)
def test_regional_forecast_historical_formats(sample):
    product, method = sample["endpoint"].split("/")
    with Client() as client:
        reader = getattr(
            getattr(client, product.replace("-", "_")),
            ("_" if method[0].isdigit() else "") + method + "_history",
        )
        rows = list(
            reader.read(
                zipped(sample["file"], (INPUTS / sample["fixture"]).read_bytes())
            )
        )
    assert len(rows) == min(3, sample["csv_rows"])
    assert rows[0].model_dump(mode="json") == sample["first_row"]


def test_intra_hour_forecasts_keep_model_alternatives():
    with Client() as client:
        forecasts = list(
            client.np4_752_cd.ih_solar_fcast_geo_history.read(
                zipped(
                    "solar.csv",
                    (INPUTS / "np4-752-cd-history-samples.csv").read_bytes(),
                )
            )
        )
    assert [row.model for row in forecasts] == ["A", "B", "C"]
    assert [row.inUseFlag for row in forecasts] == [False, True, False]
    assert len({(row.region, row.intervalEnding) for row in forecasts}) == 1
    assert forecasts[1].value == Decimal("4665.2")
    assert all(row.postedDatetime is None for row in forecasts)


@pytest.mark.parametrize(
    "sample",
    json.loads((INPUTS / "deployment-evidence.json").read_text()),
    ids=lambda entry: entry["fixture"],
)
def test_deployment_factor_historical_formats(sample):
    product, method = sample["endpoint"].split("/")
    with Client() as client:
        reader = getattr(
            getattr(client, product.replace("-", "_")),
            ("_" if method[0].isdigit() else "") + method + "_history",
        )
        rows = list(
            reader.read(
                zipped(sample["file"], (INPUTS / sample["fixture"]).read_bytes())
            )
        )
    assert len(rows) == min(3, sample["csv_rows"])
    assert rows[0].model_dump(mode="json") == sample["first_row"]


def test_deployment_factors_preserve_ruc_time_and_service_types():
    with Client() as client:
        factors = list(
            client.np5_527_cd.druc_as_deploy_factors_history.read(
                zipped(
                    "factors.csv",
                    (INPUTS / "np5-527-cd-history-samples.csv").read_bytes(),
                )
            )
        )
    assert [row.ASType for row in factors] == ["ECRS", "NSPIN", "REGDN"]
    assert [row.ASDeploymentFactors for row in factors] == [
        Decimal("0.04"),
        Decimal("0.15"),
        Decimal("0.25"),
    ]
    assert factors[0].RUCTimestamp.isoformat() == "2025-12-05T14:33:01"
    assert factors[0].deliveryDate == date(2025, 12, 6)
    assert factors[0].deliveryHour == "01:00"
