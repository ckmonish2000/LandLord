from difflib import SequenceMatcher

from src.properties.constants import NAME_MATCH_THRESHOLD
from src.whatsapp.constants import USER_SERVER


def name_matches(query: str, name: str) -> bool:
    """'vidyaranyapura' matches 'Vidyaranyapura Residents' (contained) and also
    close spellings like 'vidyaranyapur' (similar to one of the words)."""
    q, n = query.strip().lower(), name.lower()
    if not q:
        return False
    if q in n:
        return True
    candidates = [n, *n.split()]
    return max(SequenceMatcher(None, q, c).ratio() for c in candidates) >= NAME_MATCH_THRESHOLD


def member_display_name(member: dict) -> str:
    """How the landlord knows a group member: saved contact name, else their WhatsApp
    name, else their number."""
    name = member.get("saved_name") or member.get("push_name") or member.get("business_name")
    if name:
        return name.strip()
    return f"+{member['phone']}" if member.get("phone") else "Member"


def member_chat_jid(member: dict) -> str:
    """Where to message a member personally: their phone number when WhatsApp shows
    it, else their @lid id."""
    return f"{member['phone']}@{USER_SERVER}" if member.get("phone") else member["jid"]


def member_user_ids(member: dict) -> set[str]:
    """Every id a member is known by (phone, jid user, lid user), to compare against."""
    ids = {member["jid"].split("@")[0], member.get("phone") or "", (member.get("lid") or "").split("@")[0]}
    return ids - {""}
