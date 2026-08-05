import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.exceptions import NotFoundError
from core.tenant_context import get_current_user
from db.session import get_db
from models.conversation import Conversation
from models.user import User
from repositories.conversation_repo import ConversationRepository
from repositories.message_repo import MessageRepository
from repositories.query_execution_repo import QueryExecutionRepository
from schemas.conversations import (
    ConversationResponse,
    CreateConversationRequest,
    MessageResponse,
    QueryExecutionResponse,
    UpdateConversationSourcesRequest,
)

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationResponse])
def list_conversations(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return ConversationRepository(db).list_for_user(user.tenant_id, user.id)


@router.post("", response_model=ConversationResponse, status_code=201)
def create_conversation(
    payload: CreateConversationRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    conversation = Conversation(
        id=uuid.uuid4(),
        tenant_id=user.tenant_id,
        user_id=user.id,
        title=payload.title,
        active_connection_ids=[str(c) for c in payload.active_connection_ids],
        active_knowledge_base_ids=[str(k) for k in payload.active_knowledge_base_ids],
    )
    db.add(conversation)
    db.commit()
    return conversation


@router.get("/{conversation_id}", response_model=ConversationResponse)
def get_conversation(conversation_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conversation = ConversationRepository(db).get_by_id(user.tenant_id, conversation_id)
    if conversation is None:
        raise NotFoundError("Conversation not found.")
    return conversation


@router.put("/{conversation_id}/sources", response_model=ConversationResponse)
def update_sources(
    conversation_id: uuid.UUID,
    payload: UpdateConversationSourcesRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation = ConversationRepository(db).get_by_id(user.tenant_id, conversation_id)
    if conversation is None:
        raise NotFoundError("Conversation not found.")
    conversation.active_connection_ids = [str(c) for c in payload.active_connection_ids]
    conversation.active_knowledge_base_ids = [str(k) for k in payload.active_knowledge_base_ids]
    db.add(conversation)
    db.commit()
    return conversation


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
def list_messages(conversation_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conversation = ConversationRepository(db).get_by_id(user.tenant_id, conversation_id)
    if conversation is None:
        raise NotFoundError("Conversation not found.")
    return MessageRepository(db).list_for_conversation(user.tenant_id, conversation_id)


@router.get("/messages/{message_id}/sql", response_model=QueryExecutionResponse | None)
def get_message_sql(message_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return QueryExecutionRepository(db).get_for_message(user.tenant_id, message_id)
