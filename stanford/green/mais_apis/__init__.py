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

    def GET(self, url_suffix: str) -> requests.Response:
        """Do a GET on the URL suffix."""
        full_url = self.make_url(url_suffix)

        # We want a JSON response.
        headers = {'Accept': 'application/json'}

        # Set up the certificate paths
        keypair_paths = (self.cert_path, self.key_path)

        response = requests.get(
            full_url,
            cert=keypair_paths,
            headers=headers,
            timeout=self.timeout
        )
        return response

    def PUT(self, url_suffix: str) -> requests.Response:
        """Do a PUT on the URL suffix."""
        full_url = self.make_url(url_suffix)

        # We want a JSON response.
        headers = {'Accept': 'application/json'}

        # Set up the certificate paths
        keypair_paths = (self.cert_path, self.key_path)

        response = requests.put(
            full_url,
            cert=keypair_paths,
            headers=headers,
            timeout=self.timeout
        )

        return response

    def DELETE(self, url_suffix: str) -> requests.Response:
        """Do a DELETE on the URL suffix."""
        full_url = self.make_url(url_suffix)

        # We want a JSON response.
        headers = {'Accept': 'application/json'}

        # Set up the certificate paths
        keypair_paths = (self.cert_path, self.key_path)

        response = requests.delete(
            full_url,
            cert=keypair_paths,
            headers=headers,
            timeout=self.timeout
        )

        return response

