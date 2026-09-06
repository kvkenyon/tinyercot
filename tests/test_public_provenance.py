"""Check that compact public fixtures and current generation share evidence."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_every_public_fixture_has_a_hash_and_source_transformation():
    records = json.loads((ROOT / "docs/evidence/fixture-provenance.json").read_text())[
        "fixtures"
    ]
    fixtures = ROOT / "tests/fixtures/public"
    assert {r["fixture"] for r in records} == {p.name for p in fixtures.glob("*.json")}
    for record in records:
        digest = hashlib.sha256((fixtures / record["fixture"]).read_bytes()).hexdigest()
        assert digest == record["sha256"]
        assert record["transformation"]
        if record["transformation"] == "Exact public response bytes.":
            assert record["source"]["sha256"] == digest


def test_current_model_fields_come_from_retained_response_bytes():
    for contract_name, fixture_name in (
        ("dam-prices", "dam-current-page1"),
        ("dam-capacity", "capacity-current"),
        ("rt-prices", "rt-prices-current"),
        ("system-load", "system-load-current"),
    ):
        contract = json.loads(
            (ROOT / f"tools/inputs/current/{contract_name}.json").read_text()
        )
        raw = (ROOT / f"tests/fixtures/public/{fixture_name}.json").read_bytes()
        assert hashlib.sha256(raw).hexdigest() == contract["response_source"]["sha256"]
        assert json.loads(raw)["fields"] == contract["fields"]
