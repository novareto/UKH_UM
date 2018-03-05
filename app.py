# -*- coding: utf-8 -*-

import os
import json
from functools import partial
from loader import Configuration


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


with open('test_data/data.json', 'r') as fd:
    usersdata = json.load(fd)


with Configuration('config.json') as config:
    import usermanagement
    import bjoern
    from cromlech.jwt.components import JWTHandler, JWTService
    from cromlech.sqlalchemy import create_engine, SQLAlchemySession
    
    # Getting the crypto key and creating the JWT service
    key = get_key(config['crypto']['keypath'])
    service = JWTService(key, JWTHandler, lifetime=600)

    # SQLEngine
    engine = create_engine(config['db']['dsn'], 'usermanagement')

    # We Bind and Create
    engine.bind(usermanagement.UsersBase)
    print('-- creating tests users --')
    with SQLAlchemySession(engine) as session:
        usermanagement.UsersBase.metadata.create_all()
        for userdata in usersdata:
            userdata['passwort'] = 'test42'
            user = usermanagement.users.User(**userdata)
            session.add(user)
    print('-- created {} users --\n'.format(len(usersdata)))

    # Creating the application
    overhead_factory = partial(usermanagement.Overhead, engine, service)
    application = usermanagement.API(overhead_factory)
    application['/users'] = usermanagement.users.modules
    application['/auth'] = usermanagement.auth.modules

    print('-- starting --')
    bjoern.run(application, '0.0.0.0', 8080)
