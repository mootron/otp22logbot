import logging
from socket import socket as Socket


class Connection(object):
    """Wrap a socket and IRC details.

    This allows things like instrumenting interactions with the socket
    to log them, and more easily changing how sockets are handled in the
    future.
    """
    def __init__(self, sock, logger):
        self.sock = sock
        self.logger = logger
        self.last_message = None
        self.encoding = "ascii"

    @classmethod
    def new(cls, host, port, logger=None):
        logger = logger or logging.getLogger(__name__)
        sock = Socket()
        try:
            sock.connect((host, port))
        except socket.error:
            return None
        return Connection(sock, logger)

    def send(self, data):
        # IRC encoding seems dodgy. UTF-8 could be okay, or ISO 8859-1,
        # but we just don't know. So punt and make it configurable -
        # but default to enforcing ASCII.
        try:
            encoded = data.encode(self.encoding)
        except UnicodeEncodeError:
            self.logger.debug('cannot safely encode data: {0!r}'
                              .format(data))
            return
        # This especially sucks with UTF-8.
        if len(encoded) > 510:
            self.logger.debug("cannot safely send overlong data: {0!r}"
                              .format(data[:520]))
            return
        self.logger.debug('=SENDING=>[{0}]'.format(data))
        self.sock.sendall(encoded + b'\r\n')

    def recv(self, size=1024):
        # Totally ignore encoding. We can't guarantee anything about
        # what the server might be sending us, and pretty much have to
        # take whatever. Because IRC.
        buf = self.sock.recv(size)
        return buf

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        self.logger.debug("socket shutdown")
        self.sock.shutdown(socket.SHUT_RDWR)
        self.logger.debug("socket close")
        self.sock.close()

    def nick(self, nickname):
        assert nickname
        assert " " not in nickname
        # RFC 1459 4.1.2, RFC 2812 3.1.2
        self.send('NICK {0}'.format(nickname))

    def user(self, username, realname):
        assert username
        assert realname
        # RFC 1459 4.1.3 "username hostname servername :real name"
        # RFC 2812 3.1.3 "user mode unused :realname"
        self.send('USER {0} 0 * :{1}'.format(username, realname))

    def password(self, password):
        # RFC 1459 4.1.1, RFC 2812 3.1.1 - PASS before NICK, USER
        self.send('PASS {0}'.format(password))

    def join(self, channels, keys=None):
        keys = (" " + ",".join(keys)) if keys else ''
        # RFC 1459 4.2.1, RFC 2812 3.2.1
        for channel in channels:
            assert channel.startswith('#'), channel
            self.send('JOIN {0}{1}'.format(channel, keys))

    def _privmsg_any(self, targets, text):
        """Just put together and send a PRIVMSG message.

        Not meant to be used generally, since validation is so loose
        and it is a slight extra burden to pass a sequence in.
        """
        # RFC 1459 4.4.1, RFC 2812 3.3.1
        if not text:
            return
        for target in targets:
            if not target:
                continue
            self.send('PRIVMSG {0} :{1}'.format(target, text))

    def privmsg_user(self, nickname, text):
        """Send a PRIVMSG to the named user.

        Intentionally barfs if the coder tries to jam a channel
        or a list or something in.
        """
        assert nickname
        assert not nickname.startswith('#')
        assert text
        self._privmsg_any([nickname], text)

    def privmsg_channel(self, channel, text):
        """Send a PRIVMSG to the named channel.

        Intentionally barfs if the coder tries to jam a nickname
        or a list or something in. As it happens, won't deal with funky
        channels that begin with & either.
        """
        assert channel
        assert channel.startswith('#')
        assert text
        self._privmsg_any([channel], text)

    def notice(self, target, text):
        # RFC 1459 4.4.2, RFC 2812 3.3.2
        assert target
        assert text
        self.send('NOTICE {0} :{1}'.format(target, text))

    def pong(self, server):
        # RFC 1459 4.6.3, RFC 2812 3.7.3
        # - server is MY server.
        self.send('PONG {0}'.format(server))

    def quit(self, quit_message):
        # RFC 1459 4.1.6, RFC 2812 3.1.7
        self.send('QUIT :{0}'.format(quit_message))
