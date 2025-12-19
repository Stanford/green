from stanford.green.afs_admin.volume import Volume

from typing import Optional

class VolumeGroup:
    """Represents a a volume group

    A "volume group" is a RW volume together with its BK (backup) volume
    and any RO (read-only) replicas. Note that there might be no BK or RO
    volumes.

    A volume group is defined by its "groupname" which is the name or
    volume id of the RW volume.

    """
    def __init__(
            self,
            group_name: str,
            readwrite: Volume,
            backup:    Optional[Volume] = None,
            replicas:  list[Volume] = [],
    ):

        self.group_name = group_name
        self.readwrite  = readwrite
        self.backup     = backup
        self.replicas   = replicas

    def __str__(self) -> str:

        rv = ''

        separator = '-----------'

        rv += 'RW volume'
        rv += separator
        rv += self.readwrite.to_yaml()

        rv += 'BK volume'
        rv += separator
        rv += self.backup.to_yaml()

        counter = 0
        for volume in self.replicas:
            counter = counter + 1

            rv += f"RO volume {counter}"
            rv += separator
            rv += volume.to_yaml()

        return rv
