"""
AI聊天服务
"""

from typing import AsyncIterator, Dict, List
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.chat import ChatHistory
from app.services.ai_providers import AIServiceFactory
from app.services.ai_tools import AITools
from app.services.execute_service import ExecuteService
from app.services.metrics_service import MetricsService
from app.services.server_service import ServerService
from app.utils.logger import logger


class AIService:
    """AI聊天服务类"""

    def __init__(
        self,
        db: AsyncSession,
        user_id: UUID,
    ):
        self.db = db
        self.user_id = user_id

        # 创建AI提供商
        self.ai_provider = AIServiceFactory.create(
            provider=settings.ai_provider,
            model=settings.ai_model,
        )

        # 创建工具实例
        server_service = ServerService(db)
        metrics_service = MetricsService(db)
        execute_service = ExecuteService(db)

        self.ai_tools = AITools(
            server_service=server_service,
            metrics_service=metrics_service,
            execute_service=execute_service,
            user_id=user_id,
        )

    async def chat(
        self,
        message: str,
        conversation_id: UUID | None = None,
        server_id: UUID | None = None,
        max_iterations: int = 10,
    ) -> Dict:
        """
        发送聊天消息

        Args:
            message: 用户消息
            conversation_id: 会话ID（可选）
            server_id: 默认服务器ID（可选，作为工具调用的上下文）
            max_iterations: 最大迭代次数（防止无限循环）

        Returns:
            Dict: 聊天响应
        """
        try:
            # 如果提供了server_id，更新AITools的默认服务器
            if server_id:
                self.ai_tools.default_server_id = server_id

            # 获取历史消息
            history = await self._get_conversation_history(conversation_id, limit=10)

            # 构建消息列表
            messages = history + [{"role": "user", "content": message}]

            # 保存用户消息
            user_chat = await self._save_chat_message(
                conversation_id=conversation_id,
                role="user",
                content=message,
            )

            # 如果是新会话，使用新创建的conversation_id
            if not conversation_id:
                conversation_id = user_chat.conversation_id

            # 获取工具定义
            tools = self.ai_tools.get_tool_definitions()

            # 执行AI对话（支持Function Calling）
            iterations = 0
            while iterations < max_iterations:
                iterations += 1

                # 调用AI
                response = await self.ai_provider.chat(messages, tools)

                # 检查是否需要执行工具
                if response.get("tool_calls"):
                    # 处理工具调用
                    tool_calls = response["tool_calls"]

                    # 将AI的工具调用添加到消息历史
                    messages.append(
                        {
                            "role": "assistant",
                            "content": response.get("content") or "",
                            "tool_calls": tool_calls,
                        }
                    )

                    # 执行工具并收集结果
                    tool_results = []
                    for tool_call in tool_calls:
                        tool_name = tool_call["function"]["name"]
                        tool_args = tool_call["function"]["arguments"]
                        tool_id = tool_call.get("id", "")

                        logger.info(f"Executing tool: {tool_name} with args: {tool_args}")

                        # 执行工具
                        result = await self.ai_tools.execute_tool(tool_name, tool_args)

                        tool_results.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_id,
                                "name": tool_name,
                                "content": str(result),
                            }
                        )

                    # 将工具结果添加到消息历史
                    messages.extend(tool_results)

                    # 继续循环，让AI处理工具结果
                    continue

                else:
                    # 没有工具调用，返回最终响应
                    assistant_message = response.get("content", "")

                    # 保存AI响应
                    await self._save_chat_message(
                        conversation_id=conversation_id,
                        role="assistant",
                        content=assistant_message,
                    )

                    return {
                        "conversation_id": str(conversation_id),
                        "message": assistant_message,
                        "iterations": iterations,
                    }

            # 超过最大迭代次数
            error_message = "达到最大迭代次数，对话可能陷入循环。"
            await self._save_chat_message(
                conversation_id=conversation_id,
                role="assistant",
                content=error_message,
            )

            return {
                "conversation_id": str(conversation_id),
                "message": error_message,
                "iterations": iterations,
                "error": "max_iterations_reached",
            }

        except Exception as e:
            logger.error(f"Chat error: {str(e)}")
            error_message = f"处理消息时出错: {str(e)}"

            # 尝试保存错误消息
            try:
                if conversation_id:
                    await self._save_chat_message(
                        conversation_id=conversation_id,
                        role="assistant",
                        content=error_message,
                    )
            except Exception:
                pass

            return {
                "conversation_id": str(conversation_id) if conversation_id else None,
                "message": error_message,
                "error": str(e),
            }

    async def stream_chat(
        self,
        message: str,
        conversation_id: UUID | None = None,
    ) -> AsyncIterator[str]:
        """
        流式聊天（暂不支持Function Calling）

        Args:
            message: 用户消息
            conversation_id: 会话ID（可选）

        Yields:
            str: 流式响应片段
        """
        try:
            # 获取历史消息
            history = await self._get_conversation_history(conversation_id, limit=10)

            # 构建消息列表
            messages = history + [{"role": "user", "content": message}]

            # 保存用户消息
            user_chat = await self._save_chat_message(
                conversation_id=conversation_id,
                role="user",
                content=message,
            )

            # 如果是新会话，使用新创建的conversation_id
            if not conversation_id:
                conversation_id = user_chat.conversation_id

            # 获取工具定义（注意：流式模式下工具调用支持有限）
            tools = self.ai_tools.get_tool_definitions()

            # 收集完整响应以便保存
            full_response = ""

            # 流式调用AI
            async for chunk in self.ai_provider.stream_chat(messages, tools):
                full_response += chunk
                yield chunk

            # 保存完整的AI响应
            await self._save_chat_message(
                conversation_id=conversation_id,
                role="assistant",
                content=full_response,
            )

        except Exception as e:
            logger.error(f"Stream chat error: {str(e)}")
            error_message = f"处理消息时出错: {str(e)}"
            yield error_message

            # 尝试保存错误消息
            try:
                if conversation_id:
                    await self._save_chat_message(
                        conversation_id=conversation_id,
                        role="assistant",
                        content=error_message,
                    )
            except Exception:
                pass

    async def get_conversations(
        self,
        page: int = 1,
        size: int = 20,
    ) -> Dict:
        """
        获取用户的会话列表

        Args:
            page: 页码
            size: 每页数量

        Returns:
            Dict: 会话列表
        """
        # 查询总数
        from sqlalchemy import func

        count_result = await self.db.execute(
            select(func.count(func.distinct(ChatHistory.conversation_id))).where(
                ChatHistory.user_id == self.user_id
            )
        )
        total = count_result.scalar_one()

        # 查询会话（每个会话的最新消息）
        offset = (page - 1) * size

        # 子查询：每个会话的最新消息时间
        subquery = (
            select(
                ChatHistory.conversation_id,
                func.max(ChatHistory.created_at).label("last_message_at"),
            )
            .where(ChatHistory.user_id == self.user_id)
            .group_by(ChatHistory.conversation_id)
            .subquery()
        )

        # 主查询：获取会话详情
        query = (
            select(ChatHistory)
            .join(
                subquery,
                (ChatHistory.conversation_id == subquery.c.conversation_id)
                & (ChatHistory.created_at == subquery.c.last_message_at),
            )
            .order_by(desc(ChatHistory.created_at))
            .offset(offset)
            .limit(size)
        )

        result = await self.db.execute(query)
        conversations = result.scalars().all()

        items = [
            {
                "conversation_id": str(conv.conversation_id),
                "last_message": (
                    conv.content[:100] + "..." if len(conv.content) > 100 else conv.content
                ),
                "last_message_at": conv.created_at,
                "role": conv.role,
            }
            for conv in conversations
        ]

        return {
            "total": total,
            "page": page,
            "size": size,
            "items": items,
        }

    async def get_conversation_messages(
        self,
        conversation_id: UUID,
        page: int = 1,
        size: int = 50,
    ) -> Dict:
        """
        获取会话的消息历史

        Args:
            conversation_id: 会话ID
            page: 页码
            size: 每页数量

        Returns:
            Dict: 消息列表
        """
        # 查询总数
        from sqlalchemy import func

        count_result = await self.db.execute(
            select(func.count())
            .select_from(ChatHistory)
            .where(
                ChatHistory.user_id == self.user_id,
                ChatHistory.conversation_id == conversation_id,
            )
        )
        total = count_result.scalar_one()

        # 查询消息
        offset = (page - 1) * size
        query = (
            select(ChatHistory)
            .where(
                ChatHistory.user_id == self.user_id,
                ChatHistory.conversation_id == conversation_id,
            )
            .order_by(ChatHistory.created_at)
            .offset(offset)
            .limit(size)
        )

        result = await self.db.execute(query)
        messages = result.scalars().all()

        items = [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at,
            }
            for msg in messages
        ]

        return {
            "total": total,
            "page": page,
            "size": size,
            "items": items,
        }

    async def delete_conversation(self, conversation_id: UUID) -> bool:
        """
        删除会话

        Args:
            conversation_id: 会话ID

        Returns:
            bool: 是否成功删除
        """
        try:
            # 删除会话的所有消息
            from sqlalchemy import delete

            await self.db.execute(
                delete(ChatHistory).where(
                    ChatHistory.user_id == self.user_id,
                    ChatHistory.conversation_id == conversation_id,
                )
            )
            await self.db.commit()

            logger.info(f"Deleted conversation {conversation_id} for user {self.user_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting conversation: {str(e)}")
            await self.db.rollback()
            return False

    async def _get_conversation_history(
        self,
        conversation_id: UUID | None,
        limit: int = 10,
    ) -> List[Dict]:
        """
        获取会话历史消息

        Args:
            conversation_id: 会话ID
            limit: 消息数量限制

        Returns:
            List[Dict]: 消息列表
        """
        if not conversation_id:
            return []

        query = (
            select(ChatHistory)
            .where(
                ChatHistory.user_id == self.user_id,
                ChatHistory.conversation_id == conversation_id,
            )
            .order_by(desc(ChatHistory.created_at))
            .limit(limit)
        )

        result = await self.db.execute(query)
        messages = result.scalars().all()

        # 反转顺序（从旧到新）
        messages = list(reversed(messages))

        return [
            {
                "role": msg.role,
                "content": msg.content,
            }
            for msg in messages
        ]

    async def _save_chat_message(
        self,
        conversation_id: UUID | None,
        role: str,
        content: str,
    ) -> ChatHistory:
        """
        保存聊天消息

        Args:
            conversation_id: 会话ID
            role: 角色（user/assistant）
            content: 消息内容

        Returns:
            ChatHistory: 保存的消息对象
        """
        chat = ChatHistory(
            user_id=self.user_id,
            conversation_id=conversation_id,
            role=role,
            content=content,
        )

        self.db.add(chat)
        await self.db.commit()
        await self.db.refresh(chat)

        return chat
