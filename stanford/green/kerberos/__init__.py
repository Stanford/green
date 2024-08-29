"""Library to manage Kerberos tickets


.. _filelock: https://pypi.org/project/filelock/

--------
Overview
--------

Use stanford.green.kerberos to provision and maintain a Kerberos ticket
cache. Uses the `filelock <filelock_>`_ Python package to avoid two
instances attempting to write to the same ticket cache at the same time.

The `kinit` executable must be installed for this package to work.

--------
Examples
--------

Simple example::

  from stanford.green.kerberos import KerberosTicket

  keytab_path = "/etc/krb5.keytab"
  principal   = "host/myserver.stanford.edu@stanford.edu"

  kt = KerberosTicket(keytab_path, principal, age_limit_seconds=30)
  kt.create_ticket_file()
  # You now have a valid Kerberos context with the Kerberos ticket
  # file pointed to by the KRB5CCNAME environment variable.

  # Clean up the ticket file:
  kt.cleanup()
"""

import os
import time
from filelock import FileLock

from stanford.green.utility import run_command

## TYPING
from typing import Any, Optional
## END OF TYPING

class KerberosTicket():
    """A Kerberos ticket object.

    Initialization requires the passing in of the keytab file path *and* the principal
    name.

    The ticket lockfile location defaults to the ticket filename suffixed with ".lock".

    """

    def __init__(self,
                 keytab_path:       str,
                 kprincipal:        str,
                 ticket_file:       str,
                 ticket_lock_file:  Optional[str] = None,
                 age_limit_seconds: int = 300,
                 verbose:           bool = False):

        self._verbose = verbose

        self.keytab_path = keytab_path
        self.kprincipal  = kprincipal

        self.ticket_file = ticket_file

        if (ticket_lock_file is None):
            self.ticket_lock_file = f"{ticket_lock_file}.lock"
        else:
            self.ticket_lock_file = ticket_lock_file

        self.age_limit_seconds = age_limit_seconds

    def cleanup(self) -> None:
        """Remove the Kerberos ticket and lock files."""
        if (os.path.exists(self.ticket_file)):
            os.remove(self.ticket_file)

        if (os.path.exists(self.ticket_lock_file)):
            os.remove(self.ticket_lock_file)

    def debug(self, msg: str) -> None:
        if (self.verbose):
            print(f"debug: {msg}")

    ####################################################################################
    # Getters and setters
    @property
    def verbose(self) -> bool:
        return self._verbose

    @verbose.setter
    def verbose(self, value: bool) -> None:
        self._verbose = value
    ####################################################################################

    def ticket_file_needs_updating(self) -> bool:
        """Return true if the Kerberos ticket file needs updating, false otherwise.

        The Kerberos ticket file needs updating in the following cases:
          * it does not already exist;
          * it *does* exist but is empty;
          * it *does* exist but is too old. The ticket file is too old if
            the current ticket file is more than ``self.age_limit_seconds``
            seconds old.
        """
        if (not os.path.isfile(self.ticket_file)):
            # The ticket file does not exist, so it definitely needs updating.
            return True

        # If the ticket file is EMPTY it needs updating.
        if (os.stat(self.ticket_file).st_size == 0):
            return True

        # The ticket file exists. How old is it?
        modify_time_epoch = os.path.getmtime(self.ticket_file)
        age_seconds = time.time() - modify_time_epoch
        self.debug(f"age of ticket file is {age_seconds} seconds")

        if (age_seconds > self.age_limit_seconds):
            return True
        else:
            return False

    def create_ticket_file(self) -> None:
        """Create/update the Kerberos ticket file (if needed).

        Create/update the Kerberos ticket file, but only if the ticket
        file needs to be renewed. Also set the environment variable
        :envvar:`KRB5CCNAME` to point to the Kerberos ticket file.

        The path to the ticket file comes from ``self.keytab_path``.

        This method only creates the ticket file if it can acquire the
        ticket lock file.
        """
        # Does this ticket file need updating at all?
        if (self.ticket_file_needs_updating()):
            # Yes, it needs updating. So acquire the lock and update.
            # Given that creating a Kerberos ticket file takes less
            # than a second (under normal circumstances), putting a 10-second
            # timeout on acquiring the lock file is more than sufficient.
            with FileLock(self.ticket_lock_file, timeout=10):
                self.debug("acquired Kerberos ticket lock file")
                cmd = ['kinit', '-k', '-t', self.keytab_path, '-c', self.ticket_file, self.kprincipal]
                _, stderr, _ = run_command(cmd)

                if (stderr):
                    raise Exception(f"error obtaining a Kerberos ticket: {stderr}")
            self.debug(f"Kerberos lock file should now be released")
        else:
            self.debug("Kerberos ticket file is not old enough to need updating")

        # Whether the ticket file was updated or now, set KRB5CCNAME to
        # the path of the ticket file.
        os.environ["KRB5CCNAME"] = f"FILE:{self.ticket_file}"
