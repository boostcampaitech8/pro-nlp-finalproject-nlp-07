from pydantic import BaseModel
from typing import Optional

# 백엔드에서 외부 API로 보내는 요청 형식
class UpstageRequest(BaseModel):
    conversation_id: str
    message: str

# 외부 API(Upstage)에서 받는 응답 스키마
class TokensUsed(BaseModel):
    input: int
    output: int

class UpstageResponse(BaseModel):
    response: str
    conversation_id: str
    tokens_used: TokensUsed
    model: str
    status: Optional[str] = None
