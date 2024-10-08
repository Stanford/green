"""Functions of general use to the Stanford community.
"""

# pylint: disable=superfluous-parens,invalid-name

import datetime
import pytz
import random

## TYPING
from typing import Dict, Any, Optional  # pylint: disable=wrong-import-order
AttributeDict = Dict[str, Any]
## END OF TYPING

LETTER_STRING = 'abcdefghijklmnopqrstuvwxyz'
LETTERS       = [*LETTER_STRING]

def random_uid(prefix: str = "", length: Optional[int] = None) -> str:
    """Create a random Stanford-compliant uid.

    :param prefix: a string prefix (defaults to the empty string)
    :type prefix: str
    :param length: desired length of the resulting uid (optional)
    :type length: int or None
    :return: a random string between three and eight characters long that
      is a valid Stanford uid unless ``length`` is provided in which case
      the returned string will have length ``length``.
      If ``prefix`` is supplied then the returned
      string will start with ``prefix`` AND the length of returned string
      will be eight.
    :raises Exception: if ``prefix`` is eight or more characters there
      is not enough space to put the rest of the randomly generated
      characters and in this case an Exception will be raised.

    **Algorithm**

    1. If neither ``prefix`` nor ``length`` are given then a string of
    length between 3 and 8 is returned.

    2. If ``length`` is given and is smaller then 3 or larger than 8, an exception
    is raised.

    3. If ``length`` is given and is between 3 and 8 (inclusive), then
    a string of length of ``length`` is returned.

    4. If ``prefix`` is given but not ``length``, then a string of length
    8 prefixed by ``prefix`` is returned.

    5. If ``prefix`` and ``length`` are both given, then a string of length
    ``length`` + the length of ``prefix`` is returned.

    **Examples**::

      random_uid()           --> dherkk
      random_uid()           --> ioervion
      random_uid('test')     --> testcwq
      random_uid('abcdefgh') --> Exception  (prefix is too long)
      random_uid(length=5)   --> azxlg
      random_uid(prefix='abc', length=4)
                             --> abclsah

    """
    if (len(prefix) >= 8):
        msg = "cannot create a uid with prefix longer than seven characters"
        raise ValueError(msg)

    if (length is None):
        if (len(prefix) > 0):
            length = 8 - len(prefix)
        else:
            lengths = list(range(3, 8))
            length  = random.choice(lengths)

    if (length < 3):
        msg = "cannot create a uid shorter than three characters"
        raise ValueError(msg)

    if (length > 8):
        msg = "cannot create a uid longer than eight characters"
        raise ValueError(msg)

    uid = prefix
    for _ in range(length):
        uid += random.choice(LETTERS)

    return uid

def utc_datetime_secs_from_now(secs: int) -> datetime.datetime:
    """Get the datetime.datetime object corresponding to ``secs`` seconds from now.

    :return: a ``datetime.datetime`` object in the UTC timezone corresponding to the
      current time plus ``secs`` seconds.
    :rtype: datetime.datetime

    """
    current_time = datetime.datetime.now(pytz.utc)
    return current_time + datetime.timedelta(seconds=secs)
    

