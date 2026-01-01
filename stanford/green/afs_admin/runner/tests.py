import unittest

### stanford.green.afs_admin imports

from stanford.green.afs_admin.config import AFSConfig

from stanford.green.afs_admin.runner   import Runner

### end of stanford.green.afs_admin imports


class TestAFSRunner(unittest.TestCase):

    config = AFSConfig(cell='ir.stanford.edu')
    runner = Runner.make_runner_direct(config, verbose=True)

    def test_vos_eachfs(self) -> None:
        runner = TestAFSRunner.runner
        output = runner.run_vos_eachfs()

        # Break into lines.
        lines = output.split("\n")

        # Should be several lines.
        self.assertTrue(len(lines) > 5)

        # Each line should be four comma-separated fields.
        for line in lines:
            if (not line.strip()):
                # Skip blank lines
                next
            else:
                fields = line.split(',')
                self.assertEqual(len(fields), 4)

