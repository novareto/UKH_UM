# -*- coding: utf-8 -*-

import json
import inspect
from shunting.shuntbox import Router, NotFound, NotSupported
from functools import wraps
from collections import namedtuple, Iterable
from cromlech.jwt.components import TokenException
from dolmen.api_engine import validation
from dolmen.api_engine.cors import allow_origins
from dolmen.api_engine.components import BaseOverhead, View, APIView, APINode
from dolmen.api_engine.responder import reply
from dolmen.api_engine.definitions import METHODS


NOTHING = object()


def options(allowed):
    def permissive_options(environ, overhead):
        r = reply(204)
        r.headers["Access-Control-Allow-Credentials"] = "true"
        r.headers["Access-Control-Allow-Methods"] = ",".join(allowed)
        r.headers["Access-Control-Allow-Headers"] = (
            "Authorization, Content-Type, X-Requested-With")
        return r
    return permissive_options


def protected(method):
    @wraps(method)
    def jwt_protection(inst, environ, overhead):
        header = environ.get('HTTP_AUTHORIZATION')
        if header is not None and header.startswith('Bearer '):
            token = header[7:]
            try:
                payload = overhead.jwt_service.check_token(token)
                if payload is not None:
                    overhead.identity = environ['jwt.payload'] = payload
                    return method(inst, environ, overhead)
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
        route = {'ANY': endpoint.__call__}
        yield endpoint._route, route
    else:
        methods = dict(inspect.getmembers(endpoint, inspect.ismethod))
        if not methods:
            raise TypeError('Endpoint has no route information')

        for name, method in methods.items():
            if 'route' in method.__annotations__:
                route = {}
                url, methods = method.__annotations__['route']
                for http_method in methods:
                    if http_method == 'OPTIONS':
                        route[http_method] = options(methods)
                    else:
                        route[http_method] = method
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
        self.mapper = Router()
        self.overhead_factory = overhead_factory

    def add_endpoint(self, path, endpoint):
        routes = list(endpoint_routes(endpoint))
        for url, args in routes:
            self.mapper.add(url, prefix=path, **args)

    def __setitem__(self, name, values):
        for value in values:
            self.add_endpoint(name, value)

    def process_endpoint(self, environ, route):
        overhead = self.overhead_factory(route.params)
        response = allow_origins('*')(route.handler)(environ, overhead)
        return response

    def lookup(self, path_info, environ):
        return self.mapper.lookup(path_info, environ['REQUEST_METHOD'])

    def routing(self, environ):
        # according to PEP 3333 the native string representing PATH_INFO
        # (and others) can only contain unicode codepoints from 0 to 255,
        # which is why we need to decode to latin-1 instead of utf-8 here.
        # We transform it back to UTF-8
        path_info = environ['PATH_INFO'].encode('latin-1').decode('utf-8')
        route = self.lookup(path_info, environ)
        if route is NotFound:
            return reply(404)
        if route is NotSupported:
            return reply(405)
        return self.process_endpoint(environ, route)
    

def string_validator(value, max=None, min=0, **kwargs):
    if not isinstance(value, str):
        raise TypeError('Value must be a string type')
    if min and max:
        if not (min <= len(value) <= max):
            raise ValueError(
                'Value length must be between {0} and {1} characters.'.format(
                    min, max
                ))
    elif min:
        if min > len(value):
            raise ValueError(
                'Value length must be at least {0} characters.'.format(min))
    elif max:
        if max < len(value):
            raise ValueError(
                'Value length must be at most {0} characters.'.format(max))
    return True


def select_validator(value, values=None, **kwargs):
    if not value in values:
        raise ValueError('Value is must be contained in {0}.'.format(values))
    return True


def generic_validator(
        value, readonly=False, disabled=False, required=False, **kwargs):
    if value is NOTHING or not value:
        if required is True:
            raise ValueError('Value is missing.')
        return False
    return True


class validate_vbg:

    extractors = {
        'GET': validation.extract_get,
        'POST': validation.extract_post,
        'PUT': validation.extract_put,
    }

    validators = {
        "input": (generic_validator, string_validator),
        "select": (generic_validator, select_validator),
    }

    def __init__(self, schema, as_dict=False):
        self.schema = schema  # Python structure
        self.fields = schema['fields']
        self.as_dict = as_dict

    def extract(self, environ):
        method = environ['REQUEST_METHOD']
        extractor = self.extractors.get(method)
        if extractor is None:
            raise NotImplementedError('No extractor for method %s' % method)
        return extractor(environ)

    def validate(self, fields, data):
        errors = []
        extracted = {}
        for field in fields:
            fname = field['model']
            value = data.get(fname, field.get('default', NOTHING))
            validators = self.validators.get(field['type'], None)
            if validators is None:
                raise TypeError('Unknown field type: {0}'.format(vtype))
            for validator in validators:
                try:
                    further = validator(value, **field)
                    if not further:
                        break
                except (TypeError, ValueError) as error:
                    errors.append((field['model'], error))
                    break
                finally:
                    # It was extracted, whatever the cost !
                    if value is not NOTHING:
                        if not field.get('readonly', False):
                            extracted[fname] = value

        return extracted, errors

    def process_action(self, environ):
        params = self.extract(environ)
        extracted, errors = self.validate(self.fields, params)
        if errors:
            summary = {}
            for field, error in errors:
                doc = getattr(error, 'doc', error.__str__)
                field_errors = summary.setdefault(field, [])
                field_errors.append(doc())
            return extracted, summary
        return extracted, None

    def __call__(self, action):
        @wraps(action)
        def method_validation(*args):
            if isinstance(args[0], View):
                inst, environ, overhead = args
            else:
                inst = None
                environ, overhead = args

            extracted, errors = self.process_action(environ)
            if errors:
                return reply(
                    400, text=json.dumps(errors),
                    content_type="application/json")
            
            else:
                if self.as_dict:
                    result = extracted
                else:
                    names = tuple((field['model'] for field in self.fields))
                    DataClass = namedtuple(action.__name__, names)
                    result = DataClass(**extracted)

                if overhead is None:
                    overhead = result
                else:
                    assert isinstance(overhead, BaseOverhead)
                    overhead.set_data(result)

                if inst is not None:
                    return action(inst, environ, overhead)
                return action(environ, overhead)

            return result
        return method_validation
