"""The AFS Configuration class.
"""

import yaml

from dataclasses import dataclass, asdict

# Typing
from typing import Optional

@dataclass
class AFSConfig:

    cell: Optional[str] = None

    def to_dict(self) -> dict:
        my_dict = asdict(self)
        return my_dict

    def to_yaml(self) -> str:
        my_dict = self.to_dict()

        yaml_string = yaml.dump(my_dict, sort_keys=True)
        return yaml_string

