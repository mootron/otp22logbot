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
import sys
import logging
import argparse
from otp22logbot.bot import Bot


def make_parser():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        '-c', '--channel',
        help='IRC channel to join.',
        default='ircugm',
        type=str
    )
    parser.add_argument(
        '-i', '--init',
        help='Specify initialization/configuration file for logbot',
        default=False,
        type=argparse.FileType('r')
    )
    parser.add_argument(
        '-k', '--kill',
        help='Kill password to stop bot from IRC.',
        default=None,
        type=str
    )
    parser.add_argument(
        '-n', '--nick',
        help='IRC nick name.',
        default='otp22logbot',
        type=str
    )
    parser.add_argument(
        '-o', '--output',
        help='Output log filename.',
        default='otp22logbot.log',
        type=argparse.FileType('w')
    )
    parser.add_argument(
        '-p', '--port',
        help='IRC port to use.',
        default=6667,
        type=int
    )
    parser.add_argument(
        '-r', '--real',
        help='IRC real name.',
        default='otp22logbot',
        type=str
    )
    parser.add_argument(
        '-s', '--server',
        help='IRC server to connect to.',
        default='localhost',
        type=str
    )
    parser.add_argument(
        '-u', '--user',
        help='IRC user name.',
        default='otp22logbot',
        type=str
    )
    parser.add_argument(
        '--password',
        action="store",
        help="password to give to server in PASS command"
    )
    parser.add_argument(
        '--debug',
        action="store_true",
        help="print debug information"
    )
    return parser


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
