"""Data model (one JSON file each):

  properties  one per WhatsApp group the landlord manages
              {id, client_id, group_jid, name, created_at}
  houses      a unit inside a property, unique per (property_id, floor, number).
              More details (RR number, rent, ...) are added to this record later.
              {id, property_id, floor, number}
  house_members  a group member's role in the property: owner and/or living here.
              Owner is independent of any house. house_id is set only when lives_here
              (several members can share a house); otherwise null.
              {id, property_id, member_jid, house_id, is_owner, lives_here, updated_at}
"""

from src.database import JsonCollection


class PropertyRepository(JsonCollection):
    def __init__(self):
        super().__init__("properties")


class HouseRepository(JsonCollection):
    def __init__(self):
        super().__init__("houses")


class HouseMemberRepository(JsonCollection):
    def __init__(self):
        super().__init__("house_members")
