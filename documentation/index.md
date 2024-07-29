# Table of Contents

* [stanford.green](#stanford.green)
  * [random\_uid](#stanford.green.random_uid)

<a id="stanford.green"></a>

# stanford.green

Utilities functions of general use to the Stanford community.

<a id="stanford.green.random_uid"></a>

#### random\_uid

```python
def random_uid(prefix: str = "", length: Optional[int] = None) -> str
```

Create a random Stanford-compliant uid.

**Arguments**:

- `prefix` (`str`): prefix generated uid with this string.

**Raises**:

- `Exception`: if ``prefix`` is eight or more characters there
is not enough space to put the rest of the randomly generated
  characters and in this case an Excption will be raised.

Examples::

  random_uid()           --> dherkk
  random_uid()           --> ioervion
  random_uid('test')     --> testcwq
  random_uid('abcdefgh') --> Exception  (prefix is too long)

**Returns**:

a random string between three and eight characters long that
is a valid Stanford uid. If ``prefix`` is supplied then the returned
string will start with ``prefix`` AND the length of returned string
will be eight.

