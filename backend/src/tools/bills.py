"""Shared bills: splitting, recording, and tracking who was told."""

from src.bills.dependencies import get_bill_service
from src.bills.service import BillService


def split_bill(total_paise: int, people: list[dict]) -> list[dict]:
    """Even shares for people ({jid, name}): [{member_jid, name, amount_paise, delivery}].
    Leftover paise go to the first people, so shares always add up to the total."""
    return BillService.shares(total_paise, people)


def record_bill(
    client_id: str,
    property_id: str,
    item: str | None,
    currency: str,
    total_paise: int,
    shares: list[dict],
    thread_id: str,
) -> dict:
    """Save a bill and its shares (status: sending)."""
    return get_bill_service().create(client_id, property_id, item, currency, total_paise, shares, thread_id)


def get_bill_for_thread(thread_id: str) -> dict | None:
    """The bill an agent run already recorded, if any (to avoid recording it twice)."""
    return get_bill_service().get_by_thread(thread_id)


def mark_group_notified(bill_id: str, ok: bool) -> None:
    get_bill_service().mark_group_delivery(bill_id, "sent" if ok else "failed")


def mark_member_notified(bill_id: str, member_jid: str, ok: bool) -> None:
    get_bill_service().mark_delivery(bill_id, member_jid, "sent" if ok else "failed")


def mark_bill_sent(bill_id: str) -> None:
    get_bill_service().mark_sent(bill_id)
