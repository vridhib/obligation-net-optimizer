from unittest.mock import patch, Mock
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from datetime import datetime, timezone
from .factories import ObligationFactory, NettingWindowFactory, NetPositionFactory, SettlementAttemptFactory, ParticipantBalanceFactory
from obligations.models import Obligation


pytestmark = pytest.mark.django_db

# ---------- Obligation Endpoints ----------
def test_create_obligation_endpoint(api_client):
    url = reverse("obligation-list")
    data = {
        "payer": "Bank_A",
        "payee": "Bank_B",
        "amount": "100.00",
        "currency": "USD",
        "timestamp": "2026-08-11T08:00:00Z"
    }
    response = api_client.post(url, data, format="json")
    assert response.status_code == 201
    assert "tx_id" in response.data


def test_list_obligations_endpoint(api_client):
    ObligationFactory.create_batch(3)
    url = reverse("obligation-list")
    response = api_client.get(url)
    assert response.status_code == 200
    assert len(response.data) >= 3


def test_bulk_upload_csv(api_client):
    csv_content = (
        "payer,payee,amount,timestamp\n"
        "A,B,100.00,2026-08-11T08:00:00Z\n"
        "C,D,50.00,2026-08-11T08:01:00Z\n"
    )
    csv_file = SimpleUploadedFile("test.csv", csv_content.encode(), content_type="text/csv")
    url = reverse("obligation-bulk")
    response = api_client.post(url, {"file": csv_file}, format="multipart")
    assert response.status_code == 201
    assert response.data["created_count"] == 2


def test_bulk_upload_json(api_client):
    url = reverse("obligation-bulk")
    payload = [
        {
            "payer": "A",
            "payee": "B",
            "amount": "100.00",
            "currency": "USD",
            "timestamp": "2026-08-11T08:00:00Z"
        }
    ]
    response = api_client.post(url, payload, format="json")
    assert response.status_code == 201
    assert response.data["created_count"] == 1


# ---------- Netting Window Endpoints ----------
@patch("api.views.run_simulation_task.delay")
def test_trigger_netting_endpoint(mock_delay, api_client):
    mock_delay.return_value = Mock()
    mock_delay.return_value.id = "fake-task-id"
    url = reverse("nettingwindow-trigger-netting")
    response = api_client.post(url, {}, format="json")
    assert response.status_code == 202
    assert response.data["task_id"] == "fake-task-id"
    mock_delay.assert_called_once()


def test_positions_endpoint_latest(api_client):
    window = NettingWindowFactory()
    NetPositionFactory(window=window, participant="Bank_A", net_amount="-100.00")
    url = reverse("nettingwindow-positions")
    response = api_client.get(url, {"window": "latest"})
    assert response.status_code == 200
    assert response.data["window_id"] == window.window_id
    assert len(response.data["positions"]) == 1


def test_positions_endpoint_invalid_window(api_client):
    url = reverse("nettingwindow-positions")
    response = api_client.get(url, {"window": "abc"})
    assert response.status_code == 404


def test_summary_endpoint(api_client):
    w = NettingWindowFactory(
        gross_obligation_count=1,
        net_obligation_count=1,
        gross_volume="100.00",
        net_volume="50.00",
        liquidity_saved="50.00"
    )
    SettlementAttemptFactory(window=w, amount="50.00", status="settled")
    url = reverse("nettingwindow-summary")
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.data["total_windows"] == 1
    assert response.data["settled_attempts"] == 1


@pytest.mark.parametrize("window_param, view", [
    ("latest", "gross"),
    ("latest", "net"),
    ("1", "gross"),
    ("1", "net")
])
def test_graph_endpoint(window_param, view, api_client):
    window = NettingWindowFactory()
    # Create obligations or settlement attempts depending on view
    if view == "net":
        NetPositionFactory(window=window, participant="Bank_A", net_amount="-100.00")
        SettlementAttemptFactory(window=window, payer="Bank_A", payee="Bank_B", amount="50.00")
    else: # Create obligation linked to window
        ObligationFactory(payer="Bank_A", payee="Bank_B", amount=50.00, timestamp=datetime.now(timezone.utc), netting_window=window, status=Obligation.Status.NETTED)

    url = reverse("nettingwindow-graph")
    response = api_client.get(url, {"window": window_param, "view": view})
    assert response.status_code == 200
    assert response.data["window_id"] == window.window_id
    assert response.data["view"] == view
    assert len(response.data["nodes"]) >= 1
    assert len(response.data["edges"]) >= 1


def test_graph_endpoint_invalid_view(api_client):
    url = reverse("nettingwindow-graph")
    response = api_client.get(url, {"view": "invalid"})
    assert response.status_code == 400
    assert "error" in response.data


def test_graph_endpoint_invalid_window_id(api_client):
    url = reverse("nettingwindow-graph")
    response = api_client.get(url, {"window": "abc"})
    assert response.status_code == 404


# ---------- Participant Endpoint ----------
def test_participants_list(api_client):
    ParticipantBalanceFactory(participant="Bank_A", balance="1000.00")
    url = reverse("participantbalance-list")
    response = api_client.get(url)
    assert response.status_code == 200
    assert len(response.data) >= 1