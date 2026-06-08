from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attraction import Attraction
from app.models.tourism_common import ApprovalStatus, AttractionStatus
from app.models.user import User
from tests.conftest import API_PREFIX


def _attraction_payload(slug: str = "kakum-national-park", **overrides) -> dict:
    payload = {
        "slug": slug,
        "name": "Kakum National Park",
        "region": "Central",
        "description": "Canopy walkway and rainforest reserve.",
        "category": "nature",
        "entry_fee_ghs": "40.00",
        "activities": [
            {
                "name": "Canopy Walk",
                "slug": "canopy-walk",
                "description": "Guided canopy walkway experience.",
                "price_ghs": "25.00",
                "duration_minutes": 90,
                "requires_advance_booking": True,
            }
        ],
    }
    payload.update(overrides)
    return payload


@pytest.mark.asyncio
async def test_operator_creates_attraction_with_activities(
    client: AsyncClient,
    operator_auth_headers: dict,
):
    response = await client.post(
        f"{API_PREFIX}/attractions/",
        headers=operator_auth_headers,
        json=_attraction_payload(),
    )

    assert response.status_code == 201
    data = response.json()
    assert data["slug"] == "kakum-national-park"
    assert data["approval_status"] == ApprovalStatus.PENDING.value
    assert data["status"] == AttractionStatus.PENDING_APPROVAL.value
    assert len(data["activities"]) == 1
    assert data["activities"][0]["slug"] == "canopy-walk"
    assert data["activities"][0]["requires_advance_booking"] is True


@pytest.mark.asyncio
async def test_pending_attraction_not_visible_publicly(
    client: AsyncClient,
    operator_auth_headers: dict,
):
    create_response = await client.post(
        f"{API_PREFIX}/attractions/",
        headers=operator_auth_headers,
        json=_attraction_payload(slug="hidden-waterfall"),
    )
    attraction_id = create_response.json()["id"]

    list_response = await client.get(f"{API_PREFIX}/attractions")
    assert list_response.status_code == 200
    assert list_response.json()["pagination"]["total"] == 0

    get_response = await client.get(f"{API_PREFIX}/attractions/{attraction_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_approval_makes_attraction_public(
    client: AsyncClient,
    operator_auth_headers: dict,
    test_admin: User,
    redis_client,
):
    from tests.conftest import _auth_headers

    create_response = await client.post(
        f"{API_PREFIX}/attractions/",
        headers=operator_auth_headers,
        json=_attraction_payload(slug="elmina-castle", name="Elmina Castle"),
    )
    attraction_id = create_response.json()["id"]

    admin_headers = await _auth_headers(test_admin, redis_client)
    approve_response = await client.patch(
        f"{API_PREFIX}/attractions/{attraction_id}/approval",
        headers=admin_headers,
        json={"approval_status": ApprovalStatus.APPROVED.value},
    )

    assert approve_response.status_code == 200
    approved = approve_response.json()
    assert approved["approval_status"] == ApprovalStatus.APPROVED.value
    assert approved["status"] == AttractionStatus.ACTIVE.value

    list_response = await client.get(f"{API_PREFIX}/attractions")
    assert list_response.status_code == 200
    assert list_response.json()["pagination"]["total"] == 1

    get_response = await client.get(f"{API_PREFIX}/attractions/{attraction_id}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Elmina Castle"


@pytest.mark.asyncio
async def test_operator_lists_own_attractions(
    client: AsyncClient,
    operator_auth_headers: dict,
):
    await client.post(
        f"{API_PREFIX}/attractions/",
        headers=operator_auth_headers,
        json=_attraction_payload(slug="mole-national-park"),
    )

    response = await client.get(
        f"{API_PREFIX}/attractions/me",
        headers=operator_auth_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["pagination"]["total"] == 1
    assert payload["items"][0]["slug"] == "mole-national-park"


@pytest.mark.asyncio
async def test_operator_updates_own_attraction(
    client: AsyncClient,
    operator_auth_headers: dict,
):
    create_response = await client.post(
        f"{API_PREFIX}/attractions/",
        headers=operator_auth_headers,
        json=_attraction_payload(slug="boti-falls"),
    )
    attraction_id = create_response.json()["id"]

    update_response = await client.patch(
        f"{API_PREFIX}/attractions/{attraction_id}",
        headers=operator_auth_headers,
        json={"name": "Boti Falls Reserve", "is_available": False},
    )

    assert update_response.status_code == 200
    data = update_response.json()
    assert data["name"] == "Boti Falls Reserve"
    assert data["is_available"] is False


@pytest.mark.asyncio
async def test_operator_deletes_own_attraction(
    client: AsyncClient,
    operator_auth_headers: dict,
):
    create_response = await client.post(
        f"{API_PREFIX}/attractions/",
        headers=operator_auth_headers,
        json=_attraction_payload(slug="wli-waterfalls"),
    )
    attraction_id = create_response.json()["id"]

    delete_response = await client.delete(
        f"{API_PREFIX}/attractions/{attraction_id}",
        headers=operator_auth_headers,
    )
    assert delete_response.status_code == 204

    me_response = await client.get(
        f"{API_PREFIX}/attractions/me",
        headers=operator_auth_headers,
    )
    assert me_response.json()["pagination"]["total"] == 0


@pytest.mark.asyncio
async def test_unavailable_approved_attraction_hidden_from_public(
    client: AsyncClient,
    db_session: AsyncSession,
    test_operator: User,
):
    attraction = Attraction(
        slug="closed-site",
        name="Closed Site",
        region="Ashanti",
        description="Temporarily closed.",
        category="historical",
        approval_status=ApprovalStatus.APPROVED,
        status=AttractionStatus.ACTIVE,
        is_available=False,
        operator_id=test_operator.id,
    )
    db_session.add(attraction)
    await db_session.commit()

    list_response = await client.get(f"{API_PREFIX}/attractions")
    assert list_response.json()["pagination"]["total"] == 0

    get_response = await client.get(f"{API_PREFIX}/attractions/{attraction.id}")
    assert get_response.status_code == 404
