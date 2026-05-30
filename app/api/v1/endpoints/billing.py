import asyncio
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import get_current_student
from app.core.config import settings
from app.db.database import get_db
from app.db.models import Student
from app.services.billing_service import (
    construct_webhook_event,
    create_checkout_session,
    create_portal_session,
    handle_checkout_completed,
    handle_payment_failed,
    handle_subscription_deleted,
    handle_subscription_updated,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/billing", tags=["billing"])


class CheckoutRequest(BaseModel):
    success_path: str = "/dashboard?upgraded=true"
    cancel_path: str = "/pricing"


# ── POST /billing/checkout ────────────────────────────────────────────────────

@router.post("/checkout")
async def checkout(
    body: CheckoutRequest,
    student: Student = Depends(get_current_student),
):
    """Create a Stripe Checkout session. Returns a URL to redirect the student to."""
    if student.subscription_tier == "pro" and student.subscription_status == "active":
        raise HTTPException(400, detail="Already on Pro plan.")

    url = await asyncio.to_thread(
        create_checkout_session,
        str(student.id),
        student.email,
        f"{settings.frontend_url}{body.success_path}",
        f"{settings.frontend_url}{body.cancel_path}",
    )
    return {"url": url}


# ── POST /billing/portal ──────────────────────────────────────────────────────

@router.post("/portal")
async def portal(
    student: Student = Depends(get_current_student),
):
    """Create a Stripe Customer Portal session for managing subscription."""
    if not student.stripe_customer_id:
        raise HTTPException(400, detail="No billing account found. Please upgrade first.")

    url = await asyncio.to_thread(
        create_portal_session,
        student.stripe_customer_id,
        f"{settings.frontend_url}/dashboard",
    )
    return {"url": url}


# ── POST /billing/webhook ─────────────────────────────────────────────────────

@router.post("/webhook")
async def webhook(
    request: Request,
    stripe_signature: str = Header(alias="stripe-signature"),
    db: AsyncSession = Depends(get_db),
):
    """
    Stripe webhook receiver. No auth — verified by signature.
    Handles: checkout.session.completed, customer.subscription.deleted,
             invoice.payment_failed, customer.subscription.updated
    """
    payload = await request.body()

    try:
        event = await asyncio.to_thread(construct_webhook_event, payload, stripe_signature)
    except ValueError:
        raise HTTPException(400, detail="Invalid webhook signature.")

    event_type = event["type"]
    data = event["data"]["object"]
    logger.info("Stripe webhook: %s", event_type)

    try:
        if event_type == "checkout.session.completed":
            await handle_checkout_completed(data, db)
        elif event_type == "customer.subscription.deleted":
            await handle_subscription_deleted(data, db)
        elif event_type == "invoice.payment_failed":
            await handle_payment_failed(data, db)
        elif event_type == "customer.subscription.updated":
            await handle_subscription_updated(data, db)

        await db.commit()

    except Exception as e:
        logger.error("Webhook handler error [%s]: %s", event_type, e, exc_info=True)
        raise HTTPException(500, detail="Webhook processing failed.")

    return {"received": True}
