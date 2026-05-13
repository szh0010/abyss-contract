"""反诈人格评估 API 路由（需登录 · 身份从 JWT 解析）"""
from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.user_profile import UserProfile
from app.schemas.assessment import (
    AssessRequest, AssessResponse, MedalSchema,
    QuestionListResponse, QuestionItem, QuestionOption,
    ProfileResponse,
)
from app.services.auth_service import get_current_user
from app.services.personality_service import (
    QUESTION_BANK, get_personality_evaluation, merge_medal,
)

router = APIRouter(prefix="/api/assess", tags=["反诈人格评估"])


@router.get("/questions", response_model=QuestionListResponse, summary="获取测试题目")
async def list_questions(_: Annotated[User, Depends(get_current_user)]):
    """返回题库（隐藏打分字段）"""
    payload = [
        QuestionItem(
            id=q["id"],
            dimension=q["dimension"],
            text=q["text"],
            options=[QuestionOption(key=o["key"], text=o["text"]) for o in q["options"]],
        )
        for q in QUESTION_BANK
    ]
    return QuestionListResponse(questions=payload)


@router.post("", response_model=AssessResponse, summary="提交答案 → 生成人格报告")
async def submit_assessment(
    req: AssessRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    answers = [a.model_dump() for a in req.answers]

    evaluation = await get_personality_evaluation(answers)
    medal = evaluation["suggested_medal"]

    player_name = current_user.username
    stmt = select(UserProfile).where(UserProfile.player_name == player_name)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    if profile is None:
        profile = UserProfile(player_name=player_name, medals=[])
        db.add(profile)

    profile.personality_type = evaluation["personality_name"]
    profile.trait_analysis = evaluation["humorous_analysis"]
    profile.precautions = evaluation["educational_warning"]
    profile.medals = merge_medal(profile.medals, medal)
    profile.last_answers = answers

    await db.flush()

    return AssessResponse(
        personality_type=profile.personality_type,
        trait_analysis=profile.trait_analysis,
        precautions=profile.precautions,
        medal=MedalSchema(**medal, unlocked=True),
        all_medals=[MedalSchema(**m) for m in profile.medals],
        score_profile=evaluation.get("_score_profile", {}),
    )


@router.get("/profile", response_model=ProfileResponse, summary="查询当前用户档案")
async def get_my_profile(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    player_name = current_user.username
    stmt = select(UserProfile).where(UserProfile.player_name == player_name)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()
    if profile is None:
        return ProfileResponse(player_name=player_name)
    return ProfileResponse(
        player_name=profile.player_name,
        personality_type=profile.personality_type,
        trait_analysis=profile.trait_analysis,
        precautions=profile.precautions,
        medals=[MedalSchema(**m) for m in (profile.medals or [])],
    )
