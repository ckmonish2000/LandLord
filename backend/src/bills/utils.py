"""Money helpers. Amounts are kept in paise (integers) so splits always add up."""


def to_paise(amount: float) -> int:
    return round(amount * 100)


def split_evenly(total_paise: int, people: int) -> list[int]:
    """1000.00 between 3 -> [33334, 33333, 33333]: the leftover paise go to the first people."""
    if people < 1:
        raise ValueError("need at least one person")
    base, leftover = divmod(total_paise, people)
    return [base + 1 if i < leftover else base for i in range(people)]


def format_money(paise: int, currency: str = "INR") -> str:
    """100000 -> '₹1,000', 33334 -> '₹333.34'. Other currencies keep their code."""
    symbol = "₹" if currency == "INR" else f"{currency} "
    rupees, cents = divmod(paise, 100)
    return f"{symbol}{rupees:,}" if cents == 0 else f"{symbol}{rupees:,}.{cents:02d}"
