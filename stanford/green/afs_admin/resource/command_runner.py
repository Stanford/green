from __future__ import annotations

import pathlib

from enum import Enum

from stanford.green.afs_admin.file_server import AFSFileServer
from stanford.green.utility import run_command
from stanford.green.utility import run_command_to_file

# Typing
from typing import Optional

class AFSCommandError(Exception):
    pass

class CommandRunnerInterface(Enum):
    direct = 1
    afsapi = 2

class CommandRunner:

    def __init__(self, command_interface: CommandRunnerInterface):
        self.command_interface = command_interface

    def is_direct(self) -> bool:
        if (self.command_interface == CommandRunnerInterface.direct):
            return True
        else:
            return False

    def is_afsapi(self) -> bool:
        if (self.command_interface == CommandRunnerInterface.afsapi):
            return True
        else:
            return False

    def is_api(self) -> bool:
        return self.is_afsapi()

    @staticmethod
    def make_command_runner_direct() -> CommandRunner:
        return CommandRunner(CommandRunnerInterface.direct)

    ## ## #    ## ## #    ## ## #    ## ## #    ## ## #    ## ## #    ## ## #    ## ## #

    def run_vos(
            self,
            subcommand: str,
            vos_arguments: list[str],
            output_file: Optional[pathlib.Path] = None
    ) -> str | None:
        """Run a 'vos' command.

        Note that if the output_file is provided this function returns None.
        """
        if (self.is_direct()):
            command = ['vos', subcommand] + vos_arguments

            if (output_file is None):
                stdout, stderr, rc = run_command(command)
            else:
                stderr, rc = run_command_to_file(command, output_file)
                stdout = None

            if (stderr):
                command_str = ' '.join(command)
                msg = f"error running command '{command_str}': {stderr}"
                raise AFSCommandError(msg)

            return stdout
        else:
            msg = "the afs-api interface is not yet implemented for 'run_vos'"
            raise NotImplementedError(msg)

    def run_vos_examine(self, volume_name_or_id: str) -> str:
        """Return the output of "vos examine <volume_name_or_id>"
        """
        # Add the "-format" option.
        stdout = self.run_vos('examine', ['-id', volume_name_or_id, '-format'])
        assert(stdout is not None)

        return stdout

    def run_vos_listfs(self) -> str:
        """Return the list of file servers a la "vos listfs"
        """
        stdout = self.run_vos('listfs', [])
        assert(stdout is not None)

        return stdout

    def run_vos_listvol(self, file_server: AFSFileServer, output_file: pathlib.Path) -> None:
        """Saves the raw output of "vos listvol fileserver" to a file
        """
        if (file_server.fqdn is not None):
            server_id = file_server.fqdn
        elif (file_server.ip_address is not None):
            server_id = file_server.ip_address
        elif (file_server.uuid is not None):
            server_id = file_server.uuid
        else:
            msg = "cannot find any identifier for file server"
            raise ValueError(msg)

        parameters = [server_id, '-format']
        self.run_vos('listvol', parameters, output_file=output_file)
