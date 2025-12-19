from stanford.green.afs_admin.volume       import Volume
from stanford.green.afs_admin.volume_group import VolumeGroup
from stanford.green.afs_admin.volume_type  import AFSVolumeType

from stanford.green.afs_admin.resource.command_runner import CommandRunner

from typing import Self


class AFSResourceManager:
    def __init__(self, command_runner:CommandRunner):
        self.command_runner = command_runner

    def create_volume_objects(self, volume_name_or_id: str) -> list[Volume]:
        """Create a Volume object from the volume's name or id.

        If the volume corresponding to volume_name_or_id does not exist
        will raise an exception.
        """
        vos_examine_output = self.command_runner.run_vos_examine(volume_name_or_id)
        return Volume.vos_examine_to_volume(vos_examine_output)

#    def create_volume_group_object(self, volume_name_or_id: str) -> VolumeGroup:
#        """Create a VolumeGroup object from one of the volumes' name or id.
#
#        You can use the name/id of any volume in the volume group (RW, BK, or RO).
#        """
#        volumes = self.create_volume_objects(volume_name_or_id)
#        return VolumeGroup.make_volume_group(volumes)

    def make_volume_group_object(self, volume_name_or_id: str) -> Self:
        """Create a VolumeSet from volumes.

        The parameter `volumes` must be either a RW or BK volume, or the
        complete set of RO volumes.
        """

        volumes = self.create_volume_objects(volume_name_or_id)

        volume0 = volumes[0]
        header  = volume0.header

        # Step 1. Get the group name and volume type.
        group_name  = header.group_name
        volume_type = volume0.volume_type

        # ### #        # ### #        # ### #        # ### #        # ### #        # ### #
        def get_bu_volume():
            id_backup = header.id_backup
            if (id_backup is not None):
                volumes = self.create_volume_objects(id_backup)
                backup = volumes[0]
            else:
                backup = None

            return backup

        def get_ro_volumes():
            id_ronly = header.id_ronly
            if (id_ronly is not None):
                ronly_volumes = self.create_volume_objects(id_ronly)
            else:
                ronly_volumes = []

            return ronly_volumes

        def get_rw_volume():
            id_rwrite = header.id_rwrite
            if (id_rwrite is None):
                msg = "cannot have the id_rwrite value be None"
                raise ValueError(msg)

            volumes = self.create_volume_objects(id_rwrite)
            rwrite = volumes[0]

            return rwrite
        # ### #        # ### #        # ### #        # ### #        # ### #        # ### #


        # Step 2. volumes is one of RW, BK, or RO.
        match volume_type:
            case AFSVolumeType.RW:
                readwrite = volume0

                # Get the BK and RO volumes
                backup   = get_bu_volume()
                replicas = get_ro_volumes()
            case AFSVolumeType.BK:
                backup = volume0

                # Get the RW and RO volumes
                readwrite = get_rw_volume()
                replicas  = get_ro_volumes()
            case AFSVolumeType.RO:
                replicas = volumes

                # Get the RW and BK volumes
                readwrite = get_rw_volume()
                backup    = get_bu_volume()
            case _:
                msg = "programming error?!?"
                raise ValueError(msg)

        # Step 2. Get the BK volume.

        # Step 3. Get the RO replicas.

        return VolumeGroup(
            group_name=group_name,
            readwrite=readwrite,
            backup=backup,
            replicas=replicas,
            )
