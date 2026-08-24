import uuid

from fastapi import APIRouter, HTTPException, status

from app.schemas.transactions import TransactionResponse

router = APIRouter(prefix="/transactions", tags=["transactions"])

_NOT_IMPLEMENTED = "Implemented in Phase 3 (docs/roadmap.md)"


@router.get("", response_model=list[TransactionResponse])
async def list_transactions():
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, _NOT_IMPLEMENTED)


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(transaction_id: uuid.UUID):
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, _NOT_IMPLEMENTED)
