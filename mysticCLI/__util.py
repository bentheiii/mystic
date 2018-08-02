from collections import namedtuple
import re
import inspect

try:
    import tkinter as tk
    from tkinter import simpledialog as tk_simpledialog
except ImportError:
    tk = None


def bool_or_ellipsis(s: str):
    s = s.lower()
    if s == 'true' or s == 't':
        return True
    if s == 'false' or s == 'f':
        return False
    if s == '...':
        return ...
    raise TypeError(f'could not parse bool {s}')


class GreyHole:
    def __getattribute__(self, item):
        return self


func_call = namedtuple('func_call', 'func_name args')
_func_call_master_pattern = re.compile('(?P<name>[a-z0-9_]+)(\s*\((?P<args>.*)\))?;?')
_func_call_short_pattern = re.compile('(?P<name>[a-z0-9_]+)\s+(?P<args>.+)')


def parse_func_call(line):
    """
    >>> assert parse_func_call("hello('world')") == ('hello',('world',))
    >>> assert parse_func_call("hi('there',str(1+2))") == ('hi',('there','3'))
    >>> assert parse_func_call('hi') == parse_func_call('hi()') == ('hi',())
    >>> assert parse_func_call('hi there') == parse_func_call('hi("there")')
    """
    short = False
    m = _func_call_master_pattern.fullmatch(line)
    if not m:
        short = True
        m = _func_call_short_pattern.fullmatch(line)
        if not m:
            raise ValueError('could not parse line')
    name = m['name']
    joined_args = m['args']
    if joined_args:
        if short:
            joined_args = f'"""{joined_args}"""'
        joined_args += ','  # force output to be a tuple
        args = eval(joined_args, None, None)
    else:
        args = ()
    return func_call(name, args)


def get_command_sign(func):
    """
    >>> def foo(a,b=None,  *, p, q, **kwargs): pass
    >>> get_command_sign(foo)
    'foo(a, b=None)'
    >>> def foo(**kwargs): pass
    >>> get_command_sign(foo)
    'foo()'
    """
    sign = str(inspect.signature(func))
    sign = re.sub(',?(\s*\*.*, )?\*\*kwargs\)', ')', sign)
    return func.__name__ + sign


__all__ = ['bool_or_ellipsis', 'GreyHole', 'parse_func_call', 'get_command_sign']

if tk:
    class ResizableQueryString(tk_simpledialog._QueryString):
        def __init__(self, *args, width=100, **kwargs):
            self.__width = width
            super().__init__(*args, **kwargs)

        def body(self, master):
            entry = super().body(master)
            entry.config(width=self.__width)
            return entry


    def askstring(title, prompt, **kw):
        d = ResizableQueryString(title, prompt, **kw)
        return d.result


    __all__.append('askstring')

if __name__ == '__main__':
    import doctest

    doctest.testmod()
