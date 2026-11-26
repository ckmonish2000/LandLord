"""Properties (WhatsApp groups the landlord manages) and their members."""

from src.properties.dependencies import get_property_service


def _summary(p: dict) -> dict:
    return {"id": p["id"], "name": p["name"], "group_jid": p["group_jid"]}


def list_properties(client_id: str) -> list[dict]:
    """All of the landlord's properties: [{id, name, group_jid}]."""
    return [_summary(p) for p in get_property_service().list_properties(client_id)]


def find_properties(client_id: str, name: str) -> list[dict]:
    """Properties whose name contains or closely resembles `name`: [{id, name, group_jid}].
    Several results mean the landlord should choose."""
    return [_summary(p) for p in get_property_service().find_by_name(client_id, name)]


def list_member_contacts(client_id: str, property_id: str, exclude_users: set[str] = frozenset()) -> list[dict]:
    """People in the property's group: [{jid, name, phone}], sorted by name.
    `jid` is where to message them personally. Leave the landlord out via `exclude_users`."""
    return get_property_service().list_member_contacts(client_id, property_id, exclude_users)
