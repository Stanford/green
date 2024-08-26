"""Unit testing.
"""
import unittest

import datetime
import logging
import pytz
import sys

from stanford.green import random_uid

from stanford.green.zulutime import is_zulu_string
from stanford.green.zulutime import zulu_string_to_utc
from stanford.green.zulutime import dt_to_zulu_string

from stanford.green.ldap import account_attribute_is_single_valued
from stanford.green.ldap import account_attribute_is_multi_valued
from stanford.green.ldap import people_attribute_is_single_valued
from stanford.green.ldap import people_attribute_is_multi_valued
from stanford.green.ldap import LDAP

## Logging
logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

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

if __name__ == '__main__':
    unittest.main()
