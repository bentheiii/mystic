from typing import MutableSequence
from io import BytesIO

from json import dumps, loads

from cryptography.fernet import InvalidToken, Fernet

from mysticlib.mystic import Mystic
from mysticlib.exceptions import BadKey
from mysticlib.__util import *


class SingleCodedMystic(Mystic):
    """
    format:
    <header><newline>
    <number_of_passwords (1 byte)><len of pass1(1 byte)><pass1><len of pass2(1 byte)>...<enc_json_dict>
    # note, last line does NOT have newline terminator
    """
    header = b'!myst_single_coded'
    format = 'scm'

    def __init__(self):
        super().__init__()
        self.encrypted_passwords: MutableSequence[bytes] = []
        self.cache = False
        self.coded_dict = None
        self.cached_dict = None
        self._changed = False

    def _get_master(self, minor=None, prompt='enter password\n'):
        # todo cache the produced derived key
        if not self.encrypted_passwords:
            return Fernet.generate_key()
        if minor is None:
            minor = self.password_callback(prompt)
        for ep in self.encrypted_passwords:
            try:
                return dec(ep, minor)
            except InvalidToken:
                pass
        raise BadKey('bad key')

    def _commit(self, minor=None):
        assert self.cached_dict is not None
        plaintext = dumps(self.cached_dict)
        self.coded_dict = enc(plaintext, self._get_master(minor))
        self._changed = False

    def _get_dict(self, minor=None):
        if self.cached_dict is not None:
            return self.cached_dict
        master = self._get_master(minor)
        if self.coded_dict is None:
            plain = '{}'
        else:
            plain = dec(self.coded_dict, master)
        ret = loads(plain)
        if self.cache:
            self.cached_dict = ret
        return ret

    def load(self, minor=None):
        return self._get_dict(minor)

    @classmethod
    def from_stream(cls, src: BytesIO, check_header=True) -> 'SingleCodedMystic':
        if check_header:
            header = src.readline().rstrip()  # next(src).rstrip()
            if header != cls.header:
                raise ValueError(f'header mismatch, expected {cls.header}, got {header}')
        num_of_passwords = int(src.read(1)[0])
        self = SingleCodedMystic()
        self.encrypted_passwords = []
        for _ in range(num_of_passwords):
            l = int(src.read(1)[0])
            ep = src.read(l)
            self.encrypted_passwords.append(ep)
        self.coded_dict = src.read()
        assert self.coded_dict[-1]!=b'\n'
        return self

    def to_stream(self, dst: BytesIO, minor=None):
        if not self.encrypted_passwords:
            raise Exception('this mystic has no passwords set, it will be inaccessible unless at least one passwords is added')
        dst.write(self.header+b'\n')
        if len(self.encrypted_passwords) >= 256:
            raise Exception('too many passwords in singe coded mystic')
        dst.write(bytes([len(self.encrypted_passwords)]))
        for ep in self.encrypted_passwords:
            if len(ep)>256:
                raise Exception(f'password too long: {ep}')
            dst.write(bytes([len(ep)]))
            dst.write(ep)
        if self._changed:
            self._commit(minor)
        dst.write(self.coded_dict)

    def add_password(self, old_password=None, new_password=None):
        master = self._get_master(old_password, prompt='enter old password\n')
        if new_password is None:
            new_password = self.password_callback('enter new password\n')
        new_minor = enc(master, new_password)
        self.encrypted_passwords.append(new_minor)
        self._changed = True

    def __getitem__(self, item, minor=None):
        return self._get_dict(minor)[item]

    def __contains__(self, key):
        return key in self._get_dict()

    @property
    def mutable(self):
        return self.cache

    @mutable.setter
    def mutable(self, v: bool):
        self.cache = v

    def __setitem__(self, key, value, minor=None):
        self._get_dict(minor)[key] = value
        self._changed = True


    def __delitem__(self, key, minor=None):
        del self._get_dict(minor)[key]
        self._changed = True

    def del_password(self, minor=None):
        if len(self.encrypted_passwords) == 1:
            raise Exception('cannot delete the last password of a mystic')
        if minor is None:
            minor = self.password_callback()
        for ep in self.encrypted_passwords:
            try:
                dec(ep, minor)
            except InvalidToken:
                pass
            else:
                self.encrypted_passwords.remove(ep)
                self._changed = True
                return
        raise BadKey

    def __len__(self):
        return len(self._get_dict())

    def __iter__(self):
        return iter(self._get_dict())

    def get(self,*args,minor=None,**kwargs):
        if minor is None:
            return super().get(*args,**kwargs)
        return self.load(minor=minor).get(*args,**kwargs)

    def changed(self):
        return self._changed
