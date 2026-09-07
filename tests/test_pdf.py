# Report clocks deliberately preserve the published timezone-naive values.
# ruff: noqa: DTZ001
"""Published PDF values independently transcribed from rendered report tables."""

from datetime import date, datetime, time
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pytest
from pypdf import PdfReader

from tinyercot import Client

INPUTS = Path(__file__).resolve().parents[1] / "tools/inputs/history"


def zipped(name, data):
    output = BytesIO()
    with ZipFile(output, "w") as archive:
        archive.writestr(name, data)
    return output.getvalue()


def sample(period):
    return (INPUTS / f"np4-765-er-{period}.pdf").read_bytes()


@pytest.mark.parametrize("period", ["old", "current"])
def test_daily_values(period):
    with Client() as client:
        rows = list(
            client.np4_765_er.daily_values_history.read(
                zipped("nested.zip", zipped("report.pdf", sample(period)))
            )
        )
    assert len(rows) == 1
    row = rows[0]
    # Published order: installed/total discharge, installed/total charge,
    # peak load, peak discharge/charge/net, maximum discharge/charge,
    # discharge/charge at maximum penetration.
    assert [
        getattr(row, name)
        for name in (
            "installedDischargeCapacityMW",
            "totalDischargeCapacityMW",
            "installedChargeCapacityMW",
            "totalChargeCapacityMW",
            "peakLoadMW",
            "dischargeAtPeakLoadMW",
            "chargeAtPeakLoadMW",
            "netOutputAtPeakLoadMW",
            "maxDischargeMW",
            "maxChargeMW",
            "dischargeAtMaxPenetrationMW",
            "chargeAtMaxPenetrationMW",
        )
    ] == [
        Decimal(v)
        for v in (
            [5038, 7046, 7024, 7024, 49649, 430, 131, 299, 884, 616, 884, 616]
            if period == "old"
            else [
                22024,
                22536,
                21866,
                22376,
                82270,
                283,
                210,
                73,
                10838,
                10241,
                10838,
                10241,
            ]
        )
    ]
    discharge, charge = ("1.80", "1.36") if period == "old" else ("13.98", "16.35")
    assert (
        row.penetrationAtMaxDischargePercent
        == row.maxDischargePenetrationPercent
        == Decimal(discharge)
    )
    assert (
        row.penetrationAtMaxChargePercent
        == row.maxChargePenetrationPercent
        == Decimal(charge)
    )
    assert (
        row.maxDischargeTime
        == row.maxDischargePenetrationTime
        == (time(6, 36) if period == "old" else time(19, 54))
    )
    assert (
        row.maxChargeTime
        == row.maxChargePenetrationTime
        == (time(11, 45) if period == "old" else time(9, 24))
    )
    assert row.peakLoadHourEnding == (8 if period == "old" else 18)
    assert row.reportDate == (
        date(2023, 12, 5) if period == "old" else date(2026, 9, 6)
    )
    assert (
        "seasonal max. reasonability limit"
        if period == "old"
        else "seasonal net max. sustainable rating"
    ) in row.sourceNotes
    assert "Note that generation" in row.sourceNotes


def test_record_tables():
    data = zipped("report.pdf", sample("current"))
    with Client() as client:
        power = list(client.np4_765_er.power_records_history.read(data))
        penetration = list(client.np4_765_er.penetration_records_history.read(data))
        soc = list(client.np4_765_er.soc_records_history.read(data))
    assert [
        (
            r.category,
            r.recordMW,
            r.recordTime,
            r.penetrationPercent,
            r.maxSocPercent,
            r.minSocPercent,
        )
        for r in power
    ] == [
        (
            "ESR Discharge Generation",
            Decimal(13300),
            datetime(2026, 8, 23, 19, 45, tzinfo=None),
            Decimal("15.35"),
            Decimal("79.61"),
            Decimal("45.49"),
        ),
        (
            "ESR Charge Load",
            Decimal(11576),
            datetime(2026, 8, 30, 9, 29, tzinfo=None),
            Decimal("18.15"),
            Decimal("54.66"),
            Decimal("26.59"),
        ),
        (
            "ESR Injection",
            Decimal(13268),
            datetime(2026, 8, 23, 19, 45, tzinfo=None),
            Decimal("15.31"),
            Decimal("79.61"),
            Decimal("45.49"),
        ),
    ]
    # The charge record's MW differs between these two published tables.
    assert [
        (
            r.category,
            r.recordMW,
            r.recordTime,
            r.penetrationPercent,
            r.maxSocPercent,
            r.minSocPercent,
        )
        for r in penetration
    ] == [
        (
            "ESR Discharge Generation",
            Decimal(10514),
            datetime(2026, 3, 13, 19, 31, tzinfo=None),
            Decimal("20.61"),
            Decimal("75.87"),
            Decimal("41.76"),
        ),
        (
            "ESR Charge Load",
            Decimal(11564),
            datetime(2026, 8, 30, 9, 29, tzinfo=None),
            Decimal("18.15"),
            Decimal("54.66"),
            Decimal("26.59"),
        ),
    ]
    assert [(r.category, r.recordMWh, r.recordTime) for r in soc] == [
        (
            "ESR SOC Hourly Increase",
            Decimal(9946),
            datetime(2026, 8, 30, 10, 4, tzinfo=None),
        ),
        (
            "ESR SOC Hourly Decrease",
            Decimal(12934),
            datetime(2026, 8, 23, 20, 17, tzinfo=None),
        ),
    ]
    assert all(r.reportDate == date(2026, 9, 6) for r in [*power, *penetration, *soc])


def test_older_report_has_no_record_section():
    with Client() as client:
        for reader in (
            client.np4_765_er.power_records_history,
            client.np4_765_er.penetration_records_history,
            client.np4_765_er.soc_records_history,
        ):
            assert list(reader.read(zipped("report.pdf", sample("old")))) == []


@pytest.mark.parametrize(
    "before,after",
    [
        ("Current Daily Values:", "Unknown heading:"),
        ("Total ESR Discharge Capacity**", "Changed Capacity**"),
        ("22,024", "unavailable"),
        ("MW", "kW"),
    ],
)
def test_unrecognized_daily_table_raises(before, after):
    text = " ".join(
        PdfReader(BytesIO(sample("current"))).pages[0].extract_text().split()
    )
    with Client() as client, pytest.raises(ValueError):
        list(
            client.np4_765_er.daily_values_history._read_text(
                text.replace(before, after)
            )
        )


def test_malformed_records_are_not_treated_as_absent():
    text = " ".join(
        PdfReader(BytesIO(sample("current"))).pages[0].extract_text().split()
    )
    with Client() as client, pytest.raises(ValueError, match="headings"):
        list(
            client.np4_765_er.power_records_history._read_text(
                text.replace("Record Max MW Time", "Changed heading")
            )
        )


def test_missing_pdf_raises():
    with Client() as client, pytest.raises(ValueError, match="no PDF"):
        list(client.np4_765_er.daily_values_history.read(zipped("unknown.txt", b"")))


def test_hourly_chart_percentages_match_printed_labels():
    with Client() as client:
        rows = list(
            client.np4_765_er.hourly_percentages_history.read(
                zipped("report.pdf", sample("current"))
            )
        )
    assert [r.hourEnding for r in rows] == [f"{h:02d}" for h in range(1, 25)]
    assert all(r.reportDate == date(2026, 9, 6) for r in rows)
    # Transcribed from the rendered charts, including their published rounding.
    assert [r.dischargeCapacityPercent for r in rows] == [
        Decimal(x)
        for x in (
            [
                "0.6",
                "0.2",
                "0.4",
                "0.7",
                "2.5",
                "5.3",
                "11.4",
                "5.5",
                "0.1",
                "0.1",
                "0.1",
                "0.1",
                "0.6",
                "0.3",
                "0.9",
                "0.5",
                "0.3",
                "1.3",
                "14.0",
                "42.9",
                "40.0",
                "19.1",
                "4.2",
                "1.3",
            ]
        )
    ]
    assert [r.chargeCapacityPercent for r in rows] == [
        Decimal(x)
        for x in (
            [
                "1.2",
                "3.0",
                "4.4",
                "1.1",
                "0.8",
                "0.8",
                "0.8",
                "1.6",
                "18.6",
                "44.5",
                "38.9",
                "25.0",
                "15.8",
                "8.1",
                "3.7",
                "2.1",
                "1.9",
                "1.0",
                "0.9",
                "0.2",
                "0.6",
                "0.4",
                "1.3",
                "2.1",
            ]
        )
    ]
    assert {
        r.hourEnding: r.netLoadPercent for r in rows if r.netLoadPercent is not None
    } == {
        "05": Decimal("0.7"),
        "06": Decimal("1.8"),
        "07": Decimal("4.2"),
        "08": Decimal("1.6"),
        "18": Decimal("0.1"),
        "19": Decimal("3.6"),
        "20": Decimal("12.0"),
        "21": Decimal("11.4"),
        "22": Decimal("5.6"),
        "23": Decimal("0.9"),
    }
    assert sum(r.netLoadPercent is None for r in rows) == 14


@pytest.mark.parametrize("period", ["spring", "fall"])
def test_chart_hour_axis_preserves_published_dst_labels(period):
    with Client() as client:
        rows = list(
            client.np4_765_er.hourly_percentages_history.read(
                zipped("outer.zip", zipped("report.pdf", sample(period)))
            )
        )
    expected_hours = [f"{h:02d}" for h in range(1, 25) if period != "spring" or h != 3]
    assert [r.hourEnding for r in rows] == expected_hours
    assert all(
        r.reportDate == (date(2025, 3, 9) if period == "spring" else date(2025, 11, 2))
        for r in rows
    )
    if period == "spring":
        assert rows[2].hourEnding == "04"
        assert rows[2].dischargeCapacityPercent == Decimal("0.3")
        assert rows[2].chargeCapacityPercent == Decimal("6.2")
    else:
        assert rows[17].hourEnding == "18"
        assert rows[17].dischargeCapacityPercent == Decimal("30.8")
        assert rows[17].chargeCapacityPercent == Decimal("0.5")


def test_missing_chart_is_not_silent_partial_data(monkeypatch):
    from pypdf import PageObject

    original = PageObject.extract_xform_text

    def changed_legend(self, *args, **kwargs):
        return original(self, *args, **kwargs).replace(
            "Actual ESR Charging Output", "Unknown series"
        )

    monkeypatch.setattr(PageObject, "extract_xform_text", changed_legend)
    with Client() as client, pytest.raises(ValueError, match="Expected one chart"):
        list(
            client.np4_765_er.hourly_percentages_history.read(
                zipped("report.pdf", sample("current"))
            )
        )


def test_duplicate_chart_label_does_not_overwrite_values(monkeypatch):
    from pypdf import PageObject

    original = PageObject.extract_xform_text

    def duplicated_label(self, *args, **kwargs):
        callback = kwargs["visitor_text"]

        def visit(text, *position):
            callback(text, *position)
            if text.strip() == "0.6%":
                callback(text, *position)

        kwargs["visitor_text"] = visit
        return original(self, *args, **kwargs)

    monkeypatch.setattr(PageObject, "extract_xform_text", duplicated_label)
    with Client() as client, pytest.raises(ValueError, match="Ambiguous chart label"):
        list(
            client.np4_765_er.hourly_percentages_history.read(
                zipped("report.pdf", sample("current"))
            )
        )
