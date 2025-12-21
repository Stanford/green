from __future__ import annotations

import yaml

from dataclasses import dataclass, asdict

from typing import Optional

@dataclass
class AFSFileServerPartition:
    """
    name: typically something like "/vicepa" or "/vicepb".
    """
    name: str

@dataclass
class AFSFileServer:
    """Represents an AFS File Server.

    """
    fqdn:       Optional[str]
    ip_address: Optional[str]
    port:       int
    uuid:       Optional[str]  # Non-existent file servers will have UUID None

    def to_yaml(self) -> str:
        my_dict = asdict(self)

        yaml_string = yaml.dump(my_dict, sort_keys=True)
        return yaml_string

    @staticmethod
    def fqdn_to_file_server(file_servers: list[AFSFileServer]) -> dict[str, AFSFileServer]:
        """Returns a dict mapping fqdn to AFSFileServer

        Any file_server in the `file_servers` parameter that has no
        fqdn is skipped.
        """
        fqdn_to_file_server = {}
        for file_server in file_servers:
            if (file_server.fqdn is not None):
                fqdn_to_file_server[file_server.fqdn] = file_server

        return fqdn_to_file_server
