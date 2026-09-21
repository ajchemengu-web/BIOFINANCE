from pydantic import BaseModel


class ProviderCatalogEntryResponse(BaseModel):
    code: str
    display_name: str
    country_code: str
    currency: str
    category: str
    status: str

    model_config = {"from_attributes": True}
