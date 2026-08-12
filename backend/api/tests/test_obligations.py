import pytest
from django.urls import reverse
from api.tests.factories import ObligationFactory


@pytest.mark.django_db
def test_list_obligations(api_client):
    ObligationFactory.create_batch(3)
    url = reverse('obligation-list')
    response = api_client.get(url)
    assert response.status_code == 200
    assert len(response.data) == 3


@pytest.mark.django_db
def test_create_obligation(api_client):
    url = reverse('obligation-list')
    data = {
        "payer": "A", 
        "payee": "B",
        "amount": "150.00",
        "currency": "USD",
        "timestamp": "2026-08-11T08:00:00Z",
    }
    response = api_client.post(url, data, format='json')
    assert response.status_code == 201
    assert response.data['status'] == 'pending'