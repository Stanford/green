from enum        import Enum
from dataclasses import dataclass

class AFSSiteType(Enum):
    RW = 1
    RO = 2

class AFSSiteState(Enum):
    new = 1
    old = 2


class VolumeID:
    def __init__(self,
                 volume_id: str
                 ):
    volume_id = self.volume_id


class AFSSite:
    """
    sflksdf
    """

    def __init__(self,
                 file_server: AFSFileServer,
                 partition:   AFSFileServerPartition,
                 site_type:   AFSSiteType,
                 site_state:  AFSSiteState,
                 ):

    file_server: self.file_server
    partition:   self.partition
    site_type:   self.site_type
    site_state:  self.site_state


@dataclass
class AFSVolume:
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


  id_rclone: rclone volume ID number,
  id_backup: backup volume ID number,



  diskused:  the used value (in KB),

    """

    name:      str
    server:    str
    partition: str
    volume_id: str

  sites: list[AFSSite]

  id_rwrite: VolumeID
  id_ronly:  ronly volume ID number,
  "id_rclone": rclone volume ID number,
  "id_backup": backup volume ID number,
  "diskused": the used value (in KB),
  "quota": the quota (in KB),
  "created_at": epoch timestamp (UTC),
  "last_updated_at": epoch timestamp (UTC),
  "last_accessed_at": epoch timestamp (UTC),
  "access_count_today": number accesses since midnight or since last moved,
  "exists": true,
  "online": true/false,




}
