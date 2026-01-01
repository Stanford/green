import unittest

import pathlib
import re
import tempfile
import textwrap


### stanford.green.afs_admin imports
from .config import AFSConfig

from .file_server           import AFSFileServer
from .file_server.partition import AFSFileServerPartition

from .volume      import Volume
from .volume_type import AFSVolumeType

from .resource import AFSResourceManager
from .runner   import Runner
### end of stanford.green.afs_admin imports


class TestAFSAdmin(unittest.TestCase):

    # Output of "vos examine users.a.d. -format"
    vos_examine_output = """
    groupName       users.a.d
    rwrite  2003261870
    ronly   2003261871
    backup  2003261872
    rclone  0
    name    users.a.d
    id      2003261870
    serv    171.67.22.15    afssvr05.stanford.edu:7005      b4263ced-74f0-436a-8384-7a37f342d424
    part    /vicepb
    status  OK
    backupID        2003261872
    parentID        2003261870
    cloneID 2003261871
    inUse   Y
    needsSalvaged   N
    destroyMe       N
    type    RW
    creationDate    1726181899      Thu Sep 12 15:58:19 2024
    accessDate      1765669501      Sat Dec 13 15:45:01 2025
    updateDate      1765457423      Thu Dec 11 04:50:23 2025
    backupDate      1765534542      Fri Dec 12 02:15:42 2025
    copyDate        1726181899      Thu Sep 12 15:58:19 2024
    flags   0       (Optional)
    diskused        364
    maxquota        5000
    minquota        0       (Optional)
    filecount       351
    dayUse  1181
    weekUse 17753   (Optional)
    volUpdateCounter        137     (Optional)
    spare3  0       (Optional)
    site_count      3
    site_versions   same
    site_server_0   171.67.22.15    afssvr05.stanford.edu:7005      b4263ced-74f0-436a-8384-7a37f342d424
    site_partition_0        /vicepb
    site_type_0     RW
    site_state_0    new
    site_server_1   171.67.22.15    afssvr05.stanford.edu:7005      b4263ced-74f0-436a-8384-7a37f342d424
    site_partition_1        /vicepb
    site_type_1     RO
    site_state_1    new
    site_server_2   171.67.22.24    afssvr03.stanford.edu:7005      200f0f0a-2b6f-4827-b077-47736387888e
    site_partition_2        /vicepb
    site_type_2     RO
    site_state_2    new
    locked  no
    """


    #verbose = True
    verbose = False

    vos_examine_output=textwrap.dedent(vos_examine_output).strip()

    config       = AFSConfig(cell='ir.stanford.edu')
    runner       = Runner.make_runner_direct(config, verbose=True)
    afs_resource = AFSResourceManager(runner, verbose=verbose)

    def test_basic(self) -> None:
        self.assertTrue(True)

    def test_parse_vos_examine_output(self) -> None:
        """Convert the output of vos examine into a volume object.
        """
        runner = TestAFSAdmin.runner

        volumes = Volume.vos_examine_to_volume(runner, TestAFSAdmin.vos_examine_output)
        volume0 = volumes[0]
        self.assertEqual(volume0.name, 'users.a.d')

    def test_make_volume_object(self) -> None:
        runner = TestAFSAdmin.runner

        volumes = Volume.create_volume_objects(runner, 'users.a.e.readonly')

        self.assertTrue(len(volumes) > 1)

        # Get the first volume.
        volume0 = volumes[0]

        self.assertIsNotNone(volume0.name)



    def test_get_volumes(self) -> None:
        """sdfgjksdf
        """
        print('starting test_get_volumes')

        runner = TestAFSAdmin.runner
        afs_resource   = TestAFSAdmin.afs_resource

        file_servers = AFSFileServer.make_file_server_objects(runner, fqdn_rx=r'^afssvr\d\d\.')

        # Convert to a mapping of fqdn to file_server object
        fqdn_to_file_server = AFSFileServer.fqdn_to_file_server(file_servers)

        # Get the afssvr01 AFSFileServer object.
        file_server_1 = fqdn_to_file_server['afssvr01.stanford.edu']
        self.assertIsNotNone(file_server_1)

        # Run the run_vos_listvol method.
        with tempfile.NamedTemporaryFile(delete=True) as tmp:
            temp_file = pathlib.Path(tmp.name)
            runner.run_vos_listvol(
                file_server_1.identifier(),
                file_server_1.partitions[0].name,
                temp_file
            )

            self.assertTrue(temp_file.exists())

            # Get the first few lines of temp_file to make sure we got
            # some output.
            with temp_file.open('r') as fh:
                lines = [next(fh) for _ in range(3)]  # read first three lines
                self.assertTrue(len(lines) == 3)
                for line in lines:
                    self.assertTrue(len(line) > 1)

        (volumes, broken_volumes) = \
            afs_resource.get_volumes_on_server(file_server_1)

        # There should be several volumes.
        self.assertTrue(len(volumes) >= 10)

        # Get the volumes but this time only get volumes with names
        # containing the letter "a".
        (volumes, broken_volumes) = \
            afs_resource.get_volumes_on_server(file_server_1, rx=r'a')

        # There should be several volumes.
        self.assertTrue(len(volumes) >= 10)

        # Get all the backup volumes. Verify that all the volumes are, in fact, backup
        # volumes.
        (volumes, broken_volumes) = \
            afs_resource.get_volumes_on_server(file_server_1, rx=r'^.*\.backup$', rx_all=True)

        for volume in volumes:
            self.assertEqual(volume.volume_type, AFSVolumeType.BK)

        print('finished test_get_volumes')

    def test_get_partition_info(self) -> None:
        """sdfgjksdf
        """
        runner = TestAFSAdmin.runner

        file_servers = AFSFileServer.make_file_server_objects(runner, fqdn_rx=r'^afssvr\d\d\.')

        # Get the first non-secure file server
        file_server1 = None
        for file_server in file_servers:
            if ((file_server.fqdn is not None) and
               (re.search(r'^afssvr\d\d.*$', file_server.fqdn))):
                file_server1 = file_server
                break

        self.assertIsNotNone(file_server1)
        assert(file_server1 is not None)

        partitions = AFSFileServerPartition.get_partitions(runner, file_server1.identifier())
        for partition in partitions:
            self.assertRegex(partition.name, r'/vicep')

        # Get the sizes of one of these partitions.
        (used_KB, total_KB) = AFSFileServerPartition.get_partition_sizes(runner, file_server1.identifier(), partitions[0].name)
        self.assertRegex(str(used_KB),  r'^\d+$')
        self.assertRegex(str(total_KB), r'^\d+$')
        self.assertTrue((used_KB/total_KB) < 1.0)

    def test_complicated_searches(self) -> None:
        """Some complicated searches.
        """

        ## Search 1. Find all RW volumes in afssvr01 or afssvr02 that do not have a
        ##           BK volume on the same volume.
        runner = TestAFSAdmin.runner
        afs_resource   = TestAFSAdmin.afs_resource

        file_servers = AFSFileServer.make_file_server_objects(runner, fqdn_rx=r'^afssvr0(1|2)\..*$')

        # Get the volumes on each server.
        for file_server in file_servers:
            #print(file_server)
            (volumes, broken_volumes) = afs_resource.get_volumes_on_server(file_server, rx_all=True)

        ## Search 2. Find all "broken" volumes.
        if (True):
            file_servers = AFSFileServer.make_file_server_objects(runner, fqdn_rx=r'^afssvr0\d\..*$')
            for file_server in file_servers:
                print(f"counter is {runner.counter.get_count()}")
                print(f"looking for broken volumes on {file_server.fqdn}")
                (volumes, broken_volumes) = afs_resource.get_volumes_on_server(file_server, rx_all=True)
                print(broken_volumes)

