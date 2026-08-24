from fastapi import FastAPI

from app.api import auth, balances, bioid, merchants, payments, providers, routing, transactions
from app.core.logging import configure_logging

configure_logging()

app = FastAPI(title="BioFinance API", version="0.1.0")

api_prefix = "/api/v1"
app.include_router(auth.router, prefix=api_prefix)
app.include_router(bioid.router, prefix=api_prefix)
app.include_router(providers.router, prefix=api_prefix)
app.include_router(balances.router, prefix=api_prefix)
app.include_router(routing.router, prefix=api_prefix)
app.include_router(payments.router, prefix=api_prefix)
app.include_router(transactions.router, prefix=api_prefix)
app.include_router(merchants.router, prefix=api_prefix)


@app.get("/health")
async def health():
    return {"status": "ok"}
