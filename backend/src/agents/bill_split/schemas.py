from pydantic import BaseModel, Field, field_validator


class BillRequest(BaseModel):
    """What the landlord asked to split, pulled out of their message by the LLM.
    Fields the message doesn't mention stay None; the agent asks for them."""

    amount: float | None = Field(
        None, gt=0, description="Total bill amount as a number, e.g. 1000 for '1k' or '₹1,000'"
    )
    currency: str = Field("INR", description="ISO currency code; INR unless another currency is stated")
    item: str | None = Field(None, description="What the bill is for, e.g. 'water tank'")
    property_hint: str | None = Field(
        None,
        description="The property, building or area named in the message, exactly as written, e.g. 'vidyaranyapura'",
    )

    @field_validator("item", "property_hint", mode="before")
    @classmethod
    def blank_is_missing(cls, v):
        """Small models often answer "" instead of null."""
        return v.strip() or None if isinstance(v, str) else v
