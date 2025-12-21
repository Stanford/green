import yaml

from dataclasses import dataclass, asdict

from stanford.green.afs_admin.volume import Volume

from typing import Optional

@dataclass(kw_only=True)
class VolumeGroupHeader:
    group_name: str            # The volume group name (same as RW name)
    id_rwrite:  int            # The RW id is mandatory.
    id_ronly:   Optional[int]  # All RO copies of a RW volume have the same id.
    id_backup:  Optional[int]  # Not every RW volume will have a backup.
    id_rclone:  Optional[int]  # Only non-None if there is a clone operation in progress.

    def to_yaml(self) -> str:
        my_dict = asdict(self)

        yaml_string = yaml.dump(my_dict, sort_keys=True)
        return yaml_string

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
            header:    VolumeGroupHeader,
            readwrite: Volume,
            backup:    Optional[Volume] = None,
            replicas:  list[Volume] = [],
    ):

        self.header     = header
        self.readwrite  = readwrite
        self.backup     = backup
        self.replicas   = replicas

    def __str__(self) -> str:

        rv = ''

        separator = '-----------'

        rv += "Group Information\n"
        rv += separator + "\n"
        rv += self.header.to_yaml()
        rv += "\n"

        rv += "RW volume\n"
        rv += separator + "\n"
        rv += self.readwrite.to_yaml()
        rv += "\n"

        rv += "BK volume\n"
        rv += separator + "\n"
        if (self.backup is not None):
            rv += self.backup.to_yaml()
        else:
            rv += 'None'
        rv += "\n"

        counter = 0
        for volume in self.replicas:
            counter = counter + 1

            rv += f"RO volume {counter}\n"
            rv += separator + "\n"
            rv += volume.to_yaml()
            rv += "\n"

        return rv.strip()
