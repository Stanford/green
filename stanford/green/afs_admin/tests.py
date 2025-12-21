import unittest

import pathlib
import tempfile
import textwrap

from stanford.green.afs_admin.file_server import AFSFileServer

from stanford.green.afs_admin.volume   import Volume
from stanford.green.afs_admin.volume_type import AFSVolumeType

from stanford.green.afs_admin.resource import AFSResourceManager
from stanford.green.afs_admin.resource.command_runner import CommandRunner


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


    verbose = True
    #verbose = False

    vos_examine_output=textwrap.dedent(vos_examine_output).strip()

    command_runner = CommandRunner.make_command_runner_direct()
    afs_resource   = AFSResourceManager(command_runner, verbose=verbose)

    def test_basic(self):
        self.assertTrue(True)

    def test_parse_vos_examine_output(self):
        """Convert the output of vos examine into a volume object.
        """
        self.assertTrue(True)

        volumes = Volume.vos_examine_to_volume(TestAFSAdmin.vos_examine_output)
        volume0 = volumes[0]
        self.assertEqual(volume0.name, 'users.a.d')

    def test_make_volume_object(self):
        command_runner = TestAFSAdmin.command_runner
        afs_resource = AFSResourceManager(command_runner)
        volumes = afs_resource.create_volume_objects('users.a.e.readonly')

        self.assertTrue(len(volumes) > 1)

        # Get the first volume.
        volume0 = volumes[0]


    def test_make_volume_group(self):
        """sdfgjksdf
        """
        command_runner = TestAFSAdmin.command_runner
        afs_resource = AFSResourceManager(command_runner)
        volume_group = afs_resource.make_volume_group_object('users.a.e.readonly')
        print("")
        print(f"{volume_group}")

    def test_get_file_servers(self):
        """sdfgjksdf
        """
        command_runner = TestAFSAdmin.command_runner
        afs_resource = AFSResourceManager(command_runner)

        # Get the raw file server list
        raw_list = command_runner.run_vos_listfs()

        # This raw list should have several occurences of "UUID".
        lines = raw_list.splitlines()
        counter = 0
        for line in lines:
            if ("UUID" in line):
                counter = counter + 1

        # Should be several.
        self.assertTrue(counter > 3)

        ## 2. Get the list of FileServer objects.
        file_servers = afs_resource.make_file_server_objects()
        for file_server in file_servers:
            print(file_server.to_yaml())

    def test_get_volumes(self):
        """sdfgjksdf
        """

        command_runner = TestAFSAdmin.command_runner
        afs_resource   = TestAFSAdmin.afs_resource

        file_servers = afs_resource.make_file_server_objects()

        # Convert to a mapping of fqdn to file_server object
        fqdn_to_file_server = AFSFileServer.fqdn_to_file_server(file_servers)

        # Get the afssvr01 AFSFileServer object.
        file_server_1 = fqdn_to_file_server['afssvr01.stanford.edu']
        self.assertIsNotNone(file_server_1)

        # Run the run_vos_listvol method.
        with tempfile.NamedTemporaryFile(delete=True) as tmp:
            temp_file = pathlib.Path(tmp.name)
            command_runner.run_vos_listvol(file_server_1, temp_file)

            self.assertTrue(temp_file.exists())

            # Get the first few lines of temp_file to make sure we got
            # some output.
            with temp_file.open('r') as fh:
                lines = [next(fh) for _ in range(3)]  # read first three lines
                self.assertTrue(len(lines) == 3)
                for line in lines:
                    self.assertTrue(len(line) > 1)

        volumes = afs_resource.get_volumes(file_server_1)

        # There should be several volumes.
        self.assertTrue(len(volumes) >= 10)

        # Get the volumes but this time only get volumes with names
        # containing the letter "a".
        volumes = afs_resource.get_volumes(file_server_1, rx=r'a')
        print(len(volumes))

        # There should be several volumes.
        self.assertTrue(len(volumes) >= 10)

        # Get all the backup volumes. Verify that all the volumes are, in fact, backup
        # volumes.
        volumes = afs_resource.get_volumes(file_server_1, rx=r'^.*\.backup$', rx_all=True)
        for volume in volumes:
            self.assertEqual(volume.volume_type, AFSVolumeType.BK)

