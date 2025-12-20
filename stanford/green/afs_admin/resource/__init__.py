import re
import time

from stanford.green.afs_admin.file_server  import AFSFileServer

from stanford.green.afs_admin.volume       import Volume
from stanford.green.afs_admin.volume_group import VolumeGroup
from stanford.green.afs_admin.volume_group import VolumeGroupHeader
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
        """Create a VolumeSet from a volume name or id.
        """

        ## Step 1. Create the volume group header.
        # Get the "vos examine" output for this volume so we can get the
        # header information.
        vos_examine_string = self.command_runner.run_vos_examine(volume_name_or_id)
        lines = vos_examine_string.splitlines()

        # We don't need the all_sites attributes at this point, only the
        # header attributes.
        header_attributes, _ = Volume.parse_volume_lines(lines)

        # Normalize the header attributes so that their type is correct
        # and replace any '0's with None.
        my_header_attributes: dict[str, str | int | None] = {}
        ids = ['groupName', 'rwrite', 'ronly', 'backup', 'rclone']
        for id1 in ids:
            value = header_attributes[id1]
            if (value is  None):
                my_header_attributes[id1] = None
            elif ((value is not None) and (str(value.strip()) == '0')):
                my_header_attributes[id1] = None
            elif (id1 == 'groupName'):
                my_header_attributes[id1] = value
            else:
                my_header_attributes[id1] = int(value)

        assert(my_header_attributes['groupName'] is not None)
        assert(my_header_attributes['rwrite'] is not None)

        vgroup_header = VolumeGroupHeader(
            group_name=my_header_attributes['groupName'],
            id_rwrite=my_header_attributes['rwrite'],
            id_ronly=my_header_attributes['ronly'],
            id_rclone=my_header_attributes['rclone'],
            id_backup=my_header_attributes['backup'],
        )

        ## Step 2a. Create the RW volume.
        if (vgroup_header.id_rwrite is None):
            msg = "cannot have the id_rwrite value be None"
            raise ValueError(msg)

        volumes   = self.create_volume_objects(str(vgroup_header.id_rwrite))
        readwrite = volumes[0]

        ## Step 2b. Create the BK volume.
        if (vgroup_header.id_backup is None):
            backup = None
        else:
            volumes = self.create_volume_objects(str(vgroup_header.id_backup))
            backup  = volumes[0]

        ## Step 2c. Create the RO volume(s).
        if (vgroup_header.id_ronly is None):
            replicas = []
        else:
            volumes  = self.create_volume_objects(str(vgroup_header.id_ronly))
            replicas = volumes

        return VolumeGroup(
            header=vgroup_header,
            readwrite=readwrite,
            backup=backup,
            replicas=replicas,
        )

    def make_file_server_objects(self) -> list[AFSFileServer]:
        """Get the list of FileServer objects
        """
        file_server_list_raw = self.command_runner.run_vos_listfs()

        # Parse the list
        lines = file_server_list_raw.splitlines()

        uuid_rx       = re.compile(r"^UUID:\s+(\S+)\S*$")
        ip_address_rx = re.compile(r"\[((?:[0-9]{1,3}\.){3}[0-9]{1,3})\]")

        next_line_is_server = False

        file_servers = []

        for line in lines:
            if (next_line_is_server):
                server_name, port = line.split(':', 1)
                next_line_is_server = False

                # Is server_name a host name or an ip address?
                match = ip_address_rx.search(server_name)
                if (match):
                    ip_address = match.group(1)
                    fqdn       = None
                else:
                    ip_address = None
                    fqdn       = server_name

                file_server = AFSFileServer(
                    fqdn=fqdn,
                    ip_address=ip_address,
                    port=int(port),
                    uuid=uuid
                    )

                file_servers.append(file_server)

            elif ('UUID' in line):
                # start of entry
                match = re.match(uuid_rx, line)
                if (match):
                    uuid = match.group(1)

                    if (uuid.lower() == 'none'):
                        uuid = None
                    next_line_is_server = True
                else:
                    msg = f"could not parse UUID line {line}"
                    raise Exception(msg)
            else:
                # Any other line we ignore.
                next_line_is_server = False

        return file_servers

    def get_volumes(self, file_server: AFSFileServer) -> list[Volume]:
        """Get the list of FileServer objects
        """
        volumes_list_raw = self.command_runner.run_vos_listvol(file_server)

        # Iterate through the list
        # BEGIN_OF_ENTRY
        # name	class.cs357s.1264
        # id	2009441920
        # serv	171.67.22.26	afssvr01.stanford.edu:7005	57d67d95-b1f5-4eac-a991-0e813219affd
        # part	/vicepa
        # status	OK
        # backupID	2009442064
        # parentID	2009441920
        # cloneID	0
        # inUse	Y
        # needsSalvaged	N
        # destroyMe	N
        # type	RW
        # creationDate	1765923002	Tue Dec 16 14:10:02 2025
        # accessDate	1766219709	Sat Dec 20 00:35:09 2025
        # updateDate	1766120467	Thu Dec 18 21:01:07 2025
        # backupDate	1766065691	Thu Dec 18 05:48:11 2025
        # copyDate	1765923002	Tue Dec 16 14:10:02 2025
        # flags	0	(Optional)
        # diskused	90
        # maxquota	5242880
        # minquota	0	(Optional)
        # filecount	14
        # dayUse	9
        # weekUse	2975	(Optional)
        # volUpdateCounter	507	(Optional)
        # spare3	0	(Optional)
        # END_OF_ENTRY

        lines = volumes_list_raw.splitlines()

        # ###         # ###         # ###         # ###         # ###         # ###
        def begin_entry(line: str) -> bool:
            if (re.match(r'^BEGIN_OF_ENTRY.*$', line)):
                return True
            else:
                return False

        def end_entry(line: str) -> bool:
            if (re.match(r'^END_OF_ENTRY.*$', line)):
                return True
            else:
                return False

        # ###         # ###         # ###         # ###         # ###         # ###
        inside_entry = False
        bundle_lines = []
        for line in lines:
            if (begin_entry(line)):
                inside_entry = True
            elif (end_entry(line)):
                print("finished bundle")
                inside_entry = False
                _, all_sites = Volume.parse_volume_lines(bundle_lines)

                site_attributes = all_sites[0]
                print(f"SSSS {site_attributes}")
                time.sleep(30)

                bundle_lines = []
                pass
            elif (inside_entry):
                bundle_lines.append(line)
            else:
                # Not inside an entry, so skip.
                pass
