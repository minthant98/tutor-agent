import logging
import stripe
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.db.models import Student

stripe.api_key = settings.stripe_secret_key
logger = logging.getLogger(__name__)

_STATUS_MAP = {
    "active": "active",
    "trialing": "active",
    "past_due": "past_due",
    "canceled": "cancelled",
    "unpaid": "past_due",
    "incomplete": "past_due",
}


def create_checkout_session(student_id: str, student_email: str, success_url: str, cancel_url: str) -> str:
    """Create a Stripe Checkout session. Returns the checkout URL."""
    session = stripe.checkout.Session.create(
        mode="subscription",
        payment_method_types=["card"],
        customer_email=student_email,
        client_reference_id=student_id,
        line_items=[{"price": settings.stripe_pro_price_id, "quantity": 1}],
        subscription_data={"trial_period_days": 7},
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return session.url


def create_portal_session(stripe_customer_id: str, return_url: str) -> str:
    """Create a Stripe Customer Portal session. Returns the portal URL."""
    session = stripe.billing_portal.Session.create(
        customer=stripe_customer_id,
        return_url=return_url,
    )
    return session.url


def construct_webhook_event(payload: bytes, sig_header: str) -> stripe.Event:
    """Verify webhook signature and return the event. Raises ValueError on bad signature."""
    try:
        return stripe.Webhook.construct_event(payload, sig_header, settings.stripe_webhook_secret)
    except stripe.error.SignatureVerificationError as e:
        raise ValueError(f"Invalid Stripe signature: {e}") from e


async def handle_checkout_completed(session_obj: dict, db: AsyncSession) -> None:
    student_id = session_obj.get("client_reference_id")
    if not student_id:
        logger.warning("checkout.session.completed missing client_reference_id")
        return

    student = await _get_student(student_id, db)
    if not student:
        return

    student.subscription_tier = "pro"
    student.subscription_status = "active"
    student.stripe_customer_id = session_obj.get("customer")
    student.stripe_subscription_id = session_obj.get("subscription")
    await db.flush()
    logger.info("Student %s upgraded to pro", student_id)


async def handle_subscription_deleted(subscription: dict, db: AsyncSession) -> None:
    student = await _get_student_by_subscription(subscription["id"], db)
    if not student:
        return

    student.subscription_tier = "free"
    student.subscription_status = "cancelled"
    student.stripe_subscription_id = None
    await db.flush()
    logger.info("Student %s downgraded to free (subscription cancelled)", student.id)


async def handle_payment_failed(invoice: dict, db: AsyncSession) -> None:
    student = await _get_student_by_customer(invoice.get("customer"), db)
    if not student:
        return

    student.subscription_status = "past_due"
    await db.flush()
    logger.info("Payment failed for student %s", student.id)


async def handle_subscription_updated(subscription: dict, db: AsyncSession) -> None:
    student = await _get_student_by_subscription(subscription["id"], db)
    if not student:
        return

    student.subscription_status = _STATUS_MAP.get(subscription["status"], subscription["status"])
    await db.flush()
    logger.info("Subscription updated for student %s → %s", student.id, student.subscription_status)


async def _get_student(student_id: str, db: AsyncSession) -> Student | None:
    result = await db.execute(select(Student).where(Student.id == student_id))
    return result.scalar_one_or_none()


async def _get_student_by_subscription(subscription_id: str, db: AsyncSession) -> Student | None:
    result = await db.execute(
        select(Student).where(Student.stripe_subscription_id == subscription_id)
    )
    return result.scalar_one_or_none()


async def _get_student_by_customer(customer_id: str | None, db: AsyncSession) -> Student | None:
    if not customer_id:
        return None
    result = await db.execute(
        select(Student).where(Student.stripe_customer_id == customer_id)
    )
    return result.scalar_one_or_none()
