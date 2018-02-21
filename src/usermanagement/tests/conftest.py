# -*- coding: utf-8 -*-

import os
import pytest
import usermanagement
from functools import partial
from webtest import TestApp as WSGIApp
from cromlech.jwt.components import JWTHandler, JWTService
from cromlech.sqlalchemy import create_engine, SQLAlchemySession
    

@pytest.fixture(scope="module")
def application():

    # Getting the crypto key and creating the JWT service
    key = JWTHandler.generate_key()
    service = JWTService(key, JWTHandler, lifetime=600)

    # SQLEngine
    engine = create_engine('sqlite://', 'test')

    # We Bind and Create
    engine.bind(usermanagement.UsersBase)
    with SQLAlchemySession(engine) as session:
        usermanagement.UsersBase.metadata.create_all()

    # Creating the application
    overhead_factory = partial(usermanagement.Overhead, engine, service)
    application = usermanagement.API(overhead_factory)
    application['/users'] = usermanagement.users.modules
    application['/auth'] = usermanagement.auth.modules
    return WSGIApp(application)
