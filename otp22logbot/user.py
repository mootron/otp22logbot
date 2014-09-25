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

    def update(self, channels, message, now=None):
        now = now or Datetime.utcnow()
        self.channels |= set(channels)
        self.message = message
        self.seen = now
        self.time = now
