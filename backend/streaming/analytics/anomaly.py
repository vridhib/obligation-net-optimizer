from dataclasses import dataclass
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest



@dataclass
class Anomaly:
    window_id: int
    window_end: str
    metric: str
    value: float
    score: float
    method: str # "z-score" or "isolation-forest"


# Tier 1: rolling z-score (univariate)
def detect_z_score_anomalies(
    values: list[float],
    window: int = 10,
    threshold: float = 3.0
) -> list[tuple[int,float]]:
    """
    Return list of (index, z_score) where |z_score| > threshold.
    Uses a rolling mean/std from previous values only (no lookahead).
    """

    if len(values) < window + 1:
        return []


    series = pd.Series(values, dtype=float)
    rolling_mean = series.rolling(window=window).mean().shift(1)
    rolling_std = series.rolling(window=window).std().shift(1)

    z_scores = (series - rolling_mean) / rolling_std.replace(0, np.nan)

    flagged = []
    for i, z in enumerate(z_scores):
        if pd.notna(z) and abs(z) > threshold:
            flagged.append((i, float(z)))
    return flagged


# Tier 2: isolation forest (multivariate)
def detect_multivariate_anomalies(
    window_history: list[dict],
    contamination: float = 0.1
) -> list[tuple[int, float]]:
    """
    Fit Isolation Forest on multi-metric window features.
    Returns list of (index, anomaly_score) for flagged windows.

    Features: 
    total_settled, total_failed, liquidity_saved, failure_rate, 
    and gross_volume
    """

    if len(window_history) < 20:
        return []

    df = pd.DataFrame(window_history)
    features = df[[
        "total_settled", "total_failed", "liquidity_saved", 
        "failure_rate", "gross_volume"
    ]].astype(float).values

    model = IsolationForest(contamination=contamination, random_state=42, n_estimators=100)
    model.fit(features)

    # decision_function: lower = more anomalous
    scores = model.decision_function(features)
    predictions = model.predict(features) # -1 = anomaly; 1 = normal

    flagged = []
    for i, (pred, score) in enumerate(zip(predictions, scores)):
        if pred == -1:
            flagged.append((i, float(-score))) # higher = more anomalous
    return flagged


# Unified entry point
def detect_window_anomalies(window_history: list[dict]) -> list[Anomaly]:
    """
    Run both tiers and return a unified list of anomalies.
    """
    anomalies: list[Anomaly] = []

    # Tier 1: univariate z-score on failure_rate and gross_volume
    for metric in ("failure_rate", "gross_volume"):
        values = [float(w[metric]) for w in window_history]
        for idx, z in detect_z_score_anomalies(values):
            anomalies.append(Anomaly(
                window_id=window_history[idx]["window_id"],
                window_end=window_history[idx]["last_window_end"],
                metric=metric,
                value=values[idx],
                score=z,
                method="z_score"
            ))

    # Tier 2: multivariate Isolation Forest
    for idx, score in detect_multivariate_anomalies(window_history):
        anomalies.append(Anomaly(
            window_id=window_history[idx]["window_id"],
            window_end=window_history[idx]["last_window_end"],
            metric="multivariate",
            value=0.0,
            score=score,
            method="isolation_forest"
        ))

    return anomalies    