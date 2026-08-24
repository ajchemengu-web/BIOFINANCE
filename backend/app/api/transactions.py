import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.database import get_db
from app.models.transaction import PaymentAttempt, Transaction
from app.models.user import User
from app.schemas.transactions import PaymentAttemptResponse, TransactionResponse
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/transactions", tags=["transactions"])


def _to_response(transaction: Transaction, attempts: list[PaymentAttempt]) -> TransactionResponse:
    return TransactionResponse(
        id=transaction.id,
        amount=transaction.amount,
        currency=transaction.currency,
        status=transaction.status,
        selected_provider=transaction.selected_provider,
        created_at=transaction.created_at,
        completed_at=transaction.completed_at,
        attempts=[
            PaymentAttemptResponse.model_validate(attempt, from_attributes=True) for attempt in attempts
        ],
    )


@router.get("", response_model=list[TransactionResponse])
async def list_transactions(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = TransactionService(db)
    transactions = await service.list_for_user(user.id)
    responses = []
    for transaction in transactions:
        attempts = await service.get_attempts(transaction.id)
        responses.append(_to_response(transaction, attempts))
    return responses


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(transaction_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    service = TransactionService(db)
    transaction = await service.get(transaction_id)
    if transaction is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Transaction not found")
    attempts = await service.get_attempts(transaction_id)
    return _to_response(transaction, attempts)
