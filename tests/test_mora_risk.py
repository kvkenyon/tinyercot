import json
from datetime import date, time
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import httpx
import openpyxl

from tinyercot import Client, MoraRiskPoint, PublicFile
from tinyercot._mora import ResourceOutlook

INPUTS = Path(__file__).resolve().parents[1] / "tools/inputs"
SOURCES = json.loads((INPUTS / "public-mora-risk-evidence.json").read_text())["files"]
NS = {"c": "http://schemas.openxmlformats.org/drawingml/2006/chart"}


def source_bytes(source):
    with ZipFile(INPUTS / source["fixture"]) as z:
        return z.read(source["member"])


def test_all_original_curve_coordinates_and_conditions():
    counts = 0
    with Client() as client:
        for f in SOURCES[:3]:
            data = source_bytes(f)
            records = list(
                client.resource_outlook.read_risk_points(data, filename=f["member"])
            )
            with ZipFile(BytesIO(data)) as z:
                tree = ET.fromstring(z.read("xl/charts/chart1.xml"))
            expected = {}
            for series in tree.findall(".//c:ser", NS):
                label = series.findtext("./c:tx//c:v", namespaces=NS)
                x = {
                    int(p.attrib["idx"]): Decimal(p.findtext("./c:v", namespaces=NS))
                    for p in series.findall("./c:cat//c:pt", NS)
                }
                y = {
                    int(p.attrib["idx"]): Decimal(p.findtext("./c:v", namespaces=NS))
                    for p in series.findall("./c:val//c:pt", NS)
                }
                for i, value in x.items():
                    expected[label, i] = (value, y[i])
            assert len(records) == len(expected)
            book = openpyxl.load_workbook(BytesIO(data), read_only=True, data_only=True)
            try:
                for r in records:
                    assert (r.windGenerationMW, r.probability) == expected.pop(
                        (r.sourceSeries, r.sourcePointIndex)
                    )
                    assert r.sourceChart == "xl/charts/chart1.xml"
                    assert r.sourceMember == f["member"]
                    assert r.event == (
                        "EEA3_load_shed" if r.sourceSeries.startswith("EEA3") else "EEA"
                    )
                    notes = [
                        v
                        for row in book[r.sourceSheet].values
                        for v in row
                        if isinstance(v, str) and v
                    ]
                    assert r.sourceNotes == notes
                    assert r.simulationRuns == 10000
                    assert r.sourceYAxisTitle == "Probability"
                    assert r.sourceXAxisTitle.startswith("Wind Generation (MW)")
                    assert MoraRiskPoint.model_validate_json(r.model_dump_json()) == r
                    counts += 1
                first = records[0]
                if "June" in f["member"]:
                    assert first.reportMonth == date(2026, 6, 1)
                    assert first.bessAvailabilityMW == Decimal(2070)
                    assert first.chartHourEnding == first.scenarioHourEnding == time(21)
                elif "October" in f["member"]:
                    assert first.reportMonth == date(2026, 10, 1)
                    assert first.bessAvailabilityMW == Decimal(4473)
                    assert first.chartHourEnding == first.scenarioHourEnding == time(20)
                    assert records[-1].probability == 0
                else:
                    assert first.reportMonth == date(2026, 11, 1)
                    assert first.bessAvailabilityMW == Decimal(4394)
                    assert first.chartHourEnding == time(20)
                    assert first.scenarioHourEnding == time(19)
                assert not expected
            finally:
                book.close()
    assert counts == 72


def test_raster_only_report_has_no_numeric_curve():
    with Client() as client:
        assert (
            list(client.resource_outlook.read_risk_points(source_bytes(SOURCES[3])))
            == []
        )


def test_anonymous_typed_curve_query_retains_file_identity(monkeypatch):
    source = SOURCES[2]
    file = PublicFile(url=source["url"], title=source["title"])
    monkeypatch.setattr(ResourceOutlook, "files", lambda self: [file])

    def handler(request):
        assert str(request.url) == file.url
        assert "authorization" not in request.headers
        return httpx.Response(200, content=source_bytes(source))

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as http,
        Client(client=http) as client,
    ):
        records = list(
            client.resource_outlook.risk_points(
                where=lambda r: r.event == "EEA3_load_shed"
            )
        )
    assert len(records) == 13
    assert all(r.sourceFile == file for r in records)
    assert all(r.chartHourEnding != r.scenarioHourEnding for r in records)
