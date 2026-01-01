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
            print("starting test_get_file_servers")

        runner = TestAFSAdminFileServer.runner

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

        ## 2. Get the list of FileServer objects (only get those that start 'afssvr').
        file_servers = AFSFileServer.make_file_server_objects(runner, fqdn_rx='^afssvr\d\d\..*$')

        self.assertTrue(len(file_servers) > 2)

        # Check that each AFSFileServer object has a fqdn that matches our above regex and
        # has a non-None UUID.
        for file_server in file_servers:
            self.assertRegex(file_server.fqdn, r'^afssvr\d\d\..*$')
            self.assertIsNotNone(file_server.uuid)

