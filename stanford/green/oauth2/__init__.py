"""Library to interact with OAuth2 endpoints.

.. _exponential-backoff-ca: https://github.com/macrotex/python-exponential-backoff-ca

--------
Overview
--------

The ``stanford.green.oauth2`` package provides classes to connect to
an OAuth2 Authorization Server and get an access token. These classes
support retries via the
`exponential_backoff_ca Python package <exponential-backoff-ca_>`_.
Once you
have the access token it is up to you to use it to make API calls.

There is built-in file-based caching to minimize the number of times
you have to go out to the access token endpoint.


--------
Examples
--------

To connect to an OAuth2 Authorization Server and get an access token::

  from exponential_backoff_ca import ExponentialBackoff
  from stanford.green.oauth2  import AccessToken, ApiAccessTokenEndpoint

  # The URL to get the token (provided by OAuth2 Authorization Service):
  url = "https://api.endpoint.com/api/v1/token"

  # The ApiAccessTokenEndpoint object requires an exponential backoff
  # object to do the retries:
  time_slot_secs = 3.0  # The number of seconds in each time slot.
  num_iterations = 4    # The number of iterations.
  limit_value    = 10.0 # Don't wait any longer than this number of seconds.
  exp_backoff    = ExponentialBackoff(time_slot_secs, num_iterations,
                                      limit_value=limit_value, debug=True)

  # Define the ApiAccessTokenEndpoint object. The 'oauth2' tells the
  # ApiAccessTokenEndpoint class that this is an OAuth2 access token
  # endpoint.
  client_id     = 'username'
  client_secret = 'password'
  api_access    = ApiAccessTokenEndpoint('oauth2', url, client_id, client_secret,
                                          exp_backoff, scopes=['read', 'list'],
                                          verbose=True)

  # Get the token.
  access_token = api_access.get_token()

  # This token can now be used with the API to do other operations.

  # If you want to cache the token, set the "use_cache" flag to True:
  # api_access = ApiAccessTokenEndpoint('oauth2', url, client_id, client_secret,
  #                                     exp_backoff,  scopes=['read', 'list'],
  #                                     verbose=True, use_cache=True)

  # By default the request puts the client id and secret in the POSTed
  # data. However, if your Authorization Server only wants the id and
  # secret passed as a Basic Auth header set ``use_base_auth`` to ``True``:
  # api_access = ApiAccessTokenEndpoint('oauth2', url, client_id, client_secret,
  #                                     exp_backoff,  scopes=['read', 'list'],
  #                                     verbose=True, use_basic_auth=True)


To connect to an ACS-style API endpoint you use much the same code as above::

  from exponential_backoff_ca import ExponentialBackoff
  from stanford.green.oauth2  import AccessToken, ApiAccessTokenEndpoint

  # The URL to get the token (provided by OAuth2 Authorization Service):
  url = "https://api.endpoint.com/api/v1/token"

  # The ApiAccessTokenEndpoint object requires an exponential backoff
  # object to do the retries:
  time_slot_secs = 3.0  # The number of seconds in each time slot.
  num_iterations = 4    # The number of iterations.
  limit_value    = 10.0 # Don't wait any longer than this number of seconds.
  exp_backoff    = ExponentialBackoff(time_slot_secs, num_iterations,
                                      limit_value=limit_value, debug=True)

  # Define the ApiAccessTokenEndpoint object. The 'acs_api' tells the
  # ApiAccessTokenEndpoint class that this is ACS API-style endpoint.
  # Note that this kind of API access endpoint does not supply the
  # scopes parameter.
  client_id     = 'username'
  client_secret = 'password'
  api_access    = ApiAccessTokenEndpoint('acs_api', url, client_id, client_secret,
                                          exp_backoff, verbose=True)

  # Get the token.
  access_token = api_access.get_token()

  # This token can now be used with the API to do other operations.

"""
# pylint: disable=superfluous-parens
# pylint: disable=too-many-arguments
# pylint: disable=too-many-instance-attributes

import base64
import datetime
import hashlib
import json
import logging
import random
import time
import urllib

import requests
from requests.exceptions import HTTPError

# diskcache does not have type hint support, so tell the type checker to
# ignore it.
from diskcache import Cache   # type: ignore

from exponential_backoff_ca import ExponentialBackoff
import pytz

from stanford.green          import utc_datetime_secs_from_now
from stanford.green.zulutime import dt_to_zulu_string, zulu_string_to_utc

## TYPING
from typing import Optional, cast, Any, Tuple  # pylint: disable=wrong-import-order
AccessTokenDict = dict[str, str|int|datetime.datetime]
## END OF TYPING

class AccessToken():
    """An object representing an OAuth access token returned by an OAuth Authorization Server.

    :param token: the token string returned by an OAuth Authorization Server.
    :type token: str

    :param expires_at: the date and time when the token :py:attr:`token` expires.
    :type expires_at: datetime.datetime

    """
    def __init__(self, token: str, expires_at: datetime.datetime):
        if (token is None):
            msg = "the token cannot be None"
            raise ValueError(msg)

        if (token == ""):
            msg = "the token cannot be the empty string"
            raise ValueError(msg)

        self.token = token

        # Check that expires_at is _not_ datetime offset NAIVE:
        if (expires_at.tzinfo is None):
            msg = "expires_at must be offset aware"
            raise ValueError(msg)

        self.expires_at = expires_at  # datetime when token expires

    def __str__(self) -> str:
        """Return a string version of AccessToken object.
        """
        zulu_time_string = self.zulu_time_string()

        local_tz         = pytz.timezone('US/Pacific')
        local_expires_at = self.expires_at.astimezone(tz=local_tz)

        fields = []
        fields.append(f"token: {self.token}")
        fields.append(f"expires_at (UTC): {zulu_time_string}")
        fields.append(f"expires_at (local): {local_expires_at}")
        fields.append(f"expires_in (secs): {round(self.expires_in(), 1)}")

        return f"<{', '.join(fields)}>"

    ## Getters and setters

    @property
    def expires_at(self) -> datetime.datetime:
        """Return the ``expires_at`` property (datetime.datetime object when token expires)"""
        return self._expires_at

    @expires_at.setter
    def expires_at(self, value: datetime.datetime) -> None:
        """Sets the ``expires_at`` property."""
        self._expires_at = value
    ## End of getters and setters

    def zulu_time_string(self) -> str:
        """Return the ``_expires_at`` property as a Zulu time string"""
        return dt_to_zulu_string(self.expires_at)

    ### PICKLE CUSTOMIZATION ###
    # We use this custom pickle to cache an AccessToken.
    def __getstate__(self) -> AccessTokenDict:
        values: AccessTokenDict = {}
        values['token']      = self.token
        values['expires_at'] = self.expires_at

        return values

    def __setstate__(self, values: AccessTokenDict) -> None:
        self.token      = str(values['token'])
        self.expires_at = cast(datetime.datetime, values['expires_at'])
    ### END OF PICKLE CUSTOMIZATION ###


    def expires_in(self) -> int:
        """The number of seconds until access token expires.

        :return: the number of seconds until access token expires
        :rtype: int

        Note: if the token has expired this value will be negative.
        """
        current_utc_time = datetime.datetime.now(datetime.timezone.utc)
        expires_in_secs = int((self.expires_at - current_utc_time).total_seconds())

        return expires_in_secs

    def is_expired(self) -> bool:
        """Has the token expired?

        :return: ``True`` if the token has expired, ``False`` otherwise.
        :rtype: bool
        """
        if (self.expires_at is None):
            return True

        if (self.expires_at < datetime.datetime.now(tz=datetime.timezone.utc)):
            return True

        return False


class ApiAccessTokenEndpoint():
    """Represents an API endpoint returning an access token.

    :param endpoint_type: the type of API Access endpoint. Two types of endpoints are
      currently recognized:

        * ``acs_api``: a Stanford ACS-style API endpoint

        * ``oauth2``:  a generic OAuth2 Authorization token endpoint

    :type endpoint_type: str

    :param url: the URL pointing to the OAuth Server's access token endpoint. This is where
      we go to get the access token.
    :type url: str

    :param client_id: the OAuth client's identifier
    :type client_id: str

    :param client_secret: the OAuth client's secret (i.e., password)
    :type client_secret: str

    :param exp_backoff: an `ExponentialBackoff <exponential-backoff-ca_>`_
      object used for retrying access token retrieval.
    :type exp_backoff: ExponentialBackoff

    :param use_basic_auth: a boolean that when set to ``True`` means send the client id and secret
      in a Basic Auth header but when set to ``False`` means to send the client id and secret
      as parameters in the POST (this parameter is _ignored_ when ``endpoint_type`` is
      set to ``acs_api``); using  default ``False``.
    :type use_basic_auth: bool

    :param timeout: the maximum time in seconds to wait for each request attempt; default: 15.0.
    :type timeout: float

    :param use_cache: if set to ``True`` the access token will be cached; default: ``True``.
    :type use_cache: bool

    :param cache_dir: if use_cache is ``True`` then cache_dir is the caching directory to use;
      default: ``/tmp/stanford_green_cache``.
    :type cache_dir: bool

    :param grant_type: (only relevant if endpoint type is "oauth2") the OAuth grant type;
      default: "client_credentials"
    :type grant_type: str

    :param scopes: (only relevant if endpoint type is "oauth2") a list of OAuth scopes the
      client wants access to; default: the empty list
    :type scopes: list[str]

    """

    def __init__(  # pylint: disable=too-many-positional-arguments
            self,
            endpoint_type:     str,
            url:               str,
            client_id:         str,
            client_secret:     str,
            exp_backoff:       ExponentialBackoff,
            use_basic_auth:    bool=False,
            timeout:           float=15.0,
            use_cache:         bool=True,
            cache_dir:         str='/tmp/stanford_green_cacheNone',
            verbose:           bool=False,
            # OAuth stuff:
            grant_type:        str='client_credentials',
            scopes:            Optional[list[str]]=None,
            #
            use_lib:           str='requests',
    ):
        valid_endpoints = ['acs_api', 'oauth2']
        if (endpoint_type not in valid_endpoints):
            msg = f"unrecognized endpont type: '{endpoint_type}'"
            raise ValueError(msg)

        self.endpoint_type = endpoint_type

        self.url            = url
        self.client_id      = client_id
        self.client_secret  = client_secret
        self.exp_backoff    = exp_backoff
        self.use_basic_auth = use_basic_auth

        self.timeout   = timeout
        self.use_cache = use_cache
        self.verbose   = verbose

        # OAuth settings
        if (scopes is None):
            self.scopes: list[str] = []
        else:
            self.scopes     = scopes

        self.grant_type = grant_type

        self.use_lib    = use_lib  # Use this library (Must be one of 'requests' or 'urllib')

        self.base_headers = {'Accept': 'application/json'}

        if (self.use_cache):
            # We set the cache_key to be the SHA256 hash of the url. This way
            # we avoid reading anyone else's cache.
            hasher = hashlib.sha256()
            hasher.update(url.encode('ascii'))
            self.cache_key = 'access_token_' + hasher.hexdigest()
            self.cache     = Cache(cache_dir)  # Cache the access token

        self.logger = logging.getLogger(__name__)

    def is_acs_api(self) -> bool:
        """
        :return: ``True`` if ``self.endpoint_type`` is set to "acs_api", ``False`` otherwise.
        :rtype: bool
        """
        return (self.endpoint_type == 'acs_api')

    def is_oauth2(self) -> bool:
        """
        :return: ``True`` if ``self.endpoint_type`` is set to "oauth2", ``False`` otherwise.
        :rtype: bool
        """
        return (self.endpoint_type == 'oauth2')

    def cache_set(self, value: AccessToken, expires_in: int) -> None:
        """Cache the ``AccessToken`` object.

        :param value: the AccessToken to cache.
        :type value: ``AccessToken``

        :param expires_in: set the expiration to be ``expires_in`` seconds from now.
        :type expires_in: int

        We use a file-based Cache which pickles the object before
        storage.  To support this the AccessToken object has a custom
        Pickle instance (see ``__setstate__`` and ``__getstate`` in the
        ``AccessToken`` class in the source code).

        Note: this method only relevant if ``self.use_cache`` is ``True``.

        """
        self.logger.debug('entering cache_set()')

        # We subtract 5 seconds from expires_in to avoid a situation where
        # the current time is so close to the expires time that we return a
        # token that will expire in the time it takes to make the API call.
        self.logger.debug(f"setting expiration to {expires_in - 5} seconds")
        self.cache.set(self.cache_key, value, expire=(expires_in - 5))

    def cache_get(self) -> AccessToken:
        """Get the cached value.

        :return: the cached ``AccessToken`` object.
        :rtype: ``AccessToken``

        """
        self.logger.debug('entering cache_get()')
        self.logger.debug(f"attempting to get cached value with key {self.cache_key}")
        return cast(AccessToken, self.cache.get(self.cache_key))

    def get_token(self,
                  expires_at_override: Optional[datetime.datetime] = None) -> AccessToken:
        """Get access token (uses cache if enabled).

        :param expires_at_override: a ``datetime.datetime`` to use instead of
          the actual expiration time; defaults to ``None``.
        :type expires_at_override: Optional[datetime.datetime]

        :return: a valid (cached or otherwise) ``AccessToken`` object.
        :rtype: ``AccessToken``

        If the value is cached, uses the cached value, otherwise gets the
        access token using :py:func:`_get_token`.

        There are circumstances (e.g., during unit testing) when we want
        to override the expires_at time that was set by the token API
        call. For those circumstances use the `expires_at_override`
        parameter.

        """
        if (not self.use_cache):
            msg = "not using cache as the use_cache propery is True"
            self.logger.debug(msg)
            return self._get_token()

        with Cache(self.cache.directory) as _:
            access_token_cached = self.cache_get()
            if (access_token_cached is None):
                self.logger.debug('cache MISS')
                access_token = self._get_token()

                if (expires_at_override is not None):
                    access_token.expires_at = expires_at_override

                # Cache this value.
                self.cache_set(access_token, expires_in=access_token.expires_in())
                return access_token

            self.logger.debug("cache HIT")
            return access_token_cached

    def _get_token(self) -> AccessToken:
        """Get the access token from the token endpoint.

        This is a simple wrapper function that calls the appropriate
        get-token function depending on the value of ``self.endpoint_type``.
        """
        if (self.is_acs_api()):
            return self._get_token_acs_api()

        if (self.is_oauth2()):
            return self._get_token_oauth2()

        msg = "programming error?!?"
        raise RuntimeError(msg)

#    def _get_token_response(
#            self,
#            url: str,
#            headers: dict[str, str],
#            data: Optional[dict[Any, Any]] = None
#    ) -> dict[str, Any]:
#        """Get the token.
#
#        Returns a dict with these keys:
#            - access_token
#            - expires_at
#
#        """
#        self.progress("entering _get_token_response")
#
#        last_error_message = None
#        for wait_seconds in self.exp_backoff:
#            # Three possibilities:
#            # 1. No response at all (bad URL, timeout, etc.)
#            # 2. Response but not a 200
#            # 3. Response with a 200
#
#            status_code = None
#            success     = False
#            error_msg   = None
#            try:
#                if (data is None):
#                    response = requests.get(url, headers=headers, timeout=self.timeout)
#                else:
#                    response = requests.post(url, headers=headers, data=data, timeout=self.timeout)
#            except Exception as excpt:
#                error_msg = f"error making request: {str(excpt)}"
#            else:
#                status_code = response.status_code
#                success     = (status_code == 200)
#
#            if (success):
#                self.progress(f"get token request came back with some data")
#                break
#
#            # If we get here we were not successful. So, we try again.
#            if (status_code is not None):
#                msg = f"when retrieving access token got response code {response.status_code}"
#            else:
#                msg = f"error retrieving access token (no status code): {error_msg}"
#
#            last_error_msg = msg
#            msg = f"{msg} (attempt {self.exp_backoff.counter})"
#            self.progress(msg)
#
#            # Was this the last try? If not, sleep
#            if (self.exp_backoff.counter == self.exp_backoff.number_of_iterations):
#                msg = f"this was the last attempt; giving up"
#                self.progress(msg)
#                self.logger.error(msg)
#            else:
#                # Sleep a bit before retrying.
#                msg = f"will sleep for {wait_seconds} seconds before trying again"
#                self.progress(msg)
#                self.logger.info(msg)
#                time.sleep(wait_seconds)
#
#        # After all of that, did we actually get an access token?
#        if (success):
#            return response
#
#        msg = f"token request failed; last error message: {last_error_msg}"
#        self.logger.error(msg)
#        raise HTTPError(msg)


    def _make_request(
            self,
            url: str,
            headers: dict[str, str],
            data: Optional[dict[Any, Any]] = None
    ) -> Tuple[int, dict[str, Any]]:
        """Make the request and return the data as a dict.

        This method provides the option of using the requests library or the
        urllib library.
        """
        if (self.use_lib == 'requests'):
            ### Use the "requests" library.
            self.logger.debug("using http library 'requests'")
            if (data is None):
                with requests.get(url, headers=headers,
                                  timeout=self.timeout) as response:
                    status_code = response.status_code
                    response_data = response.json()
            else:
                with requests.post(url, headers=headers,
                                   data=data, timeout=self.timeout) as response:
                    status_code = response.status_code
                    response_data = response.json()

            return (status_code, cast(dict[str, Any], response_data))

        if (self.use_lib == 'urllib'):
            ### Use the "urllib" library.
            self.logger.debug("using http library 'urllib'")
            if (data is None):
                request = urllib.request.Request(url)
            else:
                data_encoded = urllib.parse.urlencode(data).encode()
                request      = urllib.request.Request(url, data=data_encoded)

            # Add headers.
            for key in headers:
                value = headers[key]
                request.add_header(key, value)

            # Make the request and get the response.
            with urllib.request.urlopen(request) as response:
                status_code          = response.getcode()
                response_data_string = response.read().decode()

                # Parse response_data_string as a JSON string.
                response_data = json.loads(response_data_string)

                return (status_code, response_data)

        msg = "unrecognized value for parameter 'use_lib': {self.use_lib}"
        raise ValueError(msg)

    def _get_token_response_data(
            self,
            url: str,
            headers: dict[str, str],
            data: Optional[dict[Any, Any]] = None
    ) -> dict[str, Any]:
        """Get the token.

        Returns a dict.
        """
        self.logger.debug("entering _get_token_response_data")

        last_error_message = None
        for wait_seconds in self.exp_backoff:
            # Three possibilities:
            # 1. No response at all (bad URL, timeout, etc.)
            # 2. Response but not a 200
            # 3. Response with a 200

            status_code = None
            success     = False
            error_msg   = None
            try:
                (status_code, response_data) = \
                  self._make_request(
                      url,
                      headers,
                      data=data,
                  )
            except Exception as excpt:
                error_msg = f"error making request: {str(excpt)}"
            else:
                success = (status_code == 200)

            if (success):
                self.logger.debug("get token request came back with some data")
                break

            # If we get here we were not successful. So, we try again.
            if (status_code is not None):
                msg = f"when retrieving access token got response code {status_code}"
            else:
                msg = f"error retrieving access token (no status code): {error_msg}"

            last_error_message = msg
            msg = f"{msg} (attempt {self.exp_backoff.counter})"
            self.logger.debug(msg)

            # Was this the last try? If not, sleep
            if (self.exp_backoff.counter == self.exp_backoff.number_of_iterations):
                msg = "this was the last attempt; giving up"
                self.logger.error(msg)
            else:
                # Sleep a bit before retrying.
                msg = f"will sleep for {wait_seconds} seconds before trying again"
                self.logger.info(msg)
                time.sleep(wait_seconds)

        # After all of that, did we actually get an access token?
        if (success):
            return response_data

        msg = f"token request failed; last error message: {last_error_message}"
        self.logger.error(msg)
        raise HTTPError(msg)

    def _get_token_acs_api(self) -> AccessToken:
        """Get an access token from an ACS-API compatible token endpoint (no caching)

        The JSON response from the ACS API token endpoint contains the
        token itself and two time-related attributes:

        * ``expires_at``: when the token expires in Zulu (UTC) time.

        * ``expires_in``: the number of seconds from when the token was
          generated until it expires.

        When creating the ``AccessToken`` object we convert the Zulu time
        ``expires_at`` string into a Python timezone-aware datetime object
        that AccessToken requires.

        Furthermore, ``AccessToken`` calculates expires_in itself so we ignore
        the response's expires_in value.

        """
        self.logger.debug("entering get_token_acs_api")

        url = self.url

        headers                  = self.base_headers
        headers['client-id']     = self.client_id
        headers['client-secret'] = self.client_secret

        response_data = self._get_token_response_data(url, headers)

        if ('access_token' in response_data):
            token          = response_data['access_token']
            expires_at_str = response_data['expires_at']

            # expires_at_str should be in "Zulu" time format, i.e.,
            # '2014-12-10T12:00:00Z'

            # Convert expires_at (a string) to an offset aware datetime object.
            expires_at = zulu_string_to_utc(expires_at_str)

            access_token = AccessToken(token, expires_at)
            return access_token

        msg = 'got a 200 response but could not find access token in response_data'
        self.logger.error(msg)
        raise KeyError(msg)

    def _get_token_oauth2(self) -> AccessToken:
        """Get an access token from an OAuth2 endpoint (no caching)

        The JSON response contains the token itself and the
        `expires_in` attribute

        * expires_in: the number of seconds from when the token was
          generated until it expires.

        """
        self.logger.debug("entering get_token_oauth2")

        url = self.url

        headers = self.base_headers

        data = {
            'grant_type': self.grant_type,
        }

        # Make a Basic Auth header and add it to the headers list.
        if (self.use_basic_auth):
            auth_string = f"{self.client_id}:{self.client_secret}"
            auth_bytes  = auth_string.encode('utf-8')
            auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')
            headers['Authorization'] = f"Basic {auth_base64}"
        else:
            data['client_id']     = self.client_id
            data['client_secret'] = self.client_secret

        # Add scopes (if there are any).
        if (len(self.scopes) > 0):
            # OAuth Authorization server expects the scopes to be passed
            # as a space-delimited string.
            scopes_delimited = ' '.join(self.scopes)

            data['scope'] = scopes_delimited

        # Make the call...
        response_data = self._get_token_response_data(url, headers, data=data)

        if ('access_token' not in response_data):
            msg = 'got a 200 response but could not find access token in data'
            self.logger.error(msg)
            raise KeyError(msg)

        if ('expires_in' not in response_data):
            msg = 'got a 200 response but could not find expires_in attribute in data'
            self.logger.error(msg)
            raise KeyError(msg)

        token          = response_data['access_token']
        expires_in_raw = response_data['expires_in']

        if (expires_in_raw is None):
            msg = "expires_in value missing"
            raise ValueError(msg)

        expires_in = int(expires_in_raw)

        # If response_data['expires_in'] cannot be converted to an int the
        # above will raise an error. But that's OK because we need
        # response_data['expires_in'] to be a number.

        expires_at = utc_datetime_secs_from_now(expires_in)

        if (token is None):
            msg = "token is empty"
            raise RuntimeError(msg)

        access_token = AccessToken(token, expires_at)

        return access_token
