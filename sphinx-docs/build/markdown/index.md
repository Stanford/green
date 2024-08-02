<!-- stanford-green documentation master file, created by
sphinx-quickstart on Mon Jul 29 16:58:49 2024.
You can adapt this file completely to your liking, but it should at least
contain the root `toctree` directive. -->

# stanford-green documentation

# Contents:

* [stanford.green Modules](modules.md)
  * [stanford.green](modules/base.md)
    * [`random_uid()`](modules/base.md#stanford.green.random_uid)
    * [`utc_datetime_secs_from_now()`](modules/base.md#stanford.green.utc_datetime_secs_from_now)
  * [stanford.green.oauth2](modules/oauth2.md)
    * [Overview](modules/oauth2.md#overview)
    * [`AccessToken`](modules/oauth2.md#stanford.green.oauth2.AccessToken)
      * [`AccessToken.expires_at`](modules/oauth2.md#stanford.green.oauth2.AccessToken.expires_at)
      * [`AccessToken.expires_in()`](modules/oauth2.md#stanford.green.oauth2.AccessToken.expires_in)
      * [`AccessToken.is_expired()`](modules/oauth2.md#stanford.green.oauth2.AccessToken.is_expired)
      * [`AccessToken.zulu_time_string()`](modules/oauth2.md#stanford.green.oauth2.AccessToken.zulu_time_string)
    * [`ApiAccessTokenEndpoint`](modules/oauth2.md#stanford.green.oauth2.ApiAccessTokenEndpoint)
      * [`ApiAccessTokenEndpoint._get_token()`](modules/oauth2.md#stanford.green.oauth2.ApiAccessTokenEndpoint._get_token)
      * [`ApiAccessTokenEndpoint._get_token_acs_api()`](modules/oauth2.md#stanford.green.oauth2.ApiAccessTokenEndpoint._get_token_acs_api)
      * [`ApiAccessTokenEndpoint._get_token_oauth2()`](modules/oauth2.md#stanford.green.oauth2.ApiAccessTokenEndpoint._get_token_oauth2)
      * [`ApiAccessTokenEndpoint.cache_get()`](modules/oauth2.md#stanford.green.oauth2.ApiAccessTokenEndpoint.cache_get)
      * [`ApiAccessTokenEndpoint.cache_set()`](modules/oauth2.md#stanford.green.oauth2.ApiAccessTokenEndpoint.cache_set)
      * [`ApiAccessTokenEndpoint.get_token()`](modules/oauth2.md#stanford.green.oauth2.ApiAccessTokenEndpoint.get_token)
      * [`ApiAccessTokenEndpoint.is_acs_api()`](modules/oauth2.md#stanford.green.oauth2.ApiAccessTokenEndpoint.is_acs_api)
      * [`ApiAccessTokenEndpoint.is_oauth2()`](modules/oauth2.md#stanford.green.oauth2.ApiAccessTokenEndpoint.is_oauth2)
      * [`ApiAccessTokenEndpoint.progress()`](modules/oauth2.md#stanford.green.oauth2.ApiAccessTokenEndpoint.progress)
  * [stanford.green.zulutime](modules/zulutime.md)
    * [`dt_to_zulu_string()`](modules/zulutime.md#stanford.green.zulutime.dt_to_zulu_string)
    * [`is_zulu_string()`](modules/zulutime.md#stanford.green.zulutime.is_zulu_string)
    * [`zulu_string_to_utc()`](modules/zulutime.md#stanford.green.zulutime.zulu_string_to_utc)
