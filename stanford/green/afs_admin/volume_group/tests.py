import unittest

from stanford.green.afs_admin.config import AFSConfig
from stanford.green.afs_admin.volume_group import VolumeGroup

from stanford.green.afs_admin.resource import AFSResourceManager
from stanford.green.afs_admin.runner   import Runner

class TestAFSAdminVolumeGroup(unittest.TestCase):

    #verbose = True
    verbose = False

    config       = AFSConfig(cell='ir.stanford.edu')
    runner       = Runner.make_runner_direct(config, verbose=verbose)
    afs_resource = AFSResourceManager(runner, verbose=verbose)

    def test_make_volume_group(self) -> None:
        """Create a VolumeGroup object.
        """
        runner = TestAFSAdminVolumeGroup.runner
        volume_group = VolumeGroup.make_volume_group_object(runner, 'users.a.e.readonly')

        self.assertIsNotNone(volume_group.header)
        self.assertIsNotNone(volume_group.readwrite)
