# pydotmailer - A lightweight wrapper for the dotMailer API, written in Python.
# Copyright (c) 2012 Triggered Messaging Ltd, released under the MIT license
# Home page:
# https://github.com/TriggeredMessaging/pydotmailer/
# See README and LICENSE files.
#
# dotMailer API docs are at http://www.dotmailer.co.uk/api/
# This class was influenced by earllier work: https://github.com/JeremyJones/dotmailer-client/blob/master/dotmailer.py

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


    class ERRORS:
        """ Defines for error codes which we're deriving from the string the dotMailer returns.
        """
        ERROR_CAMPAIGN_NOT_FOUND = 'ERROR_CAMPAIGN_NOT_FOUND'
        ERROR_CAMPAIGN_SENDNOTPERMITTED = 'ERROR_CAMPAIGN_SENDNOTPERMITTED' # dotMailer tends to return this if you've run out of campaign credits or a similar issue.
        ERROR_GENERIC = 'ERROR_UNKNOWN' # code which couldn't be parsed.

    def __init__(self, api_username='', api_password='', secure=True):
        '''
        Connect to the dotMailer API for a given list.
        
        @param string $apikey Your dotMailer apikey
        @param string $secure Whether or not this should use a secure connection
        '''
        
        # Define whether we use SSL
        self.secure = secure or False
        if secure:
            self.api_url = 'https://apiconnector.com/API.asmx?WSDL'
        else:
            self.api_url = 'http://apiconnector.com/API.asmx?WSDL'

        # log connection as time can be significant.
        logger.debug("Connecting to web service")
        self.client = SOAPClient(self.api_url)
        logger.debug("Connected to web service")
        self.api_username = api_username
        self.api_password = api_password
        if (not api_username) or (not api_password):
            raise Exception('Bad username or password')

        self.last_exception = None
 
    def unpack_exception(self,e):
        """ unpack the exception thrown by suds. This contains a string code in e.fault.faultstring containing text e.g.
        Server was unable to process request. ---> Campaign not found ERROR_CAMPAIGN_NOT_FOUND
        Use this to set a suitable value for dict_result
        @param exception
        @return dict_result, e.g. {'ok':False, 'errors':[e.message], 'error_code':PyDotMailer.ERRORS.ERROR_CAMPAIGN_NOT_FOUND }
        """
        self.last_exception = e # in case caller cares
        fault_string = e.fault.faultstring
        error_code = None
        # todo clearly a more generic way of doing this would be good.
        if 'ERROR_CAMPAIGN_NOT_FOUND' in fault_string:
            error_code = PyDotMailer.ERRORS.ERROR_CAMPAIGN_NOT_FOUND
        elif 'ERROR_CAMPAIGN_SENDNOTPERMITTED' in fault_string:
            error_code = PyDotMailer.ERRORS.ERROR_CAMPAIGN_SENDNOTPERMITTED
        else:
            error_code = PyDotMailer.ERRORS.ERROR_GENERIC
        dict_result = {'ok':False, 'errors':[e.message], 'error_code': error_code }
        return dict_result


    def add_contacts_to_address_book(self, address_book_id, s_contacts, wait_to_complete_seconds = False):
        """
        Add a list of contacts to the address book
        
        @param int the id of the address book
        @param string containing the contacts to be added. You may upload either a .csv or .xls file. It must contain one column with the heading "Email". Other columns must will attempt to map to your custom data fields.
        @param  seconds to wait.  
        @return dict  e.g. {'progress_id': 15edf1c4-ce5f-42e3-b182-3b20c880bcf8, 'ok': True, 'result': Finished}
        
        http://www.dotmailer.co.uk/api/address_books/add_contacts_to_address_book_with_progress.aspx
        """
        dict_result = {'ok':True }
        return_code=None
        base64_data  = base64.b64encode(s_contacts)

        try:
            progress_id  = self.client.service.AddContactsToAddressBookWithProgress(username=self.api_username, password=self.api_password,
                                                                                    addressbookID=address_book_id, data=base64_data, dataType='CSV')
            dict_result = {'ok':True}
            if wait_to_complete_seconds:
                # retry loop...
                dt_wait_until=datetime.utcnow() + timedelta(seconds=wait_to_complete_seconds) # wait for max
                sleep_time = 0.2 # start with short sleep between retries
                while (not return_code or return_code.get('result')=='NotFinished') and \
                        datetime.utcnow() < dt_wait_until:
                    dict_result = self.get_contact_import_progress(progress_id)
                    time.sleep(sleep_time)
                    # gradually backoff with longer sleep intervals up to a max of 5 seconds
                    sleep_time = min( sleep_time * 2, 5.0)

            dict_result.update( {'progress_id': progress_id })
        except Exception as e:
            dict_result = self.unpack_exception(e)

        return dict_result #


    def add_contact_to_address_book(self, address_book_id, email_address, d_fields, email_type="Html", audience_type = "Unknown", opt_in_type = "Unknown"):
        """
        add a single contact into an address book. - uses AddContactToAddressBook
        @param int the id of the address book
        @param email_address The email address to add
        @param d_fields - dict containing the data to be added. e.g. { 'firstname': 'mike', 'lastname': 'austin'}. columns must map
        # to standard fields in DM or will attempt to map to your custom data fields in DM.
        @param email_type = "Html" - the new contact will be set to receive this format by default.
        @return dict e.g. {'contact_id': 123532543, 'ok': True, 'contact': APIContact object }
        """
        dict_result = {'ok':False}
        # Create an APIContact object with the details of the record to load.
        contact = self.client.factory.create('APIContact')
        del contact.ID
        contact.Email=email_address

        for field_name in d_fields:
            if field_name != 'email' and d_fields.get(field_name):
                contact.DataFields.Keys[0].append(field_name)
                contact.DataFields.Values[0].append(d_fields.get(field_name))

        # remove some empty values that will upset suds/dotMailer
        #del contact.AudienceType
        #del contact.OptInType
        contact.AudienceType = audience_type
        contact.OptInType = opt_in_type
        contact.EmailType = email_type

        logging.getLogger('suds.client').setLevel(logging.DEBUG) # fixme

        try:
            created_contact = self.client.service.AddContactToAddressBook(username=self.api_username, password=self.api_password,contact=contact, addressbookId=address_book_id)
            dict_result = ({'ok':True, 'contact_id':created_contact.ID, 'contact': created_contact})
        except Exception as e:
            dict_result = self.unpack_exception(e)
        return dict_result

    def get_contact_import_progress(self, progress_id):
        """
        @param int the progress_id from add_contacts_to_address_book
        @return dict  e.g. {'ok': False, 'result': NotFinished}    or    dict: {'ok': True, 'result': Finished}
        http://www.dotmailer.co.uk/api/contacts/get_contact_import_progress.aspx
        """
        dict_result = {'ok':True }
        try:
            return_code = self.client.service.GetContactImportProgress(username=self.api_username, password=self.api_password,
                                                     progressID = progress_id)
            if return_code == 'Finished':
                dict_result = {'ok':True, 'result': return_code }
            else:
                dict_result = {'ok':False, 'result': return_code }
        except Exception as e:
            dict_result = self.unpack_exception(e)


        return dict_result

    def send_campaign_to_contact(self, campaign_id, contact_id, send_date=datetime.utcnow()):
        """
        @param int campaign_id
        @param int contact_id
        @param datetime date/time in server time when the campaign should be sent. 
        @return dict  e.g. {'ok': True} or {'ok': False, 'result': <return code if there is one>, 'errors':['sammple error'] }
        http://www.dotmailer.co.uk/api/campaigns/send_campaign_to_contact.aspx
        """
        # format the date in ISO format, e.g. "2012-03-28T19:51:00" for sending via SOAP call. 
        dict_result = {'ok':True }
        iso_send_date = self.dt_to_iso_date( send_date)
        return_code = None
        try:
            return_code = self.client.service.SendCampaignToContact(username=self.api_username, password=self.api_password,
                            campaignId= campaign_id, contactid=contact_id, sendDate=iso_send_date) #note inconsistent case in DM API
            if return_code:
                # return code, which means an error
                dict_result = {'ok':False, 'result': return_code }

        except Exception as e:
            dict_result = self.unpack_exception(e)

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
        dict_result = {'ok':True }
        try:
            return_code = self.client.service.GetContactByEmail(username=self.api_username, password=self.api_password, 
                            email=email)
            dict_result = {'ok':True, 'result': return_code }
        except Exception as e:
            logger.exception("Exception in GetContactByEmail")
            dict_result = self.unpack_exception(e)
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

