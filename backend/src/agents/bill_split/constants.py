NAME = "bill_split"
DEFAULT_CURRENCY = "INR"

ALL_OPTION = "Everyone"  # poll option that selects every member
MEMBERS_PER_POLL = 12  # WhatsApp's poll limit; the first poll also holds ALL_OPTION
OPTION_MAX_CHARS = 40
PROPERTY_LIST_MAX = 10  # WhatsApp's list row limit

CONFIRM_YES = "bill_split:yes"
CONFIRM_NO = "bill_split:no"

# Pause between personal messages. Bursts of near identical messages to many
# contacts are what get WhatsApp numbers restricted.
DELIVERY_DELAY_SECONDS = 1.5
