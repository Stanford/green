"""Library to manage AFS resources.

"""


class AFS():
    """The base AFS object.

    From this object are derived other AFS resources such as a PTS object or an
    AFS volume.
    """

    def __init__(self,
                 basedir: str,
                 verbose: bool = False
                 ):

        self.basedir  = basedir
        self._verbose = verbose

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


class AFSExecs:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls.pts = '/usr/bin/pts'

        return cls._instance
