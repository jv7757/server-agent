"""
认证服务
"""
from datetime import timedelta
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    validate_password_strength,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import LoginResponse, TokenResponse
from app.schemas.user import UserCreate, UserResponse


class AuthService:
    """认证服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, user_data: UserCreate) -> UserResponse:
        """
        用户注册

        Args:
            user_data: 用户注册数据

        Returns:
            UserResponse: 创建的用户信息

        Raises:
            ValueError: 用户名或邮箱已存在、密码强度不足
        """
        # 验证密码强度
        is_valid, error_msg = validate_password_strength(user_data.password)
        if not is_valid:
            raise ValueError(error_msg)

        # 检查用户名是否已存在
        existing_user = await self.db.execute(
            select(User).where(
                or_(User.username == user_data.username, User.email == user_data.email)
            )
        )
        if existing_user.scalar_one_or_none():
            raise ValueError("Username or email already exists")

        # 创建用户
        hashed_password = get_password_hash(user_data.password)
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            role="user",
            is_active=True,
        )

        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)

        return UserResponse.model_validate(new_user)

    async def login(self, username: str, password: str) -> LoginResponse:
        """
        用户登录

        Args:
            username: 用户名或邮箱
            password: 密码

        Returns:
            LoginResponse: 登录响应（包含用户信息和令牌）

        Raises:
            ValueError: 用户名或密码错误、账户未激活
        """
        # 查找用户（支持用户名或邮箱登录）
        result = await self.db.execute(
            select(User).where(or_(User.username == username, User.email == username))
        )
        user = result.scalar_one_or_none()

        # 验证用户存在且密码正确
        if not user or not verify_password(password, user.hashed_password):
            raise ValueError("Incorrect username or password")

        # 验证账户是否激活
        if not user.is_active:
            raise ValueError("Account is not active")

        # 生成令牌
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})

        return LoginResponse(
            user=UserResponse.model_validate(user),
            tokens=TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=settings.access_token_expire_minutes * 60,
            ),
        )

    async def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """
        刷新访问令牌

        Args:
            refresh_token: 刷新令牌

        Returns:
            TokenResponse: 新的访问令牌

        Raises:
            ValueError: 刷新令牌无效或过期
        """
        try:
            payload = decode_token(refresh_token)

            # 验证令牌类型
            if payload.get("type") != "refresh":
                raise ValueError("Invalid token type")

            user_id = payload.get("sub")
            if not user_id:
                raise ValueError("Invalid token payload")

            # 验证用户存在且激活
            result = await self.db.execute(select(User).where(User.id == UUID(user_id)))
            user = result.scalar_one_or_none()

            if not user or not user.is_active:
                raise ValueError("User not found or inactive")

            # 生成新的访问令牌
            access_token = create_access_token(data={"sub": str(user.id)})

            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,  # 返回原刷新令牌
                token_type="bearer",
                expires_in=settings.access_token_expire_minutes * 60,
            )

        except Exception as e:
            raise ValueError(f"Could not validate credentials: {str(e)}")

    async def get_current_user(self, token: str) -> User:
        """
        根据访问令牌获取当前用户

        Args:
            token: 访问令牌

        Returns:
            User: 当前用户

        Raises:
            ValueError: 令牌无效或用户不存在
        """
        try:
            payload = decode_token(token)

            # 验证令牌类型
            if payload.get("type") != "access":
                raise ValueError("Invalid token type")

            user_id = payload.get("sub")
            if not user_id:
                raise ValueError("Invalid token payload")

            # 查询用户
            result = await self.db.execute(select(User).where(User.id == UUID(user_id)))
            user = result.scalar_one_or_none()

            if not user:
                raise ValueError("User not found")

            if not user.is_active:
                raise ValueError("User is not active")

            return user

        except Exception as e:
            raise ValueError(f"Could not validate credentials: {str(e)}")

    async def change_password(
        self, user_id: UUID, old_password: str, new_password: str
    ) -> bool:
        """
        修改密码

        Args:
            user_id: 用户ID
            old_password: 旧密码
            new_password: 新密码

        Returns:
            bool: 是否成功

        Raises:
            ValueError: 旧密码错误、新密码强度不足
        """
        # 获取用户
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("User not found")

        # 验证旧密码
        if not verify_password(old_password, user.hashed_password):
            raise ValueError("Incorrect old password")

        # 验证新密码强度
        is_valid, error_msg = validate_password_strength(new_password)
        if not is_valid:
            raise ValueError(error_msg)

        # 更新密码
        user.hashed_password = get_password_hash(new_password)
        await self.db.commit()

        return True
