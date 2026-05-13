"""反诈智能客服 API 路由"""
from typing import Annotated
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.models.user import User
from app.services.auth_service import get_current_user
from app.services.chat_service import process_chat_message

router = APIRouter(
    prefix="/api/chat",
    tags=["反诈客服"],
    dependencies=[Depends(get_current_user)],
)


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000, description="用户提问")


class ChatResponse(BaseModel):
    answer: str = Field(description="回复内容")
    intent: str = Field(default="NORMAL_CHAT", description="意图分类")
    risk_level: str = Field(default="normal", description="风险等级")
    source: str = Field(default="rag_llm", description="响应来源")
    is_alert: bool = Field(default=False, description="是否为紧急警报")
    knowledge_used: list[str] = Field(default=[], description="使用的知识库条目")


@router.post("/ask", response_model=ChatResponse, summary="智能客服对话")
async def ask_question(
    req: ChatRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    反诈智能客服主接口（需登录）。
    四层流水线：安全过滤 → 规则引擎 → 知识检索 → LLM 生成。
    """
    result = await process_chat_message(req.question, user=current_user)

    return ChatResponse(
        answer=result.get("answer", ""),
        intent=result.get("intent", "NORMAL_CHAT"),
        risk_level=result.get("risk_level", "normal"),
        source=result.get("source", "rag_llm"),
        is_alert=result.get("is_alert", False),
        knowledge_used=result.get("knowledge_used", []),
    )
