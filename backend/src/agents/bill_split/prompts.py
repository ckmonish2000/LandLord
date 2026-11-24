EXTRACT_PROMPT = """You read a landlord's message about a shared bill and extract its details.

Rules:
- amount: the total as a plain number. "1k" = 1000, "1.5k" = 1500, "₹1,000" = 1000, "1000rs" = 1000.
- item: what was bought or paid for, in a few words (e.g. "water tank", "lift repair").
- property_hint: the property, building or locality named, copied as written. Do not guess one.
- Leave a field empty if the message does not say it. Never invent values."""
