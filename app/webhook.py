import hashlib
import hmac
import os

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")


def verify_signature(
    body: bytes,
    signature_header: str | None,
) -> bool:
    if not signature_header:
        return False

    expected_signature = (
        "sha256="
        + hmac.new(
            WEBHOOK_SECRET.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()
    )

    return hmac.compare_digest(
        expected_signature,
        signature_header,
    )
