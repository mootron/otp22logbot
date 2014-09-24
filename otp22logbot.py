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
        help='Kill password to stop bot. Default "killme"',
        default='killme',
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


class Connection(object):
    """Wrap a socket.

    This lets us do things like log interactions with the socket and
    easily change how we handle sockets in the future.
    """
    def __init__(self, socket, logger):
        self.socket = socket
        self.logger = logger

    def send(self, data):
        self.logger.debug('=SENDING=>[{0}]\n'.format(data))
        self.socket.send((data + '\r\n').encode('utf-8'))

    def recv(self, size=1024):
        buf = self.socket.recv(size).decode('utf-8')
        return buf

    def privmsg(self, channel, line):
        assert channel.startswith('#'), channel
        assert line
        self.send('PRIVMSG {0} :{1}'.format(channel, line))


class Bot(object):
    def __init__(self, app_args, logger):
        self.app_data = APP_DATA.copy()
        self.app_args = app_args
        self.logger = logger
        self.should_die = False

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
        return Connection(sock, self.logger)

    def handshake(self, conn):
        send = conn.send
        # @todo accept a server password
        # if app_args.password != False:
        #  sock.send('PASS {app_args.password}\r\n'.format(app_args=app_args).encode('utf-8'))
        send('NICK {0}'.format(self.app_args.nick))
        send('USER {app_args.user} {app_args.server} default :{app_args.real}'
             .format(app_args=self.app_args))
        send('JOIN #{app_args.channel}'
             .format(app_args=self.app_args))
        conn.privmsg(
            self.app_data['overlord'],
            'Greetings, overlord. I am for you.')
        conn.privmsg(
            '#' + self.app_args.channel,
            'I am a logbot and I am ready! Use ".help" for help.')

    def loop(self, conn):
        """
        This takes conn for two reasons.
        1. We may want a Bot instance to loop on an existing socket.
        2. We may want the same instance of Bot to serve multiple sockets.
        """
        send = conn.send
        last_message = ''
        message = ''
        users = {}

        while not self.should_die:
            now = datetime.utcnow()
            buf = conn.recv(1024)
            # @debug1
            self.logger.debug('received {0}'.format(buf))
            if buf.find('PING') != -1:
                send('PONG {0}\n'.format(buf.split()[1]))
            if buf.find('PRIVMSG') != -1:
                # @debug1
                self.logger.debug('handling shit')
                # @task handle input lengths. do not parse input of varied lengths.
                message = buf.split(':')
                # @debug1
                self.logger.debug('len(msg)[{0}]\n'.format(len(message)))
                if len(message) != 3:
                    continue
                else:
                    message_header = message[1].strip().split(' ')
                    message_body = message[2].strip().split(' ')
                # @debug2
                self.logger.debug("header {0}".format(message_header))
                self.logger.debug("body {0}".format(message_body))
                if not message_body:
                    continue
                if message_header:
                    channel = str(message_header[2])
                    requester = str(message_header[0].split('!')[0])
                # @task handle regular messages to the channel
                last_message = message
                message = '<{0}> {1} ({2}): {3}'.format(
                    now.strftime(self.app_data['timeformat']),
                    requester,
                    channel,
                    message[2]
                )
                users[requester] = {
                    'altnicks': [],
                    'channel': channel,
                    'message': message[2],
                    'seen': now,
                    'time': now
                }
                self.file_send(message)
                if len(message_body) > 3:
                    continue
                command = False
                parameter = False
                modifier = False
                if message_body:
                    command = str(message_body[0])
                if len(message_body) > 1:
                    parameter = str(message_body[1])
                if len(message_body) > 2:
                    modifier = str(message_body[2])
                # @debug1
                self.logger.info('cmd[{0}] param[{1}] mod[{2}] req[{3}]\n'
                                 .format(command, parameter, modifier, requester))
                if command == '.flush':
                    conn.privmsg(channel, 'Flushing and rotating logfiles...')
                elif command == '.help':
                    if not parameter:
                        line = 'Available commands (use .help <command> for more help): flush, help, kill, last, user, version'
                    elif parameter == 'flush':
                        line = ".flush: flush and rotate logfiles"
                    elif parameter == 'help':
                        line = ".help <command>: lists help for a specific command"
                    elif parameter == 'kill':
                        line = ".kill: attempts to kill this bot (good luck)"
                    elif parameter == 'last':
                        line = ".last [user]: displays last message received. if [user] is specified, displays last message sent by user"
                    elif parameter == 'user':
                        line = ".user [user]: displays information about user. if unspecified, defaults to command requester"
                    elif parameter == 'version':
                        line = ".version: displays version information"
                    conn.privmsg(channel, line)
                elif command == '.last':
                    conn.privmsg(channel, last_message)
                elif command == '.user':
                    if parameter in users:
                        this_time = users[requester]['seen'].strftime(self.app_data['timeformat_extended'])
                        user_lastmsg = users[requester]['time'].strftime(self.app_data['timeformat_extended'])
                        line = ('User {0} (last seen {1}), (last message {2} -- {3})'
                                .format(parameter, this_time, user_lastmsg,
                                        users[requester]['message']))
                    else:
                        line = 'Information unavailable for user {0}'.format(parameter)
                    conn.privmsg(channel, line)
                elif command == '.version':
                    version_string = (
                        "{app_data[version]}{app_data[phase]} by {app_data[overlord]}"
                        .format(app_data=self.app_data))
                    conn.privmsg(channel, version_string)
                elif channel != self.app_args.channel:
                    if command == '.kill':
                        if parameter == self.app_args.kill:
                            self.should_die = True
                            conn.privmsg(
                                requester,
                                'With urgency, my lord. Dying at your request.')
                            conn.privmsg(channel, 'Goodbye!')
                            send('QUIT :killed by {0}'.format(requester))
                elif command == '\x01VERSION\x01':
                    # @task respond to CTCP VERSION
                    line = (
                        '\x01VERSION OTP22LogBot '
                        'v{app_data[version]}{app_data[phase]}\x01'
                        .format(app_data=self.app_data))
                    send('NOTICE {0} :{1}'.format(requester, line))

    def shutdown(self):
        now = datetime.utcnow()
        end_message = (
            'CONNECTION STOPPED ... dying at {0}\n'
            .format(now.strftime(self.app_data['timeformat'])))
        self.file_send(end_message)
        self.logger.info(end_message)
        self.app_args.output.close()


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
    bot = Bot(app_args, logger)
    bot.startup()
    sock = bot.connect()
    bot.handshake(sock)
    bot.loop(sock)
    bot.shutdown()


if __name__ == "__main__":
    main()
