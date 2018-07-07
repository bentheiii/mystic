import os
import base64

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

ITER_LEN = 8  # maximum iterations 256^8
DEFAULT_ITER = 100_000


def _num_code(n: int):
    return n.to_bytes(ITER_LEN, 'big', signed=False)


def _num_decode(s: bytes):
    return int.from_bytes(s[:ITER_LEN], 'big', signed=False), s[ITER_LEN:]


def enc(src: str, pw: str, hash_iterations=DEFAULT_ITER, salt: bytes = None,
        add_salt=True, add_iter=True) -> bytes:
    if not isinstance(src, bytes):
        src = bytes(src, 'utf-8')
    if not isinstance(pw, bytes):
        pw = bytes(pw, 'utf-8')
    if salt is None:
        if not add_salt:
            salt = b'\0' * 16
        else:
            salt = os.urandom(16)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        salt=salt,
        length=32,
        iterations=hash_iterations,
        backend=default_backend())
    key = base64.urlsafe_b64encode(kdf.derive(pw))
    fern = Fernet(key)
    ret = fern.encrypt(src)
    # encode doesn't like it if the byte length isn't divisible by 4, so we add a padding zero to both yes and no flags,
    # if we add more flags we might change this
    if add_iter:
        ret = b'\0\1' + _num_code(hash_iterations) + ret
    else:
        ret = b'\0\0' + ret
    if add_salt:
        ret = b'\0\1' + salt + ret
    else:
        ret = b'\0\0' + ret
    # ret = base64.urlsafe_b64encode(ret)
    return ret


def dec(src: bytes, pw: str, salt: bytes = None, hash_iterations: int = None):
    if not isinstance(pw, bytes):
        pw = bytes(pw, 'utf-8')
    # src = bytes(src, 'base64')
    # src = base64.urlsafe_b64decode(src)
    saltbit = bool(src[1])
    src = src[2:]
    if saltbit:
        salt = src[:16]
        src = src[16:]
    iter_bit = bool(src[1])
    src = src[2:]
    if iter_bit:
        hash_iterations, src = _num_decode(src)

    if None in (hash_iterations, salt):
        raise Exception(
            f'a value is not supplied by the caller or the cyphertext {[a is None for a in (hash_iterations, salt)]}')

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        salt=salt,
        length=32,
        iterations=hash_iterations,
        backend=default_backend())
    key = base64.urlsafe_b64encode(kdf.derive(pw))
    fern = Fernet(key)
    return fern.decrypt(src)


__all__ = ['enc', 'dec', 'DEFAULT_ITER']
