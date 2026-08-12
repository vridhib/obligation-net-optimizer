from streaming.tasks import run_simulation_task
from unittest.mock import patch


@patch('streaming.tasks.StreamSimulator.run')
@patch('obligations.utils.persist_window')
def test_run_simulation_task(mock_persist, mock_run):
    result = run_simulation_task("dummy.csv")
    assert result['windows_processed'] == 0
    mock_run.assert_called_once()