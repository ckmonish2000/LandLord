"""First version: understands the request and confirms what it understood.

Next steps (see the design notes): match the property, poll the landlord for who
shares the bill, confirm, then message the group and each resident.
"""

from langchain_core.messages import HumanMessage, SystemMessage

from src.agents.bill_split.constants import NAME
from src.agents.bill_split.prompts import EXTRACT_PROMPT
from src.agents.bill_split.schemas import BillRequest
from src.llm import get_llm


def format_amount(amount: float, currency: str) -> str:
    """1000 -> '₹1,000', 1250.5 -> '₹1,250.50'. Other currencies keep their code."""
    symbol = "₹" if currency == "INR" else f"{currency} "
    text = f"{amount:,.0f}" if amount == int(amount) else f"{amount:,.2f}"
    return f"{symbol}{text}"


class BillSplitAgent:
    name = NAME

    def run(self, prompt: str) -> str:
        bill = self.extract(prompt)

        missing = []
        if bill.amount is None:
            missing.append("how much the bill was")
        if bill.property_hint is None:
            missing.append("which property it is for")
        if missing:
            return f"I can split that bill. Tell me {' and '.join(missing)}."

        lines = [
            "*Bill split*",
            f"Item: {bill.item or 'Not mentioned'}",
            f"Amount: {format_amount(bill.amount, bill.currency)}",
            f"Property: {bill.property_hint}",
            "",
            "Next I'll ask who to split it between. That step is coming soon.",
        ]
        return "\n".join(lines)

    @staticmethod
    def extract(prompt: str) -> BillRequest:
        llm = get_llm(temperature=0).with_structured_output(BillRequest)
        return llm.invoke([SystemMessage(EXTRACT_PROMPT), HumanMessage(prompt)])
