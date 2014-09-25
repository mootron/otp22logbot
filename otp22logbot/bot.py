from datetime import datetime as Datetime
from otp22logbot.app_data import APP_DATA
from otp22logbot.connection import Connection
from otp22logbot.user import User
from otp22logbot import protocol


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
        self.channel = '#' + self.app_args.channel
        self.nick = self.app_args.nick

    def file_send(self, data):
        self.logger.debug('=WRITING=>[{0}]'.format(data))
        self.app_args.output.write(data + '\n')
        self.app_args.output.flush()

    def startup(self):
        info = self.logger.info
        info("otp22logbot.py {0[version]}{0[phase]} by L0j1k".format(self.app_data))

        now = Datetime.utcnow().strftime(APP_DATA['timeformat'])
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
        self.logger.info("connecting to {0} {1}"
                         .format(self.app_args.server,
                                 self.app_args.port))
        return Connection.new(
            self.app_args.server, self.app_args.port,
            logger=self.logger.getChild("connection"))

    def handshake(self, conn):
        # RFC 1459 4.1.1, RFC 2812 3.1.1 - PASS before NICK, USER
        if self.app_args.password:
            conn.password(self.app_args.password)
        conn.nick(self.app_args.nick)
        conn.user(self.app_args.user, self.app_args.real)
        conn.join(['#' + self.app_args.channel])
        conn.privmsg_user(
            self.app_data['overlord'], 'Greetings, overlord. I am for you.')
        conn.privmsg_channel(
            self.channel,
            'I am a logbot and I am ready! Use ".help" for help.')

    def help(self, conn, requester, target, args):
        parameter = args[0] if args else None
        if parameter:
            line = self.helps.get(parameter)
        if not parameter or not line:
            line = 'Available commands (use .help <command> for more help): flush, help, kill, last, user, version'
        if target == self.nick:
            conn.privmsg_user(requester, line)
        else:
            conn.privmsg_channel(target, line)

    def flush(self, conn, requester, target, args):
        line = 'Flushing and rotating logfiles...'
        if target == self.nick:
            conn.privmsg_user(requester, line)
        else:
            conn.privmsg_channel(target, line)

    def version(self, conn, requester, target, args):
        line = (
            "{app_data[version]}{app_data[phase]} by {app_data[overlord]}"
            .format(app_data=self.app_data))
        if target == self.nick:
            conn.privmsg_user(requester, line)
        else:
            conn.privmsg_channel(target, line)

    def kill(self, conn, requester, target, args):
        parameter = args[0] if args else None
        if self.app_args.kill and parameter == self.app_args.kill:
            self.should_die = True
            conn.privmsg_user(
                requester, 'With urgency, my lord. Dying at your request.')
            conn.privmsg_channel(self.channel, 'Goodbye!')
            conn.quit('killed by {0}'.format(requester))

    def version_query(self, conn, requester, channel, args):
        line = (
            '\x01VERSION OTP22LogBot '
            'v{app_data[version]}{app_data[phase]}\x01'
            .format(app_data=self.app_data))
        conn.notice(requester, line)

    def last(self, conn, requester, target, args):
        parameter = args[0] if args else None
        if parameter:
            user = self.get_user(parameter)
            if not user:
                line = "unknown user"
            else:
                line = user.message
        else:
            line = conn.last_message
        line = line or "no last message"
        if target == self.nick:
            conn.privmsg_user(requester, line)
        else:
            conn.privmsg_channel(target, line)

    def format_message(self, requester, targets, content):
        now = Datetime.utcnow()
        # Ugh, encoding ambiguity
        encoding = "utf-8"
        targets = b",".join(targets).decode(encoding)
        formatted_message = '<{0}> {1} ({2}): {3}'.format(
            now.strftime(self.app_data['timeformat']),
            requester,
            targets,
            content.decode(encoding))
        return formatted_message

    def get_user(self, nick):
        user = self.users.get(nick)
        return user

    def new_user(self, nick):
        user = User(nick)
        self.users[nick] = user
        return user

    def user(self, conn, requester, target, args):
        parameter = args[0] if args else requester
        if parameter in self.users:
            user = self.users[requester]
            timeformat = self.app_data['timeformat_extended']
            this_time = user.seen.strftime(timeformat)
            user_lastmsg = user.time.strftime(timeformat)
            line = ('User {0} (last seen {1}), (last message {2} -- {3})'
                    .format(parameter, this_time, user_lastmsg, user.message))
        else:
            line = 'Information unavailable for user {0}'.format(parameter)
        if target == self.nick:
            conn.privmsg_user(requester, line)
        else:
            conn.privmsg_channel(target, line)

    def dispatch(self, conn, prefix, targets, text):
        encoding = "ascii"  # TODO
        prefix = prefix.decode(encoding)
        requester = prefix.split("!", 1)[0]
        targets = [target.decode(encoding) for target in targets]
        args = [arg.decode(encoding) for arg in text.split(b" ", 1)]

        command, args = args[0], args[1:] if len(args) > 1 else []
        function = self.commands.get(command)
        target = (
            self.channel if self.channel in targets
            else self.nick if self.nick in targets else None)
        if function and target:
            self.logger.info("{0} is running {1} {2}"
                             .format(prefix, command, args))
            # TODO: ensure downstream commands understand args,
            # possibly prechew it here - unicode, lists...
            function(conn, requester, target, args)
            return True
        return False

    def loop(self, conn):
        """
        This takes conn for two reasons.
        1. We may want a Bot instance to loop on an existing socket.
        2. We may want the same instance of Bot to serve multiple sockets.
        """
        encoding = "ascii"
        it = protocol.message_iterator(self.logger)
        it.send(None)
        formatted = ''
        with conn:
            while not self.should_die:
                try:
                    received = conn.recv(1024)
                except KeyboardInterrupt:
                    self.file_send("received KeyboardInterrupt")
                    conn.quit("Shutting down")
                    break
                if received == b'':
                    self.file_send("connection closed")
                    break
                self.logger.debug('received {0}'.format(received))
                messages = it.send(received)
                for prefix, command, params in messages:
                    now = Datetime.utcnow()
                    requester = prefix.split(b"!", 1)[0].decode(encoding)
                    if command == b"PING":
                        conn.pong(params.decode(encoding))
                    elif command == b"PRIVMSG":
                        targets, text = protocol.parse_privmsg(params)
                        formatted = self.format_message(requester, targets, text)
                        self.file_send(formatted)
                        dispatched = self.dispatch(conn, prefix, targets, text)
                        if not dispatched:
                            print("setting conn.last_message", formatted)
                            conn.last_message = formatted
                        user = self.get_user(requester) or self.new_user(requester)
                        if dispatched:
                            user.update(now=now)
                        else:
                            channels = [target for target in targets
                                        if target and target[0] == '#']
                            user.update(channels=channels, message=formatted,
                                        now=now)

    def shutdown(self):
        now = Datetime.utcnow()
        timestamp = now.strftime(self.app_data['timeformat'])
        end_message = 'shutdown at {0}'.format(timestamp)
        self.file_send(end_message)
        self.logger.info(end_message)
        self.app_args.output.close()
