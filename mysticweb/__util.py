from typing import Tuple, Union

from socket import timeout
from urllib.request import urlopen

URL_LOAD_TIMEOUT = 10


def download_page(url) -> Tuple[bool, Union[bytes, Exception]]:
    try:
        return True, urlopen(url, timeout=URL_LOAD_TIMEOUT).read()
    except (timeout, ValueError) as e:
        return False, e


def fuzzy_in(needle: str, haystack: str)->bool:
    """
    >>> assert fuzzy_in('a b c','kabracda')
    >>> assert not fuzzy_in('ab ce','abec bac')
    """
    return all(n in haystack for n in needle.split())


__all__ = ['download_page', 'fuzzy_in']

if __name__ == '__main__':
    import doctest
    doctest.testmod()