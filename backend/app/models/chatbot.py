from pydantic import BaseModel
from typing import List


class ChatRequest(BaseModel):
    message: str
    history: List[dict] = []

class ChatResponse(BaseModel):
    reply: str