from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints, model_validator

from src.whatsapp.constants import GROUP_ID_PATTERN
from src.whatsapp.schemas import GroupMemberResponse

ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20)]


class CreatePropertyRequest(BaseModel):
    group_jid: str = Field(pattern=GROUP_ID_PATTERN)  # the WhatsApp group this property is


class PropertyResponse(BaseModel):
    id: str
    group_jid: str
    name: str  # group name when the property was added
    created_at: str


class HouseAssignmentItem(BaseModel):
    """One member's role in the property.

    Owner is independent of where they live. Floor and house number are given only
    for members who live here. Neither owner nor lives_here removes the member's record.
    """

    member_jid: str
    is_owner: bool = False
    lives_here: bool = False
    floor: ShortText | None = None  # e.g. "G", "1", "2"; only when lives_here
    number: ShortText | None = None  # house / flat number, e.g. "101", "2B"; only when lives_here

    @model_validator(mode="after")
    def check(self):
        if self.lives_here and (self.floor is None or self.number is None):
            raise ValueError(f"{self.member_jid}: a member who lives here needs a floor and house number")
        if not self.lives_here and (self.floor is not None or self.number is not None):
            raise ValueError(f"{self.member_jid}: floor and house number are only for members who live here")
        return self


class SaveAssignmentsRequest(BaseModel):
    assignments: list[HouseAssignmentItem] = Field(max_length=2000)


class HouseResponse(BaseModel):
    id: str
    floor: str
    number: str


class HouseAssignmentResponse(BaseModel):
    house: HouseResponse | None  # the house they live in; None if they do not live here
    is_owner: bool
    lives_here: bool


class PropertyMemberResponse(GroupMemberResponse, HouseAssignmentResponse):
    pass


class SavedAssignmentResponse(HouseAssignmentResponse):
    member_jid: str
