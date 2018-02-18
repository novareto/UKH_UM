# -*- coding: utf-8 -*-

import os
import json
from loader import Configuration
from rutter import urlmap
from collections import namedtuple


class Overhead(object):

    def __init__(self, environ, service, auth):
        self.environ = environ
        self.service = service
        self.auth = auth


def overhead(service):
    def overhead_factory(environ):
        overhead_data = Overhead(environ=environ, service=service, auth=None)
        return overhead_data
    return overhead_factory


def get_key(path):
    if not os.path.isfile(path):
        with open(path, 'w+', encoding="utf-8") as keyfile:
            from cromlech.jwt.components import JWTHandler
            key = JWTHandler.generate_key()
            export = key.export()
            keyfile.write(export)
    else:
        with open(path, 'r', encoding="utf-8") as keyfile:
            from jwcrypto import jwk
            data = json.loads(keyfile.read())
            key = jwk.JWK(**data)

    return key


with Configuration('config.json') as config:
    from usermanagment import users
    from dolmen.api_engine.components import Endpoint
    from cromlech.jwt.components import JWTHandler, JWTService
    
    # Getting the crypto key and creating the JWT service
    key = get_key(config['crypto']['keypath'])
    service = JWTService(key, JWTHandler, lifetime=600)

    # Creating the applications
    application = urlmap.URLMap()
    application['/users'] = Endpoint(users.module, overhead(service))
