from src.bills.repository import BillRepository
from src.bills.utils import split_evenly
from src.utils import now_iso


class BillService:
    def __init__(self, bills: BillRepository):
        self.bills = bills

    @staticmethod
    def shares(total_paise: int, members: list[dict]) -> list[dict]:
        """Split evenly between members ({jid, name}); leftover paise go to the first ones."""
        amounts = split_evenly(total_paise, len(members))
        return [
            {"member_jid": m["jid"], "name": m["name"], "amount_paise": a, "delivery": "pending"}
            for m, a in zip(members, amounts)
        ]

    def create(
        self,
        client_id: str,
        property_id: str,
        item: str | None,
        currency: str,
        total_paise: int,
        shares: list[dict],
        thread_id: str,
    ) -> dict:
        now = now_iso()
        return self.bills.create({
            "client_id": client_id,
            "property_id": property_id,
            "item": item,
            "currency": currency,
            "total_paise": total_paise,
            "status": "sending",
            "thread_id": thread_id,
            "shares": shares,
            "created_at": now,
            "updated_at": now,
        })

    def get_by_thread(self, thread_id: str) -> dict | None:
        return self.bills.find_one("thread_id", thread_id)

    def mark_delivery(self, bill_id: str, member_jid: str, delivery: str) -> None:
        bill = self.bills.get_by_id(bill_id)
        shares = [
            {**s, "delivery": delivery} if s["member_jid"] == member_jid else s for s in bill["shares"]
        ]
        self.bills.update(bill_id, {"shares": shares, "updated_at": now_iso()})

    def mark_group_delivery(self, bill_id: str, delivery: str) -> None:
        self.bills.update(bill_id, {"group_delivery": delivery, "updated_at": now_iso()})

    def mark_sent(self, bill_id: str) -> None:
        self.bills.update(bill_id, {"status": "sent", "updated_at": now_iso()})
