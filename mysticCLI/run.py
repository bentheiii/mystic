from getpass import getpass
from functools import partial
import argparse
import sys
import warnings

from mysticlib import Mystic

from mysticCLI.resettable_timer import ResettableTimer
from mysticCLI.commands import Command
from mysticCLI.__data import __version__, __author__
from mysticCLI.__util import *

parser = argparse.ArgumentParser(description='A CLI tool for mystic files')
parser.add_argument('source', action='store', type=str, default='!', nargs='?',
                    help='the source mystic to load. * denotes a new file, a format can be specified after the *. Default is to ask for prompt. ! to ask for prompt.')
parser.add_argument('-t', action='store', type=int, default=30, required=False, dest='timeout',
                    help='time, in minutes, before the program automatically shuts down, -1 to disable this feature.')
parser.add_argument('-w', action='store', type=bool_or_ellipsis, default=..., required=False, dest='write',
                    help='whether to set the file to be writeable or not, default is to try, but not exit when failing')
parser.add_argument('--nsecure', action='store_true', default=False, required=False, dest='nsecure',
                    help='set the application to use a non-secure input method, in case the secure one is not supported')
parser.add_argument('--throw', action='store_true', default=False, required=False, dest='throw',
                    help='throw all internal exceptions, used for debugging')
parser.add_argument('--version', action='version', version=__version__)


def handle_line(line: str, *, throw, **kwargs) -> bool:
    if not line or line.isspace():
        return True
    try:
        call = parse_func_call(line)
    except ValueError:
        print('could not parse line, commands should be called in python syntax or no call syntax')
        return True
    except Exception as e:
        print(f'Error: {e}')
        return True

    func_name = call.func_name
    args = call.args

    comm = Command.all.get(func_name, None)
    if not comm:
        print(f'command {func_name} not recognised')
        return True

    try:
        ret = comm(*args, **kwargs)
    except Exception as e:
        if throw:
            raise
        print(f'Error: {e}')
        return True

    if isinstance(ret, str):
        print(ret)
        return True
    if isinstance(ret, bool):
        return ret
    raise TypeError(f'unhandled command return value {type(ret)}')


def main(args=None):
    args = parser.parse_args(args)

    if args.timeout < 0:
        timer = GreyHole()
    else:
        timer = ResettableTimer(args.timeout * 60, sys.exit)
    kwargs = {}

    while args.source == '!':
        args.source = input('input file or method. * is for new file.\n')

    if args.source.startswith('*'):
        form = args.source[1:]
        if form == '':
            form = 'scm'
        myst = Mystic.new_from_format(form)
    else:
        kwargs['source_path'] = args.source
        with open(args.source, mode='br') as source:
            myst = Mystic.from_stream(source)

    kwargs['commands'] = Command

    if args.nsecure:
        myst.password_callback = input
    else:
        myst.password_callback = partial(getpass, stream=sys.stdout)

    if (not myst.mutable) and args.write:
        try:
            myst.mutable = True
        except Exception as e:
            if args.write is ...:
                warnings.warn('opening in read-only mode, reason: ' + str(e))
            else:
                raise

    timer.start()

    print(
        f'Welcome to the mystic CLI console version {__version__}'
        '\nNEVER enter your master password as a function argument!'
        '\nTo see all the available functions, enter help')
    try:
        while True:
            line = input()
            if not handle_line(line, throw=args.throw, myst=myst, timer=timer, **kwargs):
                break
    finally:
        timer.cancel()


if __name__ == '__main__':
    main()
