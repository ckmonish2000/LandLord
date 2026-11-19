"""Standalone example: link and use WhatsApp with neonize's own client.

Nothing here touches gocode/_binder directly; neonize does that internally.
Not used by the app, it's just for reference.

Run from the project root:
    uv run python examples/neonize_connect.py                 # scan the QR shown in the terminal
    uv run python examples/neonize_connect.py 919876543210    # or get a pair code for this number
"""

import sys
import threading

from neonize.client import NewClient
from neonize.events import ConnectedEv, LoggedOutEv, MessageEv, PairStatusEv
from neonize.utils.jid import Jid2String
from neonize.utils.message import extract_text

PHONE = sys.argv[1] if len(sys.argv) > 1 else None  # digits only, with country code

# 1. Create the client. The string is where the session is stored
#    (SQLite file path, or a postgres:// URL).
client = NewClient("data/example.db")


# 2. Register event handlers BEFORE connect().

if PHONE:
    # Pair-code login: WhatsApp sending a QR means the connection is ready to pair,
    # so request a code then (once), instead of printing the QR.
    _pair_requested = threading.Event()

    def on_qr(c: NewClient, data: bytes):
        if not _pair_requested.is_set():
            _pair_requested.set()
            code = c.PairPhone(PHONE, show_push_notification=True)
            print(f"Pair code: {code}  (Linked devices -> Link with phone number instead)")

    client.event.qr(on_qr)
# else: neonize's default QR handler prints the QR in the terminal.


@client.event(PairStatusEv)
def on_pair(c: NewClient, ev: PairStatusEv):
    print(f"Paired as {Jid2String(ev.ID)}")


@client.event(ConnectedEv)
def on_connected(c: NewClient, ev: ConnectedEv):
    me = c.get_me()
    print(f"Connected as {Jid2String(me.JID)} ({me.PushName})")


@client.event(MessageEv)
def on_message(c: NewClient, ev: MessageEv):
    sender = ev.Info.MessageSource.Sender.User
    text = extract_text(ev.Message)
    print(f"{sender}: {text}")
    if text.strip().lower() == "ping":
        c.reply_message("pong", ev)  # simple auto-reply


@client.event(LoggedOutEv)
def on_logged_out(c: NewClient, ev: LoggedOutEv):
    print("Logged out (device was unlinked). Delete data/example.db to link again.")


# 3. Connect. Blocks until Ctrl+C; neonize runs the Go side on its own thread.
#    Second run onwards: no QR, it resumes the session saved in data/example.db.
if __name__ == "__main__":
    client.connect()
