
# influenced by https://github.com/JeremyJones/dotmailer-client/blob/master/dotmailer.py
# dotMailer docs at http://www.dotmailer.co.uk/api/

import urllib
import urllib2
import sys

import base64, time
from datetime import datetime, timedelta

from urlparse import urlparse
import suds
from suds.client  import Client as SOAPClient

__version__ = '0.1.1'

try:
    import simplejson as json
except ImportError:
    import json # fall back to traditional json module. 
    
import logging
logger = logging.getLogger(__name__)


class PyDotMailer(object):
    version = '0.1'
    
    # Cache the information on the API location on the server
    api_url = ''
    
    # Default to a 300 second timeout on server calls. Not used at present. 
    timeout = 300
    
    def __init__(self, api_username='', api_password='', secure=True, timeout=300):
        '''
        Connect to the dotMailer API for a given list.
        
        @param string $apikey Your dotMailer apikey
        @param string $secure Whether or not this should use a secure connection
        '''
        
        # Default to a 300 second timeout on server calls. Not used at present. TODO - implement.  
        self.timeout = timeout
        
        # Define whether we use SSL
        self.secure = secure or False
        if secure:
            self.api_url = 'https://apiconnector.com/API.asmx?WSDL'
        else:
            self.api_url = 'http://apiconnector.com/API.asmx?WSDL'
            
        self.client = SOAPClient(self.api_url)
        self.api_username = api_username
        self.api_password = api_password
 
 
    def add_contacts_to_address_book(self, address_book_id, s_contacts, wait_to_complete_seconds = False):
        """
        Add a list of contacts to the address book
        
        @param int the id of the address book
        @param string containing the contacts to be added. You may upload either a .csv or .xls file. It must contain one column with the heading "Email". Other columns must will attempt to map to your custom data fields.
        @param  seconds to wait.  
        @return dict  e.g. {'progress_id': 15edf1c4-ce5f-42e3-b182-3b20c880bcf8, 'ok': True, 'result': Finished}
        
        http://www.dotmailer.co.uk/api/address_books/add_contacts_to_address_book_with_progress.aspx
        """
        return_code=None
        base64_data  = base64.b64encode(s_contacts)
    
        progress_id  = self.client.service.AddContactsToAddressBookWithProgress(username=self.api_username, password=self.api_password, 
                                                                                addressbookID=address_book_id, data=base64_data, dataType='CSV')
        dict_result = {'ok':True}
        if wait_to_complete_seconds:
            dt_wait_until=datetime.utcnow() + timedelta(seconds=wait_to_complete_seconds) # wait for max
            while (not return_code or return_code.get('result')=='NotFinished') and \
                    datetime.utcnow() < dt_wait_until:
                return_code = self.get_contact_import_progress(progress_id)
                time.sleep(0.2)
            dict_result = return_code 

        dict_result.update( {'progress_id': progress_id })

        return dict_result #
 
    def get_contact_import_progress(self, progress_id):
        """
        @param int the progress_id from add_contacts_to_address_book
        @return dict  e.g. {'ok': False, 'result': NotFinished}    or    dict: {'ok': True, 'result': Finished}
        http://www.dotmailer.co.uk/api/contacts/get_contact_import_progress.aspx
        """
        return_code = self.client.service.GetContactImportProgress(username=self.api_username, password=self.api_password, 
                                                     progressID = progress_id)
        if return_code == 'Finished':
            dict_result = {'ok':True, 'result': return_code }
        else:
            dict_result = {'ok':False, 'result': return_code }
            
        return dict_result

    def send_campaign_to_contact(self, campaign_id, contact_id, send_date=datetime.utcnow()):
        """
        @param int campaign_id
        @param int contact_id
        @param datetime date/time in server time when the campaign should be sent. 
        @return dict  e.g. {'ok': True} or {'ok': False, 'result': <return code> }
        http://www.dotmailer.co.uk/api/campaigns/send_campaign_to_contact.aspx
        """    
        # format the date in ISO format, e.g. "2012-03-28T19:51:00" for sending via SOAP call. 
        iso_send_date = self.dt_to_iso_date( send_date)
        return_code = self.client.service.SendCampaignToContact(username=self.api_username, password=self.api_password, 
                        campaignId= campaign_id, contactid=contact_id, sendDate=iso_send_date) #todo report inconsistent case to dm
        if return_code:
            # return code, which means an error 
            dict_result = {'ok':False, 'result': return_code }
        else:
            # no return, which means no error. 
            dict_result = {'ok':True }
            
        return dict_result

    def get_contact_by_email(self, email):
        """
        @param string email address to search for.
        @return dict  e.g. {'ok': True, 'result': (APIContact){
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
                     }}                       
            http://www.dotmailer.co.uk/api/contacts/get_contact_by_email.aspx
        """
        return_code = self.client.service.GetContactByEmail(username=self.api_username, password=self.api_password, 
                        email=email)
        dict_result = {'ok':True, 'result': return_code }
        return dict_result


    def dt_to_iso_date(self, dt):
        """ convert a python datetime to an iso date, e.g. "2012-03-28T19:51:00"
        ready to send via SOAP
        http://www.iso.org/iso/date_and_time_format
        """
        try:
            iso_dt = dt.strftime('%Y-%m-%dT%H:%M:%S')
        except:
            logger.exception('Exception converting dt to iso')
            iso_dt = None
        return iso_dt

    



"""
might implement a command line at some point. 
def main():
    
    try:
        addressbookid    = sys.argv[2] #should use argparse or similar. 
        contactsfilename = sys.argv[3]
    except IndexError:
        print "Usage: dotmailer addcontactstoaddressbook addressbookid contactsfilename\n"
        sys.exit(1)

    initial_data = open(contactsfilename, 'r').read()

    
"""

