from otp22logbot import parse_privmsg


def test_public_nospaces():
    """Inbound channel traffic, no spaces in message
    """
    result = parse_privmsg(":L0j1k!~default@unaffiliated/l0j1k PRIVMSG #ircugm :hello")
    assert result == ("#ircugm", "L0j1k", ["hello"])


def test_public_spaces():
    """Inbound channel traffic, spaces in message
    """
    result = parse_privmsg(":L0j1k!~default@unaffiliated/l0j1k PRIVMSG #ircugm :foo bar")
    assert result == ("#ircugm", "L0j1k", ["foo", "bar"])


def test_private_nospaces():
    """Inbound private message, no spaces in message
    """
    result = parse_privmsg(":L0j1k!~default@unaffiliated/l0j1k PRIVMSG otp22logbot :hello")
    assert result == ("otp22logbot", "L0j1k", ["hello"])


def test_private_spaces():
    """Inbound private message, spaces in message
    """
    result = parse_privmsg(":L0j1k!~default@unaffiliated/l0j1k PRIVMSG otp22logbot :little bunny foo foo")
    assert result == ("otp22logbot", "L0j1k", ["little", "bunny", "foo", "foo"])
