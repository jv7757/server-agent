"""
命令验证和安全检查
"""
import re
from typing import Tuple

from app.utils.logger import logger

# 危险命令黑名单
DANGEROUS_COMMANDS = [
    # 删除命令
    r"rm\s+-rf\s+/",
    r"rm\s+-rf\s+\*",
    r"rm\s+-fr\s+/",
    r":\(\)\{\s*:\|:&\s*\};:",  # Fork bomb

    # 磁盘操作
    r"mkfs\.",
    r"dd\s+if=.*of=/dev/",
    r"fdisk",
    r"parted",

    # 系统关机/重启
    r"shutdown",
    r"reboot",
    r"halt",
    r"poweroff",
    r"init\s+[06]",

    # 用户和权限
    r"userdel\s+-r",
    r"passwd\s+root",

    # 网络破坏
    r"iptables\s+-F",
    r"iptables\s+-X",

    # 内核模块
    r"rmmod",
    r"modprobe\s+-r",

    # 危险的重定向
    r">\s*/dev/sd[a-z]",
    r">\s*/dev/nvme",
]

# 需要确认的命令（中等风险）
WARNING_COMMANDS = [
    r"rm\s+",
    r"mv\s+.*\s+/",
    r"chmod\s+-R\s+777",
    r"chown\s+-R",
    r"kill\s+-9",
    r"pkill",
    r"systemctl\s+stop",
    r"systemctl\s+disable",
    r"apt(-get)?\s+remove",
    r"yum\s+remove",
    r"docker\s+rm",
    r"docker\s+stop",
]


class CommandValidator:
    """命令验证器"""

    @staticmethod
    def is_dangerous(command: str) -> Tuple[bool, str | None]:
        """
        检查命令是否危险

        Args:
            command: 待执行的命令

        Returns:
            Tuple[bool, str | None]: (是否危险, 匹配的规则)
        """
        command = command.strip()

        # 检查黑名单
        for pattern in DANGEROUS_COMMANDS:
            if re.search(pattern, command, re.IGNORECASE):
                logger.warning(f"Dangerous command detected: {command}")
                return True, pattern

        return False, None

    @staticmethod
    def needs_confirmation(command: str) -> Tuple[bool, str | None]:
        """
        检查命令是否需要确认

        Args:
            command: 待执行的命令

        Returns:
            Tuple[bool, str | None]: (是否需要确认, 匹配的规则)
        """
        command = command.strip()

        # 检查警告列表
        for pattern in WARNING_COMMANDS:
            if re.search(pattern, command, re.IGNORECASE):
                logger.info(f"Warning command detected: {command}")
                return True, pattern

        return False, None

    @staticmethod
    def validate(
        command: str, allow_dangerous: bool = False, skip_confirmation: bool = False
    ) -> Tuple[bool, str | None]:
        """
        验证命令是否可以执行

        Args:
            command: 待执行的命令
            allow_dangerous: 是否允许危险命令
            skip_confirmation: 是否跳过确认

        Returns:
            Tuple[bool, str | None]: (是否允许执行, 拒绝原因)
        """
        # 检查命令是否为空
        if not command or not command.strip():
            return False, "Command cannot be empty"

        # 检查危险命令
        is_dangerous, pattern = CommandValidator.is_dangerous(command)
        if is_dangerous:
            if not allow_dangerous:
                return False, f"Dangerous command blocked: matches pattern '{pattern}'"
            else:
                logger.warning(f"Dangerous command allowed by user: {command}")

        # 检查需要确认的命令
        needs_confirm, pattern = CommandValidator.needs_confirmation(command)
        if needs_confirm and not skip_confirmation:
            return False, f"Command requires confirmation: matches pattern '{pattern}'"

        return True, None

    @staticmethod
    def sanitize(command: str) -> str:
        """
        清理命令字符串

        Args:
            command: 原始命令

        Returns:
            str: 清理后的命令
        """
        # 移除首尾空白
        command = command.strip()

        # 移除多余的空格
        command = re.sub(r"\s+", " ", command)

        return command

    @staticmethod
    def get_command_risk_level(command: str) -> str:
        """
        获取命令风险级别

        Args:
            command: 命令

        Returns:
            str: 风险级别 (safe, warning, dangerous)
        """
        is_dangerous, _ = CommandValidator.is_dangerous(command)
        if is_dangerous:
            return "dangerous"

        needs_confirm, _ = CommandValidator.needs_confirmation(command)
        if needs_confirm:
            return "warning"

        return "safe"
