from src.properties.exceptions import PropertyExists, PropertyNotFound
from src.properties.schemas import HouseAssignmentItem
from src.properties.repository import HouseMemberRepository, HouseRepository, PropertyRepository
from src.properties.utils import member_chat_jid, member_display_name, member_user_ids, name_matches
from src.whatsapp.service import WhatsappService
from src.utils import now_iso


def _assignment(link: dict | None, houses: dict[str, dict]) -> dict:
    """A member's house and role, from their house_members record (None = not assigned)."""
    if not link:
        return {"house": None, "is_owner": False, "lives_here": False}
    return {
        "house": houses.get(link.get("house_id")) if link["lives_here"] else None,
        "is_owner": link["is_owner"],
        "lives_here": link["lives_here"],
    }


class PropertyService:
    def __init__(
        self,
        properties: PropertyRepository,
        houses: HouseRepository,
        house_members: HouseMemberRepository,
        whatsapp: WhatsappService,
    ):
        self.properties = properties
        self.houses = houses
        self.house_members = house_members
        self.whatsapp = whatsapp

    def list_properties(self, client_id: str) -> list[dict]:
        return sorted(self.properties.find(client_id=client_id), key=lambda p: p["created_at"])

    def find_by_name(self, client_id: str, query: str) -> list[dict]:
        """The landlord's properties whose name contains or closely resembles `query`."""
        return [p for p in self.list_properties(client_id) if name_matches(query, p["name"])]

    def create_property(self, client_id: str, group_id: str) -> dict:
        """Add one of the user's WhatsApp groups as a property."""
        group = self.whatsapp.get_group(client_id, group_id)  # also checks it exists and we're in it
        if self.properties.find(client_id=client_id, group_jid=group["jid"]):
            raise PropertyExists()
        return self.properties.create({
            "client_id": client_id,
            "group_jid": group["jid"],
            "name": group["name"],
            "created_at": now_iso(),
        })

    def list_members(self, client_id: str, property_id: str, pictures: bool = True) -> list[dict]:
        """The group's current members, each with their house (or None) and whether they own / live in it."""
        prop = self._get(client_id, property_id)
        members = self.whatsapp.list_group_members(client_id, prop["group_jid"], pictures=pictures)
        houses = {h["id"]: h for h in self.houses.find(property_id=prop["id"])}
        links = {link["member_jid"]: link for link in self.house_members.find(property_id=prop["id"])}
        return [{**m, **_assignment(links.get(m["jid"]), houses)} for m in members]

    def list_member_contacts(
        self, client_id: str, property_id: str, exclude_users: set[str] | frozenset[str] = frozenset()
    ) -> list[dict]:
        """Group members as people to contact: {jid, name, phone}, sorted by name.
        `exclude_users` (phone numbers / lid ids) are left out, e.g. the landlord."""
        members = self.list_members(client_id, property_id, pictures=False)
        contacts = [
            {"jid": member_chat_jid(m), "name": member_display_name(m), "phone": m.get("phone")}
            for m in members
            if not member_user_ids(m) & exclude_users
        ]
        return sorted(contacts, key=lambda c: c["name"].lower())

    def save_assignments(self, client_id: str, property_id: str, items: list[HouseAssignmentItem]) -> list[dict]:
        """Save several members' roles at once. Owner is a flag on its own; members who live
        here are linked to the house at (floor, number), created the first time it's used.
        A member who is neither owner nor living here has their record removed."""
        prop = self._get(client_id, property_id)
        saved = []
        for item in items:
            match = {"property_id": prop["id"], "member_jid": item.member_jid}
            if not (item.is_owner or item.lives_here):
                for link in self.house_members.find(**match):
                    self.house_members.delete(link["id"])
                saved.append({"member_jid": item.member_jid, **_assignment(None, {})})
                continue
            house = None
            if item.lives_here:
                house = self.houses.upsert_where(
                    {"property_id": prop["id"], "floor": item.floor, "number": item.number}, {}
                )
            link = self.house_members.upsert_where(match, {
                "house_id": house["id"] if house else None,
                "is_owner": item.is_owner,
                "lives_here": item.lives_here,
                "updated_at": now_iso(),
            })
            houses = {house["id"]: house} if house else {}
            saved.append({"member_jid": item.member_jid, **_assignment(link, houses)})
        return saved

    def _get(self, client_id: str, property_id: str) -> dict:
        prop = self.properties.get_by_id(property_id)
        if not prop or prop["client_id"] != client_id:
            raise PropertyNotFound()
        return prop
