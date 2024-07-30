"""
Functions related to "Zulu" time; see also https://www.w3.org/TR/NOTE-datetime.
"""

import re
import datetime
import dateutil.parser
import pytz

def is_zulu_string(zulu_str: str) -> bool:
    """Is ``zulu_str`` a valid "Zulu" time format string?

    :param zulu_str: a string
    :type prefix: str
    :return: ``True`` if ``zulu_str`` is a valid Zulu time string, ``False`` otherwise.


    **Examples**::

      is_zulu_string(None)                          --> False
      is_zulu_string('hello')                       --> False
      is_zulu_string('2024-07-28T21:42:34Z')        --> True
      is_zulu_string('2024-07-28T21:42:34.123456Z') --> True
      is_zulu_string('2024-07-28T21:42:34.Z')       --> False

    """
    if (zulu_str is None):
        return False

    regex = r'^\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d(?:[.]\d+)?Z$'
    if (re.match(regex, zulu_str) is None):  # pylint: disable=simplifiable-if-statement
        return False
    else:
        return True

def zulu_string_to_utc(zulu_str: str) -> datetime.datetime:
    """Convert zulu_str to a UTC offset aware datetime object.

    :param zulu_str: a string
    :type prefix: str
    :return: a ``datetime.datetime`` in the UTC timezone.
    :raises ValueError: if ``zulu_str`` is not a valid Zulu time string.

    **Examples**::

      zulu_string_to_utc('2024-07-28T21:42:34Z')  --> 2024-07-28 21:42:34+00:00
      zulu_string_to_utc(None)                    --> ValueError
      zulu_string_to_utc('2024-07-28 T21:42:34Z') --> ValueError
    """
    if (not is_zulu_string(zulu_str)):
        msg = f"the string '{zulu_str}' is not in Zulu time format"
        raise ValueError(msg)

    zulu_dt = dateutil.parser.parse(zulu_str)

    return zulu_dt

def dt_to_zulu_string(dtime: datetime.datetime) -> str:
    """Convert a timezone-aware datetime object to a Zulu string.

    :param dtime: a timezone-aware datetime object
    :type prefix: datetime.datetime
    :return: a string in Zulu time format (see also
      https://www.w3.org/TR/NOTE-datetime)
    :raises ValueError: if ``dtime`` is not a timezone-aware ``datetime.datetime``
      object.

    **Examples**::

      local_tz = pytz.timezone('America/New_York')
      local_time = datetime.datetime.now(local_tz)
      dt_to_zulu_string(local_time) --> '2024-07-30T11:57:10Z'

      dt_to_zulu_string(None)                    --> ValueError
      dt_to_zulu_string(datetime.datetime.now()) --> ValueError  (not timezone-aware)


    """
    if (dtime is None):
        msg = "cannot convert None to a Zulu string"
        raise ValueError(msg)

    if (dtime.tzinfo is None):
        msg = "cannot convert offset naive datetime to a Zulu string"
        raise ValueError(msg)

    dtime_utc = dtime.astimezone(datetime.timezone.utc)

    return dtime_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
