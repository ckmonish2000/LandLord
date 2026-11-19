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


class GroupResponse(BaseModel):
    jid: str  # e.g. 120363012345678901@g.us
    name: str
    topic: str | None
    owner_jid: str | None
    participant_count: int
    is_announce: bool
    is_locked: bool
    is_community: bool
    picture_url: str | None  # group DP; None if no photo. WhatsApp URLs expire after a while.
