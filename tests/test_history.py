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


@pytest.mark.parametrize(
    "sample",
    json.loads((INPUTS / "curves-evidence.json").read_text()),
    ids=lambda entry: entry["fixture"],
)
def test_demand_curve_historical_formats(sample):
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


def test_demand_curve_points_keep_quantities_and_execution_time():
    with Client() as client:
        points = list(
            client.np4_214_cd.druc_as_demand_curves_history.read(
                zipped(
                    "curves.csv",
                    (INPUTS / "np4-214-cd-history-samples.csv").read_bytes(),
                )
            )
        )
    assert [row.demandCurvePoint for row in points] == [
        Decimal(1),
        Decimal(2),
        Decimal(3),
    ]
    assert [row.quantity for row in points] == [Decimal(0), Decimal(40), Decimal(41)]
    assert [row.price for row in points] == [
        Decimal(5050),
        Decimal(5050),
        Decimal("3353.06"),
    ]
    assert points[0].ASType == "ECRS"
    assert points[0].RUCTimestamp.isoformat() == "2026-02-27T14:33:01"
    assert points[0].deliveryDate == date(2026, 2, 28)


@pytest.mark.parametrize(
    "sample",
    json.loads((INPUTS / "clearing-evidence.json").read_text()),
    ids=lambda entry: entry["fixture"],
)
def test_clearing_historical_formats(sample):
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


def test_legacy_mcpc_and_indicative_timestamps_are_preserved():
    with Client() as client:
        price = next(
            client.np6_332_cd.rt_clear_price_cap_sced_history.read(
                zipped(
                    "prices.csv",
                    (INPUTS / "np6-332-cd-history-samples.csv").read_bytes(),
                )
            )
        )
        assert price.MCPC == Decimal("0.47")
        assert price.cappedMCPC is None and price.uncappedMCPC is None
        indicative = next(
            client.np6_329_cd.rtd_ind_mcpc_history.read(
                zipped(
                    "indicative.csv",
                    (INPUTS / "np6-329-cd-history-samples.csv").read_bytes(),
                )
            )
        )
        assert indicative.RTDTimestamp.isoformat() == "2025-12-05T00:00:03"
        assert indicative.intervalEnding.isoformat() == "2025-12-05T00:05:00"
        assert indicative.REGUP == Decimal("2.96")


@pytest.mark.parametrize(
    "sample",
    json.loads((INPUTS / "transmission-evidence.json").read_text()),
    ids=lambda entry: entry["fixture"],
)
def test_transmission_historical_formats(sample):
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


def test_rtd_history_keeps_forecast_time_and_legacy_point_types():
    with Client() as client:
        prices = list(
            client.np6_970_cd.rtd_lmp_node_zone_hub_history.read(
                zipped(
                    "rtd.csv", (INPUTS / "np6-970-cd-history-samples.csv").read_bytes()
                )
            )
        )
    assert prices[0].RTDTimestamp.isoformat() == "2014-05-01T00:00:01"
    assert prices[0].intervalEnding.isoformat() == "2014-05-01T00:05:00"
    assert prices[0].settlementPoint == "AMISTAD_ALL"
    assert prices[0].LMP == Decimal("28.71")
    assert prices[1].settlementPointType == "LCCRN"


@pytest.mark.parametrize(
    "sample",
    json.loads((INPUTS / "mappings-evidence.json").read_text()),
    ids=lambda entry: entry["fixture"],
)
def test_mapping_historical_formats(sample):
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


def test_load_distribution_ids_and_decimal_precision_are_preserved():
    with Client() as client:
        rows = list(
            client.np4_159_cd.load_distribution_factors_history.read(
                zipped(
                    "ldf.csv", (INPUTS / "np4-159-cd-history-samples.csv").read_bytes()
                )
            )
        )
    assert rows[0].loadId == "050"
    assert rows[0].MRIDLoad == "{356A1C81-051D-432E-A1E7-2B63E50840C3}"
    assert rows[0].MVARDistributionFactor == Decimal("0.603000342845917")
    assert rows[2].distributionFactor == Decimal("0.820144251")
    assert rows[0].postedDatetime is None


@pytest.mark.parametrize(
    "sample",
    json.loads((INPUTS / "corrections-evidence.json").read_text()),
    ids=lambda entry: entry["fixture"],
)
def test_correction_historical_formats(sample):
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


def test_correction_rows_select_documents_across_mixed_pages():
    source = (INPUTS / "np4-196-m-eblmp-current.csv").read_bytes()
    downloads = []
    pages = []

    def handler(request):
        if "b2clogin" in request.url.host:
            return httpx.Response(200, json={"id_token": "test", "expires_in": 3600})
        if request.method == "POST":
            downloads.extend(json.loads(request.content)["docIds"])
            return httpx.Response(
                200, content=zipped("pricecorrection_DAM_EBLMP_example.csv", source)
            )
        page = int(request.url.params["page"])
        pages.append(page)
        names = [
            "pricecorrection_DAM_SPP_other",
            "pricecorrection_DAM_EBLMP_first",
            "PRICECORRECTION_DAM_EBLMP_SECOND",
        ]
        return httpx.Response(
            200,
            json={
                "_meta": {"currentPage": page, "totalPages": 3},
                "product": {
                    "emilId": "NP4-196-M",
                    "name": "Corrections",
                    "reportTypeId": 13044,
                },
                "archives": [
                    {
                        "docId": page,
                        "friendlyName": names[page - 1],
                        "postDatetime": "2025-12-08T22:41:53",
                    }
                ],
            },
        )

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as http,
        Client("u", "p", "k", client=http) as client,
    ):
        rows = list(client.np4_196_m.dam_price_corrections_eblmp_history.rows())
    assert pages == [1, 2, 3]
    assert downloads == [2, 3]
    assert len(rows) == 6
    assert rows[0].electricalBus == "0022"
    assert rows[0].LMPOriginal == Decimal("45.3")
    assert rows[0].LMPCorrected == Decimal("45.31")
    assert rows[0].priceCorrectionTime.isoformat() == "2025-12-09T10:00:00"


@pytest.mark.parametrize(
    "sample",
    json.loads((INPUTS / "sog-evidence.json").read_text()),
    ids=lambda entry: entry["fixture"],
)
def test_sog_weather_historical_formats(sample):
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


def test_sog_history_keeps_long_meter_ids_and_legacy_adders():
    with Client() as client:
        prices = list(
            client.np6_327_cd.lmp_sog_price_adders_history.read(
                zipped(
                    "sog.csv", (INPUTS / "np6-327-cd-history-samples.csv").read_bytes()
                )
            )
        )
    assert prices[1].meterName == "1008901022901448240117"
    assert prices[1].meterLMP == Decimal("17.85")
    assert prices[1].RTORPA == Decimal(0)
    assert prices[1].RTORDPA == Decimal(0)
    assert prices[1].RTRDPA is None
    assert prices[1].SCEDTimestamp.isoformat() == "2022-02-11T00:05:20"


@pytest.mark.parametrize(
    "sample",
    json.loads((INPUTS / "offers-evidence.json").read_text()),
    ids=lambda entry: entry["fixture"],
)
def test_aggregated_offer_historical_formats(sample):
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


def test_aggregated_offers_keep_legacy_service_codes_and_source_order():
    with Client() as client:
        offers = list(
            client.np4_19_cd.dam_agg_as_offer_curve_history.read(
                zipped(
                    "offers.csv",
                    (INPUTS / "np4-19-cd-history-samples.csv").read_bytes(),
                )
            )
        )
    assert all(row.ancillaryType == "OFFNS" for row in offers)
    assert [row.price for row in offers] == [
        Decimal(400),
        Decimal("0.77"),
        Decimal("0.01"),
    ]
    assert [row.quantity for row in offers] == [
        Decimal(1757),
        Decimal("533.8"),
        Decimal(193),
    ]
    assert offers[0].deliveryDate == date(2014, 3, 13)


@pytest.mark.parametrize(
    "sample",
    json.loads((INPUTS / "highest-evidence.json").read_text()),
    ids=lambda entry: entry["fixture"],
)
def test_highest_price_historical_formats(sample):
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
    if rows:
        assert rows[0].model_dump(mode="json") == sample["first_row"]


def test_highest_price_history_preserves_legacy_fields():
    with Client() as client:
        old = next(
            client.np3_916_ex._3d_highest_price_offer_sced_history.read(
                zipped(
                    "old.csv", (INPUTS / "np3-916-ex-history-samples.csv").read_bytes()
                )
            )
        )
        dam = next(
            client.np3_915_ex._3d_dam_high_as_offers_history.read(
                zipped(
                    "dam.csv", (INPUTS / "np3-915-ex-history-samples.csv").read_bytes()
                )
            )
        )
        current = list(
            client.np3_914_ex._3d_sced_high_as_offers_history.read(
                zipped(
                    "current.csv",
                    (INPUTS / "np3-914-ex-history-current.csv").read_bytes(),
                )
            )
        )
    assert old.batchId == "5379175"
    assert old.LMP == Decimal("238.545806884766")
    assert old.proxyExtension == "Yes"
    assert old.penaltyFlag == "No"
    assert old.qseName is None
    assert old.dmeName is None
    assert dam.deliveryDate == date(2014, 3, 9)
    assert dam.quantity == Decimal(8)
    assert dam.resourceName == "HENNE_LD1"
    assert dam.qseName is None
    assert len(current) == 3
    assert current[0] == current[1] == current[2]


@pytest.mark.parametrize(
    "sample",
    json.loads((INPUTS / "disclosure-curves-evidence.json").read_text()),
    ids=lambda entry: entry["fixture"],
)
def test_disclosure_curve_historical_formats(sample):
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
    if rows:
        assert rows[0].model_dump(mode="json") == sample["first_row"]


def test_disclosure_curve_readers_select_their_own_tables():
    samples = json.loads((INPUTS / "disclosure-curves-evidence.json").read_text())
    content = BytesIO()
    with ZipFile(content, "w") as archive:
        for sample in samples:
            if "history-samples" in sample["fixture"]:
                archive.writestr(
                    sample["file"], (INPUTS / sample["fixture"]).read_bytes()
                )
    with Client() as client:
        system = list(client.np3_907_ex._2d_agg_edc_history.read(content.getvalue()))
        north = list(
            client.np3_907_ex._2d_agg_edc_north_history.read(content.getvalue())
        )
        supply = list(client.np3_907_ex._2d_agg_esc_history.read(content.getvalue()))
        regulation = list(
            client.np3_906_ex._2day_agg_sced_as_offers_regdn_history.read(
                content.getvalue()
            )
        )
    assert len(system) == len(north) == len(supply) == len(regulation) == 3
    assert system[0].MW == Decimal("51260.7")
    assert north[0].MW == Decimal(19048)
    assert system[1].MW == Decimal("47922.79882")
    assert supply[0].MW == Decimal(1)
    assert supply[0].price == Decimal(-250)
    assert regulation[0].MWOffered == Decimal("318.1")
    assert regulation[0].REGDNOfferPrice == Decimal(0)
    assert regulation[0].repeatHourFlag is False


@pytest.mark.parametrize(
    "sample",
    json.loads((INPUTS / "summaries2-evidence.json").read_text()),
    ids=lambda entry: entry["fixture"],
)
def test_two_day_summary_historical_formats(sample):
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
    if rows:
        assert rows[0].model_dump(mode="json") == sample["first_row"]


def test_two_day_summary_preserves_legacy_identifiers_and_categories():
    with Client() as client:
        bid = next(
            client.np3_909_er._2d_ptp_obl_bids_history.read(
                zipped(
                    "48h_PTP_Obligation_Bids-12-MAR-14.csv",
                    (
                        INPUTS / "np3-909-er--2d_ptp_obl_bids-history-samples.csv"
                    ).read_bytes(),
                )
            )
        )
        generation = next(
            client.np3_910_er._2d_agg_gen_summary_history.read(
                zipped(
                    "48h_Agg_Gen_Summary-01-MAY-14.csv",
                    (
                        INPUTS / "np3-910-er--2d_agg_gen_summary-history-samples.csv"
                    ).read_bytes(),
                )
            )
        )
        current = zipped(
            "2d_Agg_Gen_Summary-07-SEP-26.csv",
            (
                INPUTS / "np3-910-er--2d_agg_gen_summary-history-current.csv"
            ).read_bytes(),
        )
        with pytest.raises(ValueError, match="no CSV files matching"):
            list(client.np3_910_er._2d_agg_dsr_loads_history.read(current))
    assert bid.bidId == "14a9934be3fb"
    assert bid.PTPBidPrice == Decimal("-.01")
    assert generation.sumBasePointNonWGR == Decimal("25912.74570178")
    assert generation.sumHASLNonWGR == Decimal("28511.51867675")
    assert generation.sumBasePointNonIRR is None
    assert generation.sumBasePointESR is None


@pytest.mark.parametrize(
    "sample",
    json.loads((INPUTS / "sced-curves-evidence.json").read_text()),
    ids=lambda entry: entry["fixture"],
)
def test_sced_curve_historical_formats(sample):
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
    if rows:
        assert rows[0].model_dump(mode="json") == sample["first_row"]


def test_sced_curves_keep_non_wind_and_dam_tables_separate():
    samples = json.loads((INPUTS / "sced-curves-evidence.json").read_text())
    data = BytesIO()
    with ZipFile(data, "w") as archive:
        for sample in samples:
            archive.writestr(sample["file"], (INPUTS / sample["fixture"]).read_bytes())
    with Client() as client:
        old = list(client.np3_908_er._2d_agg_esc_non_wind_history.read(data.getvalue()))
        current = list(
            client.np3_908_er._2d_agg_esc_nonirr_history.read(data.getvalue())
        )
        dam = list(client.np3_908_er._2d_agg_dam_min_esc_history.read(data.getvalue()))
        empty = list(
            client.np3_908_er._2d_agg_edc_clr_west_history.read(data.getvalue())
        )
    assert len(old) == len(current) == len(dam) == 3
    assert old[0].MW == Decimal("655.49999845")
    assert current[0].MW == Decimal("1451.40000152")
    assert old[0].price == Decimal(-250)
    assert dam[0].deliveryDate == date(2014, 3, 10)
    assert dam[0].MW == Decimal(609)
    assert empty == []


@pytest.mark.parametrize(
    "sample",
    json.loads((INPUTS / "dam-as-evidence.json").read_text()),
    ids=lambda entry: entry["fixture"],
)
def test_dam_as_historical_formats(sample):
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
    if rows:
        assert rows[0].model_dump(mode="json") == sample["first_row"]


def test_dam_as_readers_keep_legacy_and_current_categories_separate():
    samples = json.loads((INPUTS / "dam-as-evidence.json").read_text())
    content = BytesIO()
    with ZipFile(content, "w") as archive:
        for sample in samples:
            archive.writestr(sample["file"], (INPUTS / sample["fixture"]).read_bytes())
    with Client() as client:
        legacy = list(
            client.np3_911_er._2d_cleared_dam_as_rrsload_history.read(
                content.getvalue()
            )
        )
        aggregate = list(
            client.np3_911_er._2d_agg_as_offers_rrspfr_history.read(content.getvalue())
        )
        dam = list(
            client.np3_911_er._2d_agg_dam_as_offers_rrspfr_history.read(
                content.getvalue()
            )
        )
    assert len(legacy) == len(aggregate) == len(dam) == 3
    assert legacy[0].totalClearedASRRSLOAD == Decimal("960.9")
    assert aggregate[0].MWOffered == Decimal("19.2")
    assert dam[0].MWOffered == Decimal(51)
    assert legacy[0].deliveryDate == date(2014, 4, 29)
    assert aggregate[0].deliveryDate == date(2025, 4, 24)
    assert dam[0].deliveryDate == date(2026, 9, 5)


@pytest.mark.parametrize(
    "sample",
    json.loads((INPUTS / "cop-obligations-evidence.json").read_text()),
    ids=lambda entry: entry["fixture"],
)
def test_cop_obligation_historical_formats(sample):
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
    if rows:
        assert rows[0].model_dump(mode="json") == sample["first_row"]


def test_cop_and_obligation_history_preserves_source_meanings():
    with Client() as client:
        cop = next(
            client.np1_301._60_cop_adj_period_snapshot_history.read(
                zipped("old.csv", (INPUTS / "np1-301-history-samples.csv").read_bytes())
            )
        )
        obligation = next(
            client.np1_302.as_obligation_history.read(
                zipped("old.csv", (INPUTS / "np1-302-history-samples.csv").read_bytes())
            )
        )
        current = next(
            client.np1_302.as_obligation_history.read(
                zipped("new.csv", (INPUTS / "np1-302-history-current.csv").read_bytes())
            )
        )
    assert cop.hourEnding == "01:00"
    assert cop.deliveryDate == date(2014, 3, 2)
    assert cop.RRS == Decimal(0)
    assert cop.RRSPFR is None
    assert obligation.RRSObligation == Decimal(1)
    assert obligation.RRSResponsibility == Decimal(0)
    assert obligation.RRSOblFinal is None
    assert current.REGUPOblAdvisory == Decimal(".07869")
    assert current.REGUPResponsibility is None
    assert current.deliveryDate == date(2026, 3, 11)


@pytest.mark.parametrize(
    "sample",
    json.loads((INPUTS / "event-sasm-evidence.json").read_text()),
    ids=lambda entry: entry["fixture"],
)
def test_event_sasm_historical_formats(sample):
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
    if rows:
        assert rows[0].model_dump(mode="json") == sample["first_row"]


def test_sasm_history_preserves_timestamp_formats_and_offer_blocks():
    with Client() as client:
        award = next(
            client.np3_990_ex._60_sasm_gen_res_as_offer_awards_history.read(
                zipped(
                    "60d_SASM_Generation_Resource_AS_Offer_Awards-26-JAN-26.csv",
                    (
                        INPUTS
                        / "np3-990-ex--60_sasm_gen_res_as_offer_awards-history-sasm-nonempty.csv"
                    ).read_bytes(),
                )
            )
        )
        offer = next(
            client.np3_990_ex._60_sasm_gen_res_as_offers_history.read(
                zipped(
                    "60d_SASM_Generation_Resource_AS_Offers-26-JAN-26.csv",
                    (
                        INPUTS
                        / "np3-990-ex--60_sasm_gen_res_as_offers-history-sasm-nonempty.csv"
                    ).read_bytes(),
                )
            )
        )
    assert award.SASMId is not None
    assert award.SASMId.isoformat() == "2025-11-27T02:45:05"
    assert offer.SASMId == award.SASMId
    assert award.RRSPFRAwarded == Decimal("1.2")
    assert award.RRSAwarded is None
    assert offer.price1RRSPFR == Decimal(5000)
    assert offer.price1RRS is None
    assert offer.quantityMW1 == Decimal(20)
    assert offer.quantityMW5 == Decimal(60)


@pytest.mark.parametrize(
    "sample",
    json.loads((INPUTS / "cop-updates-evidence.json").read_text()),
    ids=lambda entry: entry["fixture"],
)
def test_cop_update_historical_formats(sample):
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
    if rows:
        assert rows[0].model_dump(mode="json") == sample["first_row"]


def test_cop_update_timestamps_and_revisions_are_preserved():
    old = (INPUTS / "np3-991-ex-history-samples.csv").read_bytes()
    current = (INPUTS / "np3-991-ex-history-current.csv").read_bytes()
    with Client() as client:
        reader = client.np3_991_ex._60_cop_all_updates_history
        revisions = list(reader.read(zipped("old.csv", old)))
        latest = next(reader.read(zipped("new.csv", current)))
        with pytest.raises(ValueError, match="does not match"):
            list(
                reader.read(
                    zipped("bad.csv", old.replace(b"12/3/2018 11:41", b"not-a-time"))
                )
            )
    assert len(revisions) == 3
    assert revisions[0].updateTime is not None
    assert revisions[0].updateTime.isoformat() == "2018-12-03T11:41:00"
    assert latest.updateTime is not None
    assert latest.submitTime is not None
    assert latest.updateTime.isoformat() == "2026-06-30T09:01:26"
    assert latest.submitTime.isoformat() == "2026-06-30T08:01:25"
    assert revisions[0].RRS == Decimal(0)
    assert revisions[0].RRSPFR is None
    assert latest.cancelFlag is False


@pytest.mark.parametrize(
    "sample",
    json.loads((INPUTS / "sced-disclosure-evidence.json").read_text()),
    ids=lambda entry: entry["fixture"],
)
def test_sced_disclosure_historical_formats(sample):
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
    if rows:
        assert rows[0].model_dump(mode="json") == sample["first_row"]


def test_sced_disclosure_keeps_legacy_services_and_override_values():
    with Client() as client:
        legacy = next(
            client.np3_965_er._60_sced_qse_self_arranged_as_history.read(
                zipped(
                    "60d_SCED_QSE_Self_Arranged_AS-01-MAY-14.csv",
                    (
                        INPUTS
                        / "np3-965-er--60_sced_qse_self_arranged_as-history-samples.csv"
                    ).read_bytes(),
                )
            )
        )
        override = next(
            client.np3_965_er._60_hdl_ldl_man_override_history.read(
                zipped(
                    "60d_HDL_LDL_ManOverride-07-JUN-24.csv",
                    (
                        INPUTS
                        / "np3-965-er--60_hdl_ldl_man_override-history-hdl-override.csv"
                    ).read_bytes(),
                )
            )
        )
        capability = next(
            client.np3_965_er._60d_sced_as_cap_man_override_history.read(
                zipped(
                    "60d_AS_Capability_ManOverride-14-JUN-26.csv",
                    (
                        INPUTS
                        / "np3-965-er--60d_sced_as_cap_man_override-history-as-override.csv"
                    ).read_bytes(),
                )
            )
        )
    assert legacy.RRSGN == Decimal(12)
    assert legacy.RRSNC == Decimal(45)
    assert legacy.RRSPFR is None
    assert override.HDLOriginal == Decimal("95.13999938")
    assert override.HDLManual == Decimal(0)
    assert override.LDLManual == Decimal(160)
    assert capability.startTime is not None
    assert capability.startTime.isoformat() == "2026-04-15T12:03:39"
    assert capability.ASType == "REGDN"


@pytest.mark.parametrize(
    "sample",
    json.loads((INPUTS / "eia-hourly-evidence.json").read_text()),
    ids=lambda s: s["fixture"],
)
def test_eia_hourly_archive_formats(sample):
    with Client() as client:
        rows = list(
            client.eia_930_cd.hourly_operations_history.read(
                zipped(sample["file"], (INPUTS / sample["fixture"]).read_bytes())
            )
        )
    assert [r.model_dump(mode="json") for r in rows] == sample["rows"]


def test_eia_hourly_preserves_unreported_hours_and_utc_timestamps():
    with Client() as client:
        timestamps, demand = client.eia_930_cd.hourly_operations_history.read(
            zipped(
                "same-day.csv",
                (INPUTS / "eia-930-cd-remaining-archive.csv").read_bytes(),
            )
        )
    assert timestamps.dataDate == date(2026, 9, 7)
    assert timestamps.dataType == "UTC0"
    assert timestamps.HR1 == datetime(2026, 9, 7, 6, tzinfo=UTC)
    assert demand.dataType == "D"
    assert demand.HR1 == Decimal(63489)
    assert demand.HR15 is None
    assert demand.HR25 is None


def test_bundle_rows_paginate_filter_and_keep_bundle_downloads_individual():
    calls = []
    csv = (INPUTS / "np4-190-cd.csv").read_bytes()

    def handler(request):
        if "b2clogin" in request.url.host:
            return httpx.Response(200, json={"id_token": "test", "expires_in": 3600})
        assert "/bundle/np4-190-cd" in request.url.path
        if request.method == "POST":
            ids = json.loads(request.content)["docIds"]
            assert len(ids) == 1
            calls.append(ids[0])
            return httpx.Response(
                200, content=zipped("inner.zip", zipped("report.csv", csv))
            )
        assert "postDatetimeFrom" not in request.url.params
        page = int(request.url.params["page"])
        return httpx.Response(
            200,
            json={
                "_meta": {"currentPage": page, "totalPages": 3},
                "product": {
                    "emilId": "NP4-190-CD",
                    "name": "DAM",
                    "reportTypeId": 12331,
                },
                "bundles": [
                    {
                        "docId": -page,
                        "friendlyName": f"DAMSPNP4190_2018-0{page}",
                        "postDatetime": f"2018-0{page}-28T23:59:59",
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
                kind="bundle",
                batch_size=100,
                posted_from=datetime(2018, 2, 1),  # noqa: DTZ001
                posted_to=datetime(2018, 3, 31),  # noqa: DTZ001
                where=lambda row: row.settlementPoint == "AMISTAD_ALL",
            )
        )
    assert calls == [-2, -3]
    assert len(rows) == 2
    # Selection applies to bundle publication dates; payload dates and duplicates remain.
    assert rows[0] == rows[1]
    assert rows[0].deliveryDate == date(2014, 5, 2)


@pytest.mark.parametrize("contains_subtype", [False, True])
def test_correction_bundle_uses_members_instead_of_document_name(contains_subtype):
    csv = (INPUTS / "np4-196-m-spp-current.csv").read_bytes()
    filename = (
        "pricecorrection_DAM_SPP_2026.csv"
        if contains_subtype
        else "pricecorrection_DAM_MCPC_2026.csv"
    )

    def handler(request):
        if "b2clogin" in request.url.host:
            return httpx.Response(200, json={"id_token": "test", "expires_in": 3600})
        assert "/bundle/np4-196-m" in request.url.path
        if request.method == "POST":
            return httpx.Response(
                200, content=zipped("nested.zip", zipped(filename, csv))
            )
        return httpx.Response(
            200,
            json={
                "_meta": {"currentPage": 1, "totalPages": 1},
                "product": {
                    "emilId": "NP4-196-M",
                    "name": "DAM corrections",
                    "reportTypeId": 13030,
                },
                "bundles": [
                    {
                        "docId": -1,
                        "friendlyName": "DAMPriceCorrections_2026-08",
                        "postDatetime": "2026-08-31T23:59:59",
                    }
                ],
            },
        )

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as http,
        Client("u", "p", "k", client=http) as client,
    ):
        rows = list(
            client.np4_196_m.dam_price_corrections_spp_history.rows(kind="bundle")
        )
    assert len(rows) == (3 if contains_subtype else 0)


def test_bad_correction_bundle_table_still_raises():
    def handler(request):
        if "b2clogin" in request.url.host:
            return httpx.Response(200, json={"id_token": "test", "expires_in": 3600})
        return httpx.Response(
            200, content=zipped("pricecorrection_DAM_SPP_2026.csv", b"unknown\n42\n")
        )

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as http,
        Client("u", "p", "k", client=http) as client,
        pytest.raises(ValueError, match="unexpected CSV columns"),
    ):
        list(
            client.np4_196_m.dam_price_corrections_spp_history.download(
                [-1], kind="bundle"
            )
        )


@pytest.mark.parametrize(
    "sample",
    json.loads((INPUTS / "middle-evidence.json").read_text()),
    ids=lambda sample: sample["fixture"],
)
def test_intermediate_sced_and_wind_layouts(sample):
    product, method = sample["endpoint"].split("/")
    method = ("_" if method[0].isdigit() else "") + method + "_history"
    with Client() as client:
        reader = getattr(getattr(client, product.replace("-", "_")), method)
        rows = list(
            reader.read(
                zipped(sample["member"], (INPUTS / sample["fixture"]).read_bytes())
            )
        )
    assert len(rows) == sample["fixtureRows"]
    assert rows[0].model_dump(mode="json") == sample["firstRow"]
    if sample["endpoint"] == "np4-732-cd/wpp_hrly_avrg_actl_fcast":
        assert rows[0].hourEnding == 24
        assert rows[0].hourEndingTimestamp is None
        assert rows[0].genSystemWide is None
        assert rows[0].actualWestNorth is None
        assert rows[0].actualLoadZoneWest is not None
        assert rows[0].actualLoadZoneNorth is not None
    if sample["fixture"].endswith("60_load_res_data_in_sced-2020.csv"):
        assert rows[0].HASL == Decimal(0)
        assert rows[0].LASL == Decimal(0)
        # This published layout contains 35 curve points, all blank in this sample.
        assert rows[0].SCEDBidCurveMW35 is None
        assert rows[0].SCEDBidCurvePrice35 is None
        assert rows[0].ASAwardsNSPIN is None
    if sample["fixture"].endswith("60_sced_qse_self_arranged_as-2020.csv"):
        assert rows[0].SCEDTimestamp.isoformat() == "2019-12-02T00:00:22"
    if sample["fixture"].endswith("60_sced_gen_res_data-2023.csv"):
        assert rows[0].ASRRSFFR == Decimal(0)
        assert rows[0].ASECRS == Decimal(0)
        assert rows[0].ASAwardsECRS is None
