"""Library to interact with OAuth2 endpoints.

So far this library only contains the AccessToken class. This class is
used to get an OAuth2 client access token from an OAuth2 Authorization
Server.

"""

import datetime
import hashlib
import logging
import pytz
import random
import requests
from requests.exceptions import HTTPError
import time

# diskcache does not have type hint support, so tell the type checker to
# ignore it.
from diskcache import Cache   # type: ignore

from exponential_backoff_ca import ExponentialBackoff

from stanford.green.zulutime import dt_to_zulu_string, zulu_string_to_utc

## TYPING
from typing import Optional, cast
#AttributeDict         = dict[str, Any]
AccessTokenDict = dict[str, str|int|datetime.datetime]
## END OF TYPING

class AccessToken():
    """An object representing an Oauth token returned by an ACS API get-token endpoint.

    An AccessToken sets properties with these same names but with some differences:

    * token: the token string used to authenticate to an ACS API service.

    * expires_at: a Python timezone-aware datetime object when the token expires.

    * expires_in: the number of seconds from when the AccessToken
      constructor was called until expires_at.

    """
    def __init__(self, token: str, expires_at: datetime.datetime):
        if (token is None):
            msg = "the token cannot be None"
            raise ValueError(msg)

        if (token == ""):
            msg = "the token cannot be the empty string"
            raise ValueError(msg)

        self.token = token

        # Check that expires_at is _not_ offset NAIVE:
        if (expires_at.tzinfo is None):
            msg = "expires_at must be offset aware"
            raise ValueError(msg)

        self.expires_at = expires_at  # datetime when token expires

        # self.expires_in is calculated and set by the preceding
        # expires_at setter call. See the expires_at() setter below for
        # details.

    def __str__(self) -> str:
        zulu_time_string = self.zulu_time_string()

        local_tz         = pytz.timezone('US/Pacific')
        local_expires_at = self.expires_at.astimezone(tz=local_tz)

        fields = []
        fields.append(f"token: {self.token}")
        fields.append(f"expires_at (UTC): {zulu_time_string}")
        fields.append(f"expires_at (local): {local_expires_at}")
        fields.append(f"expires_in (secs): {round(self.expires_in, 1)}")

        return f"<{', '.join(fields)}>"

    @property
    def expires_in(self) -> int:
        """Return the expires_in number of seconds returned by the token API call."""
        return self._expires_in

    @expires_in.setter
    def expires_in(self, value: int) -> None:
        """Set expires_in property (also updates expires)."""
        self._expires_in = value

    @property
    def expires_at(self) -> datetime.datetime:
        """Return the _expires_at property (datetime.datetime object when token expires)"""
        return self._expires_at

    @expires_at.setter
    def expires_at(self, value: datetime.datetime) -> None:
        self._expires_at = value

        # Calculate expires_in from expires_at.
        current_utc_time = datetime.datetime.now(datetime.timezone.utc)
        self.expires_in = int((value - current_utc_time).total_seconds())

    def zulu_time_string(self) -> str:
        """Return the _expires_at as a Zulu time string"""
        return dt_to_zulu_string(self.expires_at)

    ### PICKLE CUSTOMIZATION ###
    def __getstate__(self) -> AccessTokenDict:
        values: AccessTokenDict = {}
        values['token']      = self.token
        values['expires_at'] = self.expires_at

        return values

    def __setstate__(self, values: AccessTokenDict) -> None:
        self.token      = str(values['token'])
        self.expires_at = cast(datetime.datetime, values['expires_at'])
    ### END OF PICKLE CUSTOMIZATION ###

    def is_expired(self) -> bool:
        """Is the token expired?
        """
        if (self.expires_at is None):
            return True
        elif (self.expires_at < datetime.datetime.now(tz=datetime.timezone.utc)):
            return True
        else:
            return False


class ApiAccessTokenEndpoint():
    """Represents an API endpoint returning an access token.

    timeout: the maximum time to wait for each request attempt.

    url: The full path to the token endpoint, e.g., https://api-dev.example.com/api/v1/token

    """

    def __init__(
            self,
            url:               str,
            client_id:         str,
            client_secret:     str,
            exp_backoff:       ExponentialBackoff,
            timeout:           float=15.0,
            use_cache:         bool=True,
            verbose:           bool=False,
    ):
        """
        url: the full path to the get-token API endpoint.
        """
        self.url           = url
        self.client_id     = client_id
        self.client_secret = client_secret
        self.exp_backoff   = exp_backoff

        self.timeout       = timeout

        self.use_cache     = use_cache

        self.verbose = verbose

        self.base_headers = {'Accept': 'application/json'}

        if (self.use_cache):
            # We set the cache_key to be the SHA256 hash of the url. This way
            # we avoid reading anyone else's cache.
            m = hashlib.sha256()
            m.update(url.encode('ascii'))
            self.cache_key = 'access_token_' + m.hexdigest()
            self.cache     = Cache()  # Cache the access token

        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)

    def progress(self, msg: str) -> None:
        """Show a progress message"""
        self.logger.debug(msg)
        if (self.verbose):
            now = datetime.datetime.now()
            print(f"[progress] {now} {msg}")


    def cache_set(self, value: AccessToken, expires_in: int) -> None:
        """Set the cache to value and expire in expires_in seconds."""
        self.progress('entering cache_set()')

        # We subtract 5 seconds from expires_in to avoid a situation where
        # the current time is so close to the expires time that we return a
        # token that will expire in the time it takes to make the API call.
        self.cache.set(self.cache_key, value, expire=(expires_in - 5))

    def cache_get(self) -> AccessToken:
        """Get the cached value."""
        self.progress('entering cache_get()')
        return cast(AccessToken, self.cache.get(self.cache_key))

    def get_token(self,
                  expires_at_override: Optional[datetime.datetime] = None) -> AccessToken:
        """Get the token needed to make API calls to the gadmin2 API.

        If the value is cached, uses the cached value, otherwise goes out
        to the gadmin2 token API and gets a new token.

        There are circumstances (e.g., during unit testing) when we want
        to override the expires_at time that was set by the token API
        call. For those circumstances use the `expires_in_override`
        parameter.

        """
        if (not self.use_cache):
            msg = "not using cache as the use_cache propery is True"
            self.progress(msg)
            return self._get_token()

        with Cache(self.cache.directory) as _:
            access_token_cached = self.cache_get()
            if (access_token_cached is None):
                self.progress('cache MISS')
                access_token = self._get_token()

                if (expires_at_override is not None):
                    access_token.expires_at = expires_at_override

                # Cache this value.
                self.cache_set(access_token, expires_in=access_token.expires_in)
                return access_token
            else:
                self.progress("cache HIT")
                return access_token_cached

    def _get_token(self) -> AccessToken:
        """Get the token from the API get-token endpoint (no caching)

        The get-token JSON response contains the token itself and two
        time-related attributes:

        * expires_at: when the token expires in Zulu (UTC) time.

        * expires_in: the number of seconds from when the token was
          generated until it expires.

        When creating the AccessToken object we convert the Zulu time
        expires_at string into a Python timezone-aware datetime object
        since that is what AccessToken requires.

        Furthermore, AccessToken calculates expires_in itself so we ignore
        the response's expires_in value.

        """
        self.progress("entering _get_token")

        url = self.url

        headers                  = self.base_headers
        headers['client-id']     = self.client_id
        headers['client-secret'] = self.client_secret

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
                response = requests.get(url, headers=headers, timeout=self.timeout)
            except Exception as excpt:
                error_msg = f"error making request: {str(excpt)}"
            else:
                status_code = response.status_code
                success     = (status_code == 200)

            if (success):
                self.progress(f"get token request came back with some data")
                break

            # If we get here we were not successful. So, we try again.
            if (status_code is not None):
                msg = f"when retrieving access token got response code {response.status_code}"
            else:
                msg = f"error retrieving access token: {error_msg}"

            last_error_msg = msg
            msg = f"{msg} (attempt {self.exp_backoff.counter})"
            self.progress(msg)

            # Was this the last try? If not, sleep
            if (self.exp_backoff.counter == self.exp_backoff.number_of_iterations):
                msg = f"this was the last attempt; giving up"
                self.progress(msg)
                self.logger.error(msg)
            else:
                # Sleep a bit before retrying.
                msg = f"will sleep for {wait_seconds} seconds before trying again"
                self.progress(msg)
                self.logger.info(msg)
                time.sleep(wait_seconds)

        # After all of that, did we actually get an access token?
        if (success):
            data = response.json()
            if ('access_token' in data):
                token          = data['access_token']
                expires_at_str = data['expires_at']

                # expires_at_str should be in "Zulu" time format, i.e.,
                # '2014-12-10T12:00:00Z'

                # Convert expires_at (a string) to an offset aware datetime object.
                expires_at = zulu_string_to_utc(expires_at_str)

                access_token = AccessToken(token, expires_at)
                return access_token
            else:
                msg = 'got a 200 response but could not find access token in data'
                self.logger.error(msg)
                raise KeyError(msg)
        else:
            msg = f"token request failed; last error message: {last_error_msg}"
            self.logger.error(msg)
            raise HTTPError(msg)
