"""The PTS class

"""

from stanford.green.afs     import AFS, AFSExecs
from stanford.green.utility import run_command

from typing import Tuple

class PTS():

    def __init__(self, name: str=None, pts_id: int=None, verbose=False):

        try:
            afs = AFS()
        except Exception:
            raise ValueError("cannot instantiate PTS unless an AFS object has been created")

        self.afs    = AFS()
        self.name   = name
        self.pts_id = pts_id
        self.verbose = verbose

        self.pts_exec = AFSExecs.pts

    def progress(self, msg):
        if (self.verbose):
            print(f"[progress] {msg}")

    def pts_identifier(self):
        if (self.name):
            return self.name
        else:
            return self.pts_id


    @staticmethod
    def make_pts(*args, pts_identifier: str|int, **kwargs):
        if isinstance(pts_identifier, int):
            return PTS(args, name=None, pts_id=pts_identifier)
        else:
            return PTS(name=pts_identifier, pts_id=None)

    def pts_run(self, arguments: list[str]) -> Tuple[str, str, int]:
        return run_command([self.pts_exec] + arguments)

    def exists(self) -> bool:
        """Check if a PTS entry exists.
        """
        cmd = ['examine', self.pts_identifier()]

        (stdout, stderr, rc) = self.pts_run(cmd)
        self.progress(f"pts command {cmd} returned exit code {rc}")

        if (rc == 0):
            # There IS such a user.
            return True
        else:
            # There is NO such a user.
            return False

    def get_info(self) -> bool:
        """Get PTS entry information.
        """
        cmd = ['examine', self.pts_identifier()]

        (stdout, stderr, rc) = self.pts_run(cmd)
        self.progress(f"pts command {cmd} returned stdout code {stdout}")

        # Parse the output...

    def get_next_user_id(self) -> int:
        """Get the next PTS id that would be used when creating a new user PTS entry.
        """
        pass

    def get_next_group_id(self) -> int:
        """Get the next PTS id that would be used when creating a new group PTS entry.
        """
        pass

    def get_least_unused_user_id(self, lower_bound: int=1) -> int:
        """Get the smallest unused user PTS greater than or equal to lower_bound.
        """
        pass

    def get_largest_unused_group_id(self, lower_bound: int=-1) -> int:
        """Get the largest unused user PTS less than or equal to lower_bound.

        Hint: remember that PTS group entry ids are always negative.
        """
        pass

