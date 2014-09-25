#!/usr/bin/python3
"""OTP22 Log Bot
This bot logs an IRC channel to a file. It also provides a small
number of additional features related to users and their content.

@file otp22logbot.py
This is the primary application driver file.
@author L0j1k
@contact L0j1k@L0j1k.com
@license BSD3
@version 0.0.4a
"""
import argparse
import logging
from datetime import datetime
import socket
import sys


APP_DATA = {
    'overlord': 'L0j1k',
    'phase': 'a',
    'timeformat': '%H:%M:%S',
    'timeformat_extended': '',
    'version': '0.0.4'
}


def make_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-c', '--channel',
        help='IRC channel to join. Default "otp22"',
        default='ircugm',
        nargs='?',
        type=str
    )
    parser.add_argument(
        '-i', '--init',
        help='Specify initialization/configuration file for logbot',
        default=False,
        nargs='?',
        type=argparse.FileType('r')
    )
    parser.add_argument(
        '-k', '--kill',
        help='Kill password to stop bot from IRC.',
        default=None,
        nargs='?',
        type=str
    )
    parser.add_argument(
        '-n', '--nick',
        help='IRC nick name. Default "otp22logbot"',
        default='otp22logbot',
        nargs='?',
        type=str
    )
    parser.add_argument(
        '-o', '--output',
        help='Output log filename. Default "otp22logbot.log"',
        default='otp22logbot.log',
        nargs='?',
        type=argparse.FileType('w')
    )
    parser.add_argument(
        '-p', '--port',
        help='IRC port to use. Default 6667',
        default=6667,
        nargs='?',
        type=int
    )
    parser.add_argument(
        '-r', '--real',
        help='IRC real name. Default "otp22logbot"',
        default='otp22logbot',
        nargs='?',
        type=str
    )
    parser.add_argument(
        '-s', '--server',
        help='IRC server to connect to. Default "irc.freenode.net"',
        default='irc.freenode.net',
        nargs='?',
        type=str
    )
    parser.add_argument(
        '-u', '--user',
        help='IRC user name. Default "otp22logbot"',
        default='otp22logbot',
        nargs='?',
        type=str
    )
    parser.add_argument(
        '--debug',
        action="store_true",
        help="print debug information"
    )
    return parser


class User(object):
    """Information on one IRC user.
    """
    def __init__(self, nick):
        self.nicks = set([nick])
        self.channels = set()
        self.message = None
        self.seen = None
        self.time = None

    def update(self, channel, message, now=None):
        now = now or datetime.utcnow()
        self.channels.add(channel)
        self.message = message
        self.seen = now
        self.time = now


class Connection(object):
    """Wrap a socket and IRC details.

    This lets us do things like log interactions with the socket and
    easily change how we handle sockets in the future.
    """
    def __init__(self, sock, logger):
        self.sock = sock
        self.logger = logger
        self.last_message = None

    def send(self, data):
        self.logger.debug('=SENDING=>[{0}]\n'.format(data))
        self.sock.send((data + '\r\n').encode('utf-8'))

    def recv(self, size=1024):
        buf = self.sock.recv(size).decode('utf-8')
        return buf

    def nick(self, name):
        assert name
        self.send('NICK {0}'.format(name))

    def user(self, username, server, real):
        assert username
        assert server
        assert real
        # RFC 1459 4.1.3: realname parameter [...] may contain space
        # characters and must be prefixed with a colon (':') to make
        # sure this is recognised as such.
        self.send('USER {0} {1} default :{2}'.format(username, server, real))

    def pass_(self, password):
        self.send('PASS {0}'.format(password))

    def join(self, channel):
        assert channel.startswith('#'), channel
        self.send('JOIN {0}'.format(channel))

    def privmsg(self, channel, line):
        assert channel.startswith('#'), channel
        assert line
        self.send('PRIVMSG {0} :{1}'.format(channel, line))

    def pong(self, line):
        self.send('PONG {0}\n'.format(line))

    def notice(self, name, line):
        self.send('NOTICE {0} :{1}'.format(name, line))

    def quit(self, line):
        self.send('QUIT :{0}'.format(line))


class Bot(object):
    def __init__(self, app_args, logger):
        self.app_data = APP_DATA.copy()
        self.app_args = app_args
        self.logger = logger
        self.should_die = False
        self.users = {}
        self.commands = {
            '.flush': self.flush,
            '.help': self.help,
            '.version': self.version,
            '.kill': self.kill,
            '.last': self.last,
            '.user': self.user,
            '\x01VERSION\x01': self.version_query,
        }
        self.helps = {
            'flush': ".flush: flush and rotate logfiles",
            'help': ".help <command>: lists help for a specific command",
            'kill': ".kill: attempts to kill this bot (good luck)",
            'last': ".last [user]: displays last message received. if [user] is specified, displays last message sent by user",
            'user': ".user [user]: displays information about user. if unspecified, defaults to command requester",
            'version': ".version: displays version information",
        }

    def file_send(self, data):
        self.logger.debug('=WRITING=>[{0}]\n'.format(data))
        self.app_args.output.write(str(data))

    def startup(self):
        info = self.logger.info
        info("otp22logbot.py {0[version]}{0[phase]} by L0j1k".format(self.app_data))

        now = datetime.utcnow().strftime(APP_DATA['timeformat'])
        info("started at {0}".format(now))

        config_path = self.app_args.init.name if self.app_args.init else None
        info("using configuration file: {0}".format(config_path))

        output_name = self.app_args.output.name
        info("using output logfile {0}".format(output_name))

        server = self.app_args.server
        port = self.app_args.port
        info("using server {0} on port {1}".format(server, port))

        timeformat = self.app_data["timeformat"]
        info("using timestamp format {0}".format(timeformat))

    def connect(self):
        sock = socket.socket()
        sock.connect((self.app_args.server, self.app_args.port))
        return Connection(sock, self.logger.getChild("connection"))

    def handshake(self, conn):
        if self.app_args.password:
            conn.pass_(self.app_args.password)
        conn.nick(self.app_args.nick)
        conn.user(self.app_args.user, self.app_args.server, self.app_args.real)
        conn.join('#' + self.app_args.channel)
        conn.privmsg(
            self.app_data['overlord'],
            'Greetings, overlord. I am for you.')
        conn.privmsg(
            '#' + self.app_args.channel,
            'I am a logbot and I am ready! Use ".help" for help.')

    def help(self, conn, requester, channel, args):
        parameter = args[0] if args else None
        if parameter:
            line = self.helps.get(parameter)
        if not parameter or not line:
            line = 'Available commands (use .help <command> for more help): flush, help, kill, last, user, version'
        conn.privmsg(channel, line)

    def flush(self, conn, requester, channel, args):
        conn.privmsg(channel, 'Flushing and rotating logfiles...')

    def version(self, conn, requester, channel, args):
        version_string = (
            "{app_data[version]}{app_data[phase]} by {app_data[overlord]}"
            .format(app_data=self.app_data))
        conn.privmsg(channel, version_string)

    def kill(self, conn, requester, channel, args):
        parameter = args[0] if args else None
        if self.app_args.kill and parameter == self.app_args.kill:
            self.should_die = True
            conn.privmsg(
                requester,
                'With urgency, my lord. Dying at your request.')
            conn.privmsg(channel, 'Goodbye!')
            conn.quit('killed by {0}'.format(requester))

    def version_query(self, conn, requester, channel, args):
        line = (
            '\x01VERSION OTP22LogBot '
            'v{app_data[version]}{app_data[phase]}\x01'
            .format(app_data=self.app_data))
        conn.notice(requester, line)

    def last(self, conn, requester, channel, args):
        conn.privmsg(channel, conn.last_message)

    def parse_command(self, message_body):
        if len(message_body) > 3:
            return None
        return message_body

    def format_message(self, requester, channel, content):
        now = datetime.utcnow()
        formatted_message = '<{0}> {1} ({2}): {3}'.format(
            now.strftime(self.app_data['timeformat']),
            requester, channel, content)
        return formatted_message

    def get_user(self, nick):
        user = self.users.get(nick)
        if not user:
            user = User(nick)
            self.users[nick] = user
        return user

    def user(self, conn, requester, channel, args):
        parameter = args[0] if args else None
        if parameter in self.users:
            user = self.users[requester]
            timeformat = self.appdata['timeformat_extended']
            this_time = user.seen.strftime(timeformat)
            user_lastmsg = user.time.strftime(timeformat)
            line = ('User {0} (last seen {1}), (last message {2} -- {3})'
                    .format(parameter, this_time, user_lastmsg, user.message))
        else:
            line = 'Information unavailable for user {0}'.format(parameter)
        conn.privmsg(channel, line)

    def loop(self, conn):
        """
        This takes conn for two reasons.
        1. We may want a Bot instance to loop on an existing socket.
        2. We may want the same instance of Bot to serve multiple sockets.
        """
        formatted_message = ''
        buffer = ''

        while not self.should_die:
            received = conn.recv(1024)
            self.logger.debug('received {0}'.format(received))
            buffer = buffer + received
            if message.startswith('PING'):
                conn.pong(message.split(None, 2)[1])
            elif message.startswith('PRIVMSG'):
                channel, requester, message_body = parse_privmsg(message)
                conn.last_message = formatted_message
                formatted_message = self.format_message(
                    requester, channel, message_body[2])

                user = self.get_user(requester)
                user.update(channel, message_body[2])

                self.file_send(formatted_message)
                parsed = self.parse_command(message_body)
                if not parsed:
                    self.logger.warning("parse_command failed on {0}"
                                        .format(message_body))
                    continue
                command, *args = parsed
                self.logger.info('cmd[{0}] args[{1}] req[{2}]\n'
                                 .format(command, args, requester))
                function = self.commands.get(command)
                if function:
                    function(conn, requester, channel, args)

    def shutdown(self):
        now = datetime.utcnow()
        timestamp = now.strftime(self.app_data['timeformat'])
        end_message = 'shutdown at {0}\n'.format(timestamp)
        self.file_send(end_message)
        self.logger.info(end_message)
        self.app_args.output.close()


def parse_privmsg(data):
    message = data.split(':', 3)
    if len(message) != 3:
        return None
    else:
        message_header = message[1].strip().split(' ', 3)
        args = message[2].strip().split(' ')
    if message_header:
        channel = str(message_header[2])
        requester = str(message_header[0].split('!', 1)[0])
    return channel, requester, args


def configure_logging(app_args):
    logger = logging.getLogger(__name__)
    if app_args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        fmt="[+] %(message)s",
    )
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger


def main():
    parser = make_parser()
    app_args = parser.parse_args()
    logger = configure_logging(app_args)
    bot = Bot(app_args, logger.getChild("bot"))
    bot.startup()
    try:
        sock = bot.connect()
        bot.handshake(sock)
        bot.loop(sock)
    finally:
        bot.shutdown()


if __name__ == "__main__":
    main()
