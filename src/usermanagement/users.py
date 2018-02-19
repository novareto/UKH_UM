# -*- coding: utf-8 -*-

import json
from routes import Mapper
from dolmen.api_engine.validation import validate
from dolmen.api_engine.cors import allow_origins
from dolmen.api_engine.responder import reply
from zope.interface import Interface
from zope.schema import ASCIILine
from .api import BaseAction


class ISearch(Interface):
    username = ASCIILine(
        title="User identifier",
        required=False,
    )


class Search(BaseAction):

    @allow_origins('*')
    @validate(ISearch)
    def POST(self, environ, overhead):
        listing = {'status': 'ok'}
        return reply(
            200, 
            text=json.dumps(listing), 
            content_type="application/json") 


mapper = Mapper()
mapper.connect("search", "/search", controller=Search())
