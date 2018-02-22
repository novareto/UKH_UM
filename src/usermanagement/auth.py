# -*- coding: utf-8 -*-

import json
from dolmen.api_engine.responder import reply
from dolmen.api_engine.validation import JSONSchema
from .api import route, APIView, options


USERS = {
    'cklinger@novareto.de': {
        'password': 'test',
        'profile': {
            'fullname': 'Christian Klinger',
            'company': 'Novareto',
            'title': 'Director',
            'created': '2018-02-21',
            'departments': ['IT', 'HR'],
            'emails': [
                'cklinger@novareto.de',
                'ck@novareto.de',
            ],
        }
    }
}


login_schema = JSONSchema.create_from_string("""
{
    "name": "Login",
    "description": "Please login.",
    "has_file": null,
    "type": "object",
    "properties": {
        "username": {
            "type": "string",
            "minLength": 8,
            "maxLength": 128,
            "attrs": {
                "placeholder": "Your username"
            }
        },
        "password": {
            "type": "string",
            "maxLength": 32,
            "attrs": {
                "type": "password",
                "placeholder": "Enter your password",
                "autocomplete": "off"
            }
        }
    },
    "additionalProperties": false,
    "required": ["username", "password"]
}
""")


@route('/login')
class Login(APIView):

    OPTIONS = staticmethod(options(['GET', 'POST']))

    def GET(self, environ, overhead):
        return reply(
            200, text=login_schema.string,
            content_type="application/json")

    @login_schema.json_validator
    def POST(self, environ, overhead):
        user = USERS.get(overhead.data['username'])
        if user is not None:
            if user['password'] == overhead.data['password']:
                payload = {'user': overhead.data['username']}
                jwt = overhead.jwt_service.generate(payload)
                token = json.dumps({'token': jwt})
                return reply(200, text=token, content_type="application/json")
        return reply(401)


@route('/signup')
class Signup(APIView):

    OPTIONS = staticmethod(options(['GET', 'POST']))
    
    def GET(self, environ, overhead):
        return reply(
            200, text=login_schema.string,
            content_type="application/json")

    @login_schema.json_validator
    def POST(self, environ, overhead):
        user = USERS.get(overhead.data['username'])
        return reply(202)


modules = (Login(), Signup())
