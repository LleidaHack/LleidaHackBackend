"""Offline signing tests: python -m unittest tests/test_apple_wallet.py."""

import hashlib
import io
import json
import subprocess
import tempfile
import unittest
import zipfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID

from src.utils.apple_wallet import build_pass, wallet_url


class AppleWalletTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        now = datetime.now(UTC)
        ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Test WWDR")])
        ca = (
            x509.CertificateBuilder()
            .subject_name(ca_name)
            .issuer_name(ca_name)
            .public_key(ca_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(days=1))
            .not_valid_after(now + timedelta(days=3))
            .add_extension(
                x509.BasicConstraints(ca=True, path_length=None), critical=True
            )
            .sign(ca_key, hashes.SHA256())
        )
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = x509.Name(
            [
                x509.NameAttribute(NameOID.USER_ID, "pass.cat.lleidahack.tickets"),
                x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "5F659SC689"),
            ]
        )
        certificate = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(ca_name)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(days=1))
            .not_valid_after(now + timedelta(days=1))
            .sign(ca_key, hashes.SHA256())
        )
        (self.root / "pass.p12").write_bytes(
            pkcs12.serialize_key_and_certificates(
                b"test",
                key,
                certificate,
                None,
                serialization.BestAvailableEncryption(b"test-password"),
            )
        )
        (self.root / "password").write_bytes(b"test-password")
        (self.root / "wwdr.pem").write_bytes(
            ca.public_bytes(serialization.Encoding.PEM)
        )
        self.settings = SimpleNamespace(
            apple_wallet_team_id="5F659SC689",
            apple_wallet_pass_type_id="pass.cat.lleidahack.tickets",
            apple_wallet_p12_path=str(self.root / "pass.p12"),
            apple_wallet_password_file=str(self.root / "password"),
            apple_wallet_wwdr_path=str(self.root / "wwdr.pem"),
            back_url="https://example.test/",
        )
        self.event = SimpleNamespace(
            id=2, name="HackEPS", start_date=now, location="Lleida"
        )
        self.hacker = SimpleNamespace(
            id=7, name="Participant", code="ExistingProfileCode", access_role="hacker"
        )

    def test_signed_archive_preserves_profile_qr_and_stable_serial(self):
        with zipfile.ZipFile(
            io.BytesIO(build_pass(self.settings, self.event, self.hacker))
        ) as archive:
            payload = json.loads(archive.read("pass.json"))
            self.assertEqual(payload["barcodes"][0]["message"], self.hacker.code)
            self.assertEqual(payload["serialNumber"], "event-2-hacker-7")
            self.assertEqual(
                payload["eventTicket"]["secondaryFields"][1]["value"], "Hacker"
            )
            self.assertNotIn("logoText", payload)
            self.assertIn("logo@3x.png", archive.namelist())
            manifest = json.loads(archive.read("manifest.json"))
            for name, digest in manifest.items():
                self.assertEqual(hashlib.sha1(archive.read(name)).hexdigest(), digest)
            for name in ("signature", "manifest.json"):
                (self.root / name).write_bytes(archive.read(name))
        result = subprocess.run(
            [
                "openssl",
                "smime",
                "-verify",
                "-inform",
                "DER",
                "-in",
                str(self.root / "signature"),
                "-content",
                str(self.root / "manifest.json"),
                "-noverify",
                "-out",
                str(self.root / "verified"),
            ],
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_rejects_wrong_team(self):
        self.settings.apple_wallet_team_id = "WRONGTEAM1"
        with self.assertRaises(ValueError):
            build_pass(self.settings, self.event, self.hacker)

    def test_rejects_wrong_password(self):
        (self.root / "password").write_bytes(b"wrong")
        with self.assertRaises(ValueError):
            build_pass(self.settings, self.event, self.hacker)

    def test_disabled_configuration_has_no_link(self):
        self.settings.apple_wallet_p12_path = ""
        self.assertIsNone(wallet_url(self.settings, 2, self.hacker.code))

    def test_role_comes_from_account_and_unknown_roles_are_rejected(self):
        from src.utils.apple_wallet import participant_role

        for role, label in (
            ("hacker", "Hacker"),
            ("mentor", "Mentor"),
            ("admin", "Staff"),
            ("superadmin", "Staff"),
            ("lleidahacker", "Staff"),
        ):
            self.hacker.access_role = role
            self.assertEqual(participant_role(self.hacker), label)
        self.hacker.access_role = "company"
        with self.assertRaises(ValueError):
            participant_role(self.hacker)
