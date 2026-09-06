from collections import Counter

from tinyercot.catalog import operations
from tinyercot.public import coverage


def test_every_audited_family_and_operation_has_an_explicit_scope():
    entries = coverage()
    assert len(entries) == 39 + 257 + 2
    assert len({entry.key for entry in entries}) == len(entries)
    assert Counter(entry.status for entry in entries)["covered"] == 6
    assert {entry.status for entry in entries} == {
        "covered",
        "deferred",
        "restricted",
        "unavailable",
    }
    assert all(entry.source_urls and entry.scope for entry in entries)
    family = [entry for entry in entries if entry.key.startswith("family:")]
    assert len(family) == 39 and all(entry.status != "covered" for entry in family)
    assert all(
        entry.status == "restricted"
        for entry in family
        if "Certified participant" in entry.title
        or "Secure models" in entry.title
        or "Participant EWS" in entry.title
    )


def test_typed_counts_do_not_claim_broad_api_coverage():
    observed = [operation for operation in operations() if operation.kind == "data"]
    typed = [
        entry
        for entry in coverage()
        if entry.key.startswith("api:") and entry.status == "covered"
    ]
    assert len(observed) == 243
    assert len({(op.service, op.path.split("/")[1]) for op in observed}) == 98
    assert len(typed) == 4
    assert {entry.title.split("/")[1] for entry in typed} == {
        "np4-190-cd",
        "np4-188-cd",
        "np6-905-cd",
        "np6-345-cd",
    }
