from enum import StrEnum

NAME = "alfred"
SIGNATURE = "🎩 *Alfred*"
GREETING = "Hey, this is Alfred 👋\nHow can I help you today?"

# Reply for messages no sub-agent handles yet: say what Alfred can do.
HELP = (
    f"{GREETING}\n\n"
    "Right now I can split a bill between residents. Try:\n"
    "_1000rs water tank for Vidyaranyapura, split it_"
)


class Route(StrEnum):
    """Where the router can send a message: one value per sub-agent. The values are
    what the LLM answers with and the names of the graph's nodes."""

    BILL_SPLIT = "bill_split"
    GENERAL = "general"
