from django.conf import settings
from django.urls import reverse

from orders.models import Order
from orders.models.verification import OrderPhoneVerification

from datetime import timedelta
import requests
import logging
import random
import string
import datetime
import phonenumbers


logger = logging.getLogger(__name__)


def _generate_code(length: int = 6) -> str:
    # numeric OTP for easier typing
    return ''.join(random.choices(string.digits, k=length))


def _normalize_phone(phone: str, region: str = 'LB') -> str:
    if not phone:
        return ''
    raw = phone.strip()
    if phonenumbers:
        try:
            num = phonenumbers.parse(raw, region)
            if not phonenumbers.is_valid_number(num):
                return ''
            return phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.E164)
        except Exception:
            return ''
    # Fallback: expect already E.164
    return raw.replace(' ', '')


def send_verification_code(order: Order, *, resend: bool = False, ttl_hours: int = 24) -> dict:
    """Create or reuse a pending verification and send the code via WhatsApp Graph API.

    Returns dict with success flag and message/error.
    """
    if not settings.WHATSAPP_ACCESS_TOKEN or not settings.WHATSAPP_PHONE_NUMBER_ID:
        return {"success": False, "error": "WhatsApp credentials not configured"}

    if not order or not order.customer or not order.customer.phone_number:
        return {"success": False, "error": "Missing customer phone number"}

    # Prefer region from customer address country, fallback to LB
    region = None
    try:
        if order.customer_address and order.customer_address.country:
            region = (order.customer_address.country.code or '').upper() or None
    except Exception:
        region = None

    recipient = _normalize_phone(order.customer.phone_number, region=region or 'LB')
    if not recipient:
        return {"success": False, "error": "Invalid customer phone number"}

    # Find existing pending verification if not forced resend
    verification = (
        order.phone_verifications.filter(status='pending').order_by('-created_at').first()
    )

    now = datetime.datetime.now()

    if verification and not resend and not verification.is_expired():
        code = verification.code
    else:
        # expire existing pending if any
        if verification and verification.status == 'pending':
            verification.status = 'expired'
            verification.save(update_fields=['status'])

        code = _generate_code()
        verification = OrderPhoneVerification.objects.create(
            order=order,
            phone_number=recipient,
            code=code,
            expires_at=now + timedelta(hours=ttl_hours),
            last_sent_at=now,
        )

    # Dispatch via WhatsApp Graph API
    try:
        api_url = f"https://graph.facebook.com/v20.0/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
        headers = {
            'Authorization': f'Bearer {settings.WHATSAPP_ACCESS_TOKEN}',
            'Content-Type': 'application/json'
        }

        # Prefer template if configured; otherwise send text (works only within 24h window)
        if getattr(settings, 'WHATSAPP_TEMPLATE_NAME', ''):
            payload = {
                "messaging_product": "whatsapp",
                "to": recipient,
                "type": "template",
                "template": {
                    "name": settings.WHATSAPP_TEMPLATE_NAME,
                    "language": {"code": getattr(settings, 'WHATSAPP_TEMPLATE_LANG', 'en_US')},
                    "components": [
                        {
                            "type": "body",
                            "parameters": [
                                {"type": "text", "text": code}
                            ]
                        }
                    ]
                }
            }
        else:
            message = (
                f"Your delivery verification code for order {order.tracking_number} is {code}. "
                f"It expires in {ttl_hours} hours."
            )
            payload = {
                "messaging_product": "whatsapp",
                "to": recipient,
                "type": "text",
                "text": {"preview_url": False, "body": message}
            }

        resp = requests.post(api_url, json=payload, headers=headers, timeout=15)
        if resp.status_code >= 200 and resp.status_code < 300:
            # mark last sent
            verification.last_sent_at = datetime.datetime.now()
            verification.save(update_fields=['last_sent_at'])
            return {"success": True, "message": "Verification code sent via WhatsApp"}

        try:
            data = resp.json()
        except Exception:
            data = {"error": resp.text}

        logger.warning("WhatsApp API error: %s", data)
        return {"success": False, "error": data.get('error', {}).get('message', 'Failed to send WhatsApp message')}

    except Exception as e:
        logger.exception("Error sending WhatsApp message")
        return {"success": False, "error": str(e)}


def verify_code(order: Order, code: str) -> dict:
    if not order or not code:
        return {"success": False, "error": "Invalid Code"}

    # Get latest pending verification
    v = order.phone_verifications.filter(status='pending').order_by('-created_at').first()
    if not v:
        return {"success": False, "error": "No active verification found"}

    if v.is_expired():
        v.status = 'expired'
        v.save(update_fields=['status'])
        return {"success": False, "error": "Verification code expired"}

    v.attempts += 1
    if v.code == code.strip():
        v.mark_verified()
        return {"success": True, "message": "Verification successful"}
    else:
        v.save(update_fields=['attempts'])
        return {"success": False, "error": "Invalid verification code"}


def send_order_scheduled(order: Order, tracking_url: str | None = None) -> dict:
    """Send a WhatsApp message to the customer with a tracking link.

    Falls back gracefully if WhatsApp is not configured or phone invalid.
    """
    if not settings.WHATSAPP_ACCESS_TOKEN or not settings.WHATSAPP_PHONE_NUMBER_ID:
        return {"success": False, "error": "WhatsApp credentials not configured"}

    if not order or not order.customer or not order.customer.phone_number:
        return {"success": False, "error": "Missing customer phone number"}

    # Compute tracking URL
    try:
        path = reverse('orders:public_track_detail', kwargs={'tracking_number': order.tracking_number})
    except Exception:
        path = f"/orders/track/{order.tracking_number}/"
    base = getattr(settings, 'SITE_URL', '') or ''
    url = tracking_url or (base.rstrip('/') + path) if base else path

    # Normalize phone
    region = None
    try:
        if order.customer_address and order.customer_address.country:
            region = (order.customer_address.country.code or '').upper() or None
    except Exception:
        region = None
    recipient = _normalize_phone(order.customer.phone_number, region=region or 'LB')
    if not recipient:
        return {"success": False, "error": "Invalid customer phone number"}

    # Compose and send
    api_url = f"https://graph.facebook.com/v20.0/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        'Authorization': f'Bearer {settings.WHATSAPP_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    message = (
        f"Your order {order.tracking_number} has been scheduled. "
        f"You can track it here: {url}"
    )
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient,
        "type": "text",
        "text": {"preview_url": True, "body": message}
    }

    try:
        resp = requests.post(api_url, json=payload, headers=headers, timeout=15)
        if 200 <= resp.status_code < 300:
            return {"success": True}
        try:
            data = resp.json()
        except Exception:
            data = {"error": resp.text}
        logger.warning("WhatsApp API error: %s", data)
        return {"success": False, "error": data.get('error', {}).get('message', 'Failed to send WhatsApp message')}
    except Exception as e:
        logger.exception("Error sending WhatsApp message")
        return {"success": False, "error": str(e)}
