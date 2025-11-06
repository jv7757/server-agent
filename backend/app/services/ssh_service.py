"""
SSH连接服务
"""
import asyncio
from typing import Any

import paramiko
from paramiko.ssh_exception import SSHException

from app.config import settings
from app.core.security import decrypt_ssh_credential
from app.utils.logger import logger


class SSHService:
    """SSH连接服务类"""

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str | None = None,
        private_key: str | None = None,
    ):
        """
        初始化SSH服务

        Args:
            host: 主机地址
            port: SSH端口
            username: 用户名
            password: 密码（可选）
            private_key: 私钥内容（可选）
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.private_key = private_key
        self.client: paramiko.SSHClient | None = None

    async def connect(self) -> bool:
        """
        建立SSH连接

        Returns:
            bool: 连接是否成功

        Raises:
            SSHException: SSH连接失败
        """
        try:
            # 在线程池中执行SSH连接（Paramiko是同步的）
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._connect_sync)
            return True
        except Exception as e:
            logger.error(f"SSH connection failed to {self.host}:{self.port} - {str(e)}")
            raise SSHException(f"Failed to connect: {str(e)}")

    def _connect_sync(self) -> None:
        """同步建立SSH连接"""
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        connect_kwargs = {
            "hostname": self.host,
            "port": self.port,
            "username": self.username,
            "timeout": 10,
        }

        # 优先使用私钥认证
        if self.private_key:
            try:
                import io
                key_file = io.StringIO(self.private_key)
                pkey = paramiko.RSAKey.from_private_key(key_file)
                connect_kwargs["pkey"] = pkey
            except Exception as e:
                logger.warning(f"Failed to load private key: {str(e)}, falling back to password")
                if self.password:
                    connect_kwargs["password"] = self.password
        elif self.password:
            connect_kwargs["password"] = self.password

        self.client.connect(**connect_kwargs)

    async def disconnect(self) -> None:
        """断开SSH连接"""
        if self.client:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.client.close)
            self.client = None

    async def execute_command(
        self, command: str, timeout: int | None = None
    ) -> dict[str, Any]:
        """
        执行SSH命令

        Args:
            command: 要执行的命令
            timeout: 超时时间（秒）

        Returns:
            dict: 执行结果
                - exit_code: 退出码
                - stdout: 标准输出
                - stderr: 标准错误
                - execution_time_ms: 执行时间（毫秒）

        Raises:
            Exception: 命令执行失败
        """
        if not self.client:
            raise Exception("Not connected to SSH server")

        timeout = timeout or settings.command_execution_timeout

        try:
            import time
            start_time = time.time()

            # 在线程池中执行命令
            loop = asyncio.get_event_loop()
            stdin, stdout, stderr = await loop.run_in_executor(
                None, self.client.exec_command, command, timeout
            )

            # 读取输出
            stdout_data = await loop.run_in_executor(None, stdout.read)
            stderr_data = await loop.run_in_executor(None, stderr.read)
            exit_code = stdout.channel.recv_exit_status()

            execution_time = int((time.time() - start_time) * 1000)

            result = {
                "exit_code": exit_code,
                "stdout": stdout_data.decode("utf-8", errors="ignore"),
                "stderr": stderr_data.decode("utf-8", errors="ignore"),
                "execution_time_ms": execution_time,
            }

            logger.info(f"Command executed on {self.host}: {command} (exit: {exit_code})")
            return result

        except Exception as e:
            logger.error(f"Command execution failed on {self.host}: {str(e)}")
            raise Exception(f"Command execution failed: {str(e)}")

    async def test_connection(self) -> dict[str, Any]:
        """
        测试SSH连接

        Returns:
            dict: 测试结果
                - status: success 或 error
                - message: 消息
                - latency_ms: 延迟（毫秒）
        """
        import time
        start_time = time.time()

        try:
            await self.connect()

            # 执行简单命令测试
            result = await self.execute_command("echo 'Connection test'", timeout=5)

            latency = int((time.time() - start_time) * 1000)

            await self.disconnect()

            return {
                "status": "success",
                "message": "Connection established successfully",
                "latency_ms": latency,
            }

        except Exception as e:
            latency = int((time.time() - start_time) * 1000)
            return {
                "status": "error",
                "message": str(e),
                "latency_ms": latency,
            }

    async def get_system_info(self) -> dict[str, Any]:
        """
        获取系统基本信息

        Returns:
            dict: 系统信息
        """
        try:
            # 获取操作系统信息
            os_info = await self.execute_command("uname -a")

            # 获取主机名
            hostname = await self.execute_command("hostname")

            # 获取内核版本
            kernel = await self.execute_command("uname -r")

            return {
                "os_info": os_info["stdout"].strip(),
                "hostname": hostname["stdout"].strip(),
                "kernel": kernel["stdout"].strip(),
            }

        except Exception as e:
            logger.error(f"Failed to get system info from {self.host}: {str(e)}")
            return {}

    @staticmethod
    async def create_from_encrypted(
        host: str,
        port: int,
        username: str,
        encrypted_password: str | None = None,
        encrypted_key: str | None = None,
    ) -> "SSHService":
        """
        从加密凭证创建SSH服务实例

        Args:
            host: 主机地址
            port: SSH端口
            username: 用户名
            encrypted_password: 加密的密码
            encrypted_key: 加密的私钥

        Returns:
            SSHService: SSH服务实例
        """
        password = None
        private_key = None

        if encrypted_password:
            try:
                password = decrypt_ssh_credential(encrypted_password)
            except Exception as e:
                logger.error(f"Failed to decrypt password: {str(e)}")

        if encrypted_key:
            try:
                private_key = decrypt_ssh_credential(encrypted_key)
            except Exception as e:
                logger.error(f"Failed to decrypt private key: {str(e)}")

        return SSHService(
            host=host,
            port=port,
            username=username,
            password=password,
            private_key=private_key,
        )

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        if self.client:
            self.client.close()

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.disconnect()
