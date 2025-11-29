from pydantic import BaseModel, Field

from app.models.recommendations import AlgorithmName


class ExplainRequest(BaseModel):
    user_id: str = Field(..., description="ID пользователя")
    item_id: str = Field(..., description="ID фильма")
    algo: AlgorithmName = Field(
        ...,
        description="Алгоритм, которым была получена рекомендация",
    )


class ExplainResponse(BaseModel):
    user_id: str
    item_id: str
    algo: AlgorithmName
    explanation: str
