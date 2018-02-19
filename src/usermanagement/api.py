# -*- coding: utf-8 -*-

import json
import inspect
from cromlech.jwt.components import TokenException
from dolmen.api_engine.components import Action
from dolmen.api_engine.responder import reply


# We allow only 4 methods, no matter if you defined it or not
# This is a site-wide policy to ensure consistency.
ALLOWABLE_METHODS = frozenset(('PUT', 'DELETE', 'POST', 'GET'))


def is_allowable_method(member):
    return inspect.ismethod(member) and member.__name__ in ALLOWABLE_METHODS


def permissive_options(action, environ):
    response = reply(204)
    methods = dict(inspect.getmembers(action, predicate=is_allowable_method))
    response.headers["Access-Control-Allow-Origin"] = environ["HTTP_ORIGIN"]
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = ",".join(methods.keys())
    response.headers["Access-Control-Allow-Headers"] = (
        "Authorization, Content-Type, X-Requested-With")
    return response


def protected(action):
    def jwt_protection(inst, environ, overhead):
        header = environ.get('HTTP_AUTHORIZATION')
        if header is not None and header.startswith('Bearer '):
            token = header[7:]
            try:
                payload = overhead.jwt.authenticate(token)
                if payload is not None:
                    overhead.auth_payload = environ['jwt.payload'] = payload
                    return action(inst, environ, overhead)
            except TokenException:
                # Do we need some kind of log ?
                pass
        return reply(401)
    return jwt_protection


class BaseAction(Action):

    def OPTIONS(self, environ, overhead):
        """Very generic : allow ALL. Override to specialize.
        """
        return permissive_options(self, environ)
