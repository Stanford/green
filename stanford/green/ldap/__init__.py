"""Useful LDAP functions.

--------
Overview
--------

LDAP functions useful for Stanford-based applications. Currently the
only authentication method supported when connecting to an LDAP server is GSSAPI
(Kerberos).

--------
Examples
--------

Determine if a Stanford attribute is single- or multi-valued::

  >>> from stanford.green.ldap import attribute_is_multi_valued
  >>> attribute_is_multi_valued('uid')
  False
  >>> attribute_is_multi_valued('suMailDrop')
  True

Connect to the main Stanford LDAP server and get a user's accounts-tree
information (this assumes you have a valid Kerberos context)::

  from stanford.green.ldap import LDAP

  ldap1 = LDAP()
  results = ldap1.sunetid_account_info('jstanford')  # Get account tree LDAP information for user 'jstanford'
  results = ldap1.sunetid_people_info('jstanford')   # Get people tree LDAP information for user 'jstanford'
  results = ldap1.sunetid_info('jstanford')          # Get BOTH account and people tree LDAP information for user 'jstanford'

"""
import logging
import ldap      # type: ignore
import ldap.sasl # type: ignore

## TYPING
from typing import Optional, Any, Tuple
LDAPResult = dict[str, dict[str, str|list[str]]]
## END OF TYPING

## Set up logging
logger = logging.getLogger(__name__)

class GreenUnknownLDAPAttribute(Exception):
    """Used when an unrecognized attribute found"""
    pass

class GreenLDAPNoResultsException(Exception):
    """Used when no LDAP results are found"""
    pass


"""

The following mappings are derived in large-part from the data-definition pages at
https://uit.stanford.edu/service/directory/datadefs/accounts and
https://uit.stanford.edu/service/directory/datadefs/people

However, some attributes in the two trees not listed on those pages have
been added (e.g., suPrivilegeGroup).
"""

ACCOUNT_ATTRIBUTE_TO_MULTIPLICITY = {
    'cn': 'single',
    'description': 'multi',
    'gecos': 'single',
    'gidNumber': 'single',
    'homeDirectory': 'single',
    'krb5PrincipalName': 'single',
    'loginShell': 'single',
    'owner': 'single',
    'seeAlso': 'single',
    'suAccountStatus': 'single',
    'suAfsHomeDirectory': 'single',
    'suAfsStatus': 'single',
    'suAutoreplyAlias': 'multi',
    'suAutoreplyForward': 'single',
    'suAutoreplyMsg': 'single',
    'suAutoreplyStart': 'multi',
    'suAutoreplyStatus': 'single',
    'suAutoreplyStop': 'multi',
    'suAutoreplySubj': 'single',
    'suCreateAgent': 'single',
    'suCreateAPI': 'single',
    'suDescription': 'multi',
    'suDialinStatus': 'single',
    'suEmailAccountType': 'single',
    'suEmailAdmin': 'multi',
    'suEmailQuota': 'single',
    'suEmailStatus': 'single',
    'suEntitlementName': 'multi',
    'suEntitlementStatus': 'single',
    'suEntryStatus': 'single',
    'suIdentifies': 'single',
    'suGuestAltLogin': 'single',
    'suGuestName': 'single',
    'suGuestStatus': 'single',
    'suGuestUuid': 'single',
    'suKerberosStatus': 'single',
    'suKrb4Name': 'multi',
    'suLelandStatus': 'single',
    'suMailDrop': 'multi',
    'suName': 'single',
    'suNameLF': 'single',
    'suPtsStatus': 'single',
    'suPtsUid': 'single',
    'suSeasForward': 'multi',
    'suSeasLocal': 'single',
    'suSeasStatus': 'single',
    'suSeasSunetID': 'multi',
    'suSeasSunetIDPreferred': 'single',
    'SuSeasEmailSystem': 'single',
    'suSeasUriRouteTo': 'single',
    'suService': 'multi',
    'uid': 'single',
    'uidNumber': 'single',
}

# Add some attributes not on the data definition page.
ACCOUNT_ATTRIBUTE_TO_MULTIPLICITY['dn'] = 'single'
ACCOUNT_ATTRIBUTE_TO_MULTIPLICITY['suPrivilegeGroup'] = 'multi'
ACCOUNT_ATTRIBUTE_TO_MULTIPLICITY['suSeasEmailSystem'] = 'single'
ACCOUNT_ATTRIBUTE_TO_MULTIPLICITY['suEmailSMTPEnabled'] = 'single'
ACCOUNT_ATTRIBUTE_TO_MULTIPLICITY['suKerberosPasswordExpiration'] = 'single'

PEOPLE_ATTRIBUTE_TO_MULTIPLICITY = {
    'cn': 'multi',
    'description': 'single',
    'displayName': 'single',
    'facsimileTelephoneNumber': 'single',
    'fax': 'single',
    'generationQualifier': 'single',
    'givenName': 'multi',
    'gn': 'multi',
    'homePhone': 'single',
    'homeTelephoneNumber': 'single',
    'homePostalAddress': 'single',
    'labeledURI': 'single',
    'mail': 'single',
    'rfc822Mailbox': 'single',
    'mobile': 'single',
    'mobileTelephoneNumber': 'single',
    'o': 'single',
    'organizationName': 'single',
    'ou': 'single',
    'organizationalUnitName': 'single',
    'pager': 'single',
    'pagerTelephoneNumber': 'single',
    'personalTitle': 'single',
    'postalAddress': 'single',
    'sn': 'multi',
    'surname': 'multi',
    'street': 'single',
    'streetAddress': 'single',
    'suAffiliation': 'multi',
    'suAffilJobCode': 'multi',
    'suAffilJobDescription': 'multi',
    'suAffilStandardHours': 'multi',
    'suCardNumber': 'single',
    'suCN': 'multi',
    'suDisplayAffiliation': 'multi',
    'suDisplayNameFirst': 'single',
    'suDisplayNameLast': 'single',
    'suDisplayNameLF': 'single',
    'suDisplayNameMiddle': 'single',
    'suDisplayNamePrefix': 'single',
    'suDisplayNameSuffix': 'single',
    'suEmailPager': 'single',
    'suFacultyAppointment': 'single',
    'suFacultyAppointmentShort': 'single',
    'suGeneralID': 'multi',
    'suGivenName, suGN': 'multi',
    'suGwAffilAddress1': 'single',
    'suGwAffilAddress2': 'single',
    'suGwAffilAddress3': 'single',
    'suGwAffilAddress4': 'single',
    'suGwAffilAddress5': 'single',
    'suGwAffiliation': 'multi',
    'suGwAffiliation1': 'single',
    'suGwAffiliation2': 'single',
    'suGwAffiliation3': 'single',
    'suGwAffiliation4': 'single',
    'suGwAffiliation5': 'single',
    'suGwAffilCode': 'multi',
    'suGwAffilCode1': 'single',
    'suGwAffilCode2': 'single',
    'suGwAffilCode3': 'single',
    'suGwAffilCode4': 'single',
    'suGwAffilCode5': 'single',
    'suGwAffilDate1': 'single',
    'suGwAffilDate2': 'single',
    'suGwAffilDate3': 'single',
    'suGwAffilDate4': 'single',
    'suGwAffilDate5': 'single',
    'suGwAffilFax1': 'multi',
    'suGwAffilFax2': 'multi',
    'suGwAffilFax3': 'multi',
    'suGwAffilFax4': 'multi',
    'suGwAffilFax5': 'multi',
    'suGwAffilInternalPager': 'multi',
    'suGwAffilMailCode1': 'single',
    'suGwAffilMailCode2': 'single',
    'suGwAffilMailCode3': 'single',
    'suGwAffilMailCode4': 'single',
    'suGwAffilMailCode5': 'single',
    'suGwAffilMobile': 'multi',
    'suGwAffilPager': 'multi',
    'suGwAffilPhone1': 'multi',
    'suGwAffilPhone2': 'multi',
    'suGwAffilPhone3': 'multi',
    'suGwAffilPhone4': 'multi',
    'suGwAffilPhone5': 'multi',
    'suLocalAddress': 'single',
    'suLocalPhone': 'single',
    'suMailAddress': 'single',
    'suMailCode': 'single',
    'suOtherName': 'multi',
    'suOu': 'multi',
    'suPermanentAddress': 'single',
    'suPermanentPhone': 'single',
    'suPrimaryOrganizationID': 'single',
    'suPrimaryOrganizationName': 'single',
    'suPrivilegeGroup': 'multi',
    'suProfile': 'single',
    'suProxyCardNumber': 'single',
    'suRegID': 'single',
    'suRegisteredName': 'single',
    'suRegisteredNameLF': 'single',
    'suResidenceCode': 'single',
    'suResidenceName': 'single',
    'suResidenceRequiredAttribute': 'multi',
    'suResidenceRoom': 'single',
    'suResidencePhone': 'single',
    'suResidenceTSO': 'single',
    'suSearchID': 'multi',
    'suSN': 'multi',
    'suStanfordEndDate': 'single',
    'suStudentType': 'multi',
    'suSunetID': 'multi',
    'suUniqueIdentifier': 'single',
    'suUnivID': 'single',
    'suVisibAffilAddress1': 'single',
    'suVisibAffilAddress2': 'single',
    'suVisibAffilAddress3': 'single',
    'suVisibAffilAddress4': 'single',
    'suVisibAffilAddress5': 'single',
    'suVisibAffiliation': 'multi',
    'suVisibAffiliation1': 'single',
    'suVisibAffiliation2': 'single',
    'suVisibAffiliation3': 'single',
    'suVisibAffiliation4': 'single',
    'suVisibAffiliation5': 'single',
    'suVisibAffilFax1': 'single',
    'suVisibAffilFax2': 'single',
    'suVisibAffilFax3': 'single',
    'suVisibAffilFax4': 'single',
    'suVisibAffilFax5': 'single',
    'suVisibAffilInternalPager': 'multi',
    'suVisibAffilMobile': 'multi',
    'suVisibAffilPager': 'multi',
    'suVisibAffilPhone1': 'single',
    'suVisibAffilPhone2': 'single',
    'suVisibAffilPhone3': 'single',
    'suVisibAffilPhone4': 'single',
    'suVisibAffilPhone5': 'single',
    'suVisibEmail': 'single',
    'suVisibFacsimileTelephoneNumber': 'single',
    'suVisibGwAffilCode': 'multi',
    'suVisibHomeAddress': 'single',
    'suVisibHomePage': 'single',
    'suVisibHomePhone': 'single',
    'suVisibIdentity': 'single',
    'suVisibLocalAddress': 'single',
    'suVisibLocalPhone': 'single',
    'suVisibMailAddress': 'single',
    'suVisibMailCode': 'single',
    'suVisibMobilePhone': 'single',
    'suVisibPagerEmail': 'single',
    'suVisibPagerPhone': 'single',
    'suVisibPermanentAddress': 'single',
    'suVisibPermanentPhone': 'single',
    'suVisibProfile': 'single',
    'suVisibStreet': 'single',
    'suVisibSunetID': 'single',
    'suVisibTelephoneNumber': 'single',
    'telephoneNumber': 'multi',
    'title': 'single',
    'uid': 'single',
    'userid': 'single',
}

# Add in the suGAL attributes. These attributes have the same multiplicty
# as the attributes they are derived from.
SUGAL_BASE_ATTRIBUTES = {
    'cn',
    'displayName',
    'generationQualifier',
    'givenName',
    'personalTitle',
    'sn',
    'suDisplayNameFirst',
    'suDisplayNameLast',
    'suDisplayNameLF',
    'suDisplayNameMiddle',
    'suDisplayNamePrefix',
    'suDisplayNameSuffix',
    'suFacultyAppointment',
    'suFacultyAppointmentShort',
    'suOtherName',
    'suRegID',
    'suUniqueIdentifier',
    'uid',
    'suEmailPager',
    'facsimileTelephoneNumber',
    'homePhone',
    'homePostalAddress',
    'postalAddress',
    'street',
    'labeledURI',
    'mail',
    'mobile',
    'pager',
    'suLocalAddress',
    'suResidenceRoom',
    'suLocalPhone',
    'suResidencePhone',
    'suMailAddress',
    'suPermanentAddress',
    'suPermanentPhone',
    'suSearchID',
    'suSunetID',
    'telephoneNumber',
}

SUGAL_ATTRIBUTE_TO_MULTIPLICITY = {}
for attribute_name in SUGAL_BASE_ATTRIBUTES:
    SUGAL_ATTRIBUTE_TO_MULTIPLICITY[f"suGAL{attribute_name}"] = PEOPLE_ATTRIBUTE_TO_MULTIPLICITY[attribute_name]

PEOPLE_ATTRIBUTE_TO_MULTIPLICITY_EXTRA = {
    'dn': 'single',
    'suGALsuRegID': 'single',
    'suSunetIDPreferred': 'single',
    'eduPersonOrgDN': 'single',
    'eduPersonPrincipalName': 'single',
    'eduPersonScopedAffiliation': 'single',
    'eduPersonPrimaryAffiliation': 'single',
    'eduPersonAffiliation': 'single',
    'eduPersonUniqueId': 'single',
    'eduPersonPrimaryOrgUnitDN': 'single',
    'eduPersonOrgUnitDN': 'single',
    'suOU': 'multi',
    'suMobileID': 'single',
    'suGivenName': 'multi',
    'suGwAffilQBFR1': 'single',
}

PEOPLE_ATTRIBUTE_TO_MULTIPLICITY |= SUGAL_ATTRIBUTE_TO_MULTIPLICITY
PEOPLE_ATTRIBUTE_TO_MULTIPLICITY |= PEOPLE_ATTRIBUTE_TO_MULTIPLICITY_EXTRA

# Put them together.
ATTRIBUTE_TO_MULTIPLICITY = ACCOUNT_ATTRIBUTE_TO_MULTIPLICITY | PEOPLE_ATTRIBUTE_TO_MULTIPLICITY

BASEDN          = "dc=stanford,dc=edu"
BASEDN_ACCOUNTS = "cn=accounts,dc=stanford,dc=edu"
BASEDN_PEOPLE   = "cn=people,dc=stanford,dc=edu"

def account_attribute_is_single_valued(attribute_name: str) -> bool:
    """Return True if `attribute_name` is a single-valued account-tree attribute, False otherwise.

    :param attribute_name: a string
    :type prefix: str
    :return: ``True`` if `attribute_name` is single-valued and a valid
      account-tree attribute, ``False`` otherwise.

    :raises GreenUnknownLDAPAttribute: if `attribute_name` is not a valid
      account-tree attribute name.

    """
    if (attribute_name in ACCOUNT_ATTRIBUTE_TO_MULTIPLICITY):
        return (ACCOUNT_ATTRIBUTE_TO_MULTIPLICITY[attribute_name] == 'single')
    else:
        msg = f"'{attribute_name}' is not an account-tree attribute"
        raise GreenUnknownLDAPAttribute(msg)

def account_attribute_is_multi_valued(attribute_name: str) -> bool:
    """Return True if `attribute_name` is multi-valued account-tree, False otherwise.

    :param attribute_name: a string
    :type prefix: str
    :return: ``True`` if `attribute_name` is a valid
      account-tree attribute and is multi-valued, ``False`` otherwise.

    :raises GreenUnknownLDAPAttribute: if `attribute_name` is not a valid
      account-tree attribute name.

    """
    return not account_attribute_is_single_valued(attribute_name)

def people_attribute_is_single_valued(attribute_name: str) -> bool:
    """Return True if `attribute_name` is single-valued people-tree, False otherwise.

    :param attribute_name: a string
    :type prefix: str
    :return: ``True`` if `attribute_name` is single-valued, ``False`` otherwise.

    :raises GreenUnknownLDAPAttribute: if `attribute_name` is not a valid
      people-tree attribute name.
    """
    if (attribute_name in PEOPLE_ATTRIBUTE_TO_MULTIPLICITY):
        return (PEOPLE_ATTRIBUTE_TO_MULTIPLICITY[attribute_name] == 'single')
    else:
        msg = f"'{attribute_name}' is not a people-tree attribute"
        raise GreenUnknownLDAPAttribute(msg)

def people_attribute_is_multi_valued(attribute_name: str) -> bool:
    """Return True if `attribute_name` is single-valued, False otherwise.

    :param attribute_name: a string
    :type prefix: str
    :return: ``True`` if `attribute_name` is single-valued, ``False`` otherwise.

    :raises GreenUnknownLDAPAttribute: if `attribute_name` is not a valid
      people-tree attribute name.
    """
    return not people_attribute_is_single_valued(attribute_name)

def attribute_is_single_valued(attribute_name: str) -> bool:
    """Return True if `attribute_name` is single-valued, False otherwise.

    :param attribute_name: a string
    :type prefix: str
    :return: ``True`` if `attribute_name` is single-valued, ``False`` otherwise.

    :raises GreenUnknownLDAPAttribute: if `attribute_name` is not a valid
      attribute name.
    """

    if (attribute_name in ATTRIBUTE_TO_MULTIPLICITY):
        return (ATTRIBUTE_TO_MULTIPLICITY[attribute_name] == 'single')
    else:
        msg = f"'{attribute_name}' is not a recognized attribute"
        raise GreenUnknownLDAPAttribute(msg)

def attribute_is_multi_valued(attribute_name: str) -> bool:
    """Return True if `attribute_name` is multi-valued, False otherwise.

    :param attribute_name: a string
    :type prefix: str
    :return: ``True`` if `attribute_name` is multi-valued, ``False`` otherwise.

    :raises GreenUnknownLDAPAttribute: if `attribute_name` is not a valid
      attribute name.
    """
    return not attribute_is_single_valued(attribute_name)

class LDAP():
    """The LDAP class.

    :param host: the LDAP host name, defaults to ``ldap.stanford.edu``
    :type prefix: str

    :param connect_on_init: set to ``True`` to connect ``host`` on object
      creation, ``False`` otherwise, defaults to ``True``.
    :type prefix: bool

    """

    def __init__(self,
                 host: str = 'ldap.stanford.edu',
                 connect_on_init: bool = True):
        self.host = host

        if (connect_on_init):
            self.ldap = self.connect()

    def connect(self) -> Any:
        """Create a connected ldap object.

        Currently, the only connection method is using GSSAPI. That is, there
        must be a valid Kerberos context.
        """
        ldap_conn = ldap.initialize(
            f"ldap://{self.host}"
        )
        ldap_conn.sasl_non_interactive_bind_s('GSSAPI')
        logger.debug(f"making LDAP SASL bind to {self.host}")

        return ldap_conn

    def scope_normalize(self, scope: str) -> Any:
        scopes = {
            'sub':  ldap.SCOPE_SUBTREE,
            'base': ldap.SCOPE_BASE,
            'one':  ldap.SCOPE_ONELEVEL,
        }

        # Add some aliases
        scopes['subtree']  = scopes['sub']
        scopes['onelevel'] = scopes['one']

        return scopes[scope]


    def process_result(self, result: Tuple[str, dict[str, list[Any]]]) -> Tuple[str, LDAPResult]:
        dn     = result[0]
        logger.info(f"dn is {dn}")

        values = result[1]

        return_values = {}
        for attribute in values.keys():
            # Skip objectClass
            if (attribute == 'objectClass'):
                continue

            if (attribute_is_single_valued(attribute)):
                single_value = values[attribute][0].decode("utf-8")
                return_values[attribute] = single_value
                logger.debug(f"{attribute}: {single_value}")
            else:
                multi_values = values[attribute]
                multi_values_decoded = []
                for multi_value in multi_values:
                    multi_values_decoded.append(multi_value.decode("utf-8"))

                return_values[attribute] = multi_values_decoded
                logger.debug(f"{attribute}: {multi_values_decoded}")

        return (dn, return_values)


    def search(
            self,
            basedn:    str,
            filterstr: str='(objectClass=*)',
            attrlist:  Optional[list[str]]=None,
            scope:     str='sub'
    ) -> dict[str, LDAPResult]:
        """Perform an LDAP search.

        :param basedn: base DN on which to search
        :type basedn: str

        :param filterstr: a valid LDAP filter clause (e.g., ``(uid=jstanford)``)
        :type filterstr: str

        :param attrlist: a list of attributes to return
        :type attrlist: list[str]

        :param scope: the search scope; must be one "sub", "base", or "one".
        :type scope: str

        This method is a thin wrapper around the ldap package's search method. The
        difference is in how it behaves when there are no results and the format
        of the returned value.

        The returned result is a dict where each key is the dn of some
        tree result. Each key maps to another dict containing the attributes. This
        is most easily explained with an example::

          basedn = "dc=stanford,dc=edu"
          filterstr = "uid=jstanford"
          results = search(basdn, filterstr=filterstr)
          #
          # results will look something like
          # {
          #   'suRegID=f0d08565850320613717ebf068585447,cn=people,dc=stanford,dc=edu':
          #     {'suMailCode': '4321', 'suGwAffilCode1': 'stanford:staff', ... }
          #   'uid=jstanford,cn=accounts,dc=stanford,dc=edu':
          #     { 'uid': 'jstanford', 'suSeasSunetID': ['jstanford', 'jane.stanford'], ... }
          # }
          #
          # There are two keys in the above: the "suRegID=f0..." one and the "uid=jstanford,..." one.

        Note that the attributes are returned as either a string (for
        single-valued attributes) or a list (for multi-valued attributes).
        Furthermore, LDAP returns vaules as byte-strings so this method
        converts these byte-strings into regular utf8 strings.

        If no results are returned this method raises the
        `GreenLDAPNoResultsException` exception.

        """
        search_scope  = self.scope_normalize(scope)

        logger.debug(f"basedn:         {basedn}")
        logger.debug(f"search scope:   {search_scope}")
        logger.debug(f"search filter:  {filterstr}")
        logger.debug(f"attribute list: {attrlist}")

        ldap_result_id = self.ldap.search(
            basedn,
            search_scope,
            filterstr=filterstr,
            attrlist=attrlist
        )

        logger.debug(f"ldap_result_id is {ldap_result_id}")

        results = []
        end_of_results = False
        while not end_of_results:
            try:
                result_type, result_data = self.ldap.result(ldap_result_id, 0)
            except ldap.NO_SUCH_OBJECT as _:
                # No dn found, so nothing to add.
                logger.error("no such object")
                pass
            else:
                if result_type == ldap.RES_SEARCH_ENTRY:
                    logger.debug("found an LDAP entry")
                    results.append(result_data)
                else:
                    logger.debug("no more LDAP data")
                    end_of_results = True

        logger.info(f"found {len(results)} results")

        if (len(results) == 0):
            msg = "no LDAP results"
            raise GreenLDAPNoResultsException(msg)

        # Process the results
        result_set = {}
        for result in results:
            # The result will be of the form [(dn, {attributes})]
            (dn, attribute_values) = self.process_result(result[0])
            result_set[dn] = attribute_values

        return result_set

    def sunetid_account_info(self, sunetid: str, attrlist:  Optional[list[str]]=None) -> dict[str, LDAPResult]:
        """Return the account tree information for user with uid equal to ``sunetid``.

        :param sunetid: sunetid of user whose information you seek
        :type sunetid: str

        :param attrlist: a list of attributes to return
        :type attrlist: list[str]

        :raises GreenLDAPNoResultsException: if there are no results.

        Example::

          # results = LDAP.sunetid_account_info('jstanford')
          #
          # results will look something like
          # {
          #   'uid=jstanford,cn=accounts,dc=stanford,dc=edu':
          #     { 'uid': 'jstanford', 'suSeasSunetID': ['jstanford', 'jane.stanford'], ... }
          # }
          #

        This method (like :py:meth:`~search`) raises the
        :py:exc:`~GreenLDAPNoResultsException` exception if no results are
        returned, so be sure to trap that error if your code is OK with
        getting no results.

        """
        basedn    = BASEDN_ACCOUNTS
        filterstr = f"uid={sunetid}"
        return self.search(basedn, filterstr=filterstr, attrlist=attrlist)

    def sunetid_people_info(self, sunetid: str, attrlist:  Optional[list[str]]=None) -> dict[str, LDAPResult]:
        """Return the people tree information for user with uid equal to ``sunetid``.

        :param sunetid: sunetid of user whose information you seek
        :type sunetid: str

        :param attrlist: a list of attributes to return
        :type attrlist: list[str]

        :raises GreenLDAPNoResultsException: if there are no results.

        Example::

          # results = LDAP.sunetid_people_info('jstanford')
          #
          # results will look something like
          # {
          #   'suRegID=f0d08565850320613717ebf068585447,cn=people,dc=stanford,dc=edu':
          #     {'suMailCode': '4321', 'suGwAffilCode1': 'stanford:staff', ... }
          # }
          #

        This method (like :py:meth:`~search`) raises the
        :py:exc:`~GreenLDAPNoResultsException` exception if no results are
        returned, so be sure to trap that error if your code is OK with
        getting no results.

        """
        basedn    = BASEDN_PEOPLE
        filterstr = f"uid={sunetid}"
        return self.search(basedn, filterstr=filterstr, attrlist=attrlist)

    def sunetid_info(self, sunetid: str, attrlist:  Optional[list[str]]=None) -> dict[str, LDAPResult]:
        """Return the people and accounts tree information for user with uid equal to ``sunetid``.

        :param sunetid: sunetid of user whose information you seek
        :type sunetid: str

        :param attrlist: a list of attributes to return
        :type attrlist: list[str]

        :raises GreenLDAPNoResultsException: if there are no results.

        Example::

          # results = LDAP.sunetid_info('jstanford')
          #
          # results will look something like
          # {
          #   'uid=jstanford,cn=accounts,dc=stanford,dc=edu':
          #     { 'uid': 'jstanford', 'suSeasSunetID': ['jstanford', 'jane.stanford'], ... },
          #   'suRegID=f0d08565850320613717ebf068585447,cn=people,dc=stanford,dc=edu':
          #     {'suMailCode': '4321', 'suGwAffilCode1': 'stanford:staff', ... }
          # }
          #

        This method (like :py:meth:`~search`) raises the
        :py:exc:`~GreenLDAPNoResultsException` exception if no results are
        returned, so be sure to trap that error if your code is OK with
        getting no results.

        """
        basedn    = BASEDN
        filterstr = f"uid={sunetid}"
        return self.search(basedn, filterstr=filterstr, attrlist=attrlist)

