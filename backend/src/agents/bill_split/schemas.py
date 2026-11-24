from pydantic import BaseModel, Field


class BillRequest(BaseModel):
    """What the landlord asked to split, pulled out of their message by the LLM.
    Fields the message doesn't mention stay None; the agent asks for them."""

    amount: float | None = Field(None, gt=0, description="Total bill amount as a number, e.g. 1000 for '1k' or '₹1,000'")
    currency: str = Field("INR", description="ISO currency code; INR unless another currency is stated")
    item: str | None = Field(None, description="What the bill is for, e.g. 'water tank'")
    property_hint: str | None = Field(
        None, description="The property, building or area named in the message, exactly as written, e.g. 'vidyaranyapura'"
    )
