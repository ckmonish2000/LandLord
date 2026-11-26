from src.database import JsonCollection


class BillRepository(JsonCollection):
    """One record per split bill.

    {id, client_id, property_id, item, currency, total_paise, status, thread_id,
     shares: [{member_jid, name, amount_paise, delivery}], created_at, updated_at}

    status: sending | sent; delivery (per share) and group_delivery: pending | sent | failed.
    Shares are what a dues / unpaid rent agent reads later.
    """

    def __init__(self):
        super().__init__("bills")
