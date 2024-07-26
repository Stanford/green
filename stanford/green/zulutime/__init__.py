"""
Functions related to "Zulu" time; see also https://www.w3.org/TR/NOTE-datetime.
"""

import re
import datetime
import dateutil.parser
import pytz

def is_zulu_string(zulu_str: str) -> bool:
    """Check if zulu_str is in "Zulu" time format.

      '2014-12-10T12:00:00Z'
    """
    if (zulu_str is None):
        return False

    regex = r'^\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\dZ$'
    if (re.match(regex, zulu_str) is None):  # pylint: disable=simplifiable-if-statement
        return False
    else:
        return True

def zulu_string_to_utc(zulu_str: str) -> datetime.datetime:
    """Convert zulu_str to a UTC offset aware datetime object.

    """
    if (not is_zulu_string(zulu_str)):
        msg = f"the string '{zulu_str}' is not in Zulu time format"
        raise ValueError(msg)

    zulu_dt = dateutil.parser.parse(zulu_str)

    return zulu_dt

def dt_to_zulu_string(dtime: datetime.datetime) -> str:
    """Convert dt to a Zulu string. Assumes that dt is offset aware.

      '2014-12-10T12:00:00Z'

    """
    if (dtime is None):
        msg = "cannot convert None to a Zulu string"
        raise TypeError(msg)

    if (dtime.tzinfo is None):
        msg = "cannot convert offset naive datetime to a Zulu string"
        raise ValueError(msg)

    dtime_utc = dtime.astimezone(datetime.timezone.utc)

    return dtime_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
