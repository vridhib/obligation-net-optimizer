import pytest
from unittest.mock import patch
from obligations.models import Obligation
from streaming.tasks import run_simulation_task
from api.tests.factories import ObligationFactory


@pytest.mark.django_db
@patch('streaming.tasks.StreamSimulator.run')
def test_run_simulation_task_no_pending(mock_run):
    result = run_simulation_task()
    assert result['windows_processed'] == 0
    mock_run.assert_not_called()


@pytest.mark.django_db
@patch('streaming.tasks.StreamSimulator.run')
def test_run_simulation_task_with_pending(mock_run):
    # Create 2 pending obligations
    ObligationFactory.create_batch(2, status=Obligation.Status.PENDING)
    result = run_simulation_task()

    # Task should return 0 windows (since mocked)
    assert result["windows_processed"] == 0
    mock_run.assert_called_once()

    # Extract obligations passed to run
    args, _ = mock_run.call_args
    obligations_passed = args[0]
    print(obligations_passed)
    assert len(obligations_passed) == 2
    assert all(isinstance(o, tuple) for o in obligations_passed)
    assert obligations_passed[0].tx_id == str(Obligation.objects.last().tx_id)