import unittest


from stanford.green.afs_admin.config import AFSConfig

from stanford.green.afs_admin.file_server import AFSFileServer
from stanford.green.afs_admin.runner   import Runner
from stanford.green.afs_admin.resource import AFSResourceManager

class TestAFSAdminFileServer(unittest.TestCase):

    verbose = True
    #verbose = False

    config       = AFSConfig(cell='ir.stanford.edu')
    runner       = Runner.make_runner_direct(config)
    afs_resource = AFSResourceManager(runner, verbose=verbose)

    def test_get_file_servers(self) -> None:
        """sdfgjksdf
        """
        if (TestAFSAdminFileServer.verbose):
            print(f"starting test_get_file_servers")

        runner       = TestAFSAdminFileServer.runner
        afs_resource = AFSResourceManager(runner)

        # Get the raw file server list
        raw_list = runner.run_vos_listfs()

        # This raw list should have several occurences of "UUID".
        lines = raw_list.splitlines()
        counter = 0
        for line in lines:
            if ("UUID" in line):
                counter = counter + 1

        # Should be several.
        self.assertTrue(counter > 3)

        ## 2. Get the list of FileServer objects.
        file_servers = AFSFileServer.make_file_server_objects(runner, fqdn_rx='^afssvr\d\d\..*$')

        self.assertTrue(len(file_servers) > 1)

