class AlreadyLinked(Exception):
    pass


class NotLinked(Exception):
    pass


class NotReady(Exception):
    pass


class GroupNotFound(Exception):
    pass


class NotGroupMember(Exception):
    pass


class WhatsappRequestFailed(Exception):
    """WhatsApp rejected or failed a request (e.g. fetching groups)."""
