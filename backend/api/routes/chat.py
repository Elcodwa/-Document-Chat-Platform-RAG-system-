import json
import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.exceptions import NotFoundError
from core.tenant_context import get_current_user
from db.session import get_db
from models.user import User
from repositories.conversation_repo import ConversationRepository
from schemas.conversations import MessageResponse, SendMessageRequest
from services import chat_service

router = APIRouter(prefix="/api/conversations", tags=["chat"])


@router.post("/{conversation_id}/messages", response_model=MessageResponse)
def send_message(
    conversation_id: uuid.UUID,
    payload: SendMessageRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation = ConversationRepository(db).get_by_id(user.tenant_id, conversation_id)
    if conversation is None:
        raise NotFoundError("Conversation not found.")

    return chat_service.run_and_persist(db, conversation, user, payload.content)


@router.post("/{conversation_id}/messages/stream")
def send_message_stream(
    conversation_id: uuid.UUID,
    payload: SendMessageRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation = ConversationRepository(db).get_by_id(user.tenant_id, conversation_id)
    if conversation is None:
        raise NotFoundError("Conversation not found.")

    def event_stream():
        for event_name, payload_data in chat_service.stream_and_persist(db, conversation, user, payload.content):
            if event_name == "done":
                message = payload_data
                data = MessageResponse.model_validate(message).model_dump(mode="json")
                yield f"event: done\ndata: {json.dumps(data)}\n\n"
            else:
                yield f"event: stage\ndata: {json.dumps(payload_data)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
