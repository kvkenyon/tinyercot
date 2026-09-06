from tools.probe_registry import remaining_periods


def test_explicit_failure_retry_preserves_successful_historical_observation():
    records = [
        {
            "period": "latest",
            "status": "failed",
            "error_type": "SourceUnavailableError",
        },
        {"period": "oldest", "status": "typed", "rows": 1},
    ]
    assert remaining_periods(records) == (("latest", "desc"),)
    assert len(records) == 2


def test_recovered_observation_is_not_repeated_or_its_prior_failure_erased():
    records = [
        {
            "period": "latest",
            "status": "failed",
            "error_type": "SourceUnavailableError",
        },
        {"period": "latest", "status": "typed", "rows": 1},
        {"period": "oldest", "status": "typed", "rows": 1},
    ]
    assert remaining_periods(records) == ()
    assert len(records) == 3


def test_empty_response_does_not_establish_typed_row_retrieval():
    assert remaining_periods([{"period": "latest", "status": "empty", "rows": 0}]) == (
        ("latest", "desc"),
        ("oldest", "asc"),
    )
