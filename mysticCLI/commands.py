from __future__ import annotations

from typing import Dict, Type

from getpass import getpass
import re
import textwrap

from mysticlib import Mystic
from mysticCLI.resettable_timer import ResettableTimer
from mysticCLI.__util import *


class Command:
    all: Dict[str, Command] = {}

    def __init__(self, func):
        assert func.__name__ not in self.all
        self.all[func.__name__] = self
        self.sign = get_command_sign(func)
        self.help = textwrap.dedent(func.__doc__)
        self.func = func

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)


@Command
def add_password(*, myst: Mystic, **kwargs):
    """
    Add a password to the mystic. Takes no arguments. You will be prompted to enter the new password. If a password already exists, you will be prompted to enter it too.
    """
    if not myst.mutable:
        return 'the myst is in read-only mode, use the enable_write command to enable editing'
    myst.add_password()
    return 'new password added'


@Command
def del_password(*, myst: Mystic, **kwargs):
    """
    Delete a password from the mystic. Takes no arguments. Yuo will be prompted to enter the password to delete. You cannot delete the only password, add a password beforehand.
    """
    if not myst.mutable:
        return 'the myst is in read-only mode, use the enable_write command to enable editing'
    myst.del_password()
    return 'password deleted'


@Command
def get(key, *, myst: Mystic, **kwargs):
    """
    Retrieve the value of a specific key. Note that the key must match exactly, use either search or lookup for a fuzzy search. Takes the key as a single argument.
    """
    return myst[key]


def _search(myst, pattern):
    p = re.compile(pattern)
    results = []
    for k, v in myst.items():
        if p.search(k):
            results.append((k, v))
    if len(results) == 0:
        return 'no results found matching pattern'
    if len(results) == 1:
        return results[0]

    for i, (k, _) in enumerate(results):
        print(f'{i}\t{k}')
    while True:
        i = input('enter the number of the key, or "x" to cancel search\n')
        if i == 'x':
            return 'search cancelled'
        try:
            i = int(i)
            ret = results[i]
        except ValueError:
            print('invalid number')
        except IndexError:
            print('index out of bounds')
        else:
            break

    return ret


@Command
def search(pattern, *, myst: Mystic, **kwargs):
    """
    Search for a key in the mystic. Prompting you for all the possible keys matching a regular expression pattern. Accepts a regex pattern.
    """
    r = _search(myst, pattern)
    if isinstance(r, str):
        return r
    k, v = r
    return f'{k}: {v}'


def _lookup(myst, auto_display_thresh=10, start=''):
    orig_cands = set(myst.items())
    candidates = set(orig_cands)
    pattern = start
    while True:
        if len(candidates) == 0:
            if pattern == '':
                return 'no candidates'
            response = input(f'no valid candidates for pattern {pattern}, go back one? [y/n]\n').lower()
            if response == 'y':
                pattern = pattern[:-1]
                candidates = {(k, v) for (k, v) in orig_cands if (pattern in k)}  # todo fuzzy search
                continue
            return 'lookup cancelled'
        if len(candidates) == 1:
            return next(iter(candidates))

        next_letters = None
        if len(candidates) < auto_display_thresh:
            disp = True
        else:
            response = input(
                f'there are {len(candidates)} candidates, enter #d to display, letters to continue searching, or #x to cancel\n')
            if response == '#d':
                disp = True
            elif response == '#x':
                return 'lookup cancelled'
            else:
                disp = False
                next_letters = response

        if disp:
            assert next_letters is None
            print('query: '+pattern)
            c = sorted(candidates, key=lambda x: x[0])
            for i, (k, _) in enumerate(c):
                print(f'#{i}\t{k}')
            while next_letters is None:
                response = input(
                    'enter the number (starting with #) to access that key, #x to cancel, or letters to continue searching\n')
                if response == '#x':
                    return 'lookup cancelled'
                if response.startswith('#'):
                    response = response[1:]
                    try:
                        ret = int(response)
                        return c[ret]
                    except ValueError:
                        print('could not parse number ' + response)
                    except IndexError:
                        print('out of bounds')
                next_letters = response

        assert next_letters is not None
        pattern += next_letters
        for k, _ in list(candidates):
            if pattern not in k:  # todo fuzzy search
                candidates.remove((k, _))


@Command
def lookup(start='', *, myst, **kwargs):
    """
    Search for a key in the mystic. Prompting you for additional letters to search for until only a few remain. Accepts an optional first characters to begin the search with.
    """
    r = _lookup(myst, start=start)
    if isinstance(r, str):
        return r
    k, v = r
    return f'{k}: {v}'


@Command
def add(key=None, value=None, *, myst, **kwargs):
    """
    Add a new key-value pair. Accepts a optional key and an optional value for the key. If the key or value is not entered, a secure input will be prompted to enter them.
    """
    if not myst.mutable:
        return 'the myst is in read-only mode, use the enable_write command to enable editing'
    if key is None:
        key = getpass('enter the key')
    if key in myst:
        return 'key already exists, use update or set_pair to change existing pairs'
    if value is None:
        value = getpass(f'enter the value')

    myst[key] = value
    return 'pair added'


@Command
def update(key=None, value=None, *, myst, **kwargs):
    """
    Update a key-value pair to a new value. Accepts a optional key and an optional value for the key. If the key or value is not entered, a secure input will be prompted to enter them. If the value ends with a '[', the previous value will be appended to its new value in square brackets.
    """
    if not myst.mutable:
        return 'the myst is in read-only mode, use the enable_write command to enable editing'
    if key is None:
        key = getpass('enter the key')
    if key not in myst:
        return 'key does not exists, use add or set_pair to add new pairs'
    if value is None:
        value = getpass(f'enter the value')
    if value.endswith('['):
        value = value + myst[key] + ']'
    myst[key] = value
    return 'pair updated'


@Command
def update_search(pattern, value=None, *, myst, **kwargs):
    """
    Update a key-value pair to a new value, searching for the key with a regex pattern. Accepts a regular expression pattern and an optional value. If the value is not provided, a secure input will be prompted to enter it. If the value ends with a '[', the previous value will be appended to its new value in square brackets.
    """
    if not myst.mutable:
        return 'the myst is in read-only mode, use the enable_write command to enable editing'

    r = _search(myst, pattern)
    if isinstance(r, str):
        return r
    key, prev = r

    if value is None:
        value = getpass(f'enter the value')
    if value.endswith('['):
        value = value + prev + ']'
    myst[key] = value

    return 'pair updated'


@Command
def update_lookup(value=None, *, myst, **kwargs):
    """
    Update a key-value pair to a new value, looking for the key via simple search. Accepts an optional value. If the value is not provided, a secure input will be prompted to enter it. If the value ends with a '[', the previous value will be appended to its new value in square brackets.
    """
    if not myst.mutable:
        return 'the myst is in read-only mode, use the enable_write command to enable editing'

    r = _lookup(myst)
    if isinstance(r, str):
        return r
    key, prev = r

    if value is None:
        value = getpass(f'enter the value')
    if value.endswith('['):
        value = value + prev + ']'
    myst[key] = value

    return 'pair updated'


@Command
def set_pair(key=None, value=None, *, myst, **kwargs):
    """
    Set a key-value pair to a new value, regardless of whether the key already exists. Accepts an optional key and an optional value for the key. If the key or value is not entered, a secure input will be prompted to enter them.
    """
    if not myst.mutable:
        return 'the myst is in read-only mode, use the enable_write command to enable editing'
    if key is None:
        key = getpass('enter the key')
    if value is None:
        value = getpass(f'enter the value')
    myst[key] = value
    return 'pair set'


@Command
def quit(*, myst: Mystic, **kwargs):
    """
    Exit the mysticCLI. Will prompt if any unsaved changes are recorded.
    """
    if myst.changed():
        response = input('unsaved changes are recorded, press enter to continue, enter anything to cancel\n').lower()
        if response:
            return ''
    return False


@Command
def save(path=None, *, myst: Mystic, timer: ResettableTimer, **kwargs):
    """
    Will save the mystic to a file. Accepts a path for the file. If the path is not provided, the mystic's source path will be used, if available. Will also reset the auto-close timer.
    """
    if path is None:
        path = kwargs.get('source_path', None)
        if path is None:
            return 'A path must be entered for newly created files'
    with open(path, 'wb') as dst:
        myst.to_stream(dst)
    timer.reset()
    return f'saved to {path}, timer reset.'


@Command
def enable_write(*, myst: Mystic, **kwargs):
    """
    Set the mystic to write mode.
    """
    if myst.mutable:
        return 'already in write mode'
    myst.mutable = True
    return 'myst in write mode'


@Command
def help(command=None, *, commands: Type[Command], **kwargs):
    """
    Display help for all commands. Accepts an optional command name argument, if entered, only help for that command is displayed.
    """
    if command is None:
        coms = sorted(commands.all.items(), key=lambda x: x[0])
    else:
        v = commands.all.get(command, None)
        if not v:
            return f'command {command} not found'
        coms = [(command, v)]

    ret = []
    for n, v in coms:
        ret.append(v.sign)
        ret.extend(textwrap.wrap(v.help, 100, initial_indent = '\t', subsequent_indent='\t'))
        ret.append('')

    return '\n'.join(ret)


@Command
def dump(pattern='', separator=': ', *, myst: Mystic, **kwargs):
    """
    Display all the entries in the myst. Accepts an optional pattern and an optional separator. Only keys matching the pattern will be returned, and the separator will be between every key and value.
    """
    p = re.compile(pattern)
    ret = []
    for k, v in myst.items():
        if p.search(k):
            ret.append(f'{k}{separator}{v}')
    return '\n'.join(ret)


_load_pattern = re.compile('(?P<key>.+?)\s*[:\-=\t]+\s*(?P<val>.+)')


@Command
def load(file=None, *, myst: Mystic, **kwargs):
    """
    Load pairs from a file. Accepts an optional file path. If the path is not supplied, input will be taken through the console, until a line that is just #end. Each line from the input is scanned for the first separator (any of :-=).
    """
    if not myst.mutable:
        return 'the myst is in read-only mode, use the enable_write command to enable editing'
    if file is not None:
        with open(file) as r:
            lines = (l.rstrip() for l in r.readlines())
    else:
        lines = []
        print('enter lines to load')
        while True:
            l = input()
            if l == '#end':
                break
            lines.append(l)
    bad_lines = []
    successful = 0
    for line in lines:
        if line.isspace() or not line:
            continue
        m = _load_pattern.fullmatch(line)
        if not m:
            bad_lines.append(line)
        else:
            key, val = m['key'], m['val']
            myst[key] = val
            successful += 1
    if bad_lines:
        return f'{successful} lines successfully parsed, {len(bad_lines)} could not be parsed:\n' + '\n'.join(bad_lines)
    else:
        return f'{successful} lines successfully parsed'


@Command
def delete(key=None, *, myst, **kwargs):
    """
    Deelte a key-value pair. Accepts a optional key. If the key is not entered, a secure input will be prompted to enter it.
    """
    if not myst.mutable:
        return 'the myst is in read-only mode, use the enable_write command to enable editing'
    if key is None:
        key = getpass('enter the key')
    if key not in myst:
        return 'key not found'
    del myst[key]
    return 'pair deleted'


@Command
def delete_search(pattern, *, myst, **kwargs):
    """
    Delete a key-value pair, searching for the key with a regex pattern. Accepts a regular expression pattern.
    """
    if not myst.mutable:
        return 'the myst is in read-only mode, use the enable_write command to enable editing'

    r = _search(myst, pattern)
    if isinstance(r, str):
        return r
    key, prev = r
    del myst[key]

    return 'pair deleted'


@Command
def delete_lookup(*, myst, **kwargs):
    """
    Delete a key-value pair, looking for the key via simple search.
    """
    if not myst.mutable:
        return 'the myst is in read-only mode, use the enable_write command to enable editing'

    r = _lookup(myst)
    if isinstance(r, str):
        return r
    key, prev = r
    del myst[key]

    return 'pair deleted'

#todo version