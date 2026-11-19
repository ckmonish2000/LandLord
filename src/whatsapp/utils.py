from collections.abc import Iterable

from neonize.proto.Neonize_pb2 import JID, Contact, ContactInfo, GroupInfo, GroupParticipant
from neonize.utils.jid import Jid2String

from src.whatsapp.constants import GROUP_SERVER


def group_jid(group_id: str) -> JID:
    """'120363...@g.us' or '120363...' -> group JID."""
    user = group_id.split("@", 1)[0]
    return JID(User=user, Server=GROUP_SERVER, Device=0, RawAgent=0, Integrator=0, IsEmpty=False)


def _key(jid: JID) -> str:
    return f"{jid.User}@{jid.Server}"


def contacts_by_jid(contacts: Iterable[Contact]) -> dict[str, ContactInfo]:
    """Index the contact store by 'user@server' for quick lookups."""
    return {_key(c.JID): c.Info for c in contacts if c.JID.User}


def find_contact(p: GroupParticipant, contacts: dict[str, ContactInfo]) -> ContactInfo | None:
    """A member can be stored under their phone JID or their LID; try both."""
    for jid in (p.PhoneNumber, p.JID, p.LID):
        if jid.User and (info := contacts.get(_key(jid))):
            return info
    return None


def member_to_dict(
    p: GroupParticipant,
    picture_url: str | None = None,
    contact: ContactInfo | None = None,
) -> dict:
    """Flatten a GroupParticipant. In privacy (LID) groups p.JID is an @lid id
    and the phone number, if visible, is in p.PhoneNumber."""
    if p.PhoneNumber.User:
        phone = p.PhoneNumber.User
    elif p.JID.Server == "s.whatsapp.net":
        phone = p.JID.User
    else:
        phone = None

    if p.LID.User:
        lid = Jid2String(p.LID)
    elif p.JID.Server == "lid":
        lid = Jid2String(p.JID)
    else:
        lid = None

    c = contact or ContactInfo()
    return {
        "jid": Jid2String(p.JID),
        "phone": phone,
        "lid": lid,
        # Name saved in the linked account owner's phone contacts
        "saved_name": c.FullName or c.FirstName or None,
        # Name the member set on their own WhatsApp profile
        "push_name": c.PushName or p.DisplayName or None,
        "business_name": c.BusinessName or None,
        "is_admin": p.IsAdmin or p.IsSuperAdmin,
        "is_super_admin": p.IsSuperAdmin,
        "picture_url": picture_url,
    }


def group_to_dict(group: GroupInfo, picture_url: str | None = None) -> dict:
    """Flatten neonize's GroupInfo protobuf into plain fields for the API."""
    return {
        "jid": Jid2String(group.JID),
        "name": group.GroupName.Name,
        "topic": group.GroupTopic.Topic or None,
        "owner_jid": Jid2String(group.OwnerJID) if group.OwnerJID.User else None,
        "participant_count": len(group.Participants),
        "is_announce": group.GroupAnnounce.IsAnnounce,  # only admins can send
        "is_locked": group.GroupLocked.isLocked,  # only admins can edit info
        "is_community": group.GroupParent.IsParent,
        "picture_url": picture_url,
    }
