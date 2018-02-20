# -*- coding: utf-8 -*-

import os
import json
from functools import partial
from loader import Configuration


class Overhead(object):

    def __init__(self, engine, service, environ):
        self.engine = engine
        self.service = service
        self.auth = None


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
    import usermanagement
    from cromlech.jwt.components import JWTHandler, JWTService
    from cromlech.sqlalchemy import create_engine
    
    # Getting the crypto key and creating the JWT service
    key = get_key(config['crypto']['keypath'])
    service = JWTService(key, JWTHandler, lifetime=600)

    # SQLEngine
    engine = create_engine(config['db']['dsn'], 'usermanagement')

    # Creating the application
    application = usermanagement.make_api(partial(Overhead, engine, service))
