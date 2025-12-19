from __future__ import annotations

import copy
import yaml

from dataclasses import dataclass, asdict
from datetime    import datetime

from stanford.green.afs_admin.volume_type import AFSVolumeType

from typing import Optional, cast
AttributeDict = dict[str, str]


@dataclass(kw_only=True)
class VolumeHeader:
    group_name: str            # The volume group name (same as RW name)
    id_rwrite:  str            # The RW id is mandatory.
    id_ronly:   Optional[str]  # All RO copies of a RW volume have the same id.
    id_backup:  Optional[str]  # Not every RW volume will have a backup.
    id_rclone:  Optional[str]  # Only non-None if there is a clone operation in progress.

@dataclass(kw_only=True)
class Volume:
    """A class representing an AFS volume.

    This class represents an AFS volume together with its backup (if it
    has one) and any read-only clones.

    name: the name of the volume

    volume_id: although this is a number we represent it a string in case it
             any leading zeros (?)

    id_rwrite: the volume ID number of the read/write volume

    id_ronly: the volume ID number of any read-only replicas (all read-only
              replicas share the same volume ID number). Not every AFSVolume
              has read-only replicas.


    diskused:  the used value (in KB),

    """
    header: VolumeHeader

    volume_type: AFSVolumeType

    name:       str

    server:     str
    uuid:       str
    ip_address: str
    port:       int
    partition:  str

    volume_id: str

    in_use:    bool

    created_at:        datetime
    last_accessed_at:  datetime
    last_updated_at:   datetime
    last_backed_up_at: datetime
    copied_at:         datetime

    disk_used_kb: int
    max_quota_kb: int
    file_count:   int

    def to_dict(self) -> dict:
        my_dict = asdict(self)
        return my_dict

    def to_yaml(self) -> str:
        my_dict = self.to_dict()

        # "Fix" some of the values
        my_dict['volume_type'] = str(my_dict['volume_type'])

        yaml_string = yaml.dump(my_dict, sort_keys=True)
        return yaml_string

    @staticmethod
    def vos_examine_to_volume(vos_examine_str: str) -> list[Volume]:
        """Given the output of a "vos examine VOLUME -format" return AFSVolume object(s).

        For a RW or BK volume the vos_examine_str should look like this:

           groupName    users.a.e
           rwrite       2003261873
           ronly        2003261874
           backup       2003261875
           rclone       0
           name         users.a.e.backup
           ...
           spare3       0 (Optional)
           site_count   4
           ...

        For RO volumes the vos_examine_str should look like this:

           groupName    users.a.e
           rwrite       2003261873
           ronly        2003261874
           backup       2003261875
           rclone       0
           name         users.a.e.readonly
           ...
           spare3       0 (Optional)
           name         users.a.e.readonly
           ...
           spare3       0 (Optional)
           .
           .
           .
           site_count   4
           ...


        The vos_examine_str string has three sections.

        1. The "header" the first five lines ("groupName" through "rclone").

        2. One or more "sites": the lines "name" thruogh "spare3". Note that only
           a RO volume will have more than one site section.

        3. The "footer": everything after the last site section. We ignore
           this section.

        """

        # Convert the string into a sequence of lines.
        lines = vos_examine_str.strip().split("\n")

        # ###         # ###         # ###         # ###         # ###
        def is_header(key: str) -> bool:
            header_keys = [
                'groupName',
                'rwrite',
                'ronly',
                'backup',
                'rclone',
            ]
            return key in header_keys

        def is_site(key: str) -> bool:
            site_keys = [
                'name',
                'id',
                'serv',
                'part',
                'status',
                'backupID',
                'parentID',
                'cloneID',
                'inUse',
                'needsSalvaged',
                'destroyMe',
                'type',
                'creationDate',
                'accessDate',
                'updateDate',
                'backupDate',
                'copyDate',
                'flags',
                'diskused',
                'maxquota',
                'minquota',
                'filecount',
                'dayUse',
                'weekUse',
                'volUpdateCounter',
                'spare3',
            ]
            return key in site_keys

        def is_first_site_key(key: str) -> bool:
            if (key == 'name'):
                return True
            else:
                return False
        # ###         # ###         # ###         # ###         # ###

        # Iterate over the lines.
        header_attributes:       AttributeDict = {}
        current_site_attributes: AttributeDict = {}
        all_sites = []

        for line in lines:
            try:
                key, value = line.split(None, 1)
            except Exception as excp:
                msg = f"problem parsing line '{line}': {excp}"
                raise ValueError(msg)

            key = key.strip()

            if (is_header(key)):
                header_attributes[key] = value.strip()
            elif (is_site(key)):
                if (is_first_site_key(key)):
                    # We are in a NEW site.
                    if (current_site_attributes):
                        all_sites.append(current_site_attributes)
                        current_site_attributes = {}

                current_site_attributes[key] = value.strip()
            else:
                if (current_site_attributes):
                    all_sites.append(current_site_attributes)
                    current_site_attributes = {}

        ## For each site return a Volume object.
        all_volumes = []
        for site_attributes in all_sites:
            volume = Volume.volume_from_site(header_attributes, site_attributes)
            all_volumes.append(volume)

        return all_volumes

    @staticmethod
    def volume_from_site(header_attributes: AttributeDict, site_attributes: AttributeDict) -> Volume:

        ## Header attributes.
        ids = ['rwrite', 'ronly', 'backup', 'rclone']
        my_header_attributes = cast(dict[str, str | None], copy.deepcopy(header_attributes))
        for id1 in ids:
            value = my_header_attributes[id1]
            if ((value is not None) and (str(value.strip()) == '0')):
                my_header_attributes[id1] = None

        assert(my_header_attributes['groupName'] is not None)
        assert(my_header_attributes['rwrite'] is not None)

        header = VolumeHeader(
            group_name=my_header_attributes['groupName'],
            id_rwrite=my_header_attributes['rwrite'],
            id_ronly=my_header_attributes['ronly'],
            id_rclone=my_header_attributes['rclone'],
            id_backup=my_header_attributes['backup'],
        )

        ## volume type
        raw_type = site_attributes['type']

        if (raw_type == 'RW'):
            volume_type = AFSVolumeType.RW
        elif (raw_type == 'RO'):
            volume_type = AFSVolumeType.RO
        elif (raw_type == 'BK'):
            volume_type = AFSVolumeType.BK
        else:
            msg = f"could not interpret volume type '{raw_type}'"
            raise ValueError(msg)

        ## Server attributes
        # serv    171.67.22.15    afssvr05.stanford.edu:7005      b4263ced-74f0-436a-8384-7a37f342d424
        ip_address, fqdn_port, uuid = site_attributes['serv'].split()

        # split server into name and port
        fqdn, port = fqdn_port.split(':')


        ## in use.
        if (site_attributes['inUse'] == 'Y'):
            in_use = True
        else:
            in_use = False

        ## Dates.
        # ## #        # ## #        # ## #        # ## #        # ## #
        def examine_date_to_dt(examine_time_str: str) -> datetime | None :
            epoch, date_string = examine_time_str.split(None, 1)
            if (int(epoch) == 0):
                return None
            else:
                return datetime.fromtimestamp(int(epoch))
        # ## #        # ## #        # ## #        # ## #        # ## #

        created_at        = examine_date_to_dt(site_attributes['creationDate'])
        last_accessed_at  = examine_date_to_dt(site_attributes['accessDate'])
        last_updated_at   = examine_date_to_dt(site_attributes['updateDate'])
        last_backed_up_at = examine_date_to_dt(site_attributes['backupDate'])
        copied_at         = examine_date_to_dt(site_attributes['copyDate'])

        ## Storage amounts.
        disk_used_kb = int(site_attributes['diskused'])
        max_quota_kb = int(site_attributes['maxquota'])
        file_count   = int(site_attributes['filecount'])

        ###
        ### Step 2. Map the attributes to the parameters.
        params = {
            'header': header,
            #
            'name':       site_attributes['name'],
            'volume_id':  site_attributes['id'],
            #
            'server':     fqdn,
            'ip_address': ip_address,
            'port':       int(port),
            'uuid':       uuid,
            #
            'partition':   site_attributes['part'],
            'in_use':      in_use,
            'volume_type': volume_type,
            #
            'created_at':        created_at,
            'last_accessed_at':  last_accessed_at,
            'last_updated_at':   last_updated_at,
            'last_backed_up_at': last_backed_up_at,
            'copied_at':         copied_at,
            #
            'disk_used_kb': disk_used_kb,
            'max_quota_kb': max_quota_kb,
            'file_count':   file_count,
        }

        afs_volume = Volume(**params)  # type: ignore

        return afs_volume


@dataclass(kw_only=True)
class RWVolume(Volume):
    """A class representing a RW (read/write) AFS volume.

    """

    volume_type: AFSVolumeType = AFSVolumeType.RW


@dataclass(kw_only=True)
class ROVolumes(Volume):
    """A class representing the set of RO (read-only AFS volumes associated with a RW volume.

    Note the 's' in 'ROVolumes'. This is because it is often the case that
    if a RW volume has a clone it has more than once.
    """

    volume_type: AFSVolumeType = AFSVolumeType.RO
