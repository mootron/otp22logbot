import re


class ParseError(Exception):
    def __init__(self, message=None, data=None):
        Exception.__init__(self, message)
        self.data = data

    def __str__(self):
        return repr(self.data[:100])


class TooBig(ParseError):
    """Input message was bigger than safe for IRC.
    """


class Malformed(ParseError):
    """Input message was in some way syntactically wrong for IRC.
    """


class NoTerminator(Malformed):
    """Input message did not end in CR LF.
    """


def parse_message(data):
    # Don't be silent if we get non-bytes - coder needs to know that
    # and fix it early, NOT silence it with try/except.
    # There is no "handling" this. The error is coder's.
    assert isinstance(data, bytes)
    # If we get a falsy value, just skip this.
    if not data:
        return None
    # RFC2812 2.3 IRC messages are always lines of characters terminated
    # with a CR-LF (Carriage Return - Line Feed) pair, and these
    # messages SHALL NOT exceed 512 characters in length, counting all
    # characters including the trailing CR-LF.
    if len(data) > 512:
        raise TooBig(data=data)
    if not data[-2:] == b"\r\n":
        raise NoTerminator(data=data)
    else:
        data = data[:-2]

    # Now parse out prefix, if any.
    # RFC2812 2.3: The presence of a prefix is indicated with a single
    # leading ASCII colon character
    if data[0:1] == b":":
        pos = data.find(b" ")
        # RFC2812 2.3: There MUST be NO gap (whitespace) between the
        # colon and the prefix. Could be unsafe.
        if pos == 0:
            raise Malformed(data=data)
        elif pos == -1:
            # Prefix indicated with leading : but no space, not valid
            raise Malformed(data=data)
        prefix = data[1:pos]
        data = data[pos + 1:]
    else:
        prefix = ''

    # Now find the split between IRC command and params, if any.
    # Params can have spaces in it.
    result = data.split(b" ", 1)
    if len(result) > 1:
        command, params = result
    else:
        command, params = result, b""

    return prefix, command, params


def parse_messages(data, logger):
    """Find possible IRC messages and trailing data in given bytes.
    """
    assert isinstance(data, bytes)
    messages = []
    end = 0
    for match in re.finditer(b'(.{0,510}\r\n)', data):
        line = match.group(1)
        try:
            message = parse_message(line)
            messages.append(message)
        # This is tough, but I don't want to automatically lose
        # all the messages in this batch because one didn't parse,
        # yet it's not okay for even that one parse to fail *silently*.
        # So we end up logging the exceptions, which seems a bit messy,
        # but it allows the error to be highlighted or silenced by user
        # according to situations.
        except ParseError:
            logger.exception("Caught error during message parse")
        end = match.end()
    unconsumed = data[end:]
    return messages, unconsumed


def message_iterator(logger):
    """Handle fragments and call parse_messages for consumers.
    """
    messages = []
    old_data = ''
    while True:
        new_data = yield messages
        if new_data:
            all_data = b"".join([old_data, new_data])
            messages, old_data = parse_messages(all_data, logger)


def parse_privmsg(params):
    """Parse the params part of a PRIVMSG command.
    """
    assert isinstance(params, bytes)
    target_spec, text = params.split(b" ", 1)
    targets = target_spec.split(b",")
    if text.startswith(b":"):
        text = text[1:]
    else:
        text = text.split(b" ", 1)[0]
    return (targets, text)
