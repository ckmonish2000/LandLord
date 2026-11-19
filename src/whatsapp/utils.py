from neonize.proto.Neonize_pb2 import GroupInfo
from neonize.utils.jid import Jid2String


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
