EXTRACT_PROMPT = """You read a landlord's message about a shared bill and extract its details.

Rules:
- amount: the total as a plain number. "1k" = 1000, "4.5k" = 4500, "₹1,000" = 1000, "1000rs" = 1000.
- item: what was bought or paid for, in a few words (e.g. "water tank", "lift repair"). Leave out the word "bill".
- property_hint: the property, building, block or locality the bill is for, copied as written.
  It often follows "for", "at", "in" or comes before "residents" / "flats" / "tenants".
- Use null for anything the message does not say. Never invent values.

Examples:
"1000rs water tank was ordered for vidyaranyapura, split it"
  → amount 1000, item "water tank", property_hint "vidyaranyapura"
"split the lift repair bill between block B residents, 4.5k"
  → amount 4500, item "lift repair", property_hint "block B"
"₹1,250 for cleaning, divide it"
  → amount 1250, item "cleaning", property_hint null
"split the tank bill"
  → amount null, item "water tank", property_hint null"""
