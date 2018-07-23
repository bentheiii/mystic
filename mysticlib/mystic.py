#from __future__ import annotations

from typing import Callable, Optional, Type, Dict
from abc import ABC, abstractmethod
from io import IOBase

from typing import MutableMapping

PASS_CB = Callable[[Optional[str]], str]


class Mystic(ABC, MutableMapping[str, str]):
    __slots__ = 'password_callback'

    def __init__(self):
        self.password_callback = None

    headers: Dict[bytes, Type['Mystic']] = {}
    formats: Dict[str, Type['Mystic']] = {}

    def __init_subclass__(cls):
        cls.headers[cls.header] = cls
        cls.formats[cls.format] = cls

    @classmethod
    def new_from_format(cls, format_: str)->'Mystic':
        subclass = cls.formats.get(format_, None)
        if subclass is None:
            raise ValueError(f'unrecognized format {format_}')
        return subclass()

    @abstractmethod
    def __getitem__(self, item: str) -> str:
        pass

    @classmethod
    @abstractmethod
    def from_stream(cls, src: IOBase, check_header=True) -> 'Mystic':
        assert check_header
        header = src.readline().rstrip()
        subclass = cls.headers.get(header,None)
        if subclass is None:
            raise ValueError(f'unrecognised file header {header}')
        return subclass.from_stream(src,check_header=False)

    @abstractmethod
    def __delitem__(self, item: str) -> str:
        pass

    @abstractmethod
    def __setitem__(self, item: str, val: str) -> str:
        pass

    @abstractmethod
    def to_stream(self, dst: IOBase, minor=None):
        pass

    @property
    @abstractmethod
    def mutable(self) -> bool:
        pass

    @mutable.setter
    @abstractmethod
    def mutable(self, v: bool):
        pass

    @abstractmethod
    def add_password(self, old_password=None, new_password=None):
        pass

    @abstractmethod
    def del_password(self, minor=None):
        pass

    @abstractmethod
    def changed(self)->bool:
        pass
