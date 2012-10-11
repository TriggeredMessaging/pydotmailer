# dotmailsudsplugin - Patch SOAP calls for the dotMailer API, written in Python.
# Copyright (c) 2012 Triggered Messaging Ltd, released under the MIT license
# Home page:
# https://github.com/TriggeredMessaging/pydotmailer/
# See README and LICENSE files.
#
# dotMailer API docs are at http://www.dotmailer.co.uk/api/

import suds
from suds.client  import Client as SOAPClient

__version__ = '0.1.1'

try:
    import simplejson as json
except ImportError:
    import json # fall back to traditional json module. 
    
import logging
logger = logging.getLogger(__name__)


from suds.plugin import *
class DotMailerSudsPlugin(MessagePlugin):
    """ case 649
    plugin for SUDS which can inspect and manipulate the xml packets sent to/from the soap server.
    docs here https://fedorahosted.org/suds/wiki/Documentation#MessagePlugin
    """
    def marshalled(self, context):
        """ member function which is called by SUDS when it starts to render/marshall the
        xml to send to the server. At this stage, we have an in-memory set of objects 
        starting with the SOAP context. Any chances we make to the nest of objects
        will then be rendered to XML by our caller. 
        """


        try:
            context.envelope.set('xmlns:apic','http://apiconnector.com')
            context.envelope.set('xmlns:xsd','http://www.w3.org/2001/XMLSchema')

            body = context.envelope.getChild('Body')
            if body:
                add_contact_to_address_book = body.getChild('AddContactToAddressBook')
                if add_contact_to_address_book:
                    # We need to manipulate the "Values" sub-sub-node to set xsi:type="xsd:string" on each element. i.e.
                    # we start with: <apic:anyType >Jim</apic:anyType>
                    # we need: <apic:anyType xsi:type="xsd:string">Jim</apic:anyType>

                    contact = add_contact_to_address_book.getChild('contact')
                    if contact:
                        data_fields = contact.getChild('DataFields')
                        if data_fields:
                            values = data_fields.getChild('Values')
                            for value in values:
                                value.set('xsi:type','xsd:string')


        except:
            logger.exception("Exception in DotMailerSudsPlugin::marshalled")