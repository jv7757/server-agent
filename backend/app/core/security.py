"""
安全相关工具：JWT、密码哈希、加密
"""

from datetime import datetime, timedelta
from typing import Any

from cryptography.fernet import Fernet
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

# 密码上下文
# Note: bcrypt has a 72-byte password limit, passlib handles this automatically
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  # Explicitly set rounds for consistency
)

# Fernet加密器（用于加密SSH密钥和密码）
try:
    fernet = Fernet(settings.encryption_key.encode())
except Exception as e:
    print("\n" + "=" * 80)
    print("ERROR: Invalid ENCRYPTION_KEY in environment variables!")
    print("=" * 80)
    print("\nTo generate a valid Fernet key, run this command:")
    print(
        '\n  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
    )
    print("\nThen add it to your .env file:")
    print("  ENCRYPTION_KEY=<generated_key>")
    print("\nExample .env entry:")
    print("  ENCRYPTION_KEY=xQzT-Hn8vYc6MZi2V7fKJ9kL3pN5rS8tA1wD4eG6hB0=")
    print("\n" + "=" * 80 + "\n")
    raise ValueError(f"Invalid ENCRYPTION_KEY: {str(e)}")


# ========== 密码哈希 ==========


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码

    Args:
        plain_password: 明文密码
        hashed_password: 哈希后的密码

    Returns:
        bool: 密码是否匹配

    Note:
        Applies the same 72-byte truncation as get_password_hash for consistency.
    """
    # Apply same truncation as get_password_hash
    password_bytes = plain_password.encode("utf-8")[:72]
    truncated_password = password_bytes.decode("utf-8", errors="ignore")
    return pwd_context.verify(truncated_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    生成密码哈希

    Args:
        password: 明文密码

    Returns:
        str: 哈希后的密码

    Note:
        bcrypt has a 72-byte password limit. Passwords are truncated to 72 bytes
        before hashing to prevent errors.
    """
    # bcrypt can only handle passwords up to 72 bytes
    # Encode to bytes, truncate, then decode back for passlib
    password_bytes = password.encode("utf-8")[:72]
    truncated_password = password_bytes.decode("utf-8", errors="ignore")
    return pwd_context.hash(truncated_password)


# ========== JWT Token ==========


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    创建访问令牌

    Args:
        data: 要编码的数据
        expires_delta: 过期时间增量

    Returns:
        str: JWT访问令牌
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    创建刷新令牌

    Args:
        data: 要编码的数据

    Returns:
        str: JWT刷新令牌
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def decode_token(token: str) -> dict[str, Any]:
    """
    解码JWT令牌

    Args:
        token: JWT令牌

    Returns:
        dict: 解码后的数据

    Raises:
        JWTError: Token无效或过期
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError as e:
        raise JWTError(f"Could not validate credentials: {str(e)}")


# ========== SSH凭证加密 ==========


def encrypt_ssh_credential(credential: str) -> str:
    """
    加密SSH凭证（密码或私钥）

    Args:
        credential: 明文凭证

    Returns:
        str: 加密后的凭证（Base64编码）
    """
    encrypted = fernet.encrypt(credential.encode())
    return encrypted.decode()


def decrypt_ssh_credential(encrypted_credential: str) -> str:
    """
    解密SSH凭证

    Args:
        encrypted_credential: 加密的凭证

    Returns:
        str: 明文凭证

    Raises:
        Exception: 解密失败
    """
    try:
        decrypted = fernet.decrypt(encrypted_credential.encode())
        return decrypted.decode()
    except Exception as e:
        raise Exception(f"Failed to decrypt credential: {str(e)}")


# ========== 密码强度验证 ==========


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    验证密码强度

    Args:
        password: 密码

    Returns:
        tuple[bool, str]: (是否有效, 错误消息)
    """
    if len(password) < settings.password_min_length:
        return False, f"Password must be at least {settings.password_min_length} characters"

    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)

    if not (has_upper and has_lower and has_digit):
        return (
            False,
            "Password must contain at least one uppercase letter, one lowercase letter, and one digit",
        )

    return True, ""
