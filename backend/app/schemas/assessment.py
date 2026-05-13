"""反诈人格评估接口的 Pydantic schemas"""
from pydantic import BaseModel, Field


class AnswerItem(BaseModel):
    id: str = Field(..., description="题目 id，如 q1")
    selected: str = Field(..., description="选项 key，如 A/B/C/D")


class AssessRequest(BaseModel):
    answers: list[AnswerItem] = Field(..., min_length=1, max_length=20)


class MedalSchema(BaseModel):
    id: str
    name: str
    icon: str
    tier: str
    unlocked: bool = True
    acquired_at: str | None = None


class AssessResponse(BaseModel):
    personality_type: str
    trait_analysis: str
    precautions: str
    medal: MedalSchema
    all_medals: list[MedalSchema]
    score_profile: dict


class QuestionOption(BaseModel):
    key: str
    text: str


class QuestionItem(BaseModel):
    id: str
    dimension: str
    text: str
    options: list[QuestionOption]


class QuestionListResponse(BaseModel):
    questions: list[QuestionItem]


class ProfileResponse(BaseModel):
    player_name: str
    personality_type: str | None = None
    trait_analysis: str | None = None
    precautions: str | None = None
    medals: list[MedalSchema] = []
