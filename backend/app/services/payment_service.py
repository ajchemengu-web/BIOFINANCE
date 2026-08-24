"""Payment lifecycle orchestration (creation, idempotency, cancellation). Phase 3."""


class PaymentService:
    async def create_payment(self, bio_id, merchant_id, amount, currency, idempotency_key):
        raise NotImplementedError("PaymentService.create_payment — implemented in Phase 3")

    async def get_payment(self, payment_id):
        raise NotImplementedError("PaymentService.get_payment — implemented in Phase 3")

    async def cancel_payment(self, payment_id):
        raise NotImplementedError("PaymentService.cancel_payment — implemented in Phase 3")
