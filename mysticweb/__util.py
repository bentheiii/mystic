from typing import Tuple, Union

from socket import timeout
from urllib.request import urlopen
from urllib.parse import urlparse
import re
import itertools as it

URL_LOAD_TIMEOUT = 10


def download_page(url) -> Tuple[bool, Union[bytes, Exception]]:
    try:
        return True, urlopen(url, timeout=URL_LOAD_TIMEOUT).read()
    except (timeout, ValueError) as e:
        return False, e


def fuzzy_in(needle: str, haystack: str) -> bool:
    """
    >>> assert fuzzy_in('a b c','kabracda')
    >>> assert not fuzzy_in('ab ce','abec bac')
    >>> assert fuzzy_in('aB ce','abcE')
    """
    haystack = haystack.lower()
    return all(n.lower() in haystack for n in needle.split())


def parts(max_, repeat):
    re_parts = [f'[{a}]{{,{max_}}}' for a in ('a-z', 'A-Z', '0-9', '\u05D0-\u05EA')]
    return tuple(re.compile(r'[-\s_]?'.join(p)) for p in it.product(re_parts, repeat=repeat))


_weak_patterns = (
    (re.compile(''),),
    parts(4, 1),
    parts(3, 2),
    parts(2, 3),
    parts(1, 4),
)
_weak_levels = (
    'trivial',
    'miserably weak',
    'extremely weak',
    'very weak',
    'weak'
)


def pass_strength(password):
    """
    >>> _ = lambda x: _weak_levels.index(pass_strength(x))
    >>> _("")
    0
    >>> _("abcd")
    1
    >>> _("1234")
    1
    >>> _("glu 12")
    2
    >>> _("gluer")
    2
    """
    for level, patterns in zip(_weak_levels, _weak_patterns):
        if any(p.fullmatch(password) for p in patterns):
            return level
    return None


def is_local(url):
    parsed = urlparse(url)
    if parsed.hostname in ('127.0.0.1', 'localhost'):
        return True
    return False


__all__ = ['download_page', 'fuzzy_in', 'pass_strength', 'is_local']

if __name__ == '__main__':
    import doctest

    doctest.testmod()
