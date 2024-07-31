# stanford.green

Functions of general use to the Stanford community.

### stanford.green.random_uid(prefix: str = '', length: int | None = None)

Create a random Stanford-compliant uid.

* **Parameters:**
  * **prefix** (*str*) – a string prefix (defaults to the empty string)
  * **length** (*int* *or* *None*) – desired length of the resulting uid (optional)
* **Returns:**
  a random string between three and eight characters long that
  is a valid Stanford uid unless `length` is provided in which case
  the returned string will have length `length`.
  If `prefix` is supplied then the returned
  string will start with `prefix` AND the length of returned string
  will be eight.
* **Raises:**
  **Exception** – if `prefix` is eight or more characters there
  is not enough space to put the rest of the randomly generated
  characters and in this case an Excption will be raised.

**Algorithm**

1. If neither `prefix` nor `length` are given then a string of
length between 3 and 8 is returned.

2. If `length` is given and is smaller then 3 or larger than 8, an exception
is raised.

3. If `length` is given and is between 3 and 8 (inclusive), then
a string of length of `length` is returned.

4. If `prefix` is given but not `length`, then a string of length
8 prefixed by `prefix` is returned.

5. If `prefix` and `length` are both given, then a string of length
`length` + the length of `prefix` is returned.

**Examples**:

```default
random_uid()           --> dherkk
random_uid()           --> ioervion
random_uid('test')     --> testcwq
random_uid('abcdefgh') --> Exception  (prefix is too long)
random_uid(length=5)   --> azxlg
random_uid(prefix='abc', length=4)
                       --> abclsah
```
