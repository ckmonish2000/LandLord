NAME = "alfred"
SIGNATURE = "🎩 *Alfred*"
GREETING = "Hey, this is Alfred 👋\nHow can I help you today?"

# Reply for messages no sub-agent handles yet: say what Alfred can do.
HELP = (
    f"{GREETING}\n\n"
    "Right now I can split a bill between residents. Try:\n"
    "_1000rs water tank for Vidyaranyapura, split it_"
)

# Where the router can send a message. Add one per sub-agent.
ROUTE_BILL_SPLIT = "bill_split"
ROUTE_GENERAL = "general"
