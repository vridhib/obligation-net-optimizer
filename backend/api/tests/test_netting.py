from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
import pytest


@pytest.mark.django_db
@patch('streaming.tasks.run_simulation_task.delay')
def test_trigger_netting(mock_delay, api_client):
    mock_delay.return_value.id = "fake-task-id"

    csv_content = b"tx_id,payer,payee,amount,currency,timestamp\n1,A,B,100,USD,2026-08-11T08:00:00Z\n"
    csv_file = SimpleUploadedFile("test.csv", csv_content, content_type="text/csv")

    url = reverse('nettingwindow-trigger-netting')
    response = api_client.post(url, {'file': csv_file}, format='multipart')

    assert response.status_code == 202
    assert response.data['task_id'] == "fake-task-id"
    mock_delay.assert_called_once()