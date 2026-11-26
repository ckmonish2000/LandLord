"""Turning the landlord's message into a structured bill request (the LLM step)."""

from langchain_core.messages import HumanMessage, SystemMessage

from src.agents.bill_split.prompts import EXTRACT_PROMPT
from src.agents.bill_split.schemas import BillRequest
from src.llm import get_llm


def extract_bill(prompt: str) -> BillRequest:
    llm = get_llm(temperature=0).with_structured_output(BillRequest)
    return llm.invoke([SystemMessage(EXTRACT_PROMPT), HumanMessage(prompt)])
