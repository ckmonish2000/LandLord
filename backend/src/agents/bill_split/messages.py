"""Every text the bill split agent sends. Kept together so the wording is easy to review."""

from src.bills.utils import format_money

ASK_AMOUNT = "I can split that bill. How much was it? For example: _1000rs water tank for Vidyaranyapura_"
NO_PROPERTIES = "You haven't added any properties yet. Add one in the Landlord app, then ask me again."
NO_MEMBERS = "I couldn't find anyone else in the *{property}* group to split this with."
CANCELLED = "Okay, I won't send it."


def label(bill: dict) -> str:
    """'water tank bill (₹1,000)'"""
    item = bill.get("item") or "shared"
    return f"{item} bill ({format_money(bill['total_paise'], bill['currency'])})"


def ask_property(bill: dict, matched: bool) -> str:
    lead = "A few properties match that name." if matched else "Which property is this for?"
    return f"{lead}\nPick the one for the {label(bill)}."


def poll_question(bill: dict, part: int, parts: int) -> str:
    suffix = f" ({part} of {parts})" if parts > 1 else ""
    return f"Who shares the {label(bill)}?{suffix}"


def confirm(bill: dict, property_name: str, shares: list[dict]) -> str:
    total = format_money(bill["total_paise"], bill["currency"])
    amounts = {s["amount_paise"] for s in shares}
    if len(amounts) == 1:
        each = f"*{format_money(shares[0]['amount_paise'], bill['currency'])}* each"
    else:
        each = "about *" + format_money(min(amounts), bill["currency"]) + "* each (a few paise differ)"
    lines = [
        f"*{(bill.get('item') or 'Bill').capitalize()}* · {property_name}",
        f"{total} split between {len(shares)} {'person' if len(shares) == 1 else 'people'}: {each}",
        "",
        *[f"• {s['name']}: {format_money(s['amount_paise'], bill['currency'])}" for s in shares],
        "",
        "Send this to the group and to each person?",
    ]
    return "\n".join(lines)


def group_notice(bill: dict, shares: list[dict]) -> str:
    total = format_money(bill["total_paise"], bill["currency"])
    item = (bill.get("item") or "shared bill").capitalize()
    return "\n".join(
        [
            f"🧾 *{item}*: {total}",
            f"Split between {len(shares)}:",
            *[f"• {s['name']}: {format_money(s['amount_paise'], bill['currency'])}" for s in shares],
            "",
            "Each person has also been sent their share personally.",
        ]
    )


def personal_notice(bill: dict, property_name: str, share: dict, people: int) -> str:
    total = format_money(bill["total_paise"], bill["currency"])
    item = bill.get("item") or "shared"
    amount = format_money(share["amount_paise"], bill["currency"])
    return (
        f"Hi {share['name']}, the {item} bill for {property_name} was {total}, "
        f"split between {people} people.\nYour share is *{amount}*."
    )


def report(property_name: str, group_ok: bool, sent: list[str], failed: list[str]) -> str:
    lines = [f"Sent ✅ {property_name}"]
    lines.append("• Group message: sent" if group_ok else "• Group message: failed")
    lines.append(f"• Personal messages: {len(sent)} of {len(sent) + len(failed)} sent")
    if failed:
        lines.append(f"Couldn't reach: {', '.join(failed)}")
    return "\n".join(lines)
