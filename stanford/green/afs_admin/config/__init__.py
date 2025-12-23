"""The AFS Configuration class.

--------
Overview
--------

Use the stanford.green.afs_admin.config class to set the following global
configuration variables:

* ``cell``: the AFS cell (defaults to ``None``). If set this will be
  passed as the argument to ``-cell`` in all the ``vos`` commands; for
  more information see the man page for ``vos``.

--------
Examples
--------

.. code-block:: python

    from stanford.green.afs_admin.config import AFSConfig
    from stanford.green.afs_admin.runner import Runner

    config = AFSConfig(
        cell='my.example.com'
    )

    # An AFSConfig object is required when creating a Runner:
    runner = Runner.make_runner_direct(config)

You can omit the cell parameter and everything still works

.. code-block:: python

    from stanford.green.afs_admin.config import AFSConfig
    from stanford.green.afs_admin.runner import Runner

    config = AFSConfig()
    runner = Runner.make_runner_direct(config)

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

