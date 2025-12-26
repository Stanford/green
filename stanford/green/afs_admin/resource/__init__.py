import datetime
import logging
import pathlib
import re
import tempfile

### stanford.green.afs_admin imports
from ..file_server           import AFSFileServer
from ..file_server.partition import AFSFileServerPartition

from ..runner import Runner

from ..volume_type import AFSVolumeType

from ..volume import Volume
from ..volume import BrokenVolume

from ..utility import volume_base_name
### end of stanford.green.afs_admin imports

# Typing
from typing import Tuple

logger = logging.getLogger(__name__)


class AFSResourceManager:
    def __init__(self, runner: Runner, verbose: bool=False):
        self.runner  = runner
        self.verbose = verbose

    @staticmethod
    def get_timestamp() -> str:
        # From ChatGPT
        now = datetime.datetime.now()

        # Format: YYYY-MM-DD HH:MM:SS.S  (S = tenths of a second)
        time_str = now.strftime('%Y-%m-%d %H:%M:%S.') + str(int(now.microsecond / 100000))
        return time_str

    def progress(self, msg: str) -> None:
        if (self.verbose):
            time_str = AFSResourceManager.get_timestamp()
            msg = f"[progress] [{time_str}] {msg}"
            print(msg)

        return

    def get_volumes_on_server(
            self,
            file_server: AFSFileServer,
            rx: str = r'^.*$',
            rx_all: bool = False
    ) -> Tuple[list[Volume], list[BrokenVolume]]:

        good_volumes   = []
        broken_volumes = []

        for partition in file_server.partitions:
            good_volumes_current, broken_volumes_current = \
                self.get_volumes_on_partition(
                    file_server,
                    partition,
                    rx=rx,
                    rx_all=rx_all
                )

            good_volumes   += good_volumes_current
            broken_volumes += broken_volumes_current

        return (good_volumes, broken_volumes)

    def get_volumes_on_partition(
            self,
            file_server: AFSFileServer,
            partition:   AFSFileServerPartition,
            rx: str = r'^.*$',
            rx_all: bool = False,
    ) -> Tuple[list[Volume], list[BrokenVolume]]:
        """Get the list Volumes on a file server.

        Normally when using the rx to filter volume names any ".backup" or
        ".readonly" are ignored. However, there may be times when you do
        not want to ignore those parts of the name (e.g., if you are
        searching for all .backup volumes). When you do NOT want to ignore
        those suffixes set `rx_all` to True.
        """

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

        # Compile the rx.
        rx_compiled = re.compile(rx)

        all_volumes    = []
        broken_volumes = []
        with tempfile.NamedTemporaryFile(delete=True) as tmp:
            self.runner.run_vos_listvol(
                file_server.identifier(),
                partition.name,
                pathlib.Path(tmp.name)
            )

            with open(tmp.name, 'r') as fh:

                inside_entry = False
                bundle_lines: list[str] = []

                for line in fh:
                    if (begin_entry(line)):
                        inside_entry = True
                    elif (end_entry(line)):
                        inside_entry = False
                        _, all_sites = Volume.parse_volume_lines(bundle_lines)

                        site_attributes = all_sites[0]

                        if ('name' in site_attributes):
                            volume_name = site_attributes['name']
                            assert(volume_name is not None)

                            if (rx_all):
                                normalized_volume_name = volume_name
                            else:
                                normalized_volume_name = volume_base_name(volume_name)

                            if (rx_compiled.search(normalized_volume_name)):
                                self.progress(f"volume name {volume_name} matches")
                                volume = Volume.volume_from_site(self.runner, site_attributes)
                                self.progress(f"created volume object {volume.name}")
                                all_volumes.append(volume)
                            else:
                                self.progress(f"volume name {volume_name} does NOT match; skipping")

                        else:
                            if ('type' in site_attributes):
                                type_raw = site_attributes['type']
                                if (type_raw is not None):
                                    volume_type = AFSVolumeType.infer_type(type_raw)
                                else:
                                    volume_type = None
                            else:
                                volume_type = None

                            if ('id' in site_attributes):
                                volume_id = site_attributes['id']
                            else:
                                volume_id = None

                            broken_volume = BrokenVolume(
                                name=None,
                                volume_id=volume_id,
                                file_server=file_server,
                                volume_type=volume_type,
                                partition=partition.name,
                            )

                            broken_volumes.append(broken_volume)

                            msg = f"missing required name in site_attributes: {site_attributes}/{bundle_lines}"
                            logger.warn(msg)

                        bundle_lines = []

                    elif (inside_entry):
                        bundle_lines.append(line)
                    else:
                        # Not inside an entry, so skip.
                        pass

        return (all_volumes, broken_volumes)
