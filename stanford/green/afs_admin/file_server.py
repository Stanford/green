from dataclasses import dataclass

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
    fqdn:       str
    ip_address: str
    port:       int
    guid:       Optional[str]
