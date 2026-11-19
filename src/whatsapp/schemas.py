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


class GroupMemberResponse(BaseModel):
    jid: str  # 919876543210@s.whatsapp.net, or 123456789012345@lid in privacy-mode groups
    phone: str | None  # None when WhatsApp hides the number
    lid: str | None
    saved_name: str | None  # name in the linked account owner's phone contacts
    push_name: str | None  # name the member set on their own WhatsApp profile
    business_name: str | None  # WhatsApp Business name, if any
    is_admin: bool
    is_super_admin: bool  # group creator
    picture_url: str | None  # member's DP; None if no photo or hidden by their privacy settings
