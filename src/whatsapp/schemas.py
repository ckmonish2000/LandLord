import re

from pydantic import BaseModel, field_validator


class PairCodeRequest(BaseModel):
    phone: str  # country code + number, e.g. 919876543210

    @field_validator("phone")
    @classmethod
    def digits_only(cls, v: str) -> str:
        digits = re.sub(r"\D", "", v)
        if not 8 <= len(digits) <= 15:
            raise ValueError("phone must be country code + number, digits only")
        return digits
