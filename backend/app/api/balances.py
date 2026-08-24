from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.database import get_db
from app.models.provider import ProviderAccount, ProviderConnection
from app.models.user import User
from app.providers.registry import get_provider
from app.schemas.balances import BalancesResponse, ProviderBalance

router = APIRouter(prefix="/balances", tags=["balances"])


@router.get("", response_model=BalancesResponse)
async def get_balances(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ProviderConnection, ProviderAccount)
        .join(ProviderAccount, ProviderAccount.provider_connection_id == ProviderConnection.id)
        .where(ProviderConnection.user_id == user.id, ProviderConnection.status == "CONNECTED")
    )

    balances: list[ProviderBalance] = []
    for connection, account in result.all():
        provider = get_provider(connection.provider_code)
        balance = await provider.get_balance(account.external_account_ref)
        balances.append(ProviderBalance(provider_code=connection.provider_code, amount=balance.amount))

    total = sum((balance.amount for balance in balances), start=Decimal("0"))
    return BalancesResponse(total=total, by_provider=balances)
