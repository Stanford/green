import datetime
import pathlib
import re
import tempfile

from stanford.green.afs_admin.file_server  import AFSFileServer
from stanford.green.afs_admin.file_server  import AFSFileServerPartition

from stanford.green.afs_admin.runner import Runner

from stanford.green.afs_admin.volume import Volume

from stanford.green.afs_admin.utility import volume_base_name

# Typing
from typing import Tuple

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



    def make_file_server_objects(self) -> list[AFSFileServer]:
        """Get the list of FileServer objects
        """
        uuid: str | None  # For mypy

        file_server_list_raw = self.runner.run_vos_listfs()

        # Parse the list
        lines = file_server_list_raw.splitlines()

        uuid_rx       = re.compile(r"^UUID:\s+(\S+)\S*$")
        ip_address_rx = re.compile(r"\[((?:[0-9]{1,3}\.){3}[0-9]{1,3})\]")

        next_line_is_server = False

        file_servers = []
        uuid = None

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

                # Reset the variables.
                uuid = None

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

    def get_volumes(
            self,
            file_server: AFSFileServer,
            rx: str = r'^.*$',
            rx_all: bool = False,
    ) -> list[Volume]:
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

        all_volumes = []
        with tempfile.NamedTemporaryFile(delete=True) as tmp:
            self.runner.run_vos_listvol(file_server, pathlib.Path(tmp.name))

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
                        volume_name = site_attributes['name']
                        assert(volume_name is not None)

                        if (rx_all):
                            normalized_volume_name = volume_name
                        else:
                            normalized_volume_name = volume_base_name(volume_name)

                        if (rx_compiled.search(normalized_volume_name)):
                            self.progress(f"volume name {volume_name} matches")
                            volume = Volume.volume_from_site(site_attributes)
                            self.progress(f"created volume object {volume.name}")
                            all_volumes.append(volume)
                        else:
                            self.progress(f"volume name {volume_name} does NOT match; skipping")

                        bundle_lines = []
                        pass
                    elif (inside_entry):
                        bundle_lines.append(line)
                    else:
                        # Not inside an entry, so skip.
                        pass

        return all_volumes

    def get_partitions(
            self,
            file_server: AFSFileServer
    ) -> list[AFSFileServerPartition]:
        """Get a list of paritions on a file server.
        """
        raw_output = self.runner.run_vos_listpart(file_server)

        # The output will look like this:
        # The partitions on the server are:
        #     /vicepa     /vicepb
        #     Total: 2

        rx = r'The partitions on the server are:(.*)Total:.*'
        match = re.match(rx, raw_output, re.MULTILINE | re.DOTALL)

        partitions = []

        if (match):
            partitions_raw  = match.group(1).strip()
            partition_names = partitions_raw.split()

            for partition_name in partition_names:
                partition = AFSFileServerPartition(
                    name=partition_name
                )
                partitions.append(partition)
        else:
            msg = f"could not find partition information for file server {file_server.identifier()}"
            raise Exception(msg)

        return partitions

    def get_partition_sizes(
            self,
            file_server: AFSFileServer,
            partition:   AFSFileServerPartition
    ) -> Tuple[int, int]:
        """Get the sizes of a partition.

        Returns the tuple (used_KB, total_KB).
        """
        raw_output = self.runner.run_vos_partinfo(file_server, partition)

        # The output will look like this:
        # Free space on server afssvr06.stanford.edu:7005 partition /vicepa: 1443189276 K blocks out of total 4292876288

        pname = partition.name
        rx = rf"^Free space.*{pname}: (\d+) K blocks out of total (\d+).*$"
        match = re.match(rx, raw_output)

        if (match):
            used_KB  = match.group(1)
            total_KB = match.group(2)
        else:
            msg = f"could not find partition information for file server {file_server.identifier()}"
            raise Exception(msg)

        return (int(used_KB), int(total_KB))
