""" test_api_token_handling unit tests. For use from Aptana, the debug configuration must be of type "Python Unit Test" with
Main executable:
${workspace_loc:TriggeredMessagingV1/python/lib/tests/test_api_token_handling.py}

"""

import xmlrunner # http://www.stevetrefethen.com/blog/Publishing-Python-unit-test-results-in-Jenkins.aspx
import unittest
import os

from tms_base_test_case.tms_base_test_case import TMSBaseTestCase
from pydotmailer.pydotmailer import PyDotMailer

import logging
logger = logging.getLogger(__name__)


"""
 to go with these tests, you will need a file called secrets.py with details of your dotMailer account. The contents should be of the form:
class Secrets():
    api_username = "apiuser-1234567890@apiconnector.com"
    api_password = "sd234lkj2"
    campaign_id = 1234567 # a test campaign to be sent by the tests
    test_address = 'blackhole@triggeredmessaging.com'
    address_book_id = 565970
"""
from secrets import Secrets

def resolve_relative_path(file, rel_path):
    """ resolve a path that's relative to the current executing .py (i.e. usually the caller of this function)
    Example Usage: 
    abs_path = resolve_relative_path(__file__,'/fixtures/)
    """
    pathname = os.path.dirname(os.path.realpath(file))  # folder this .py is executing in     
    file_path = os.path.normpath( os.path.join(pathname, rel_path) ) 
    return file_path

class TestPyDotMailer(TMSBaseTestCase):
    def setUp(self):
        #global server_process
        #logger.info('TestPyDotMailer Starting and initialising API server. ')
        # run the server process that we need for our tests.
        #dir_test_code = os.path.dirname(__file__) # directory containing the current .py
        #self.start_server_process(['node', '%s/../../node/personServer/personServer.js' % (dir_test_code),'-n test_personServer','--debug','-r testserver', '-i 0'])
        #self.start_server_process(['python', self.resolve_relative_path(__file__,'../tms_api/tms_api_server_base.py' ),'-n test_api_server','--debug','-r testserver', '-i 0', '-s 18001', '-e 18199'])
        self.dot_mailer = PyDotMailer(api_username = Secrets.api_username, api_password=Secrets.api_password )
        self.address_book_id = Secrets.address_book_id # comes from dotmailer UI, under Contacts, Edit Address Book. Look for the field with label "id"
        # must be an address book specially created for your test purposes, cannot use the built-in address books like "test"
        pass
    
                    
    def test_add_contacts_to_address_book(self):
        """ Test function to test add_contacts_to_address_book. """
        logger.info("test_api_tokens starting")

        contacts_filename = "fixtures/test_contacts.csv"
        s_contacts = open(self.resolve_relative_path(__file__,contacts_filename), 'r').read()

        dict_result = self.dot_mailer.add_contacts_to_address_book(address_book_id=self.address_book_id, s_contacts=s_contacts, wait_to_complete_seconds=60)

        if not dict_result.get('ok'):
            logger.error("Failure return: %s" % (dict_result) )
        self.assertTrue(dict_result.get('ok'), 'add_contacts_to_address_book returned failure ')


        # =======
        
    def test_add_and_send_single(self):
        """ test function to test single contact functions e.g.
        get_contact_by_email and send_campaign_to_contact
        """
        logger.info("test_add_and_send_single starting")
        
        email = Secrets.test_address  
        # first ensure this address is in an address book. 
        dict_result = self.dot_mailer.add_contacts_to_address_book(address_book_id=self.address_book_id, s_contacts='email\n%s\n' % email, wait_to_complete_seconds=60)
        self.assertTrue(dict_result.get('ok'), "creating test address failed")

        # now get the ID for this address. 
        dict_result = self.dot_mailer.get_contact_by_email(email)
        
        # dict_result.get('result') is of type 'instance' and contains an APIContact record. See pydotmailer function definition for details. 
      
        campaign_id = Secrets.campaign_id
        contact_id = dict_result.get('result').ID

        dict_result = self.dot_mailer.send_campaign_to_contact(campaign_id=campaign_id, contact_id=contact_id) # , send_date=send_date)
        self.assertTrue(dict_result.get('ok'), "sending single message failed")

        logger.info('All done, exiting. ')

    

# use a custom TestRunner to create JUnit output files in TriggeredMessagingV1/results
# in jenkins, Junit pattern is results/*.xml
if __name__ == '__main__':
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output=resolve_relative_path(__file__,'../../../results')))
