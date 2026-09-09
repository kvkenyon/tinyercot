import hashlib
import json
from datetime import date, datetime
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import httpx
import openpyxl
import pytest

from tinyercot import AncillaryServiceRequirements, Client

INPUTS = Path(__file__).resolve().parents[1] / "tools/inputs/as-requirements"
SOURCES = json.loads((INPUTS / "sources.json").read_text())
RRS_FIELDS = [
    "totalRrsMW",
    "pfrsMW",
    "lrsMW",
    "equivalencyRatio",
    "fractionFromLrs",
    "totalEquivalentPfrsMW",
]


def original(member):
    with ZipFile(INPUTS / "originals.zip") as z:
        return z.read(member)


def number(value):
    return None if value is None else Decimal(str(value))


def label(value):
    return value.date().isoformat() if isinstance(value, datetime) else str(value)


@pytest.mark.parametrize(
    "source", SOURCES["files"], ids=lambda s: s["member"].split("/")[-1]
)
def test_all_original_requirement_cells(source):
    data = original(source["member"])
    assert hashlib.sha256(data).hexdigest() == source["sha256"]
    with Client() as c:
        (doc,) = c.ancillary_requirements.read(data, filename=source["member"])
    assert (
        AncillaryServiceRequirements.model_validate_json(doc.model_dump_json()) == doc
    )
    workbook = openpyxl.load_workbook(BytesIO(data), read_only=True, data_only=True)
    matrices = {s.title: list(s.values) for s in workbook}
    workbook.close()
    numeric = {
        (s, r + 1, c + 1)
        for s, rows in matrices.items()
        for r, row in enumerate(rows)
        for c, v in enumerate(row)
        if type(v) in (int, float)
    }
    accounted = set()
    for q in doc.quantities:
        rows = matrices[q.sourceSheet]
        assert q.quantityMW == number(rows[q.sourceRow - 1][q.sourceColumn - 1])
        assert q.hourEnding == rows[q.sourceRow - 1][0]
        header = next(
            row for row in reversed(rows[: q.sourceRow - 1]) if row[0] == "HE"
        )
        assert q.period == label(header[q.sourceColumn - 1])
        assert q.kind == (
            "change" if q.sourceSheet.startswith("Change") else "requirement"
        )
        accounted.update(
            [
                (q.sourceSheet, q.sourceRow, q.sourceColumn),
                (q.sourceSheet, q.sourceRow, 1),
            ]
        )
    for a in doc.rrsAllocations:
        rows = matrices[a.sourceSheet]
        header_index = next(
            r
            for r in reversed(range(a.sourceRow - 1))
            if rows[r][a.sourceColumn - 1] == "HE"
        )
        assert a.period == label(rows[header_index - 1][a.sourceColumn - 1])
        assert a.hourEnding == rows[a.sourceRow - 1][a.sourceColumn - 1]
        accounted.add((a.sourceSheet, a.sourceRow, a.sourceColumn))
        for offset, field in enumerate(RRS_FIELDS, 1):
            col = a.sourceColumn - 1 + offset
            present = col < len(rows[header_index]) and rows[header_index][col] not in (
                None,
                "",
                "HE",
            )
            assert getattr(a, field) == (
                number(rows[a.sourceRow - 1][col]) if present else None
            )
            if present:
                accounted.add((a.sourceSheet, a.sourceRow, col + 1))
    for a in doc.adjustments:
        rows = matrices[a.sourceSheet]
        assert a.adjustmentMW == number(rows[a.sourceRow - 1][a.sourceColumn - 1])
        assert a.period == rows[a.sourceRow - 1][0]
        header_index = next(
            r for r in reversed(range(a.sourceRow - 1)) if rows[r][0] == "Month"
        )
        assert a.hourEnding == rows[header_index][a.sourceColumn - 1]
        assert a.basis in [row[0] for row in rows[:header_index] if row]
        accounted.update(
            [
                (a.sourceSheet, a.sourceRow, a.sourceColumn),
                (a.sourceSheet, header_index + 1, a.sourceColumn),
            ]
        )
    for v in doc.supportingValues:
        raw = matrices[v.sourceSheet][v.sourceRow - 1]
        assert v.value == number(raw[v.sourceColumn - 1])
        assert v.label == (raw[0] if isinstance(raw[0], str) else None)
        accounted.add((v.sourceSheet, v.sourceRow, v.sourceColumn))
    assert numeric - accounted == set(), "Unaccounted source numeric cells"
    for note in doc.notes:
        assert (
            note.text
            == matrices[note.sourceSheet][note.sourceRow - 1][note.sourceColumn - 1]
        )


def test_vintages_partial_months_changes_and_adjustment_units():
    with Client() as c:
        docs = list(
            c.ancillary_requirements.read((INPUTS / "originals.zip").read_bytes())
        )
    assert len(docs) == 15
    assert {d.year for d in docs} == set(range(2016, 2027))
    current = next(d for d in docs if d.effectiveDate == date(2026, 9, 1))
    assert {q.service for q in current.quantities} == {
        "RegUp",
        "RegDown",
        "RRS",
        "NSRS",
        "ECRS",
    }
    assert len(current.adjustments) == 1152
    assert any("Solar" in a.basis and "1000 MW" in a.basis for a in current.adjustments)
    assert any(n.text == "#REF!" for n in current.notes)
    revisions = [d for d in docs if d.year == 2021]
    assert {d.effectiveDate for d in revisions} == {
        date(2021, 1, 1),
        date(2021, 7, 12),
        date(2021, 9, 1),
    }
    july = next(d for d in revisions if d.effectiveDate.month == 7)
    assert {"Jul 1 - 11", "Jul 12 - 31"} <= {q.period for q in july.quantities}
    assert "2021-06-01" in {q.period for q in july.quantities}
    old = next(d for d in docs if d.year == 2016)
    assert 0 in {r.hourEnding for r in old.rrsAllocations}
    assert any(q.kind == "change" for d in docs for q in d.quantities)
    assert next(d for d in docs if d.year == 2020).effectiveDate is None
    assert len({d.sourceMember for d in docs}) == 15


def test_anonymous_discovery_download_and_revision_filter():
    calls = []

    def handle(request):
        calls.append(str(request.url))
        if request.url.path == "/mktinfo/dam":
            return httpx.Response(
                200,
                text=f'<a href="{SOURCES["url"]}">Methodology for Determining Minimum Ancillary Service Requirements</a>',
            )
        assert str(request.url) == SOURCES["url"]
        return httpx.Response(200, content=(INPUTS / "originals.zip").read_bytes())

    with (
        httpx.Client(transport=httpx.MockTransport(handle)) as http,
        Client(client=http) as c,
    ):
        docs = list(
            c.ancillary_requirements.rows(
                where=lambda d: d.effectiveDate == date(2026, 9, 1)
            )
        )
    assert len(docs) == 1
    assert calls == ["https://www.ercot.com/mktinfo/dam", SOURCES["url"]]
