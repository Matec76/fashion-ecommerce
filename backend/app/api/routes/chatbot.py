from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from app.models.chatbot import ChatRequest, ChatResponse
from app.services import chatbot_service

router = APIRouter()

@router.post("/", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat_with_ai(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    API Chatbot AI:
    - Nhận tin nhắn và lịch sử chat từ người dùng.
    - Tìm kiếm sản phẩm trong Database (Full Text Search).
    - Trả về câu trả lời tư vấn bán hàng.
    """
    try:
        reply_text = await chatbot_service.process_chat_message(
            db=db, 
            message=request.message, 
            history=request.history
        )
        return ChatResponse(reply=reply_text)
        
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Đã xảy ra lỗi khi xử lý tin nhắn."
        )