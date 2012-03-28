
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
    import json

class PyDotMailer(object):
    version = '0.1'
    
    # Cache the information on the API location on the server
    apiUrl = ''
    
    # Default to a 300 second timeout on server calls
    timeout = 300
    
    def __init__(self, api_username='', api_password='', secure=False, timeout=300):
        '''
        Connect to the dotMailer API for a given list.
        
        @param string $apikey Your dotMailer apikey
        @param string $secure Whether or not this should use a secure connection
        '''
        
        self.apiUrl = 'todo' # urlparse('http://%s.api.mailchimp.com/%s/?output=json' % (datacenter, self.version))
        
        # Default to a 300 second timeout on server calls
        self.timeout = timeout
        
        # Define whether we use SSL
        self.secure = secure or False

        url = 'http://apiconnector.com/API.asmx?WSDL'
        self.client = SOAPClient(url)
        self.api_username = api_username
        self.api_password = api_password
 
 
    def add_contacts_to_address_book(self, address_book_id, s_contacts, wait_to_complete_seconds = False):
        """
        Add a list of contacts to the address book
        
        @param int the id of the address book
        @param string containing the contacts to be added. You may upload either a .csv or .xls file. It must contain one column with the heading "Email". Other columns must will attempt to map to your custom data fields.
        @param into seconds to wait.  
        @return boolean True on success
        
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

        #mycount = 0
        #for i in range(10):
        #    mycount = getAddressBookContactCount(addressbookid)
        #    if mycount > 0:
        #        break 
        #    time.sleep(1)
    
        return {'ok':True, 'progress_id': progress_id, 'return_code': return_code}
 
    def get_contact_import_progress(self, progress_id):
        """
        @param int the progress_id from add_contacts_to_address_book
        
        http://www.dotmailer.co.uk/api/contacts/get_contact_import_progress.aspx
        """
        return_code = self.client.service.GetContactImportProgress(username=self.api_username, password=self.api_password, 
                                                     progressID = progress_id)
        if return_code == 'Finished':
            dict_result = {'ok':True, 'result': return_code }
        else:
            dict_result = {'ok':False, 'result': return_code }
            
        return dict_result
    
    def setTimeout(self, seconds):
        self.timeout = seconds
    
    def getTimeout(self):
        return self.timeout
    
    def useSecure(self, val):
        if val == True:
            self.secure = True
        else:
            self.secure = False




    def ping(self):
        '''
        "Ping" the dotMailer API - a simple method you can call that will return a constant value as long as everything is good. Note
        than unlike most all of our methods, we don't throw an Exception if we are having issues. You will simply receive a different
        string back that will explain our view on what is going on.
        
        @section Helper
        @example xml-rpc_ping.php
        
        @return string returns "Everything's ok!" if everything is ok, otherwise returns an error message
        '''
        return self.callServer("ping")
    

    def call_server(self, method, params={}):
        '''
        Actually connect to the server and call the requested methods, parsing the result
        You should never have to call this function manually
        '''
        pass



def main():
    
    try:
        addressbookid    = sys.argv[2]
        contactsfilename = sys.argv[3]
    except IndexError:
        print "Usage: dotmailer addcontactstoaddressbook addressbookid contactsfilename\n"
        sys.exit(1)

    initial_data = open(contactsfilename, 'r').read()

    
