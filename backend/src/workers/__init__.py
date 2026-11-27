"""Workers: process incoming events off the channel's event threads.

One sub-package per channel, each laid out the same way:
    worker.py     the worker class
    constants.py  its settings and fixed texts
    schemas.py    data passed around inside it
    utils.py      small helpers

Today: whatsapp/ (the landlord's WhatsApp messages → agents).
"""
