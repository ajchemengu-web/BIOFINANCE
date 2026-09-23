import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.database import get_db
from app.models.provider import ProviderAccount, ProviderConnection
from app.models.user import User
from app.schemas.providers import ProviderConnectionResponse, ProviderConnectRequest
from app.services.audit_service import AuditService
from app.services.payment_service import PaymentService
from app.services.provider_catalog_service import ProviderCatalogService

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("", response_model=list[ProviderConnectionResponse])
async def list_providers(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ProviderConnection).where(ProviderConnection.user_id == user.id))
    return result.scalars().all()


@router.post("/connect", response_model=ProviderConnectionResponse, status_code=status.HTTP_201_CREATED)
async def connect_provider(
    payload: ProviderConnectRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    provider_code must be a real, connectable entry in the provider
    catalog (docs/architecture.md "Provider catalog") — the database's own
    foreign key would reject an unknown code anyway, but checking status
    here lets a COMING_SOON/DISABLED entry give a clear 409 instead of a
    raw constraint-violation 500.
    """
    catalog_entry = await ProviderCatalogService(db).get_by_code(payload.provider_code)
    if catalog_entry is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown provider_code")
    if catalog_entry.status != "AVAILABLE":
        raise HTTPException(status.HTTP_409_CONFLICT, f"{payload.provider_code} is not yet available ({catalog_entry.status})")

    connection = ProviderConnection(user_id=user.id, provider_code=payload.provider_code)
    db.add(connection)
    await db.flush()

    db.add(
        ProviderAccount(
            provider_connection_id=connection.id,
            external_account_ref=payload.external_account_ref,
        )
    )
    AuditService(db).log("PROVIDER_CONNECTED", user_id=user.id, connection_id=str(connection.id), provider_code=payload.provider_code)
    await db.commit()
    await db.refresh(connection)
    return connection


@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_provider(
    provider_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    connection = await db.get(ProviderConnection, provider_id)
    if connection is None or connection.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Provider connection not found")
    connection.status = "DISCONNECTED"
    AuditService(db).log(
        "PROVIDER_DISCONNECTED", user_id=user.id, connection_id=str(connection.id), provider_code=connection.provider_code
    )
    await db.commit()


@router.post("/daraja/callback")
async def daraja_callback(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Safaricom's STK push result webhook — no BioFinance auth on this route,
    Safaricom calls it directly. Body shape per the Daraja docs:
    {"Body": {"stkCallback": {"CheckoutRequestID": ..., "ResultCode": ...}}}.
    Always acknowledge with 200 + ResultCode 0 regardless of whether the
    CheckoutRequestID matched anything on our side — Safaricom retries
    undelivered callbacks, and a duplicate/unmatched one isn't an error on
    our end, just a no-op.
    """
    body = await request.json()
    callback = body.get("Body", {}).get("stkCallback", {})
    checkout_request_id = callback.get("CheckoutRequestID")
    result_code = callback.get("ResultCode")

    if checkout_request_id is not None and result_code is not None:
        await PaymentService(db).handle_daraja_callback(checkout_request_id, int(result_code))

    return {"ResultCode": 0, "ResultDesc": "Accepted"}
