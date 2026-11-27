import hashlib
import hmac
import secrets

# scrypt cost settings (CPU and memory per hash)
_N, _R, _P = 2**14, 8, 1


def hash_password(password: str) -> str:
    """'scrypt$<salt hex>$<hash hex>': a random salt per password, stored with it."""
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P)
    return f"scrypt${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    _, salt_hex, digest_hex = stored.split("$")
    digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt_hex), n=_N, r=_R, p=_P)
    return hmac.compare_digest(digest.hex(), digest_hex)  # constant time
