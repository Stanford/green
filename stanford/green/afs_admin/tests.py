import unittest

import textwrap

from stanford.green.afs_admin.volume   import Volume
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


    vos_examine_output=textwrap.dedent(vos_examine_output).strip()

    command_runner = CommandRunner.make_command_runner_direct()

    def test_basic(self):
        self.assertTrue(True)

    def test_parse_vos_examine_output(self):
        """Convert the output of vos examine into a volume object.
        """
        self.assertTrue(True)

        volumes = Volume.vos_examine_to_volume(TestAFSAdmin.vos_examine_output)
        volume0 = volumes[0]
        self.assertEqual(volume0.header.group_name, 'users.a.d')

    def test_make_volume_object(self):
        command_runner = TestAFSAdmin.command_runner
        afs_resource = AFSResourceManager(command_runner)
        volumes = afs_resource.create_volume_objects('users.a.e.readonly')

        self.assertTrue(len(volumes) > 1)

        # Get the first volume.
        volume0 = volumes[0]

        # All the volumes should have the same header information.
        for volume in volumes:
            self.assertEqual(volume.header, volume0.header)


    def test_make_volume_set(self):
        """sdfgjksdf
        """
        command_runner = TestAFSAdmin.command_runner
        afs_resource = AFSResourceManager(command_runner)
        volume_group = afs_resource.make_volume_group_object('users.a.e.readonly')
        print(f"VGVGVGVG {volume_group}")


