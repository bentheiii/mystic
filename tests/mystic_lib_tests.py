from io import BytesIO
import unittest
import random
import itertools as it

from mysticlib.__util import enc, dec, DEFAULT_ITER
from mysticlib import SingleCodedMystic, Mystic

SKIP_SLOW_TESTS = True

class EncTests(unittest.TestCase):
    handles = [
        'a', 'ab'
             '', 'ab' * 2000, 'hello world',
        'שלום',
                 '\0\t\f' * 1_000
    ]

    @unittest.skipIf(SKIP_SLOW_TESTS,'skipping slow tests')
    def test_enc(self):
        for pw, pt in it.product(self.handles, repeat=2):
            for ah, ai in it.product([True, False], repeat=2):
                cypher = enc(pt, pw, add_salt=ah, add_iter=ai)
                salt = None
                if not ah:
                    salt = b'\0' * 16
                iters = None
                if not ai:
                    iters = DEFAULT_ITER
                de = dec(cypher, pw, salt=salt, hash_iterations=iters)
                dec_str = str(de, 'utf-8')
                self.assertEqual(pt, dec_str)


class SCMTests(unittest.TestCase):
    @staticmethod
    def pass_callback(*args):
        if random.uniform(0, 1) < 0.5:
            return 'abcd'
        return 'efgh'

    def make_from_scratch(self):
        scm = SingleCodedMystic()
        scm.password_callback = self.pass_callback
        scm.mutable = True
        scm.add_password(new_password='abcd')
        scm.add_password('abcd', 'efgh')
        scm['one'] = '1'
        scm['two'] = '2'
        scm['three'] = 'שלוש'
        self.assertEqual(scm['one'], '1')
        buffer = BytesIO()
        scm.to_stream(buffer)
        return buffer

    def load_no_mutable(self, buffer):
        buffer.seek(0)
        loaded = SingleCodedMystic.from_stream(buffer)
        loaded.password_callback = self.pass_callback
        self.assertEqual(loaded['one'], '1')
        self.assertEqual(loaded['two'], '2')
        self.assertEqual(loaded['three'], 'שלוש')
        self.assertIsNone(loaded.cached_dict)
        self.assertFalse(loaded._changed)
        return buffer

    def load_gen_no_mutable(self, buffer):
        buffer.seek(0)
        loaded = Mystic.from_stream(buffer)
        loaded.password_callback = self.pass_callback
        self.assertEqual(loaded['one'], '1')
        self.assertEqual(loaded['two'], '2')
        self.assertEqual(loaded['three'], 'שלוש')
        self.assertIsNone(loaded.cached_dict)
        self.assertFalse(loaded.changed())
        return buffer

    def load_mutable(self, buffer):
        buffer.seek(0)
        loaded = SingleCodedMystic.from_stream(buffer)
        loaded.mutable = True
        loaded.password_callback = self.pass_callback
        self.assertEqual(loaded['one'], '1')
        self.assertEqual(loaded['two'], '2')
        self.assertEqual(loaded['three'], 'שלוש')
        loaded['hi'] = 'shalom'
        del loaded['one']
        loaded['three'] = '3'
        buffer = BytesIO()
        loaded.to_stream(buffer)
        return buffer

    def test_make_and_load(self):
        new = self.make_from_scratch()
        self.load_no_mutable(new)
        self.load_gen_no_mutable(new)
        rewritten = self.load_mutable(new)
        rewritten.seek(0)
        last = SingleCodedMystic.from_stream(rewritten)
        last.password_callback = self.pass_callback
        d = last.load()
        self.assertEqual(d, {'two':'2','three':'3','hi':'shalom'})
