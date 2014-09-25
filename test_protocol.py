import logging
from protocol import parse_message, parse_messages, parse_privmsg


class Test_parse_message(object):

    def test_privmsg_public_nospaces(self):
        data = b":L0j1k!~default@unaffiliated/l0j1k PRIVMSG #ircugm :hello\r\n"
        result = parse_message(data)
        assert result == (b"L0j1k!~default@unaffiliated/l0j1k", b"PRIVMSG", b"#ircugm :hello")

    def test_privmsg_public_spaces(self):
        data = b":L0j1k!~default@unaffiliated/l0j1k PRIVMSG #ircugm :foo bar\r\n"
        result = parse_message(data)
        assert result == (b"L0j1k!~default@unaffiliated/l0j1k", b"PRIVMSG", b"#ircugm :foo bar")

    def test_privmsg_private_nospaces(self):
        data = b":L0j1k!~default@unaffiliated/l0j1k PRIVMSG otp22logbot :hello\r\n"
        result = parse_message(data)
        assert result == (b"L0j1k!~default@unaffiliated/l0j1k", b"PRIVMSG", b"otp22logbot :hello")

    def test_privmsg_private_spaces(self):
        data = b":L0j1k!~default@unaffiliated/l0j1k PRIVMSG otp22logbot :little bunny foo foo\r\n"
        result = parse_message(data)
        assert result == (b"L0j1k!~default@unaffiliated/l0j1k", b"PRIVMSG", b"otp22logbot :little bunny foo foo")

    def test_privmsg_outgoing(self):
        data = b":sendak.freenode.net 401 otp22logbot L0j1k: :No such nick/channel\r\n"
        result = parse_message(data)
        assert result == (b"sendak.freenode.net", b"401", b"otp22logbot L0j1k: :No such nick/channel")

    def test_quit(self):
        data = b":Guest80053!~default@cpe-70-112-152-59.austin.res.rr.com QUIT :Quit: leaving\r\n"
        result = parse_message(data)
        assert result == (b"Guest80053!~default@cpe-70-112-152-59.austin.res.rr.com", b"QUIT", b":Quit: leaving")

    def test_join(self):
        data = b":default!~default@cpe-70-112-152-59.austin.res.rr.com JOIN #ircugm\r\n"
        result = parse_message(data)
        assert result == (b"default!~default@cpe-70-112-152-59.austin.res.rr.com", b"JOIN", b"#ircugm")

    def test_nick(self):
        data = b":default!~default@cpe-70-112-152-59.austin.res.rr.com NICK :Guest64847\r\n"
        result = parse_message(data)
        assert result == (b"default!~default@cpe-70-112-152-59.austin.res.rr.com", b"NICK", b":Guest64847")


class Test_parse_messages(object):
    logger = logging.getLogger("")

    def test_one_with_unconsumed(self):
        data = b":Guest80053!~default@cpe-70-112-152-59.austin.res.rr.com QUIT :Quit: leaving\r\nmore crap here"
        result = parse_messages(data, self.logger)
        assert result == ([
            (b"Guest80053!~default@cpe-70-112-152-59.austin.res.rr.com", b"QUIT", b":Quit: leaving")
        ], b"more crap here")

    def test_two_no_unconsumed(self):
        data = b"".join([
            b":Guest80053!~default@cpe-70-112-152-59.austin.res.rr.com QUIT :Quit: leaving\r\n",
            b":default!~default@cpe-70-112-152-59.austin.res.rr.com JOIN #ircugm\r\n"
        ])
        result = parse_messages(data, self.logger)
        assert result == ([
            (b"Guest80053!~default@cpe-70-112-152-59.austin.res.rr.com", b"QUIT", b":Quit: leaving"),
            (b"default!~default@cpe-70-112-152-59.austin.res.rr.com", b"JOIN", b"#ircugm")
        ], b"")

    def test_two_with_unconsumed(self):
        data = b"".join([
            b":Guest80053!~default@cpe-70-112-152-59.austin.res.rr.com QUIT :Quit: leaving\r\n",
            b":default!~default@cpe-70-112-152-59.austin.res.rr.com JOIN #ircugm\r\n"
            b"more crap here\nafter newline \0after nul"
        ])
        result = parse_messages(data, self.logger)
        assert result == ([
            (b"Guest80053!~default@cpe-70-112-152-59.austin.res.rr.com", b"QUIT", b":Quit: leaving"),
            (b"default!~default@cpe-70-112-152-59.austin.res.rr.com", b"JOIN", b"#ircugm")
        ], b"more crap here\nafter newline \0after nul")


class Test_parse_privmsg(object):
    def test_public_nospaces(self):
        data = b"#ircugm :hello"
        result = parse_privmsg(data)
        assert result == ([b"#ircugm"], b"hello")

    def test_public_spaces(self):
        data = b"#ircugm :foo bar"
        result = parse_privmsg(data)
        assert result == ([b"#ircugm"], b"foo bar")

    def test_private_nospaces(self):
        data = b"otp22logbot :hello"
        result = parse_privmsg(data)
        assert result == ([b"otp22logbot"], b"hello")

    def test_private_spaces(self):
        data = b"otp22logbot :little bunny foo foo"
        result = parse_privmsg(data)
        assert result == ([b"otp22logbot"], b"little bunny foo foo")
