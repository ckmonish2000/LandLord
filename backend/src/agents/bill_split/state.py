from typing import TypedDict

from src.agents.base import Waiting


class Member(TypedDict):
    jid: str  # where to message them personally
    name: str  # unique within this run; also their poll option


class BillSplitState(TypedDict, total=False):
    # shared with Alfred's graph
    prompt: str
    reply: str
    outcome: str  # done | cancelled

    # private to this sub-agent (saved by the checkpointer between questions)
    bill: dict  # BillRequest fields
    candidates: list[dict]  # properties offered in the list
    property: dict  # {id, name, group_jid}
    members: list[Member]
    polls: dict[str, list[str]]  # poll message id -> option names
    selected: list[str]  # member jids sharing the bill
    shares: list[dict]  # from BillService.shares
    waiting: Waiting  # the question we're paused on
