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
from datetime import datetime
import textwrap
import socket
import sys


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
    return parser


def filesend(handle, data):
    if APP_DATA['debug']:
        sysprint('=WRITING=>[{0}]\n'.format(data))
    handle.write(str(data))


def socksend(socket, data):
    if APP_DATA['debug']:
        sysprint('=SENDING=>[{0}]\n'.format(data))
    socket.send((data + '\r\n').encode('utf-8'))


def sysprint(data):
    sys.stdout.write(data)
    sys.stdout.flush()


# @todo stub
def process_command(command):
    sysprint(command)


APP_DATA = {
    'debug': True,
    'kill': False,
    'overlord': 'L0j1k',
    'phase': 'a',
    'timeformat': '%H:%M:%S',
    'timeformat_extended': '',
    'version': '0.0.4'
}

def startup(app_args):
    now = datetime.utcnow()
    template = textwrap.dedent("""
        otp22logbot.py {app_data[version]}{app_data[phase]} by L0j1k\n
        [+] started at {time}
        [+] using configuration file: {config_path}
        [+] using output logfile {app_args.output.name}
        [+] using server {app_args.server} on port {app_args.port}
        [+] using timestamp format {app_data[timeformat]}
        """).strip()
    message = template.format(
        app_data=APP_DATA, app_args=app_args,
        time=now.strftime(APP_DATA['timeformat']),
        config_path=app_args.init.name if app_args.init else None
    )
    sysprint(message)


def connect(app_args):
    sock = socket.socket()
    sock.connect((app_args.server, app_args.port))

    # @todo accept a server password
    # if app_args.password != False:
    #  sock.send('PASS {app_args.password}\r\n'.format(app_args=app_args).encode('utf-8'))
    socksend(sock, 'NICK {0}'.format(app_args.nick))
    socksend(sock, 'USER {app_args.user} {app_args.server} default :{app_args.real}'
                   .format(app_args=app_args))
    socksend(sock, 'JOIN #{app_args.channel}'
                   .format(app_args=app_args))
    socksend(sock, 'PRIVMSG {app_data[overlord]} :Greetings, overlord. I am for you.'
                   .format(app_data=APP_DATA))
    socksend(sock, 'PRIVMSG #{app_args.channel} :I am a logbot and I am ready! Use ".help" for help.'
                   .format(app_args=app_args))
    return sock


# @debug
# ==> outgoing private message
#:sendak.freenode.net 401 otp22logbot L0j1k: :No such nick/channel
# ==> inbound channel traffic
#:L0j1k!~default@unaffiliated/l0j1k PRIVMSG #ircugm :hello
#:L0j1k!~default@unaffiliated/l0j1k PRIVMSG #ircugm :foo bar
# ==> inbound private message
#:L0j1k!~default@unaffiliated/l0j1k PRIVMSG otp22logbot :hello
#:L0j1k!~default@unaffiliated/l0j1k PRIVMSG otp22logbot :little bunny foo foo
# ==> user quits
#:Guest80053!~default@cpe-70-112-152-59.austin.res.rr.com QUIT :Quit: leaving
# ==> user joins
#:default!~default@cpe-70-112-152-59.austin.res.rr.com JOIN #ircugm
# ==> nick change
#:default!~default@cpe-70-112-152-59.austin.res.rr.com NICK :Guest64847

def loop(sock, app_args):
    last_message = ''
    message = ''
    users = {}

    while not APP_DATA['kill']:
        now = datetime.utcnow()
        buf = sock.recv(1024).decode('utf-8')
        # @debug1
        sysprint(buf)
        if buf.find('PING') != -1:
            socksend(sock, 'PONG {0}\n'.format(buf.split()[1]))
        if buf.find('PRIVMSG') != -1:
            # @debug1
            sysprint('handling shit...\n')
            # @task handle input lengths. do not parse input of varied lengths.
            message = buf.split(':')
            # @debug1
            sysprint('len(msg)[{0}]\n'.format(len(message)))
            if len(message) != 3:
                continue
            else:
                message_header = message[1].strip().split(' ')
                message_body = message[2].strip().split(' ')
            # @debug2
            print(message_header)
            print(message_body)
            if not message_body:
                continue
            if message_header:
                channel = str(message_header[2])
                requester = str(message_header[0].split('!')[0])
            # @task handle regular messages to the channel
            last_message = message
            message = '<{0}> {1} ({2}): {3}'.format(
                now.strftime(APP_DATA['timeformat']),
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
            filesend(app_args.output, message)
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
            sysprint('cmd[{0}] param[{1}] mod[{2}] req[{3}]\n'
                     .format(command, parameter, modifier, requester))
            if command == '.flush':
                socksend(sock, 'PRIVMSG {0} :Flushing and rotating logfiles...'
                               .format(channel))
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
                socksend(sock, 'PRIVMSG {0} :{1}'.format(channel, line))
            elif command == '.last':
                socksend(sock, 'PRIVMSG {0} :{1}'.format(channel, last_message))
            elif command == '.user':
                if parameter in users:
                    this_time = users[requester]['seen'].strftime(APP_DATA['timeformat_extended'])
                    user_lastmsg = users[requester]['time'].strftime(APP_DATA['timeformat_extended'])
                    line = ('User {0} (last seen {1}), (last message {2} -- {3})'
                            .format(parameter, this_time, user_lastmsg,
                                    users[requester]['message']))
                else:
                    line = 'Information unavailable for user {0}'.format(parameter)
                socksend(sock, 'PRIVMSG {0} :{1}'.format(channel, line))
            elif command == '.version':
                version_string = (
                    "{app_data[version]}{app_data[phase]} by {app_data[overlord]}"
                    .format(app_data=APP_DATA))
                socksend(sock, 'PRIVMSG {0} :{1}'.format(channel, version_string))
            elif channel != app_args.channel:
                if command == '.kill':
                    if parameter == app_args.kill:
                        APP_DATA['kill'] = True
                        socksend(sock, 'PRIVMSG {0} :With urgency, my lord. '
                                       'Dying at your request.'.format(requester))
                        socksend(sock, 'PRIVMSG {0} :Goodbye!'.format(channel))
                        socksend(sock, 'QUIT :killed by {0}'.format(requester))
            elif command == '\x01VERSION\x01':
                # @task respond to CTCP VERSION
                line = (
                    '\x01VERSION OTP22LogBot '
                    'v{app_data[version]}{app_data[phase]}\x01'
                    .format(app_data=APP_DATA))
                socksend(sock, 'NOTICE {0} :{1}'.format(requester, line))


def shutdown(app_args):
    now = datetime.utcnow()
    end_message = ('[+] CONNECTION STOPPED ... dying at {0}\n'
                   .format(now.strftime(APP_DATA['timeformat'])))
    filesend(app_args.output, end_message)
    sysprint(end_message)
    app_args.output.close()


def main():
    parser = make_parser()
    app_args = parser.parse_args()
    startup(app_args)
    sock = connect(app_args)
    loop(sock, app_args)
    shutdown(app_args)


if __name__ == "__main__":
    main()
