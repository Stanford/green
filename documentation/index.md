<!-- stanford-green documentation master file, created by
sphinx-quickstart on Mon Jul 29 09:40:26 2024.
You can adapt this file completely to your liking, but it should at least
contain the root `toctree` directive. -->

# stanford-green documentation

Add your content using `reStructuredText` syntax. See the
[reStructuredText](https://www.sphinx-doc.org/en/master/usage/restructuredtext/index.html)
documentation for details.

<a id="module-stanford.green"></a>

Utilities functions of general use to the Stanford community.

### stanford.green.random_uid(prefix: str = '', length: int | None = None)

Create a random Stanford-compliant uid.

* **Parameters:**
  **prefix** (*str*) – prefix generated uid with this string.
* **Returns:**
  a random string between three and eight characters long that
  is a valid Stanford uid. If `prefix` is supplied then the returned
  string will start with `prefix` AND the length of returned string
  will be eight.
* **Raises:**
  **Exception** – if `prefix` is eight or more characters there
  is not enough space to put the rest of the randomly generated
  characters and in this case an Excption will be raised.

Examples:

```default
random_uid()           --> dherkk
random_uid()           --> ioervion
random_uid('test')     --> testcwq
random_uid('abcdefgh') --> Exception  (prefix is too long)
```

<a id="module-stanford.green.zulutime"></a>

Functions related to “Zulu” time; see also [https://www.w3.org/TR/NOTE-datetime](https://www.w3.org/TR/NOTE-datetime).

### stanford.green.zulutime.dt_to_zulu_string(dtime: datetime)

Convert dt to a Zulu string. Assumes that dt is offset aware.

‘2014-12-10T12:00:00Z’

### stanford.green.zulutime.is_zulu_string(zulu_str: str)

Check if zulu_str is in “Zulu” time format.

> ‘2014-12-10T12:00:00Z’

or
: ‘2014-12-10T12:00:00.123456Z’

We do NOT allow ‘2014-12-10T12:00:00.Z’

### stanford.green.zulutime.zulu_string_to_utc(zulu_str: str)

Convert zulu_str to a UTC offset aware datetime object.
