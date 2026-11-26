from src.agents.bill_split.constants import OPTION_MAX_CHARS
from src.agents.bill_split.state import Member


def as_poll_members(contacts: list[dict]) -> list[Member]:
    """Contacts ({jid, name, phone}) with names that work as poll options: short,
    and unique ('Ravi' twice becomes 'Ravi (…3210)'), since a vote only says which
    option names were picked."""
    members: list[Member] = []
    taken: set[str] = set()
    for c in contacts:
        name = _unique(c["name"][:OPTION_MAX_CHARS].strip(), c.get("phone"), taken)
        taken.add(name)
        members.append({"jid": c["jid"], "name": name})
    return members


def _unique(name: str, phone: str | None, taken: set[str]) -> str:
    if name not in taken:
        return name
    if phone and (candidate := f"{name} (…{phone[-4:]})") not in taken:
        return candidate
    n = 2
    while f"{name} {n}" in taken:
        n += 1
    return f"{name} {n}"
