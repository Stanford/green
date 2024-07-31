# stanford.green.zulutime

Functions related to “Zulu” time; see also [https://www.w3.org/TR/NOTE-datetime](https://www.w3.org/TR/NOTE-datetime).

### stanford.green.zulutime.dt_to_zulu_string(dtime: datetime)

Convert a timezone-aware datetime object to a Zulu string.

* **Parameters:**
  **dtime** – a timezone-aware datetime object
* **Returns:**
  a string in Zulu time format (see also
  [https://www.w3.org/TR/NOTE-datetime](https://www.w3.org/TR/NOTE-datetime))
* **Raises:**
  **ValueError** – if `dtime` is not a timezone-aware `datetime.datetime`
  object.

**Examples**:

```default
local_tz = pytz.timezone('America/New_York')
local_time = datetime.datetime.now(local_tz)
dt_to_zulu_string(local_time) --> '2024-07-30T11:57:10Z'

dt_to_zulu_string(None)                    --> ValueError
dt_to_zulu_string(datetime.datetime.now()) --> ValueError  (not timezone-aware)
```

### stanford.green.zulutime.is_zulu_string(zulu_str: str)

Is `zulu_str` a valid “Zulu” time format string?

* **Parameters:**
  **zulu_str** – a string
* **Returns:**
  `True` if `zulu_str` is a valid Zulu time string, `False` otherwise.

**Examples**:

```default
is_zulu_string(None)                          --> False
is_zulu_string('hello')                       --> False
is_zulu_string('2024-07-28T21:42:34Z')        --> True
is_zulu_string('2024-07-28T21:42:34.123456Z') --> True
is_zulu_string('2024-07-28T21:42:34.Z')       --> False
```

### stanford.green.zulutime.zulu_string_to_utc(zulu_str: str)

Convert zulu_str to a UTC offset aware datetime object.

* **Parameters:**
  **zulu_str** – a string
* **Returns:**
  a `datetime.datetime` in the UTC timezone.
* **Raises:**
  **ValueError** – if `zulu_str` is not a valid Zulu time string.

**Examples**:

```default
zulu_string_to_utc('2024-07-28T21:42:34Z')  --> 2024-07-28 21:42:34+00:00
zulu_string_to_utc(None)                    --> ValueError
zulu_string_to_utc('2024-07-28 T21:42:34Z') --> ValueError
```
