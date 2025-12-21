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

    def get_info(self):
        """Returns the size and used (in KB).
        """
        pass

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

    def identifier(self) -> str:
        """Returns the best "name" for this file server.

        Returns the first of fqdn, uuid, or ip_address that is not None.
        If all three are None raises a ValueError.
        """
        if (self.fqdn is not None):
            return self.fqdn
        elif (self.uuid is not None):
            return self.uuid
        elif (self.ip_address is not None):
            return self.ip_address
        else:
            msg = "cannot return a server identifier as all of fqdn, ip_addres, and uuid are None"
            raise ValueError(msg)
