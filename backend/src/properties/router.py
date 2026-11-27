"""Properties: WhatsApp groups the landlord manages, and the house each member lives in."""

from fastapi import APIRouter, Depends, HTTPException

from src.auth import dependencies as auth_dependencies
from src.properties.dependencies import get_property_service
from src.properties.exceptions import PropertyExists, PropertyNotFound
from src.properties.schemas import (
    CreatePropertyRequest,
    PropertyMemberResponse,
    PropertyResponse,
    SaveAssignmentsRequest,
    SavedAssignmentResponse,
)
from src.properties.service import PropertyService
from src.whatsapp.router.errors import whatsapp_http_errors

router = APIRouter(prefix="/properties", tags=["properties"])


@router.get("", response_model=list[PropertyResponse])
def list_properties(
    user: dict = Depends(auth_dependencies.get_current_user),
    service: PropertyService = Depends(get_property_service),
):
    return service.list_properties(user["id"])


@router.post("", response_model=PropertyResponse, status_code=201)
def create_property(
    body: CreatePropertyRequest,
    user: dict = Depends(auth_dependencies.get_current_user),
    service: PropertyService = Depends(get_property_service),
):
    try:
        with whatsapp_http_errors():
            return service.create_property(user["id"], body.group_jid)
    except PropertyExists as e:
        raise HTTPException(409, "This group is already a property") from e


@router.get("/{property_id}/members", response_model=list[PropertyMemberResponse])
def list_members(
    property_id: str,
    user: dict = Depends(auth_dependencies.get_current_user),
    service: PropertyService = Depends(get_property_service),
):
    try:
        with whatsapp_http_errors():
            return service.list_members(user["id"], property_id)
    except PropertyNotFound as e:
        raise HTTPException(404, "Property not found") from e


@router.put("/{property_id}/members/houses", response_model=list[SavedAssignmentResponse])
def save_assignments(
    property_id: str,
    body: SaveAssignmentsRequest,
    user: dict = Depends(auth_dependencies.get_current_user),
    service: PropertyService = Depends(get_property_service),
):
    """Save the floor, house number, owner and lives-here of several members in one go."""
    try:
        return service.save_assignments(user["id"], property_id, body.assignments)
    except PropertyNotFound as e:
        raise HTTPException(404, "Property not found") from e
