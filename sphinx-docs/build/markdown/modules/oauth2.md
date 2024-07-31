# stanford.green.oauth2

Library to interact with OAuth2 endpoints.

So far this library only contains the AccessToken class. This class is
used to get an OAuth2 client access token from an OAuth2 Authorization
Server.

### *class* stanford.green.oauth2.AccessToken(token: str, expires_at: datetime)

An object representing an OAuth access token returned by an OAuth Authorization Server.

* **Parameters:**
  * **token** (*str*) – the token string returned by an OAuth Authorization Server.
  * **expires_at** (*datetime.datetime*) – the date and time when the token `token` expires.

#### *property* expires_at *: datetime*

Return the `_expires_at` property (datetime.datetime object when token expires)

#### expires_in()

The number of seconds until access token expires.

* **Returns:**
  the number of seconds until access token expires
* **Return type:**
  int

Note: if the token has expired this value will be negative.

#### is_expired()

Is the token expired?

* **Returns:**
  `True` if the token has expired, `False` otherwise.
* **Return type:**
  bool

#### zulu_time_string()

Return the `_expires_at` as a Zulu time string

### *class* stanford.green.oauth2.ApiAccessTokenEndpoint(endpoint_type: str, url: str, client_id: str, client_secret: str, exp_backoff: ExponentialBackoff, timeout: float = 15.0, use_cache: bool = True, verbose: bool = False, grant_type: str = 'client_credentials', scope: str | None = None)

Represents an API endpoint returning an access token.

* **Parameters:**
  * **endpoint_type** (*str*) – 

    the type of API Access endpoint. Two types of endpoints are
    currently recognized:
    > * `acs_api`: a Stanford ACS-style API endpoint
    > * `oauth2`:  a generic OAUth2 Authorization token endpoint
  * **url** (*str*) – the URL pointing to the OAuth Server’s access token endpoint. This is where
    we go to get the access token.
  * **client_id** (*str*) – the OAuth client’s identifier
  * **client_secret** (*str*) – the OAuth client’s secret (i.e., password)
  * **exp_backoff** (*ExponentialBackoff*) – an `ExponentialBackoff` object used for retrying access token retrieval.
  * **timeout** (*float*) – the maximum time in seconds to wait for each request attempt; default: 15.0.
  * **use_cache** (*bool*) – if set to `True` the access token will be cached; default: `True`.
  * **verbose** (*bool*) – if set to `True` progress information will be sent to standard output; default: `False`.
  * **grant_type** (*str*) – (only relevant if endpoint type is “oauth2”) the OAuth grant type;
    default: “client_credentials”
  * **scopes** (*list* *[**str* *]*) – (only relevant if endpoint type is “oauth2”) a list of OAuth scopes the
    client wants access to; default: the empty list

#### \_get_token()

Get the access token from the token endpoint.

#### cache_get()

Get the cached value.

* **Returns:**
  the cached `AccessToken` object.
* **Return type:**
  `AccessToken`

#### cache_set(value: [AccessToken](#stanford.green.oauth2.AccessToken), expires_in: int)

Cache the `AccessToken` object.

* **Parameters:**
  * **value** (`AccessToken`) – the AccessToken to cache.
  * **expires_in** (*int*) – set the expiration to be `expires_in` seconds from now.

We use a file-based Cache which pickles the object before
storage.  To support this the AccessToken object has a custom
Pickle instance (see `__setstate__` and `__getstate` in the
`AccessToken` class in the source code).

Note: this method only relevant if `self.use_cache` is `True`.

#### get_token(expires_at_override: datetime | None = None)

Get access token using the cache if enabled.

* **Parameters:**
  **expires_at_override** (*Optional* *[**datetime.datetime* *]*) – a `datetime.datetime` to use instead of
  the actual expiration time; defaults to `None`.
* **Returns:**
  a valid (cached or otherwise) `AccessToken` object.
* **Return type:**
  `AccessToken`

If the value is cached, uses the cached value, otherwise gets the
access token using [`_get_token()`](#stanford.green.oauth2.ApiAccessTokenEndpoint._get_token).

There are circumstances (e.g., during unit testing) when we want
to override the expires_at time that was set by the token API
call. For those circumstances use the expires_in_override
parameter.

#### get_token_acs_api()

Get the token from the API get-token endpoint (no caching)

The get-token JSON response contains the token itself and two
time-related attributes:

* expires_at: when the token expires in Zulu (UTC) time.
* expires_in: the number of seconds from when the token was
  generated until it expires.

When creating the AccessToken object we convert the Zulu time
expires_at string into a Python timezone-aware datetime object
since that is what AccessToken requires.

Furthermore, AccessToken calculates expires_in itself so we ignore
the response’s expires_in value.

#### get_token_oauth2()

Get the token from an OAuth2 get-token endpoint (no caching)

The get-token JSON response contains the token itself and the
expires_in attribute

* expires_in: the number of seconds from when the token was
  generated until it expires.

#### is_acs_api()

* **Returns:**
  `True` if `self.endpoint_type` is set to “acs_api”, `False` otherwise.
* **Return type:**
  bool

#### is_oauth2()

* **Returns:**
  `True` if `self.endpoint_type` is set to “oauth2”, `False` otherwise.
* **Return type:**
  bool

#### progress(msg: str)

Show a progress message
