"""Library to manage AFS resources.

"""

import os
from pathlib import Path

class AFS():
    """The base AFS object.

    From this object are derived other AFS resources such as a PTS object or an
    AFS volume.
    """


    _instance = None

    def __new__(cls, basedir=None, kerb_tkt: KerberosTicket=None, verbose=False):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

            if (basedir is None):
                raise ValueError("cannot create an AFS object without a basedir")

            cls._instance.basedir  = basedir
            cls._instance.verbose  = verbose
            cls._instance.kerb_tkt = kerb_tkt

            if (verbose):
                print("creating instance of AFS")


    ####################################################################################
    # Getters and setters
    @property
    def verbose(self) -> bool:
        """Return the verbose setting."""
        return self._verbose

    @verbose.setter
    def verbose(self, value: bool) -> None:
        """Set the verbose attribute."""
        self._verbose = value

    ##

    @property
    def basedir(self) -> str:
        """Return the basedir setting."""
        return self._basedir

    @basedir.setter
    def basedir(self, value: str) -> None:
        """Set the basedir attribute."""

        if (not value.startswith('/afs/')):
            raise Exception(f"basedir {value} does not start with '/afs/'")

        self._basedir = value
    ####################################################################################

    def refresh_ticket(self):
        """Create/update the Kerberos ticket file.
        """

        if (self.kerb_tkt is None):
            msg = "cannot refresh: the kerberos ticket is not defined"
            raise ValueError(msg)

        return self.kerb_tkt.create_ticket_file()

class AFSExecs:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

            pts_execs = ['/usr/bin/pts']
            for pts_exec in pts_execs:
                if os.access(pts_exec, os.X_OK):
                    cls.pts = AFSExecs.find_exec(['/usr/bin/pts'])
                    cls.vos = AFSExecs.find_exec(['/usr/sbin/vos', '/usr/bin/vos', '/usr/local/sbin/vos'])
                    cls.fs  = AFSExecs.find_exec(['/usr/bin/fs', '/usr/afsws/bin/fs', '/usr/pubsw/bin/fs'])

    @staticmethod
    def find_exec(exec_possibilities: list[str]) -> str:
        """Find the first executable in the list of executable possibilities.
        """
        chosen_exec: str = None

        for exec1 in exec_possibilities:
            exec1_filename = Path(exec1)
            if exec1_filename.exists() and exec1_filename.is_file() and os.access(exec1_filename, os.X_OK):
                chosen_exec = exec1
                break


        if (chosen_exec is None):
            raise ValueError(f"could not find a valid executable among {exec_possibilities}")

        return chosen_exec

_ = AFSExecs()
