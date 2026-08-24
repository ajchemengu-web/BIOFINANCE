"""Transaction state machine and history (docs/database-schema.md). Phase 3."""


class TransactionService:
    async def list_for_user(self, user_id):
        raise NotImplementedError("TransactionService.list_for_user — implemented in Phase 3")

    async def get(self, transaction_id):
        raise NotImplementedError("TransactionService.get — implemented in Phase 3")

    async def transition(self, transaction_id, new_status):
        raise NotImplementedError("TransactionService.transition — implemented in Phase 3")
