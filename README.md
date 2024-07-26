# Stanford Green

Python libraries generally useful to the Stanford community.

stanford.green
  - random_uid

stanford.green.zulutime
  - is_zulu_string
  - zulu_string_to_utc
  - dt_to_zulu_string


## stanford.green.oauth2

Use stanford.green.oauth2.AccessToken to get an OAuth2 token from an
OAuth2 Authorization server.

### Example
```
from exponential_backoff_ca import ExponentialBackoff
from stanford.green.oauth2  import AccessToken, ApiAccessTokenEndpoint

url = "https://api.endpoint.com/api/v1/token"  # The URL to get the token (provided by API vendor)

# The ApiAccessTokenEndpoint object requires an exponential backoff object.
time_slot_secs = 3.0  # The number of seconds in each time slot.
num_iterations = 4    # The number of iterations.
limit_value    = 10.0 # Don't wait any longer than this number of seconds.
exp_backoff    = ExponentialBackoff(time_slot_secs, num_iterations, limit_value=limit_value, debug=True)

# Define the ApiAccessTokenEndpoint object.
client_id     = 'username'
client_secret = 'password'
api_access    = ApiAccessTokenEndpoint(url, client_id, client_secret, exp_backoff, verbose=True)

# If you want to cache the token set the "use_cache" flag to True:
# api_access = ApiAccessTokenEndpoint(url, client_id, client_secret, exp_backoff, verbose=True, use_cache=True)

# Get the token.
access_token = api_access.get_token()

# This token can now be used with the API to do other operations.
```

The exponential backoff object is used for retrying token access provisioning in
case of initial failures.
