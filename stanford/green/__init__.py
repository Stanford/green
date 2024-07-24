"""Utilities functions of general use to teh Stanford community.
"""

# pylint: disable=superfluous-parens,invalid-name

import random

## TYPING
from typing import Dict, Any, Optional  # pylint: disable=wrong-import-order
AttributeDict = Dict[str, Any]
## END OF TYPING

LETTER_STRING = 'abcdefghijklmnopqrstuvwxyz'
LETTERS       = [*LETTER_STRING]

def random_uid(prefix: str = "", length: Optional[int] = None) -> str:
    """Create a random Stanford-compliant uid.

    :param prefix: prefix generated uid with this string.
    :type prefix: str
    :return: a random string between three and eight characters long that
      is a valid Stanford uid. If ``prefix`` is supplied then the returned
      string will start with ``prefix`` AND the length of returned string
      will be eight.
    :raises Exception: if ``prefix`` is eight or more characters there
      is not enough space to put the rest of the randomly generated
      characters and in this case an Excption will be raised.

    Examples::

      random_uid()           --> dherkk
      random_uid()           --> ioervion
      random_uid('test')     --> testcwq
      random_uid('abcdefgh') --> Exception  (prefix is too long)

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


