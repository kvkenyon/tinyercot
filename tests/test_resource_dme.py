"""Source-cell fixtures for exact-text public resource CSV decoding."""

import csv
import datetime
import hashlib
import io
import json
import zipfile
from dataclasses import replace
from pathlib import Path

import pytest

from tinyercot.public._http import (
    AccessDeniedError,
    LimitError,
    Receipt,
    SchemaMismatchError,
)
from tinyercot.public.api_archives import APIArchive, APIArchiveFile
from tinyercot.public.resource_dme import ResourceDmeRow, iter_resource_dme

EVIDENCE = json.loads(
    (Path(__file__).parent / "fixtures/public/resource-dme-excerpt.json").read_text()
)


def source_file(sample, *, rows=None, header=None, csv_bytes=None):
    text = io.StringIO(newline="")
    writer = csv.writer(text)
    writer.writerow(sample["header"] if header is None else header)
    writer.writerows(sample["rows"] if rows is None else rows)
    raw = io.BytesIO()
    with zipfile.ZipFile(raw, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            sample["member"],
            text.getvalue().encode() if csv_bytes is None else csv_bytes,
        )
    body = raw.getvalue()
    document = APIArchive(
        "np3-988-er", sample["document_id"], "source fixture", "2026-09-05T05:02:43.000"
    )
    receipt = Receipt(
        sample["receipt"]["source_url"],
        datetime.datetime.now(datetime.UTC),
        hashlib.sha256(body).hexdigest(),
        len(body),
    )
    return APIArchiveFile(document, receipt, (sample["member"],), body)


@pytest.mark.parametrize("sample", EVIDENCE["samples"])
def test_current_and_historical_text_cells(sample):
    rows = list(iter_resource_dme(source_file(sample)))
    assert len(rows) == 3 and rows[0].record_number == 2
    assert isinstance(rows[0].row, ResourceDmeRow)
    for record, original in zip(rows, sample["rows"], strict=True):
        assert list(record.row.model_dump().values()) == original
    assert any(record.row.dme_duns.startswith("0") for record in rows)


def test_blanks_whitespace_quotes_and_multiline_are_preserved():
    cells = [
        "  Owner ",
        "resource, name",
        'Quoted "name"',
        "",
        "line1\nline2",
        "0000123",
        "N",
    ]
    row = next(iter_resource_dme(source_file(EVIDENCE["samples"][0], rows=[cells]))).row
    assert list(row.model_dump().values()) == cells


def test_complete_iteration_exceeds_default_budget():
    sample = EVIDENCE["samples"][0]
    archive = source_file(sample, rows=sample["rows"] * 400)
    assert sum(1 for _ in iter_resource_dme(archive, max_rows=None)) == 1200
    with pytest.raises(LimitError, match="row budget"):
        list(iter_resource_dme(archive))


@pytest.mark.parametrize(
    "change",
    [
        {"header": ["unknown"] * 7},
        {"rows": [["too", "short"]]},
        {"csv_bytes": b"\xff\xfe\xff"},
        {"csv_bytes": b'"unterminated'},
    ],
)
def test_unknown_schema_and_encoding_fail_closed(change):
    with pytest.raises(SchemaMismatchError):
        list(iter_resource_dme(source_file(EVIDENCE["samples"][0], **change)))


def test_source_identity_receipt_and_expansion_checks():
    source = source_file(EVIDENCE["samples"][0])
    with pytest.raises(AccessDeniedError):
        list(
            iter_resource_dme(
                replace(source, document=replace(source.document, emil_id="private"))
            )
        )
    with pytest.raises(SchemaMismatchError, match="receipt"):
        list(iter_resource_dme(replace(source, body=source.body + b"changed")))
    with pytest.raises(LimitError):
        list(iter_resource_dme(source, max_expanded_bytes=1))
