""" test_api_token_handling unit tests. For use from Aptana, the debug configuration must be of type "Python Unit Test" with
Main executable:
${workspace_loc:TriggeredMessagingV1/python/lib/tests/test_api_token_handling.py}

"""

import xmlrunner # http://www.stevetrefethen.com/blog/Publishing-Python-unit-test-results-in-Jenkins.aspx
import unittest
from tms_utils.utils import resolve_relative_path
from tms_api.tms_api_client_base import ApiClientBase, NODE_TYPES, unregister_active_instances
#from tms_api.tms_api_server_base import run_server, shutdown_all

import time


#import os
from tms_base_test_case.tms_base_test_case import TMSBaseTestCase
from pydotmailer.pydotmailer import PyDotMailer

#import logging
#logging.basicConfig()
#logger = logging.getLogger(__name__)
#logging.getLogger().setLevel(logging.DEBUG) # set the level on the root logger. This controls the level sent to the console. Must be after all other imports.

import logging
from tms_logging.stack_logging import StackLoggingHandler, StackLoggingFormatter, log_function_start, log_function_end, tms_init_logging, ADMIN_USAGE, log_security_event
logger = tms_init_logging("test_api_token_handling")


"""
 to go with these tests, you will need a file called secrets.py with details of your dotMailer account. The contents should be of the form:
class Secrets():
    api_username = "apiuser-1234567890@apiconnector.com"
    api_password = "sd234lkj2"
    campaign_id = 1234567 # a test campaign to be sent by the tests
    
"""
from secrets import Secrets

class TestPyDotMailer(TMSBaseTestCase):
    def setUp(self):
        #global server_process
        #logger.info('TestPyDotMailer Starting and initialising API server. ')
        # run the server process that we need for our tests.
        #dir_test_code = os.path.dirname(__file__) # directory containing the current .py
        #self.start_server_process(['node', '%s/../../node/personServer/personServer.js' % (dir_test_code),'-n test_personServer','--debug','-r testserver', '-i 0'])
        #self.start_server_process(['python', self.resolve_relative_path(__file__,'../tms_api/tms_api_server_base.py' ),'-n test_api_server','--debug','-r testserver', '-i 0', '-s 18001', '-e 18199'])
        pass
    
                    
    def test_pydotmailer(self):
        """ Test function to todo. """
        logger.info("test_api_tokens starting")

        mailer = PyDotMailer(api_username = Secrets.api_username, api_password=Secrets.api_password )
        contacts_filename = "fixtures/test_contacts.csv"
        address_book_id = 615970 # comes from dotmailer UI, under Contacts, Edit Address Book. Look for the field with label "id"
        # must be an address book specially created for cart abandonmenr, cannot use the built-in address books like "test"
        s_contacts = open(self.resolve_relative_path(__file__,contacts_filename), 'r').read()

        dict_result = mailer.add_contacts_to_address_book(address_book_id=address_book_id, s_contacts=s_contacts, wait_to_complete_seconds=20)

        if not dict_result.get('ok'):
            logger.error("Failure return: %s" % (dict_result) )
        self.assertTrue(dict_result.get('ok'), 'add_contacts_to_address_book returned failure ')


        # =======
        email = 'test@blackhole.triggeredmessaging.com'
        dict_result = mailer.get_contact_by_email(email)
        
        """ dict_result.get('result') is of type 'instance' and contains e.g. 
        (APIContact){
               ID = 367568124
               Email = "test@blackhole.triggeredmessaging.com"
               AudienceType = "Unknown"
               DataFields = 
                  (ContactDataFields){
                     Keys = 
                        (ArrayOfString){
                           string[] = 
                              "FIRSTNAME",
                              "FULLNAME",
                              "GENDER",
                              "LASTNAME",
                              "POSTCODE",
                        }
                     Values = 
                        (ArrayOfAnyType){
                           anyType[] = 
                              None,
                              None,
                              None,
                              None,
                        }
                  }
               OptInType = "Unknown"
               EmailType = "Html"
               Notes = None
       """
        # dict_result.get('result').AudienceType == "Unknown"
      
        campaign_id = Secrets.campaign_id
        contact_id = dict_result.get('result').ID
        send_date = None

        dict_result = mailer.send_campaign_to_contact(campaign_id=campaign_id, contact_id=contact_id) # , send_date=send_date)
        self.assertTrue(dict_result.get('ok'), "sending single message failed")

        logger.info('All done, exiting. ')

    

# use a custom TestRunner to create JUnit output files in TriggeredMessagingV1/results
# in jenkins, Junit pattern is results/*.xml
if __name__ == '__main__':
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output=resolve_relative_path(__file__,'../../../results')))
