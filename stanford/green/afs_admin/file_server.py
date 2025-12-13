
class AFSFileServerPartition:
    """
    name: typically something like "/vicepa" or "/vicepb".
    """
    name: str

class AFSFileServer:
    """
    sdfljk

    """

    fqdn:       str
    ip_address: str
    port:       int
    partitions: list[AFSPartition]

