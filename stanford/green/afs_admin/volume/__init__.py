"""The Volume class models an AFS volume.

--------
Overview
--------

The stanford.green.afs_admin.volume.Volume class models an AFS
volume.

--------
Examples
--------

More...

"""

from __future__ import annotations

import yaml

from dataclasses import dataclass, asdict
from datetime    import datetime, timezone

from stanford.green.afs_admin.file_server import AFSFileServer
from stanford.green.afs_admin.runner      import Runner
from stanford.green.afs_admin.runner      import GreenAFSNoRunnerError
from stanford.green.afs_admin.volume_type import AFSVolumeType

# Typing
from typing import Tuple, Optional
AttributeDict = dict[str, str | None]

@dataclass(kw_only=True)
class Volume:
    """A class representing an AFS volume.

    name: the name of the volume

    volume_id: although this is a number we represent it a string in case it
             any leading zeros (?)

    id_rwrite: the volume ID number of the read/write volume

    id_ronly: the volume ID number of any read-only replicas (all read-only
              replicas share the same volume ID number). Not every AFSVolume
              has read-only replicas.


    diskused:  the used value (in KB),

    """
    runner: Optional[Runner] = None

    volume_type: AFSVolumeType

    name:       str

    file_server: AFSFileServer

    partition:  str

    volume_id: int

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

    def get_runner(self) -> Runner:
        """Return self.runner, raising the ??? error if not runner is defined.
        """
        if (not self.runner):
            msg = "no Runner has been defined for this object"
            raise GreenAFSNoRunnerError(msg)

        return self.runner


    @staticmethod
    def create_volume_objects(runner: Runner, volume_name_or_id: str) -> list[Volume]:
        """Create a Volume object from the volume's name or id.

        If the volume corresponding to volume_name_or_id does not exist
        will raise an exception.
        """
        vos_examine_output = runner.run_vos_examine(volume_name_or_id)
        return Volume.vos_examine_to_volume(runner, vos_examine_output)

    @staticmethod
    def vos_examine_to_volume(runner: Runner, vos_examine_str: str) -> list[Volume]:
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

        # For a Volume object we don't use the header_attributes.
        _, all_sites = Volume.parse_volume_lines(lines)

        ## For each site return a Volume object.
        all_volumes = []
        for site_attributes in all_sites:
            volume = Volume.volume_from_site(runner, site_attributes)
            all_volumes.append(volume)

        return all_volumes

    @staticmethod
    def volume_from_site(runner: Runner, site_attributes: AttributeDict) -> Volume:

        # To make myp happy as well as to do some basic sanity checks,
        # verify that some of the values of site_attributes are not None.
        assert(site_attributes['id'] is not None)
        assert(site_attributes['serv'] is not None)
        assert(site_attributes['creationDate'] is not None)
        assert(site_attributes['accessDate'] is not None)
        assert(site_attributes['updateDate'] is not None)
        assert(site_attributes['backupDate'] is not None)
        assert(site_attributes['copyDate'] is not None)
        assert(site_attributes['diskused'] is not None)
        assert(site_attributes['maxquota'] is not None)
        assert(site_attributes['filecount'] is not None)

        ## volume type
        raw_type    = site_attributes['type']
        if (raw_type is not None):
            volume_type = AFSVolumeType.infer_type(raw_type)
        else:
            volume_type = None

        ## Server attributes
        # serv    171.67.22.15    afssvr05.stanford.edu:7005      b4263ced-74f0-436a-8384-7a37f342d424
        file_server = AFSFileServer.serv_line_to_file_server(site_attributes['serv'], runner)

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
                return datetime.fromtimestamp(int(epoch), tz=timezone.utc)
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
            'name':       site_attributes['name'],
            'volume_id':  int(site_attributes['id']),
            #
            'file_server': file_server,
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

    @staticmethod
    def parse_volume_lines(lines: list[str]) -> Tuple[AttributeDict, list[AttributeDict]]:
        """Parse a list of raw output lines and return header and all_sites

        Given a list of lines from "vos examine" or "vos listfs" return
        the header attributes and an array of site_attributes.

        Note that the output of "vos listfs" does not contain any group header
        information so this function will return the empty dict for header
        attributes in that case.
        """

        # ###         # ###         # ###         # ###         # ###
        def is_first_site_key(key: str) -> bool:
            if (key == 'name'):
                return True
            else:
                return False
        # ###         # ###         # ###         # ###         # ###

        # Iterate over the lines.
        header_attributes:       AttributeDict = {}
        current_site_attributes: AttributeDict = {}
        all_sites                              = []

        for line in lines:
            try:
                key, value = line.split(None, 1)
            except Exception as excp:
                msg = f"problem parsing line '{line}': {excp}"
                raise ValueError(msg)

            key = key.strip()

            if (Volume.is_header_field(key)):
                # This is a header line.
                header_attributes[key] = value.strip()

                # Convert any header of '0' to None
                if (str(header_attributes[key]) == '0'):
                    header_attributes[key] = None
            elif (Volume.is_site_field(key)):
                # This is a site line.
                if (is_first_site_key(key)):
                    # We are in a NEW site.
                    if (current_site_attributes):
                        all_sites.append(current_site_attributes)
                        current_site_attributes = {}

                current_site_attributes[key] = value.strip()
            else:
                # This is neither a header or site line.
                if (current_site_attributes):
                    all_sites.append(current_site_attributes)
                    current_site_attributes = {}

        # In case we have not appended the last site, do so now.
        if (current_site_attributes):
            all_sites.append(current_site_attributes)
            current_site_attributes = {}

        return (header_attributes, all_sites)


    @staticmethod
    def is_header_field(field: str) -> bool:
        header_fields = [
            'groupName',
            'rwrite',
            'ronly',
            'backup',
            'rclone',
        ]
        return field in header_fields

    @staticmethod
    def is_site_field(field: str) -> bool:
        site_fields = [
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
        return field in site_fields

    @staticmethod
    def non_none_fields() -> list[str]:
        """Return an array of fields that should never be empty (None).
        """
        never_none_fields = [
            'name',
            'id',
            'serv',
            'part',
            'status',
            'parentID',
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
            'filecount',
            'dayUse',
            'weekUse',
            'volUpdateCounter',
        ]
        return never_none_fields


@dataclass(kw_only=True)
class BrokenVolume:
    """A class representing an AFS volume with incomplete information.

    Use this class to store AFS volume attributes for a volume that is
    "broken", for example, one that is missing a volume id or name.

    All attributes are Optional.

    """

    volume_type: Optional[AFSVolumeType] = None
    name:        Optional[str] = None
    file_server: Optional[AFSFileServer] = None
    partition:   Optional[str] = None
    volume_id:   Optional[int] = None

    def to_dict(self) -> dict:
        my_dict = asdict(self)
        return my_dict

    def to_yaml(self) -> str:
        my_dict = self.to_dict()

        # "Fix" some of the values
        if (my_dict['volume_type'] is not None):
            my_dict['volume_type'] = str(my_dict['volume_type'])

        yaml_string = yaml.dump(my_dict, sort_keys=True)
        return yaml_string
