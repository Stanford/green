"""A command runner class

The Runner class is used to run command-line commands like
``vos``, ``fs``, ``pts``, etc.

This class does _not_ return AFS objects like Volume or AFSFileServer,
rather, it returns the text output of command.

"""

from __future__ import annotations

import logging
import pathlib

from enum import Enum

from stanford.green.utility import run_command
from stanford.green.utility import run_command_to_file
from stanford.green.utility import local_env_set

from stanford.green.afs_admin.config import AFSConfig

logger = logging.getLogger(__name__)

# Typing
from typing import Optional

class GreenAFSNoRunnerError(Exception):
    """Raise when an expected Runner is missing.
    """
    pass

class GreenAFSRunnerError(Exception):
    """Raise when there is a Runner error.
    """
    pass

class RunnerInterface(Enum):
    """The kind of interface the Runner uses.

    Currently there are only two recognized interfaces: "direct" and "afsapi".

    The "direct" interface uses AFS program calls (``vos``, ``pts``, etc.). The
    "afsapi" uses calls to the AFS-API service.

    The only interface implemented so far is "direct".
    """
    direct = 1
    afsapi = 2

class Runner:
    """The Runner class.
    """


    def __init__(self, config: AFSConfig, command_interface: RunnerInterface):
        self.config            = config
        self.command_interface = command_interface

    def __str__(self) -> str:
        fields = []

        fields.append(f"config: {self.config}")
        fields.append(f"command_interface: {self.command_interface}")

        return f"<{','.join(fields)}>"



    def is_direct(self) -> bool:
        if (self.command_interface == RunnerInterface.direct):
            return True
        else:
            return False

    def is_afsapi(self) -> bool:
        if (self.command_interface == RunnerInterface.afsapi):
            return True
        else:
            return False

    def is_api(self) -> bool:
        return self.is_afsapi()

    @staticmethod
    def make_runner_direct(config: AFSConfig) -> Runner:
        return Runner(config, RunnerInterface.direct)

    ## ## #    ## ## #    ## ## #    ## ## #    ## ## #    ## ## #    ## ## #    ## ## #

    def run_vos(
            self,
            subcommand: str,
            vos_arguments: list[str],
            output_file: Optional[pathlib.Path] = None
    ) -> str | None:
        """Run a ``vos`` command.

        :param subcommand: the ``vos`` "action" (e.g., ``examine`` or ``listfs``).
        :type prefix: str

        :param vos_arguments: the rest of the command-line arguments to pass to ``vos subcommand``.
        :type prefix: list[str]

        :param output_file: if this parameter is passed rather than returning the
          standard output string save the standard output to the file specified by
          ``output_file``; note that this will *overwrite* ``output_file``.
        :type prefix: Optional[str]

        :return: the standard output of the ``vos`` command unless the ``output_file`` parameter
          is provided, in which case nothing is returned.

        If the output_file is provided this function returns ``None``.

        We run all vos commands with the :envvar:`TZ` environment variable set to
        ``UTC``.

        For an example of use, see :meth:`Runner.run_vos_examine`.
        """
        if (self.is_direct()):
            command = ['vos', subcommand] + vos_arguments

            # If the cell is configured add that option.
            if (self.config.cell):
                cell_options = ['-cell', self.config.cell]
            else:
                cell_options = []

            command += cell_options

            with local_env_set('TZ', 'UTC'):
                if (output_file is None):
                    stdout, stderr, rc = run_command(command)
                else:
                    stderr, rc = run_command_to_file(command, output_file)
                    stdout = None

            if (stderr):
                command_str = ' '.join(command)
                msg = f"error running command '{command_str}': {stderr}"
                raise GreenAFSRunnerError(msg)

            return stdout
        else:
            msg = "the afs-api interface is not yet implemented for 'run_vos'"
            raise NotImplementedError(msg)

    def run_vos_examine(self, volume_name_or_id: str|int) -> str:
        """Return the output of ``vos examine <volume_name_or_id> -format``.
        """
        # Add the "-format" option.
        stdout = self.run_vos('examine', ['-id', str(volume_name_or_id), '-format'])
        assert(stdout is not None)

        return stdout

    def run_vos_listfs(self) -> str:
        """Return the list of file servers a la "vos listfs"
        """
        stdout = self.run_vos('listfs', [])
        assert(stdout is not None)

        return stdout

    def run_vos_listvol(
            self, file_server_identifier: str,
            partition_name: str,
            output_file: pathlib.Path) -> None:
        """Saves the raw output of "vos listvol FILESERVER -format" to a file
        """
        parameters  = []
        parameters += ['-server',    file_server_identifier]
        parameters += ['-partition', partition_name]
        parameters += ['-format']

        self.run_vos('listvol', parameters, output_file=output_file)

    def run_vos_listpart(self, file_server_identifier: str) -> str:
        """Return the output of the "vos listpart" command.
        """
        parameters = [
            '-server', file_server_identifier,
            ]

        stdout = self.run_vos('listpart', parameters)
        assert(stdout is not None)

        return stdout

    def run_vos_partinfo(self,
                         file_server_identifier: str,
                         partition_name: str) -> str:
        """Return the output of the "vos partinfo" command.
        """
        parameters = [
            '-server', file_server_identifier,
            '-partition', partition_name,
            ]

        stdout = self.run_vos('partinfo', parameters)
        assert(stdout is not None)

        return stdout
