"""File Server
"""

from __future__ import annotations

import logging
import re
import yaml

from dataclasses import dataclass, asdict

from cachetools      import cached, FIFOCache
from cachetools.keys import hashkey

from stanford.green.afs_admin.file_server.partition  import AFSFileServerPartition

from stanford.green.afs_admin.runner import Runner
from stanford.green.afs_admin.runner import GreenAFSNoRunnerError

from typing import Optional, ClassVar

logger = logging.getLogger(__name__)

@dataclass
class AFSFileServer:
    """Represents an AFS File Server.

    """
    partitions: list[AFSFileServerPartition]

    fqdn:       Optional[str]
    ip_address: Optional[str]
    port:       int            # The volume server port (usually 7005)
    uuid:       Optional[str]  # Non-existent file servers will have no UUID

    runner:     Optional[Runner]

    # Because there are only a few AFS file servers and many thousands of
    # volumes, we want to cache the AFSFileServer objects. See the
    # make_file_server_object() moethod below.
    cache: ClassVar[FIFOCache] = FIFOCache(maxsize=100)

    def __post_init__(self) -> None:
        """After initialization populate the partitions attribute.

        Skip this step if uuid is None as this means the file server is not available.
        """
        if (self.uuid is not None):
            runner = self.get_runner()
            assert(runner is not None)

            partitions = AFSFileServerPartition.get_partitions(runner, self.identifier())
            self.partitions = partitions

    def get_runner(self) -> Runner:
        """Return self.runner, raising the GreenAFSNoRunnerError error if no runner is defined.
        """
        if (not self.runner):
            msg = "no Runner has been defined for this object"
            raise GreenAFSNoRunnerError(msg)

        return self.runner


    def to_yaml(self) -> str:
        my_dict = asdict(self)

        yaml_string = yaml.dump(my_dict, sort_keys=True)
        return yaml_string

    # ### #    # ### #    # ### #    # ### #    # ### #    # ### #    # ### #    # ### #
    @staticmethod
    @cached(
        cache=cache,
        key=lambda fqdn, ip_address, port, uuid, runner: hashkey(fqdn, ip_address, port, uuid)
    )
    def make_file_server_object(
            fqdn:       Optional[str],
            ip_address: Optional[str],
            port:       int,
            uuid:       Optional[str],
            runner:     Runner
    ) -> AFSFileServer:
        """Return an AFSFileServer object.

        We cache on all parameters except runner.
        """
        # print(f"Creating AFSFileServer ({fqdn}, {ip_address}, {port}, {uuid}) ...")
        file_server = AFSFileServer(
            partitions=[],
            fqdn=fqdn,
            ip_address=ip_address,
            port=int(port),
            uuid=uuid,
            runner=runner
        )

        return file_server

    # ### #    # ### #    # ### #    # ### #    # ### #    # ### #    # ### #    # ### #
    @staticmethod
    def fqdn_to_file_server(file_servers: list[AFSFileServer]) -> dict[str, AFSFileServer]:
        """Returns a dict mapping fqdn to AFSFileServer

        Any file_server in the `file_servers` parameter that has no
        fqdn is skipped.
        """
        fqdn_to_file_server = {}
        for file_server in file_servers:
            if (file_server.fqdn is not None):
                fqdn_to_file_server[file_server.fqdn] = file_server

        return fqdn_to_file_server

    def identifier(self) -> str:
        """Returns the best "name" for this file server.

        Returns the first of ``fqdn``, ``uuid``, or ``ip_address`` that is not ``None``.
        If all three are ``None`` raises a ``ValueError``.
        """
        if (self.fqdn is not None):
            return self.fqdn
        elif (self.uuid is not None):
            return self.uuid
        elif (self.ip_address is not None):
            return self.ip_address
        else:
            msg = "cannot return a server identifier as all of fqdn, ip_addres, and uuid are None"
            raise ValueError(msg)

    @staticmethod
    def make_file_server_objects(runner: Runner, fqdn_rx: str = r'^.*$') -> list[AFSFileServer]:
        """Get the list of FileServer objects.

        """
        uuid: str | None  # For mypy

        mpfx = 'make_file_server_objects'

        file_servers = []

        # Reset lap counter so we can see how many external command
        # were called.
        runner.counter.reset_lap()

        file_server_list_raw = runner.run_vos_eachfs()

        # Parse the list
        lines = file_server_list_raw.splitlines()

        number_skipped = 0
        for line in lines:
            if (not line.strip()):
                # Skip blank lines.
                next
            else:
                fqdn, port, ip_address, uuid = line.split(',')

            if (uuid.upper() == 'NO_UUID'):
                uuid = None

            # Only create the AFSFileServer if fqdn_rx matches.
            if ((fqdn is not None) and (re.search(fqdn_rx, fqdn))):
                file_server = AFSFileServer.make_file_server_object(
                    fqdn=fqdn,
                    ip_address=ip_address,
                    port=int(port),
                    uuid=uuid,
                    runner=runner
                )

                file_servers.append(file_server)
            else:
                number_skipped += 1

        # How many commands were used?
        commands_used = runner.counter.get_lap_count()
        msg = f"[{mpfx}] used {commands_used} commands"
        logger.info(msg)

        total_found = number_skipped + len(file_servers)
        msg = f"[{mpfx}] found {total_found} file servers, skipped {number_skipped} (filter: '{fqdn_rx}')"
        logger.info(msg)

        return file_servers


    @staticmethod
    def serv_line_to_file_server(line: str, runner: Runner) -> AFSFileServer:
        """Parse a "serv" line into an AFSFileServer object.

        A "serv" line is line that is output by a "vos" command. It will look
        like this::

            serv   171.67.22.15  afssvr05.stanford.edu:7005  b4263ced-74f0-436a-8384-7a37f342d424

        This method takes such a line and returns the corresponding
        AFSFileServer object.
        """
        ip_address, fqdn_port, uuid = line.split()

        # Split server into name and port:
        fqdn, port = fqdn_port.split(':')

        file_server = AFSFileServer.make_file_server_object(
            fqdn=fqdn,
            ip_address=ip_address,
            port=int(port),
            uuid=uuid,
            runner=runner
        )

        return file_server
