from __future__ import annotations

from enum import Enum

from stanford.green.utility import run_command

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

    def run_vos(self, subcommand: str, vos_arguments: list[str]) -> str:
        """Run a 'vos' command.
        """
        if (self.is_direct()):
            command            = ['vos', subcommand] + vos_arguments
            stdout, stderr, rc = run_command(command)

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
        return self.run_vos('examine', ['-id', volume_name_or_id, '-format'])
