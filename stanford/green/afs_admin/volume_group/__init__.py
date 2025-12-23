from __future__ import annotations

import yaml

from dataclasses import dataclass, asdict

from stanford.green.afs_admin.runner import GreenAFSNoRunnerError
from stanford.green.afs_admin.runner import Runner

from stanford.green.afs_admin.volume import Volume

from typing import Optional, Tuple

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
            runner:    Optional[Runner] = None
    ):

        self.header     = header
        self.readwrite  = readwrite
        self.backup     = backup
        self.replicas   = replicas

        self.runner     = runner

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

    def get_runner(self) -> Runner:
        """Return self.runner, raising the ??? error if not runner is defined.
        """
        if (not self.runner):
            msg = "no Runner has been defined for this object"
            raise GreenAFSNoRunnerError(msg)

        return self.runner

    def refresh(self) -> None:
        """Refresh the data in this VolumeGroup.
        """
        runner = self.get_runner()

        (readwrite, backup, replicas) = \
            VolumeGroup.make_volume_group_volumes(
                runner,
                self.readwrite.volume_id,
                header=self.header

            )

        self.readwrite = readwrite
        self.backup    = backup
        self.replicas  = replicas

        return


    @staticmethod
    def make_volume_group_header(runner: Runner, volume_name_or_id: str|int) \
            -> VolumeGroupHeader:
        """Create a VolumeGroupHeader from a volume name or id."""

        vos_examine_string = runner.run_vos_examine(volume_name_or_id)
        lines = vos_examine_string.splitlines()

        # We don't need the all_sites attributes at this point, only the
        # header attributes.
        header_attributes, _ = Volume.parse_volume_lines(lines)

        assert(header_attributes['groupName'] is not None)
        assert(header_attributes['rwrite']    is not None)

        group_name = header_attributes['groupName']
        id_rwrite  = int(header_attributes['rwrite'])

        # Normalize the header attributes so that their type is correct
        # and replace any '0's with None.
        ids = ['ronly', 'backup', 'rclone']
        optional_header_attributes: dict[str, int | None] = {}

        for id1 in ids:
            value = header_attributes[id1]
            if (value is  None):
                optional_header_attributes[id1] = None
            elif ((value is not None) and (str(value.strip()) == '0')):
                optional_header_attributes[id1] = None
            else:
                optional_header_attributes[id1] = int(value)

        vgroup_header = VolumeGroupHeader(
            group_name=group_name,
            id_rwrite=id_rwrite,
            id_ronly=optional_header_attributes['ronly'],
            id_rclone=optional_header_attributes['rclone'],
            id_backup=optional_header_attributes['backup'],
        )

        return vgroup_header

    @staticmethod
    def make_volume_group_volumes(
            runner: Runner,
            volume_name_or_id: str|int,
            header: Optional[VolumeGroupHeader]=None
    ) -> Tuple[Volume, Optional[Volume], list[Volume]]:
        """Create the volumes that go in a VolumeGroup object.

        Returns the Tuple (read/write volume, backup volume, replica volume(s))

        """
        ## Step 1. Create the VolumeGroupHeader (if not provided).
        if (not header):
            header = VolumeGroup.make_volume_group_header(runner, volume_name_or_id)

        ## Step 2a. Create the RW volume.
        if (header.id_rwrite is None):
            msg = "cannot have the id_rwrite value be None"
            raise ValueError(msg)

        volumes   = Volume.create_volume_objects(runner, str(header.id_rwrite))
        readwrite = volumes[0]

        ## Step 2b. Create the BK volume.
        if (header.id_backup is None):
            backup = None
        else:
            volumes = Volume.create_volume_objects(runner, str(header.id_backup))
            backup  = volumes[0]

        ## Step 2c. Create the RO volume(s).
        if (header.id_ronly is None):
            replicas = []
        else:
            volumes  = Volume.create_volume_objects(runner, str(header.id_ronly))
            replicas = volumes

        return (readwrite, backup, replicas)


    @staticmethod
    def make_volume_group_object(runner: Runner, volume_name_or_id: str|int) -> VolumeGroup:
        """Create a VolumeGroup from a volume name or id.
        """
        header = VolumeGroup.make_volume_group_header(runner, volume_name_or_id)

        (readwrite, backup, replicas) = \
            VolumeGroup.make_volume_group_volumes(
                runner,
                volume_name_or_id,
                header=header
            )

        return VolumeGroup(
            header=header,
            readwrite=readwrite,
            backup=backup,
            replicas=replicas,
        )
