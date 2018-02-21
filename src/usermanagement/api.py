# -*- coding: utf-8 -*-

import inspect
from abc import ABC
from selector import Selector
from cromlech.jwt.components import TokenException
from dolmen.api_engine.components import BaseOverhead, APIView, APINode
from dolmen.api_engine.responder import reply
from dolmen.api_engine.definitions import METHODS


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


def route(url, methods=None):
    def write_routing_attribute(routed):
        if inspect.isclass(routed):
            if issubclass(routed, APIView):
                routed._route = url
                return routed
            raise RuntimeError(
                'In order to route classes, you need to subclass APIView.')
        elif inspect.isfunction(routed):
            if not methods:
                raise RuntimeError(
                    'No HTTP methods defined for {0}'.format(routed))
            routed.__annotations__['route'] = (url, methods)
        else:
            raise RuntimeError(
                'You can only route functions or APIView subclasses')
        return routed
    return write_routing_attribute


def endpoint_routes(endpoint):
    if isinstance(endpoint, APIView):
        route = {}
        for verb in METHODS:
            method = getattr(endpoint, verb, None)
            if method is not None:
                route[verb] = method
        yield endpoint._route, route
    else:
        methods = dict(inspect.getmembers(endpoint, inspect.ismethod))
        if not methods:
            raise TypeError('Endpoint has no route information')

        for name, method in methods.items():
            if 'route' in method.__annotations__:
                route = {}
                url, methods = method.__annotations__['route']
                for verb in methods:
                    if verb == 'OPTIONS':
                        route[verb] = options(methods)
                    else:
                        route[verb] = method
                yield url, route


class Overhead(BaseOverhead):

    __slots__ = ('engine', 'service', 'parameters', 'identity', 'data')

    def __init__(self, engine, jwt_service, args, identity=None):
        self.engine = engine
        self.jwt_service = jwt_service
        self.parameters = args
        self.identity = identity
        self.data = None

    def set_data(self, data):
        self.data = data


class API(APINode):
    
    def __init__(self, overhead_factory):
        mapper = Selector()
        mapper.status404 = reply(404)
        mapper.status405 = reply(405)
        self.mapper = mapper
        self.overhead_factory = overhead_factory

    def add_endpoint(self, path, endpoint):
        routes = list(endpoint_routes(endpoint))
        for url, args in routes:
            self.mapper.add(url, method_dict=args, prefix=path)

    def __setitem__(self, name, values):
        for value in values:
            self.add_endpoint(name, value)

    def process_endpoint(self, environ, routing_args):
        action, args, allowed, path = routing_args
        if not path:
            # This is an error
            response = action
        else:
            overhead = self.overhead_factory(args)
            response = action(environ, overhead)
        return response
            
    def lookup(self, path_info, environ):
        return self.mapper.select(path_info, environ['REQUEST_METHOD'])
