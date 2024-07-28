"""Unit testing.
"""
import unittest

from stanford.green import random_uid

from stanford.green.zulutime import is_zulu_string
from stanford.green.zulutime import zulu_string_to_utc

class TestGreen(unittest.TestCase):

    def test_random_uid(self) -> None:
        for _ in list(range(1,20)):
            uid = random_uid()
            self.assertTrue(len(uid) >= 3, msg=f"'{uid}' is too short (no prefix)")
            self.assertTrue(len(uid) <= 8, msg=f"'{uid}' is too long (no prefix)")

        # Run this next one several times as the length
        # is randomly chosen so we want to give a good chance
        # to hit all the possible lengths.
        for _ in list(range(1,20)):
            uid = random_uid(prefix='abc')
            self.assertRegex(uid, r'^abc')
            self.assertTrue(len(uid) == 8, msg=f"'{uid}' is not eight characters (prefix)")

        for i in list(range(3,8)):
            self.assertTrue(len(random_uid(length=i)) == i)

        with self.assertRaises(Exception) as _:
            # Put in a prefix that is too long (remember that sunetid's
            # cannot be longer than 8 characters).
            random_uid(prefix='abcdefghijk')

        with self.assertRaises(Exception) as _:
            # Put in a length that is too long.
            random_uid(length=9)

        with self.assertRaises(Exception) as _:
            # Put in a length that is too short.
            random_uid(length=2)


    def test_is_zulu_string(self) -> None:

        # VALID
        # Test strings both with decimal seconds and without decimal seconds.
        valid_zulu_strings = [
            '2024-07-28T21:42:34Z',
            '2024-07-28T21:42:34.1Z',
            '2024-07-28T21:42:34.12Z',
            '2024-07-28T21:42:34.123Z',
            '2024-07-28T21:42:34.1234Z',
            '2024-07-28T21:42:34.12345Z',
            '2024-07-28T21:42:34.123456Z',
            ]
        for zulu_string in valid_zulu_strings:
            self.assertTrue(is_zulu_string(zulu_string), f"string is {zulu_string}")

        # INVALID
        invalid_zulu_strings = [
            None,
            '2024-07-28T21:42:34',
            '2024-07-28T21:42:34.Z',
            '2024-07-28T21:42:34Z.123',
            '2024 07 28T21:42:34Z.123',
        ]
        for zulu_string in invalid_zulu_strings:
            self.assertFalse(is_zulu_string(zulu_string), f"string is {zulu_string}")

    def test_zulu_string_to_utc(self):
        pass

        valid_zulu_strings = [
            '2024-07-28T21:42:34Z',
            '2024-07-28T21:42:34.1Z',
            '2024-07-28T21:42:34.12Z',
            '2024-07-28T21:42:34.123Z',
            '2024-07-28T21:42:34.1234Z',
            '2024-07-28T21:42:34.12345Z',
            '2024-07-28T21:42:34.123456Z',
            ]

        # Get the "base" time, that is, the one without decimal time.
        # We convert all of these and ensure the date difference is less than
        # two seconds.
        base_datetime = zulu_string_to_utc(valid_zulu_strings[0])

        for zulu_string in valid_zulu_strings:
            current_datetime = zulu_string_to_utc(zulu_string)
            diff_seconds = abs((base_datetime - current_datetime ).total_seconds())
            self.assertTrue(diff_seconds < 2.0)

if __name__ == '__main__':
    unittest.main()
