from __future__ import annotations

import re

from dataclasses import dataclass, asdict

from stanford.green.afs_admin.runner import Runner

# Typing
from typing import Tuple

@dataclass
class AFSFileServerPartition:
    """
    name: typically something like "/vicepa" or "/vicepb".
    """
    name: str

    used_KB:  int
    total_KB: int

    @staticmethod
    def get_partitions(runner: Runner, file_server_identifier: str) -> list[AFSFileServerPartition]:
        """Get a list of partitions on a file server.
        """
        raw_output = runner.run_vos_listpart(file_server_identifier)

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
                (used_KB, total_KB) = AFSFileServerPartition.get_partition_sizes(
                    runner,
                    file_server_identifier,
                    partition_name
                )

                partition = AFSFileServerPartition(
                    name=partition_name,
                    used_KB=used_KB,
                    total_KB=total_KB
                )
                partitions.append(partition)
        else:
            msg = f"could not find partition information for file server {file_server_identifier}"
            raise Exception(msg)

        return partitions

    @staticmethod
    def get_partition_sizes(runner: Runner, file_server_identifier: str, partition_name: str) -> Tuple[int, int]:
        """Get the sizes of a partition.

        Returns the tuple (used_KB, total_KB).
        """
        raw_output = runner.run_vos_partinfo(file_server_identifier, partition_name)

        # The output will look like this:
        # Free space on server afssvr06.stanford.edu:7005 partition /vicepa: 1443189276 K blocks out of total 4292876288

        pname = partition_name
        rx = rf"^Free space.*{pname}: (\d+) K blocks out of total (\d+).*$"
        match = re.match(rx, raw_output)

        if (match):
            used_KB  = match.group(1)
            total_KB = match.group(2)
        else:
            msg = f"could not find partition information for file server {file_server_identifier}"
            raise Exception(msg)

        return (int(used_KB), int(total_KB))
