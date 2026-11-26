from src.bills.repository import BillRepository
from src.bills.service import BillService


def get_bill_service() -> BillService:
    return BillService(BillRepository())
