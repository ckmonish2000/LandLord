from src.properties.repository import HouseMemberRepository, HouseRepository, PropertyRepository
from src.properties.service import PropertyService
from src.whatsapp.dependencies import get_whatsapp_service


def get_property_service() -> PropertyService:
    return PropertyService(PropertyRepository(), HouseRepository(), HouseMemberRepository(), get_whatsapp_service())
