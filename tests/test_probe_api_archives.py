"""Offline checks for the installed probe's receipt-verified cache binding."""

import json
from dataclasses import asdict

import pytest
from test_resource_dme import EVIDENCE, source_file

from tinyercot.public._http import SchemaMismatchError
from tools.probe_api_archives import cached_file


def write_evidence(tmp_path):
    archive = source_file(EVIDENCE["samples"][0])
    path = tmp_path / f"download--np3-988-er--{archive.document.document_id}.zip"
    path.write_bytes(archive.body)
    path.with_suffix(".receipt.json").write_text(
        json.dumps(asdict(archive.receipt), default=str)
    )
    (tmp_path / "archive--np3-988-er.json").write_text(
        json.dumps(
            {
                "archives": [
                    {
                        "docId": archive.document.document_id,
                        "friendlyName": archive.document.friendly_name,
                        "postDatetime": archive.document.post_datetime,
                    }
                ]
            }
        )
    )
    return archive, path


def test_cached_document_preserves_original_receipt(tmp_path):
    archive, _ = write_evidence(tmp_path)
    verified = cached_file(tmp_path, archive.document)
    assert verified == archive


def test_changed_file_or_receipt_fails_without_network(tmp_path):
    archive, path = write_evidence(tmp_path)
    path.write_bytes(archive.body + b"changed")
    with pytest.raises(SchemaMismatchError, match="receipt"):
        cached_file(tmp_path, archive.document)


def test_publication_metadata_cannot_be_rebound(tmp_path):
    archive, _ = write_evidence(tmp_path)
    source = tmp_path / "archive--np3-988-er.json"
    body = json.loads(source.read_text())
    body["archives"][0]["postDatetime"] = "2026-01-01T00:00:00"
    source.write_text(json.dumps(body))
    with pytest.raises(SchemaMismatchError, match="metadata changed"):
        cached_file(tmp_path, archive.document)
