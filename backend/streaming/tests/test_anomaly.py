from streaming.analytics.anomaly import detect_z_score_anomalies, detect_multivariate_anomalies, detect_window_anomalies


def test_z_score_flags_injected_spike():
    # 20 normal points, then 1 huge spike
    values = [100.0] * 20 + [100.0 + (i % 3) for i in range(10)] + [5000.0]
    flagged = detect_z_score_anomalies(values, window=10, threshold=3.0)
    indices = [i for i, _ in flagged]
    print(indices)
    assert 30 in indices


def test_z_score_ignores_stable_series():
    values = [100.0] * 50
    flagged = detect_z_score_anomalies(values)
    assert flagged == []


def test_z_score_insufficient_data():
    assert detect_z_score_anomalies([100.0] * 5, window=10) == []


def test_isolation_forest_flags_injected_multivariate_anomaly():
    # 30 normal windows with modest variance
    normal = [
        {
            "total_settled": 1000 + (i % 5) * 10,
            "total_failed": 20 + (i % 3),
            "liquidity_saved": 500 + (i % 4) * 5,
            "failure_rate": 0.02,
            "gross_volume": 1500 + (i % 5) * 20
        }
        for i in range(30)
    ]
    # Inject 3 anomalies with wildly different metrics
    anomalies = [
        {"total_settled": 100, "total_failed": 900, "liquidity_saved": 10,
         "failure_rate": 0.9, "gross_volume": 1000},
        {"total_settled": 50000, "total_failed": 0, "liquidity_saved": 40000,
         "failure_rate": 0.0, "gross_volume": 80000},
        {"total_settled": 1000, "total_failed": 500, "liquidity_saved": 100,
         "failure_rate": 0.5, "gross_volume": 1500}
    ]
    history = normal + anomalies

    flagged = detect_multivariate_anomalies(history, contamination=0.1)
    flagged_indices = [i for i, _ in flagged]

    # At least 2 of 3 injected anomalies should be caught
    injected_indices = {30, 31, 32}
    caught = injected_indices & set(flagged_indices)
    assert len(caught) >= 2


def test_isolation_forest_insufficient_data():
    assert detect_multivariate_anomalies([{"a": 1}]) == []


def test_detect_window_anomalies_returns_structured_output():
    history = [
        {
            "window_id": 1, "last_window_end": f"2026-08-11T08:{i:02d}:00Z",
            "total_settled": 1000, "total_failed": 20,
            "liquidity_saved": 500, "failure_rate": 0.02,
            "gross_volume": 1500
        }
        for i in range(25)
    ]
    history.append({
        "window_id": 1, "last_window_end": "2026-08-11T09:00:00Z",
        "total_settled": 100, "total_failed": 900,
        "liquidity_saved": 10, "failure_rate": 0.9,
        "gross_volume": 1000
    })

    anomalies = detect_window_anomalies(history)
    assert isinstance(anomalies, list)
    for a in anomalies:
        assert a.method in ("z_score", "isolation_forest")
        assert isinstance(a.score, float)