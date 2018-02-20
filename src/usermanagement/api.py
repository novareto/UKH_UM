# -*- coding: utf-8 -*-

import inspect
from posixpath import join as urljoin
from functools import wraps
from cromlech.jwt.components import TokenException
from dolmen.api_engine.components import BaseOverhead
from dolmen.api_engine.responder import reply


def options(allowed):
    def permissive_options(environ, overhead):
        r = reply(204)
        # Origin might need some love.
        r.headers["Access-Control-Allow-Origin"] = '*'
        r.headers["Access-Control-Allow-Credentials"] = "true"
        r.headers["Access-Control-Allow-Methods"] = ",".join(allowed)
        r.headers["Access-Control-Allow-Headers"] = (
            "Authorization, Content-Type, X-Requested-With")
        return r
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


def endpoint_routes(endpoint):
    methods = dict(inspect.getmembers(endpoint, inspect.ismethod))
    if not methods:
        raise TypeError('Endpoint has no route information')

    routes = []
    for name, method in methods.items():
        if 'route' in method.__annotations__:
            url, methods, action = method.__annotations__['route']
            route = {}
            for http_method in methods:
                if http_method == 'OPTIONS':
                    route[http_method] = options(methods)
                else:
                    route[http_method] = method
            yield url, route


class Overhead(BaseOverhead):
    
    __slots__ = ('engine', 'service', 'parameters', 'identity', 'data')

    def __init__(self, engine, service, args, identity=None):
        self.engine = engine
        self.service = service
        self.parameters = args
        self.identity = identity
        self.data = None

    def set_data(self, data):
        self.data = data


class API:

    def __init__(self, mapper, overhead_factory):
        self.overhead_factory = overhead_factory
        self.mapper = mapper

    def add_endpoint(self, path, endpoint):
        routes = list(endpoint_routes(endpoint))
        for url, args in routes:
            routepath = urljoin(path, url.lstrip('/'))
            self.mapper.add(routepath, method_dict=args)

    def __setitem__(self, name, value):
        self.add_endpoint(name, value)
        
    def __call__(self, environ, start_response):
        path_info = environ['PATH_INFO'].encode('latin-1').decode('utf-8')
        action, args, allowed, path = self.mapper.select(
            path_info, environ['REQUEST_METHOD'])

        if not path:
            # This is an error
            response = action
        else:
            overhead = self.overhead_factory(args)
            response = action(environ, overhead)

        return response(environ, start_response)
