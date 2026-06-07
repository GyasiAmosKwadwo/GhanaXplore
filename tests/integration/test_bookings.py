from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import API_PREFIX
from app.models.attraction import Attraction
from app.models.booking import Booking
from app.models.time_slot import TimeSlot
from app.models.tourism_common import ApprovalStatus, AttractionStatus, BookingStatus
from app.models.user import User


@pytest.mark.asyncio
async def test_create_booking_with_capacity_check(
    client: AsyncClient,
    auth_headers: dict,
    approved_attraction: Attraction,
    time_slot: TimeSlot,
    visit_date: date,
):
    response = await client.post(
        f"{API_PREFIX}/bookings/",
        headers=auth_headers,
        json={
            "attraction_id": str(approved_attraction.id),
            "time_slot_id": str(time_slot.id),
            "visit_date": visit_date.isoformat(),
            "party_size": 4,
            "total_amount_ghs": "200.00",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == BookingStatus.PENDING.value
    assert data["time_slot_id"] == str(time_slot.id)
    assert data["party_size"] == 4
    assert data["booking_reference"].startswith("GHX-")
    assert data["qr_code_token"] is None


@pytest.mark.asyncio
async def test_create_booking_capacity_exceeded_returns_409(
    client: AsyncClient,
    auth_headers: dict,
    db_session: AsyncSession,
    test_user: User,
    approved_attraction: Attraction,
    visit_date: date,
):
    full_slot = TimeSlot(
        attraction_id=approved_attraction.id,
        start_time="14:00",
        end_time="16:00",
        max_capacity=5,
        is_active=True,
    )
    db_session.add(full_slot)
    await db_session.flush()

    existing = Booking(
        tourist_id=test_user.id,
        attraction_id=approved_attraction.id,
        time_slot_id=full_slot.id,
        visit_date=visit_date,
        party_size=4,
        total_amount_ghs=Decimal("200.00"),
        status=BookingStatus.CONFIRMED,
        booking_reference=uuid4().hex,
    )
    db_session.add(existing)
    await db_session.commit()

    response = await client.post(
        f"{API_PREFIX}/bookings/",
        headers=auth_headers,
        json={
            "attraction_id": str(approved_attraction.id),
            "time_slot_id": str(full_slot.id),
            "visit_date": visit_date.isoformat(),
            "party_size": 2,
            "total_amount_ghs": "100.00",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Time slot capacity exceeded"


@pytest.mark.asyncio
async def test_cancel_booking(
    client: AsyncClient,
    auth_headers: dict,
    approved_attraction: Attraction,
    time_slot: TimeSlot,
    visit_date: date,
):
    create_response = await client.post(
        f"{API_PREFIX}/bookings/",
        headers=auth_headers,
        json={
            "attraction_id": str(approved_attraction.id),
            "time_slot_id": str(time_slot.id),
            "visit_date": visit_date.isoformat(),
            "party_size": 2,
            "total_amount_ghs": "100.00",
        },
    )
    booking_id = create_response.json()["id"]

    cancel_response = await client.patch(
        f"{API_PREFIX}/bookings/{booking_id}/cancel",
        headers=auth_headers,
    )

    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == BookingStatus.CANCELLED.value


@pytest.mark.asyncio
async def test_operator_lists_managed_bookings(
    client: AsyncClient,
    auth_headers: dict,
    operator_auth_headers: dict,
    approved_attraction: Attraction,
    time_slot: TimeSlot,
    visit_date: date,
):
    await client.post(
        f"{API_PREFIX}/bookings/",
        headers=auth_headers,
        json={
            "attraction_id": str(approved_attraction.id),
            "time_slot_id": str(time_slot.id),
            "visit_date": visit_date.isoformat(),
            "party_size": 3,
            "total_amount_ghs": "150.00",
        },
    )

    response = await client.get(
        f"{API_PREFIX}/bookings/managed",
        headers=operator_auth_headers,
        params={"attraction_id": str(approved_attraction.id)},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["pagination"]["total"] == 1
    assert len(payload["items"]) == 1
    assert payload["items"][0]["attraction_id"] == str(approved_attraction.id)


@pytest.mark.asyncio
async def test_confirm_booking_issues_qr_token(
    client: AsyncClient,
    auth_headers: dict,
    operator_auth_headers: dict,
    approved_attraction: Attraction,
    time_slot: TimeSlot,
    visit_date: date,
):
    create_response = await client.post(
        f"{API_PREFIX}/bookings/",
        headers=auth_headers,
        json={
            "attraction_id": str(approved_attraction.id),
            "time_slot_id": str(time_slot.id),
            "visit_date": visit_date.isoformat(),
            "party_size": 1,
            "total_amount_ghs": "50.00",
        },
    )
    booking_id = create_response.json()["id"]

    confirm_response = await client.patch(
        f"{API_PREFIX}/bookings/{booking_id}/confirm",
        headers=operator_auth_headers,
    )

    assert confirm_response.status_code == 200
    data = confirm_response.json()
    assert data["status"] == BookingStatus.CONFIRMED.value
    assert data["qr_code_token"] is not None
    assert len(data["qr_code_token"]) >= 32


@pytest.mark.asyncio
async def test_create_booking_rejects_past_visit_date(
    client: AsyncClient,
    auth_headers: dict,
    approved_attraction: Attraction,
    time_slot: TimeSlot,
):
    past_date = date.today() - timedelta(days=1)
    response = await client.post(
        f"{API_PREFIX}/bookings/",
        headers=auth_headers,
        json={
            "attraction_id": str(approved_attraction.id),
            "time_slot_id": str(time_slot.id),
            "visit_date": past_date.isoformat(),
            "party_size": 1,
            "total_amount_ghs": "50.00",
        },
    )

    assert response.status_code == 400
    assert "past" in response.json()["detail"].lower()
