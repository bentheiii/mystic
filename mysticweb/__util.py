from typing import Tuple, Union

from socket import timeout
from urllib.request import urlopen

URL_LOAD_TIMEOUT = 10

def download_page(url)->Tuple[bool,Union[bytes, Exception]]:
    try:
        return True, urlopen(url, timeout=URL_LOAD_TIMEOUT).read()
    except (timeout, ValueError) as e:
        return False, e

__all__ = ['download_page']