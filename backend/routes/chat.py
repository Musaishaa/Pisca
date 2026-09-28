from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Conversation, Message
from backend.schemas import ChatRequest, ChatResponse, ConversationResponse
from backend.services.chat_service import ChatService
from backend.services.llm_service import LLMUnavailableError, get_llm_service

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    try:
        answer, memory_used, conversation_id = await ChatService(get_llm_service()).reply(
            db, request.message, request.conversation_id
        )
        return ChatResponse(answer=answer, memory_used=memory_used, conversation_id=conversation_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except LLMUnavailableError as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)) from error


@router.get("/conversations", response_model=list[ConversationResponse])
def conversations(db: Session = Depends(get_db)):
    items = db.scalars(select(Conversation).order_by(Conversation.updated_at.desc())).all()
    return [
        ConversationResponse(
            id=item.id,
            created_at=item.created_at,
            updated_at=item.updated_at,
            preview=(db.scalar(select(Message.content).where(Message.conversation_id == item.id).order_by(Message.id)) or "Percakapan baru")[:60],
        )
        for item in items
    ]


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(conversation_id: int, db: Session = Depends(get_db)):
    conversation = db.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Percakapan tidak ditemukan.")
    db.delete(conversation)
    db.commit()
