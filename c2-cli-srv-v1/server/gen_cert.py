"""
Generate self-signed certificate for the HTTPS (TLS) server.
Requires: pip install cryptography
"""

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import datetime, ipaddress, os

OUT_DIR  = os.path.dirname(__file__)
CERT_OUT = os.path.join(OUT_DIR, "cert.pem")
KEY_OUT  = os.path.join(OUT_DIR, "key.pem")

key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

subject = issuer = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME,        "KR"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME,   "WhatsUp Demo"),
    x509.NameAttribute(NameOID.COMMON_NAME,         "127.0.0.1"),
])

cert = (
    x509.CertificateBuilder()
    .subject_name(subject)
    .issuer_name(issuer)
    .public_key(key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
    .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3650))
    .add_extension(
        x509.SubjectAlternativeName([
            x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
        ]),
        critical=False,
    )
    .sign(key, hashes.SHA256())
)

with open(KEY_OUT, "wb") as f:
    f.write(key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    ))

with open(CERT_OUT, "wb") as f:
    f.write(cert.public_bytes(serialization.Encoding.PEM))

print(f"cert → {CERT_OUT}")
print(f"key  → {KEY_OUT}")
