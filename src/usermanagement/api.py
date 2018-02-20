# -*- coding: utf-8 -*-

import inspect
from posixpath import join as urljoin
from functools import wraps
from cromlech.jwt.components import TokenException
from dolmen.api_engine.responder import reply
from dolmen.api_engine.components import Endpoint


def options(controller, allowed):
    @wraps(controller)
    def permissive_options(environ, overhead):
        if environ['REQUEST_METHOD'].upper() == 'OPTIONS':
            r = reply(204)
            r.headers["Access-Control-Allow-Origin"] = environ["HTTP_ORIGIN"]
            r.headers["Access-Control-Allow-Credentials"] = "true"
            r.headers["Access-Control-Allow-Methods"] = ",".join(allowed)
            r.headers["Access-Control-Allow-Headers"] = (
                "Authorization, Content-Type, X-Requested-With")
            return r
        return controller(environ, overhead)
    return permissive_options


def protected(verb):
    def jwt_protection(inst, environ, overhead):
        header = environ.get('HTTP_AUTHORIZATION')
        if header is not None and header.startswith('Bearer '):
            token = header[7:]
            try:
                payload = overhead.jwt.authenticate(token)
                if payload is not None:
                    overhead.auth_payload = environ['jwt.payload'] = payload
                    return verb(inst, environ, overhead)
            except TokenException:
                # Do we need some kind of log ?
                pass
        return reply(401)
    return jwt_protection


def route(url, methods, action=None):
    def write_routing_attribute(routed):
        routed.__annotations__['route'] = (url, methods, action)
        return routed
    return write_routing_attribute


def is_routed(method):
    return 'route' in getattr(method, '__annotations__', {})


def endpoint_routes(endpoint, allowed=None):
    methods = dict(inspect.getmembers(endpoint, predicate=is_routed))
    if not methods:
        raise TypeError('Endpoint has no route information')
    for name, method in methods.items():
        url, methods, action = method.__annotations__['route']
        if 'OPTIONS' in methods:
            method = options(method, methods)
        args = {
            'controller': method,
            'action': action,
            'conditions': {"method": methods},
        }
        yield name, url, args


class API(Endpoint):

    def add_endpoint(self, path, endpoint):
        routes = list(endpoint_routes(endpoint))
        for name, url, args in routes:
            routepath = urljoin(path, url.lstrip('/'))
            self.mapper.connect(name, routepath, **args)

    def __setitem__(self, name, value):
        self.add_endpoint(name, value)

    def routing(self, environ):
        # We want to override default Routes behavior and have a real
        # message for forbidden methods access.
        path_info = environ['PATH_INFO'].encode('latin-1').decode('utf-8')
        matching = self.mapper.routematch(path_info)
        if matching is not None:
            routing, route = matching
            methods = route.conditions.get('method')
            if methods and not environ['REQUEST_METHOD'].upper() in methods:
                return reply(405)
            return self.process_action(environ, routing)
        return None
