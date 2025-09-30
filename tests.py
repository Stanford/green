"""Unit testing.
"""
import unittest

import datetime
import logging
import pytz
import sys
import time

from stanford.green import random_uid

from stanford.green.zulutime import is_zulu_string
from stanford.green.zulutime import zulu_string_to_utc
from stanford.green.zulutime import dt_to_zulu_string

from stanford.green.ldap import account_attribute_is_single_valued
from stanford.green.ldap import account_attribute_is_multi_valued
from stanford.green.ldap import people_attribute_is_single_valued
from stanford.green.ldap import people_attribute_is_multi_valued
from stanford.green.ldap import LDAP

from stanford.green.oauth2 import AccessToken
from stanford.green.oauth2 import ApiAccessTokenEndpoint

from exponential_backoff_ca import ExponentialBackoff
from stanford.green.mais_apis.workgroup import WorkgroupAPI

from stanford.green.afs import AFS, AFSExecs
from stanford.green.afs.pts import PTS

## Logging
logger = logging.getLogger(__name__)
#logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

### ## #### ## #### ## #### ## #### ## #### ## #### ## #### ## #### ## #### ## #
def read_test_config():
    """Read the test config file test_config.yaml"""
    import yaml

    with open('test_config.yaml', 'r') as f:
        Config = yaml.safe_load(f)

    return Config

def read_secret(client_secret_path):
    with open(client_secret_path, 'r', encoding='utf-8') as file1:
        lines = file1.readlines()
        return lines[0].strip()

### ## #### ## #### ## #### ## #### ## #### ## #### ## #### ## #### ## #### ## #

class TestGreen(unittest.TestCase):

    # INVALID Zulu strings
    invalid_zulu_strings = [
        None,
        '2024-07-28T21:42:34',
        '2024-07-28T21:42:34.Z',
        '2024-07-28 T21:42:34Z',
    ]

    # VALID Zulu string
    valid_zulu_strings = [
        '2024-07-28T21:42:34Z',
        '2024-07-28T21:42:34.1Z',
        '2024-07-28T21:42:34.12Z',
        '2024-07-28T21:42:34.123Z',
        '2024-07-28T21:42:34.1234Z',
        '2024-07-28T21:42:34.12345Z',
        '2024-07-28T21:42:34.123456Z',
    ]

    def test_random_uid(self) -> None:
        for _ in list(range(1,20)):
            uid = random_uid()
            self.assertTrue(len(uid) >= 3, msg=f"'{uid}' is too short (no prefix)")
            self.assertTrue(len(uid) <= 8, msg=f"'{uid}' is too long (no prefix)")

        # Run this next one several times as the length
        # is randomly chosen so we want to give a good chance
        # to hit all the possible lengths.
        for _ in list(range(1,20)):
            uid = random_uid(prefix='abc')
            self.assertRegex(uid, r'^abc')
            self.assertTrue(len(uid) == 8, msg=f"'{uid}' is not eight characters (prefix)")

        for i in list(range(3,8)):
            self.assertTrue(len(random_uid(length=i)) == i)

        with self.assertRaises(Exception) as _:
            # Put in a prefix that is too long (remember that sunetid's
            # cannot be longer than 8 characters).
            random_uid(prefix='abcdefghijk')

        with self.assertRaises(Exception) as _:
            # Put in a length that is too long.
            random_uid(length=9)

        with self.assertRaises(Exception) as _:
            # Put in a length that is too short.
            random_uid(length=2)

    def test_is_zulu_string(self) -> None:

        for zulu_string in TestGreen.valid_zulu_strings:
            self.assertTrue(is_zulu_string(zulu_string), f"string is {zulu_string}")

        for zulu_string in TestGreen.invalid_zulu_strings:
            self.assertFalse(is_zulu_string(zulu_string), f"string is {zulu_string}")

    def test_zulu_string_to_utc(self):

        # Get the "base" time, that is, the one without decimal time.
        # We convert all of these and ensure the date difference is less than
        # two seconds.
        base_datetime = zulu_string_to_utc(TestGreen.valid_zulu_strings[0])

        for zulu_string in TestGreen.valid_zulu_strings:
            current_datetime = zulu_string_to_utc(zulu_string)
            diff_seconds = abs((base_datetime - current_datetime ).total_seconds())
            self.assertTrue(diff_seconds < 2.0)

            # Verify that current_datetime is timezone-aware and has the UTC
            # timezone
            self.assertIsNotNone(current_datetime.tzinfo)
            self.assertTrue(abs(current_datetime.utcoffset().total_seconds()) < 0.0001)

        # Verify that zulu_string_to_utc raises a ValueError when passed an invalid
        # Zulu string.
        for zulu_str in TestGreen.invalid_zulu_strings:
            with self.assertRaises(ValueError) as _:
                _ = zulu_string_to_utc(zulu_str)

    def test_dt_to_zulu_string(self):

        # None as an argument should raise a ValueError.
        with self.assertRaises(ValueError) as _:
            _ = dt_to_zulu_string(None)

        # If the datetime.datetime object is not timezone aware this
        # should also raise a ValueError.
        with self.assertRaises(ValueError) as _:
            _ = dt_to_zulu_string(datetime.datetime.now())

        # Get the current time as local timezone-aware object.
        local_tz = pytz.timezone('America/New_York')
        local_time = datetime.datetime.now(local_tz)
        self.assertTrue(is_zulu_string(dt_to_zulu_string(local_time)))
        print(dt_to_zulu_string(local_time))


    def test_ldap_attributes(self):
        ## ACCOUNTS TREE
        single_valued_account_attributes = [
            'suAfsHomeDirectory',
            'suEmailStatus',
            'dn',
            'uid',
            'suLelandStatus',
            'suCreateAgent',
            'suPtsStatus',
            'suAfsHomeDirectory',
            'suDialinStatus',
            'suEmailQuota',
            'suSeasLocal',
            'suAfsStatus',
            'suAccountStatus',
            'suCreateAPI',
            'suEmailStatus',
            'suSeasUriRouteTo',
            'suEntryStatus',
            'uidNumber',
            'krb5PrincipalName',
            'loginShell',
            'homeDirectory',
            'suSeasStatus',
            'suPtsUid',
            'suKerberosStatus',
            'owner',
            'gidNumber',
            'seeAlso',
            'suEmailAccountType',
            'suSeasSunetIDPreferred',
            'suSeasEmailSystem',
            'suEmailSMTPEnabled',
            'suNameLF',
            'suName',
            'cn',
            'gecos',
            'suKerberosPasswordExpiration',
        ]

        multi_valued_account_attributes = [
            'suPrivilegeGroup',
            'suSeasSunetID',
            'suMailDrop',
        ]

        for attribute in single_valued_account_attributes:
            self.assertTrue(account_attribute_is_single_valued(attribute), f"{attribute} is single-valued")
            self.assertFalse(account_attribute_is_multi_valued(attribute), f"{attribute} is not multi-valued")

        for attribute in multi_valued_account_attributes:
            self.assertFalse(account_attribute_is_single_valued(attribute))
            self.assertTrue(account_attribute_is_multi_valued(attribute))

        ## PEOPLE TREE
        single_valued_people_attributes = [
            'dn',
            'suMailCode',
            'suGwAffilCode1',
            'suVisibHomePhone',
            'suRegID',
            'o',
            'suRegisteredName',
            'suRegisteredNameLF',
            'suUnivID',
            'uid',
            'suVisibAffiliation1',
            'suVisibMailCode',
            'suVisibAffilAddress1',
            'suVisibStreet',
            'suVisibAffilPhone1',
            'suGALsuRegID',
            'suGALuid',
            'suDisplayNameLast',
            'suGALsuDisplayNameLast',
            'suUniqueIdentifier',
            'suGALsuUniqueIdentifier',
            'homePhone',
            'homePostalAddress',
            'suVisibEmail',
            'mobile',
            'suVisibMobilePhone',
            'suGALmobile',
            'suMailAddress',
            'suPermanentAddress',
            'suPermanentPhone',
            'suVisibSunetID',
            'suVisibTelephoneNumber',
            'suVisibPermanentPhone',
            'suVisibHomeAddress',
            'suVisibPermanentAddress',
            'suVisibMailAddress',
            'suSunetIDPreferred',
            'suVisibIdentity',
            'suDisplayNameFirst',
            'suGALsuDisplayNameFirst',
            'suProxyCardNumber',
            'suCardNumber',
            'street',
            'postalAddress',
            'suGwAffilAddress1',
            'title',
            'eduPersonOrgDN',
            'eduPersonPrincipalName',
            'eduPersonScopedAffiliation',
            'eduPersonPrimaryAffiliation',
            'eduPersonAffiliation',
            'eduPersonUniqueId',
            'eduPersonPrimaryOrgUnitDN',
            'ou',
            'suPrimaryOrganizationName',
            'description',
            'suPrimaryOrganizationID',
            'eduPersonOrgUnitDN',
            'suGwAffiliation1',
            'suGwAffilDate1',
            'suMobileID',
            'mail',
            'suGALmail',
            'suDisplayNameMiddle',
            'displayName',
            'suDisplayNameLF',
            'suGALsuDisplayNameMiddle',
            'suGALdisplayName',
            'suGALsuDisplayNameLF',
        ]

        multi_valued_people_attributes = [
            'suSN',
            'suGwAffilCode',
            'suDisplayAffiliation',
            'suAffiliation',
            'suAffilStandardHours',
            'suGwAffilPhone1',
            'suGwAffilPhone2',
            'suGwAffilPhone3',
            'suGwAffilPhone4',
            'suGwAffilPhone5',
            'suGALsuSearchID',
            'suGALsuSunetID',
            'telephoneNumber',
            'suGALtelephoneNumber',
            'sn',
            'suGALsn',
            'givenName',
            'suGivenName',
            'suGALgivenName',
            'suGALcn',
            'suPrivilegeGroup',
            'suGwAffiliation',
            'suOU',
            'suAffilJobCode',
            'suAffilJobDescription',
            'suCN',
            'cn',
            'suGeneralID',
            'suSearchID',
            'suSunetID',
        ]

        for attribute in single_valued_people_attributes:
            self.assertTrue(people_attribute_is_single_valued(attribute), f"{attribute} is single-valued")
            self.assertFalse(people_attribute_is_multi_valued(attribute), f"{attribute} is not multi-valued")

        for attribute in multi_valued_people_attributes:
            self.assertFalse(people_attribute_is_single_valued(attribute))
            self.assertTrue(people_attribute_is_multi_valued(attribute))


        # Do a search
        ldap1 = LDAP()
        basedn =    'dc=stanford,dc=edu'
        filterstr = 'uid=adamhl'
        results = ldap1.search(basedn, filterstr=filterstr)

        results = ldap1.sunetid_account_info('adamhl')
        #print(results)

        results = ldap1.sunetid_account_info('adamhl', attrlist=['uid', 'suMailDrop'])
        print(results)

        results = ldap1.sunetid_people_info('adamhl', attrlist=['sn', 'displayName'])
        print(results)

        results = ldap1.sunetid_info('adamhl', attrlist=['suMailDrop', 'displayName'])
        print(results)

class TestGreenWorkgroupAPI(unittest.TestCase):

    BASE_URL  = 'https://aswsuat.stanford.edu/mais/workgroupsvc/workgroups/2.0'
    CERT_PATH = 'wg-api.crt'
    KEY_PATH  = 'wg-api.key'

    def test_list_members_and_admins(self):
        Config = read_test_config()
        workgroup_name = Config['workgroup_api']['workgroup_name']

        wg_api = WorkgroupAPI(
            base_url=TestGreenWorkgroupAPI.BASE_URL,
            cert_path=TestGreenWorkgroupAPI.CERT_PATH,
            key_path=TestGreenWorkgroupAPI.KEY_PATH,
            name=workgroup_name
        )

        str_representation = str(wg_api)
        self.assertIn(workgroup_name, str_representation)
        self.assertIn(TestGreenWorkgroupAPI.BASE_URL, str_representation)

        members = wg_api.list_members()

        # Remove all the members:
        for member in members:
            print(f"removing member {member}")
            wg_api.remove_user(member)

        # Wait until the removals have settled.
        for i in range(8):
            members = wg_api.list_members()
            if (len(members) == 0):
                # We are done.
                break
            # Skeep a bit before trying again.
            print(f"sleeping a bit to give removals a chance to settle")
            time.sleep(5.0)
        # ###        # ###        # ###        # ###        # ###        # ###

        members = wg_api.list_members()
        self.assertEqual(members, [], "there should be no members right now")

        # Add some members
        members_to_add = ['jholder']
        for member in members_to_add:
            print(f"adding member {member}")
            wg_api.add_user(member)

        # Wait until the adds have settled.
        for i in range(15):
            members = wg_api.list_members()
            if (len(members) == len(members_to_add)):
                # We are done.
                break
            # Sleep a bit before trying again.
            print(f"sleeping a bit to give adds a chance to settle")
            time.sleep(7.0)

        members = wg_api.list_members()
        self.assertEqual(len(members), len(members_to_add))


class TestGreenOAuth2(unittest.TestCase):

    Config = read_test_config()

    def test_oauth2_get_token(self):

        time_slot_secs = 3.0  # The number of seconds in each time slot.
        num_iterations = 4    # The number of iterations.
        limit_value    = 4.0  # Don't wait any longer than this number of seconds.
        exp_backoff    = ExponentialBackoff(time_slot_secs, num_iterations,
                                            limit_value=limit_value, debug=True)

        url                = TestGreenOAuth2.Config['oauth2']['url']
        client_id          = TestGreenOAuth2.Config['oauth2']['client_id']
        client_secret_path = TestGreenOAuth2.Config['oauth2']['client_secret_path']

        client_secret = read_secret(client_secret_path)

        for use_lib in ['requests', 'urllib']:
            print(f"testing use_lib '{use_lib}'")
            api_access    = ApiAccessTokenEndpoint('oauth2', url, client_id, client_secret,
                                                   exp_backoff, scopes=['read', 'list'],
                                                   use_lib=use_lib, verbose=True)
            access_token = api_access.get_token()
            token        = access_token.token

            self.assertTrue(len(token) > 20)
            self.assertIsNotNone(access_token.expires_at)


class TestGreenAFS(unittest.TestCase):

    def test_find_exec(self):
        possible_execs = ['/etc/', '/sdlfkjsdfl', '/usr/bin/ls']
        self.assertEqual(AFSExecs.find_exec(possible_execs), '/usr/bin/ls')

        all_bad = ['sdfkljsd', '/sdlfkjsdfl', '/sdfsdf/sdf/sdf/sdf']
        with self.assertRaises(ValueError) as _:
            AFSExecs.find_exec(all_bad)

        all_dirs = ['/etc/', '/etc', '/var/log']
        with self.assertRaises(ValueError) as _:
            AFSExecs.find_exec(all_dirs)

        empty = []
        with self.assertRaises(ValueError) as _:
            AFSExecs.find_exec(empty)

        # Check that the executables are set properly.
        self.assertIn('pts', AFSExecs.pts)
        self.assertIn('vos', AFSExecs.vos)
        self.assertIn('fs',  AFSExecs.fs)


    def test_pts_exec(self):
        # Check that a pts exists
        afs = AFS(basedir='/afs/ir', verbose=True)

        pts = PTS(name='adamhl', verbose=True)
        self.assertTrue(pts.exists())

        pts = PTS(name='bogusbogus', verbose=True)
        self.assertFalse(pts.exists())

        pts = PTS(name='adamhl', verbose=True)
        info = pts.get_info()


if __name__ == '__main__':
    #unittest.main()
    #unittest.main(argv=['', 'TestGreenOAuth2'])
    unittest.main(argv=['', 'TestGreenAFS'])
