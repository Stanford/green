"""Miscellaneous and utility functions

"""
import os
import pathlib
import subprocess

from contextlib import contextmanager


# pylint: disable=superfluous-parens

## TYPING
from typing import Tuple, List, Iterator  # pylint: disable=wrong-import-order
## END OF TYPING

def run_command(cmd: List[str], raise_exception_on_error: bool = False) \
    -> Tuple[str, str, int]:
    """Run the command in the array ``cmd``

    If the raise_exception_on_error parameter is left at its default
    value of False, return stdout, stderr, and the exit code even if
    the command exits with an error.

    If the raise_exception_on_error parameter is set to True, if the
    command exists with a non-zero value rise an exception with the
    exception message containing stderr and the exit code.

    """
    result     = subprocess.run(cmd, capture_output=True, check=False)
    stdout_b   = result.stdout
    stderr_b   = result.stderr
    returncode = result.returncode

    # I am fairly sure that with capture_output set to True stdout_b
    # and stderr_b will never be None, but I check just in case.
    if (stdout_b is None):
        stdout = None  # pragma: no cover
    else:
        stdout = stdout_b.decode("utf-8")

    if (stderr_b is None):
        stderr = None  # pragma: no cover
    else:
        stderr = stderr_b.decode("utf-8")

    if (raise_exception_on_error and (returncode != 0)):
        msg = f"command '{cmd}' had non-zero exit code {returncode}; " \
              f"error output was '{stderr}'"
        raise RuntimeError(msg)

    return stdout, stderr, returncode

def run_command_to_file(
        cmd: List[str],
        output_file: pathlib.Path,
        raise_exception_on_error: bool = False
) -> Tuple[str, int]:
    """Run the command in the array ``cmd`` sending output to output_file.

    See run_command for an explanation on how raise_exception_on_error
    works.
    """

    with output_file.open('w') as fh:
        result = subprocess.run(
            cmd,
            stdout=fh,               # Redirect stdout to file
            stderr=subprocess.PIPE
        )

        stderr_b   = result.stderr
        returncode = result.returncode

    if (stderr_b is None):
        stderr = None  # pragma: no cover
    else:
        stderr = stderr_b.decode("utf-8")

    if (raise_exception_on_error and (returncode != 0)):
        msg = f"command '{cmd}' had non-zero exit code {returncode}; " \
              f"error output was '{stderr}'"
        raise RuntimeError(msg)

    return stderr, returncode

@contextmanager
def local_env_set(variable_name: str, variable_value: str) -> Iterator[None]:
    """Define a context manager to do local environment variable setting.

    """
    old_value = os.environ.get(variable_name)
    os.environ[variable_name] = variable_value
    try:
        yield
    finally:
        if old_value is None:
            del os.environ[variable_name]
        else:
            os.environ[variable_name] = old_value

