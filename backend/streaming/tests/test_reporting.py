import pytest
import pandas as pd
from decimal import Decimal
import matplotlib
matplotlib.use("Agg")
from streaming.reporting import ReportGenerator
from ..stream_simulator import Snapshot


@pytest.fixture
def snapshot_with_history():
    snapshot = Snapshot()
    snapshot.window_history = [
        {
            "last_window_end": "2026-08-11T08:01:00Z",
            "total_settled": Decimal("150.00"),
            "total_failed": Decimal("20.00"),
            "liquidity_used": Decimal("150.00"),
            "liquidity_saved": Decimal("80.00"),
            "gross_volume": Decimal("230.00"),
            "failure_rate": Decimal("0.1176"),
            "balances": {"A": Decimal("1000"), "B": Decimal("900")},
            "net_positions": {"A": Decimal("-100"), "B": Decimal("100")},
        },
        {
            "last_window_end": "2026-08-11T08:02:00Z",
            "total_settled": Decimal("30.00"),
            "total_failed": Decimal("0.00"),
            "liquidity_used": Decimal("180.00"),
            "liquidity_saved": Decimal("0.00"),
            "gross_volume": Decimal("30.00"),
            "failure_rate": Decimal("0.0"),
            "balances": {"A": Decimal("970"), "B": Decimal("930")},
            "net_positions": {"A": Decimal("-30"), "B": Decimal("30")},
        },
    ]
    snapshot.net_positions = {"A": Decimal("-130"), "B": Decimal("130")}
    snapshot.balances = {"A": Decimal("970"), "B": Decimal("930")}
    return snapshot


def test_generate_returns_none_without_history():
    snapshot = Snapshot()
    generator = ReportGenerator(snapshot)
    assert generator.generate() is None


def test_prepare_dataframe(snapshot_with_history):
    generator = ReportGenerator(snapshot_with_history)
    df = generator._prepare_dataframe()
    assert isinstance(df, pd.DataFrame)
    assert df.index.name == "last_window_end"
    # Check float conversion
    assert df["gross_volume"].dtype == "float64"
    assert df["total_settled"].iloc[0] == pytest.approx(150.0)


def test_generate_creates_file(tmp_path, snapshot_with_history):
    output_path = tmp_path / "report.png"
    generator = ReportGenerator(snapshot_with_history)
    result_df = generator.generate(str(output_path))
    assert output_path.exists()
    assert isinstance(result_df, pd.DataFrame)