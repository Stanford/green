import re

import requests


class MaIS_API():

    def __init__(
            self,
            base_url: str,
            cert_path: str,
            key_path: str,
            timeout: float=15.0
    ):
        """

        You will need a public/private key-pair in the form of a certificate
        and a private key.

        cert_path: path to the file containing the certificate.
        key_path:  path to the file containing the private key.
        """
        self.base_url = re.sub(r"/+$", "", base_url) # strip trailing slashes.

        self.cert_path = cert_path
        self.key_path  = key_path

        self.timeout  = timeout

    def make_url(self, url_suffix: str) -> str:
        """Concatenate the base_url with the url_suffix"""
        return f"{self.base_url}/{url_suffix}"

    def make_request(self, method: str, url_suffix: str):
        full_url = self.make_url(url_suffix)

        # Use a context for session because setting the client certs
        # outside of a session makes all other HTTP requests use that
        # client cert.
        with requests.session() as http_session:
            http_session.cert = (self.cert_path, self.key_path)

            # We want a JSON response.
            headers = {'Accept': 'application/json'}
            http_session.headers = headers

            response = http_session.request(
                method,
                full_url,
                timeout=self.timeout
            )

            return response

    def GET(self, url_suffix: str) -> requests.Response:
        """Do a GET on the URL suffix."""
        return self.make_request('GET', url_suffix)

    def PUT(self, url_suffix: str) -> requests.Response:
        """Do a PUT on the URL suffix."""
        return self.make_request('PUT', url_suffix)

    def DELETE(self, url_suffix: str) -> requests.Response:
        """Do a DELETE on the URL suffix."""
        return self.make_request('DELETE', url_suffix)

