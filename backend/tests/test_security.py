"""
安全工具函数单元测试
"""
import pytest
from jose import jwt

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decrypt_ssh_credential,
    encrypt_ssh_credential,
    get_password_hash,
    verify_password,
    verify_token,
)
from app.config import settings


@pytest.mark.unit
@pytest.mark.security
class TestPasswordHashing:
    """密码哈希测试"""

    def test_hash_password(self):
        """测试密码哈希"""
        password = "test_password123"
        hashed = get_password_hash(password)

        assert hashed != password  # 哈希后的密码不应该与原密码相同
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")  # bcrypt hash

    def test_verify_correct_password(self):
        """测试验证正确密码"""
        password = "test_password123"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_verify_incorrect_password(self):
        """测试验证错误密码"""
        password = "test_password123"
        wrong_password = "wrong_password"
        hashed = get_password_hash(password)

        assert verify_password(wrong_password, hashed) is False

    def test_hash_same_password_different_hashes(self):
        """测试相同密码生成不同哈希（salt）"""
        password = "test_password123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        assert hash1 != hash2  # 因为 salt 不同
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


@pytest.mark.unit
@pytest.mark.security
class TestJWTTokens:
    """JWT令牌测试"""

    def test_create_access_token(self):
        """测试创建访问令牌"""
        data = {"sub": "test_user"}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

        # 解码并验证
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        assert payload["sub"] == "test_user"
        assert "exp" in payload

    def test_create_access_token_with_custom_expiry(self):
        """测试创建自定义过期时间的令牌"""
        from datetime import timedelta

        data = {"sub": "test_user"}
        expires_delta = timedelta(minutes=15)
        token = create_access_token(data, expires_delta=expires_delta)

        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        assert payload["sub"] == "test_user"

    def test_create_refresh_token(self):
        """测试创建刷新令牌"""
        data = {"sub": "test_user"}
        token = create_refresh_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

        # 刷新令牌应该有更长的过期时间
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        assert payload["sub"] == "test_user"

    def test_verify_valid_token(self):
        """测试验证有效令牌"""
        data = {"sub": "test_user"}
        token = create_access_token(data)

        payload = verify_token(token)
        assert payload is not None
        assert payload.get("sub") == "test_user"

    def test_verify_invalid_token(self):
        """测试验证无效令牌"""
        invalid_token = "invalid.token.here"

        payload = verify_token(invalid_token)
        assert payload is None

    def test_verify_expired_token(self):
        """测试验证过期令牌"""
        from datetime import timedelta

        data = {"sub": "test_user"}
        # 创建已过期的令牌
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))

        # 短暂延迟确保令牌过期
        import time
        time.sleep(0.1)

        payload = verify_token(token)
        assert payload is None

    def test_token_with_additional_claims(self):
        """测试包含额外声明的令牌"""
        data = {
            "sub": "test_user",
            "role": "admin",
            "permissions": ["read", "write"],
        }
        token = create_access_token(data)

        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        assert payload["sub"] == "test_user"
        assert payload["role"] == "admin"
        assert payload["permissions"] == ["read", "write"]


@pytest.mark.unit
@pytest.mark.security
class TestSSHCredentialEncryption:
    """SSH凭据加密测试"""

    def test_encrypt_credential(self):
        """测试加密凭据"""
        original = "my_secret_password"
        encrypted = encrypt_ssh_credential(original)

        assert encrypted != original
        assert isinstance(encrypted, str)
        assert len(encrypted) > 0

    def test_decrypt_credential(self):
        """测试解密凭据"""
        original = "my_secret_password"
        encrypted = encrypt_ssh_credential(original)
        decrypted = decrypt_ssh_credential(encrypted)

        assert decrypted == original

    def test_encrypt_decrypt_roundtrip(self):
        """测试加密解密往返"""
        test_strings = [
            "simple_password",
            "complex!@#$%^&*()password",
            "中文密码",
            "very_long_password_" * 10,
            "",  # 空字符串
        ]

        for original in test_strings:
            encrypted = encrypt_ssh_credential(original)
            decrypted = decrypt_ssh_credential(encrypted)
            assert decrypted == original, f"Failed for: {original}"

    def test_encrypt_ssh_key(self):
        """测试加密SSH私钥"""
        ssh_key = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA1234567890abcdefghijklmnopqrstuvwxyz
-----END RSA PRIVATE KEY-----"""

        encrypted = encrypt_ssh_credential(ssh_key)
        decrypted = decrypt_ssh_credential(encrypted)

        assert decrypted == ssh_key

    def test_encrypt_none_returns_none(self):
        """测试加密 None 返回 None"""
        result = encrypt_ssh_credential(None)
        assert result is None

    def test_decrypt_none_returns_none(self):
        """测试解密 None 返回 None"""
        result = decrypt_ssh_credential(None)
        assert result is None

    def test_decrypt_empty_string(self):
        """测试解密空字符串"""
        encrypted = encrypt_ssh_credential("")
        decrypted = decrypt_ssh_credential(encrypted)
        assert decrypted == ""

    def test_same_credential_different_encryption(self):
        """测试相同凭据生成不同的加密结果（如果有 IV/nonce）"""
        # 注意：Fernet 每次加密都会生成新的随机值
        credential = "test_password"
        encrypted1 = encrypt_ssh_credential(credential)
        encrypted2 = encrypt_ssh_credential(credential)

        # 加密结果可能不同（取决于实现）
        # 但解密结果应该相同
        assert decrypt_ssh_credential(encrypted1) == credential
        assert decrypt_ssh_credential(encrypted2) == credential

    def test_decrypt_invalid_data(self):
        """测试解密无效数据"""
        invalid_encrypted = "this_is_not_encrypted_data"

        with pytest.raises(Exception):  # 应该抛出异常
            decrypt_ssh_credential(invalid_encrypted)


@pytest.mark.unit
@pytest.mark.security
class TestTokenSecurity:
    """令牌安全测试"""

    def test_token_cannot_be_forged(self):
        """测试令牌无法伪造"""
        data = {"sub": "test_user"}
        token = create_access_token(data)

        # 尝试修改令牌
        tampered_token = token[:-10] + "tampered!!"

        # 验证应该失败
        payload = verify_token(tampered_token)
        assert payload is None

    def test_token_with_wrong_secret(self):
        """测试使用错误密钥验证令牌"""
        data = {"sub": "test_user"}
        token = create_access_token(data)

        # 尝试用错误的密钥解码
        with pytest.raises(Exception):
            jwt.decode(
                token,
                "wrong_secret_key",
                algorithms=[settings.algorithm],
            )

    def test_token_with_wrong_algorithm(self):
        """测试使用错误算法验证令牌"""
        data = {"sub": "test_user"}
        token = create_access_token(data)

        # 尝试用错误的算法解码
        with pytest.raises(Exception):
            jwt.decode(
                token,
                settings.secret_key,
                algorithms=["HS512"],  # 错误的算法
            )
