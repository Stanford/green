from enum import Enum

class AFSVolumeType(Enum):
    RW = 1
    RO = 2
    BK = 3

    def __str__(self) -> str:
        return self.name

