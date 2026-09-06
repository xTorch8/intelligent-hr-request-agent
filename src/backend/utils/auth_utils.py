import base64
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import jwt
from typing import Any, Dict, Optional

from ..configs.auth_config import AuthConfig


def hash_password(password: str, salt: Optional[str] = None) -> str:
    if not salt:
        salt = "salt123"
    pwd_bytes = password.encode("utf-8")
    salt_bytes = salt.encode("utf-8")
    dk = hashlib.pbkdf2_hmac("sha256", pwd_bytes, salt_bytes, 100000)
    hash_hex = dk.hex()
    return f"pbkdf2_sha256$100000${salt}${hash_hex}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password or not plain_password:
        return False
    parts = hashed_password.split("$")
    if len(parts) == 4 and parts[0] == "pbkdf2_sha256":
        salt = parts[2]
        expected_hash = hash_password(plain_password, salt = salt)
        return hmac.compare_digest(expected_hash, hashed_password)
    plain_hash = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()
    return hmac.compare_digest(plain_hash, hashed_password)


def _b64encode_url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64decode_url(data_str: str) -> bytes:
    padding = 4 - (len(data_str) % 4)
    if padding != 4:
        data_str += "=" * padding
    return base64.urlsafe_b64encode(base64.urlsafe_b64decode(data_str.encode("utf-8")))


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes = AuthConfig.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": int(expire.timestamp()), "iat": int(now.timestamp())})

    try:
        return jwt.encode(to_encode, AuthConfig.SECRET_KEY, algorithm = AuthConfig.ALGORITHM)
    except ImportError:
        header = {"alg": "HS256", "typ": "JWT"}
        header_b64 = _b64encode_url(json.dumps(header, separators = (",", ":")).encode("utf-8"))
        payload_b64 = _b64encode_url(json.dumps(to_encode, separators = (",", ":")).encode("utf-8"))
        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
        signature = hmac.new(AuthConfig.SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
        sig_b64 = _b64encode_url(signature)
        return f"{header_b64}.{payload_b64}.{sig_b64}"


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        try:
            return jwt.decode(token, AuthConfig.SECRET_KEY, algorithms = [AuthConfig.ALGORITHM])
        except ImportError:
            parts = token.split(".")
            if len(parts) != 3:
                return None
            header_b64, payload_b64, sig_b64 = parts
            signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
            expected_sig = hmac.new(AuthConfig.SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
            actual_sig = base64.urlsafe_b64decode(sig_b64 + "=" * ((4 - len(sig_b64) % 4) % 4))
            if not hmac.compare_digest(expected_sig, actual_sig):
                return None
            payload_json = base64.urlsafe_b64decode(payload_b64 + "=" * ((4 - len(payload_b64) % 4) % 4)).decode("utf-8")
            payload = json.loads(payload_json)
            exp = payload.get("exp")
            if exp and int(datetime.now(timezone.utc).timestamp()) > exp:
                return None
            return payload
    except Exception:
        return None
