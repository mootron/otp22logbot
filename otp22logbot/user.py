from datetime import datetime as Datetime


class User(object):
    """Information on one IRC user.
    """
    def __init__(self, nick):
        self.nicks = set([nick])
        self.channels = set()
        self.message = None
        self.seen = None
        self.time = None

    def update(self, channels=None, message=None, now=None):
        now = now or Datetime.utcnow()
        if channels:
            self.channels |= set(channels)
        if message:
            self.message = message
        self.seen = now
        self.time = now
