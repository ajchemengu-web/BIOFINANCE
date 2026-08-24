from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, balances, bioid, merchants, payments, providers, routing, transactions
from app.core.config import get_settings
from app.core.logging import configure_logging

configure_logging()

app = FastAPI(title="BioFinance API", version="0.1.0")

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    # Auth is a bearer token in the Authorization header, not cookies —
    # doesn't need CORS "credentials" mode, which also can't be combined
    # with a wildcard origin anyway.
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
