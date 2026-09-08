"""Numerical chart caches for MORA's conditional wind/BESS risk profiles."""

import re
from collections.abc import Iterator
from datetime import date, time
from decimal import Decimal
from io import BytesIO
from posixpath import dirname, join, normpath
from typing import Literal
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from pydantic import BaseModel, ConfigDict

from ._load import _sheets
from ._public_tables import PublicFile

_NS = {
    "s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}


class MoraRiskPoint(BaseModel):
    """A published conditional simulation point, not an observed outcome.

    Probability remains a fraction. Wind and BESS availability are fixed inputs
    to the simulation. Chart and scenario hours remain separate when they
    disagree, with no inferred time zone or availability timestamp.
    """

    model_config = ConfigDict(extra="forbid")
    reportMonth: date
    event: Literal["EEA", "EEA3_load_shed"]
    windGenerationMW: Decimal
    probability: Decimal
    bessAvailabilityMW: Decimal | None
    simulationRuns: int | None
    chartHourEnding: time | None
    scenarioHourEnding: time | None
    sourceReportLabel: str
    sourceSeries: str
    sourceXAxisTitle: str
    sourceYAxisTitle: str
    sourceNotes: list[str]
    sourceMember: str
    sourceSheet: str
    sourceChart: str
    sourcePointIndex: int
    sourceFile: PublicFile | None = None


def _relationships(book: ZipFile, part: str) -> dict[str, tuple[str, str]]:
    path = join(dirname(part), "_rels", part.rsplit("/", 1)[-1] + ".rels")
    if path not in book.namelist():
        return {}
    return {
        r.attrib["Id"]: (
            normpath(join(dirname(part), r.attrib["Target"])).lstrip("/"),
            r.attrib["Type"].rsplit("/", 1)[-1],
        )
        for r in ET.fromstring(book.read(path))
        if r.attrib.get("TargetMode") != "External"
    }


def _charts(book: ZipFile) -> Iterator[tuple[str, str]]:
    workbook = ET.fromstring(book.read("xl/workbook.xml"))
    sheets = _relationships(book, "xl/workbook.xml")
    for sheet in workbook.findall("./s:sheets/s:sheet", _NS):
        part, _ = sheets[sheet.attrib[f"{{{_NS['r']}}}id"]]
        tree = ET.fromstring(book.read(part))
        links = _relationships(book, part)
        for drawing in tree.findall("./s:drawing", _NS):
            target, _ = links[drawing.attrib[f"{{{_NS['r']}}}id"]]
            chart_links = _relationships(book, target)
            for chart in ET.fromstring(book.read(target)).findall(".//c:chart", _NS):
                chart_part, _ = chart_links[chart.attrib[f"{{{_NS['r']}}}id"]]
                yield sheet.attrib["name"], chart_part


def _hour(label: str) -> time | None:
    match = re.search(
        r"Hour Ending\s*(?:\(HE\)\s*)?(\d{1,2})(?::(\d{2}))?\s*([ap])\.m\.", label
    )
    if not match:
        return None
    return time(int(match[1]) % 12 + (12 if match[3] == "p" else 0), int(match[2] or 0))


def _risk_points(
    data: bytes, member: str, month: date, report_label: str, source: PublicFile | None
) -> Iterator[MoraRiskPoint]:
    with ZipFile(BytesIO(data)) as book:
        charts = list(_charts(book))
        if not charts:
            return
        sheet_names = {s for s, _ in charts}
        notes = {
            name: [v for row in rows for v in row if isinstance(v, str) and v]
            for name, rows in _sheets(data, date_columns=())
            if name in sheet_names
        }
        for sheet, chart in charts:
            tree = ET.fromstring(book.read(chart))
            titles = [
                "".join(n.itertext()) for n in tree.findall(".//c:title//a:t", _NS)
            ]
            x_title = next(
                (t for t in titles if t.startswith("Wind Generation (MW)")), None
            )
            if x_title is None or "Probability" not in titles:
                raise ValueError(f"{member}/{chart}: Unknown MORA risk chart axes")
            context = "\n".join(notes[sheet])
            bess = re.search(r"BESS availability is also fixed at ([\d,]+) MW", context)
            runs = re.search(r"All ([\d,]+) model runs", context)
            for series in tree.findall(".//c:ser", _NS):
                label = "\n".join(
                    n.text or "" for n in series.findall("./c:tx//c:v", _NS)
                )
                event: Literal["EEA", "EEA3_load_shed"]
                if label.startswith("EEA3 Load Shed Probability"):
                    event = "EEA3_load_shed"
                elif label.startswith("EEA Probability"):
                    event = "EEA"
                else:
                    raise ValueError(f"{member}/{chart}: Unknown risk series {label!r}")
                coordinates = {
                    role: {
                        int(p.attrib["idx"]): Decimal(
                            p.findtext("./c:v", namespaces=_NS) or ""
                        )
                        for p in series.findall(f"./c:{role}//c:pt", _NS)
                    }
                    for role in ("cat", "val")
                }
                if (
                    not coordinates["cat"]
                    or coordinates["cat"].keys() != coordinates["val"].keys()
                ):
                    raise ValueError(
                        f"{member}/{chart}: Unpaired risk chart coordinates"
                    )
                for index, wind in coordinates["cat"].items():
                    yield MoraRiskPoint(
                        reportMonth=month,
                        event=event,
                        windGenerationMW=wind,
                        probability=coordinates["val"][index],
                        bessAvailabilityMW=Decimal(bess[1].replace(",", ""))
                        if bess
                        else None,
                        simulationRuns=int(runs[1].replace(",", "")) if runs else None,
                        chartHourEnding=_hour(x_title),
                        scenarioHourEnding=_hour(context),
                        sourceReportLabel=report_label,
                        sourceSeries=label,
                        sourceXAxisTitle=x_title,
                        sourceYAxisTitle="Probability",
                        sourceNotes=notes[sheet],
                        sourceMember=member,
                        sourceSheet=sheet,
                        sourceChart=chart,
                        sourcePointIndex=index,
                        sourceFile=source,
                    )
