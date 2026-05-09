# Covers: BE-RES-001, BE-RES-002, BE-RES-003
import pytest
from django.urls import reverse
from rest_framework import status

from tests.unit.api_test_helpers import authenticated_client, create_org, create_user


@pytest.mark.regression
@pytest.mark.p1
@pytest.mark.contracts
@pytest.mark.django_db
def test_be_res_001_validation_error_payload_shape_is_consistent():
    org = create_org("Contract Org")
    actor = create_user(org, email="contract-user@example.com")
    client = authenticated_client(actor)

    response = client.post(
        reverse("service-order-list-create"),
        {
            "org_id": org.id,
            "description": "missing title and customer_id",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert isinstance(response.data, dict)
    assert "detail" in response.data or "errors" in response.data


@pytest.mark.regression
@pytest.mark.p1
@pytest.mark.contracts
@pytest.mark.django_db
def test_be_res_002_not_found_payload_shape_is_consistent():
    org = create_org("Contract Org")
    actor = create_user(org, email="contract-user2@example.com")
    client = authenticated_client(actor)

    response = client.get(reverse("service-order-detail", kwargs={"order_id": 999999}), {"org_id": org.id})

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert isinstance(response.data, dict)
    assert "detail" in response.data


@pytest.mark.regression
@pytest.mark.p1
@pytest.mark.contracts
@pytest.mark.django_db
def test_be_res_003_method_not_allowed_payload_shape_is_consistent():
    org = create_org("Contract Org")
    actor = create_user(org, email="contract-user3@example.com")
    client = authenticated_client(actor)

    response = client.put(reverse("auth-login"), {"org_id": org.id}, format="json")

    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    assert isinstance(response.data, dict)
    assert "detail" in response.data
