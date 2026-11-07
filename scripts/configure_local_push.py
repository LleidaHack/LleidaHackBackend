"""Generate local-only Web Push keys without exposing the private key."""

import base64
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

root = Path(__file__).resolve().parents[1]
env = root / ".env.operations.local"
if not env.exists():
    raise SystemExit("Run scripts/local-operations.sh first")
if "VAPID_PRIVATE_KEY=" not in env.read_text():
    key = ec.generate_private_key(ec.SECP256R1())
    private_path = root / ".vapid.operations.local.pem"
    private_path.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    private_path.chmod(0o600)
    public = (
        base64.urlsafe_b64encode(
            key.public_key().public_bytes(
                serialization.Encoding.X962,
                serialization.PublicFormat.UncompressedPoint,
            )
        )
        .rstrip(b"=")
        .decode()
    )
    with env.open("a") as stream:
        stream.write(
            f"VAPID_PRIVATE_KEY={private_path}\nVAPID_PUBLIC_KEY={public}\nVAPID_SUBJECT=mailto:organizer@example.test\n"
        )
print("Local Web Push keys are configured. Restart the API and run the push worker.")
