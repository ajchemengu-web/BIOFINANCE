"""
BioRouter — the routing engine described in docs/architecture.md. Selects a
provider from the user's routing policy, attempts authorization, and falls
back per policy on decline. Implemented in Phase 3 (docs/roadmap.md); the
PaymentProvider interface it will depend on already exists in
app/providers/base.py.
"""


class RouterService:
    async def route_payment(self, bio_id, amount, currency):
        raise NotImplementedError("RouterService.route_payment — implemented in Phase 3")
