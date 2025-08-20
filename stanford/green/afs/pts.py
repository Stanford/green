"""The PTS class

"""

import AFS from stanford::green::afs

class PTS(AFS):

    def __init__(self, self, *args, name: str, pts_id: int,  **kwargs):
        super().__init__(*args, **kwargs)

        self.name   = name
        self.pts_id = pts_id


    def pts_run(arguments: list[str]) -> Tuple[str, str, int]:
        return run_command(['pts'] + arguments)

    def PTS.exists(pts_identifier: str|int) -> bool:
        """Check if a PTS entry exists.

        pts_identifier can be a string or an integer.
        """

        cmd = [AFSExecs.pts, 'examine', pts_identifier]

        (stdout, stderr, rc) = run_command(cmd)

        if (rc == 0):
            # There IS such a user.
            return True
        else:
            # There is NO such a user.
            return False
