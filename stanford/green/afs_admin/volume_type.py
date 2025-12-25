from __future__ import annotations

from enum import Enum

class AFSVolumeType(Enum):
    RW = 1
    RO = 2
    BK = 3

    def __str__(self) -> str:
        return self.name


    @staticmethod
    def infer_type(type_str: str) -> AFSVolumeType:
        type_str_uc = type_str.upper()

        if (type_str_uc   == 'RW'):
            return AFSVolumeType.RW
        elif (type_str_uc == 'RO'):
            return AFSVolumeType.RO
        elif (type_str_uc == 'BK'):
            return AFSVolumeType.BK
        else:
            msg = f"could not interpret volume type '{type_str}'"
            raise ValueError(msg)
