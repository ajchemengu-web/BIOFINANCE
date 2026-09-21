from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base
from app.models.mixins import CreatedAtMixin


class ProviderCatalogEntry(Base, CreatedAtMixin):
    """
    The business/product truth of "which financial providers exist and can
    be connected" — decoupled from app/providers/registry.py, which is the
    technical truth of "how do we talk to it" (real adapter vs. generic
    mock). Adding a provider worldwide is a catalog row (+ a real adapter
    once there's an actual integration agreement); it never requires
    touching BioRouter or the payment services. See docs/architecture.md
    "Provider catalog".
    """

    __tablename__ = "provider_catalog"

    code: Mapped[str] = mapped_column(String, primary_key=True)
    display_name: Mapped[str] = mapped_column(String)
    country_code: Mapped[str] = mapped_column(String)  # ISO 3166-1 alpha-2, or "GLOBAL"
    currency: Mapped[str] = mapped_column(String)  # ISO 4217
    category: Mapped[str] = mapped_column(String)  # MOBILE_MONEY, BANK, CARD, WALLET
    status: Mapped[str] = mapped_column(String, default="COMING_SOON")  # AVAILABLE, COMING_SOON, DISABLED
