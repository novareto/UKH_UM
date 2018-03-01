# -*- coding: utf-8 -*-

import json
from cromlech.sqlalchemy import SQLAlchemySession
from dolmen.api_engine.responder import reply

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from dolmen.api_engine.components import View
from .api import route, protected, validate_vbg
from .auth import USERS


Base = declarative_base()


class User(Base):
    __tablename__ = "User"

    id = sa.Column(
        sa.Integer,
        primary_key=True,
        doc="primary key",
    )

    name = sa.Column(
        sa.String(255),
        nullable=False,
    )

    surname = sa.Column(
        sa.String(255),
        nullable=False,
    )

    password = sa.Column(
        sa.String(255),
        nullable=False,
    )

    companyID = sa.Column(
        sa.String(255),
        nullable=False,
    )


SCHEMA = {
    'fields': [
        {
            'type': "input",
            'inputType': "text",
            'label': "ID (disabled text field)",
            'model': "id",
            'readonly': True,
            'disabled': True,
        },
        {
            'type': "input",
            'inputType': "text",
            'label': "Name",
            'model': "name",
            'placeholder': "Your name",
            'featured': True,
            'required': True,
        },
        {
            'type': "input",
            'inputType': "surname",
            'label': "Surname",
            'model': "surname",
            'placeholder': "User's surname",
            'required': True,
        },
        {
            'type': "input",
            'inputType': "password",
            'label': "Password",
            'model': "password",
            'min': 6,
            'required': True,
            'hint': "Minimum 6 characters",
            'required': True,
        },
        {
            'type': "input",
            'inputType': "companyID",
            'label': "Surname",
            'model': "companyID",
            'placeholder': "User's company",
            'required': True,
        },
    ],
}

SCHEMA_STRING = json.dumps(SCHEMA, sort_keys=True, indent=4)


class ManageUser(View):

    @route("/schema", methods=['GET', 'OPTIONS'])
    def schema(self, environ, overhead):
        return reply(
            200, text=SCHEMA_STRING,
            content_type="application/json")

    @route("/get/{id:digits}", methods=['GET', 'OPTIONS'])
    def get(self, environ, overhead):
        listing = {
            'status': 'ok',
            'fetched_user': overhead.parameters['id'],
        }
        return reply(
            200,
            text=json.dumps(listing, sort_keys=True),
            content_type="application/json")

    @route("/create", methods=['POST', 'OPTIONS'])
    @validate_vbg(SCHEMA)
    def create(self, environ, overhead):
        # Create
        with SQLAlchemySession(overhead.engine) as session:
            listing = {'status': 'ok'}
        return reply(
            200,
            text=json.dumps(listing),
            content_type="application/json")

    @route("/update/{id:digits}", methods=['PUT', 'OPTIONS'])
    @validate_vbg(SCHEMA)
    def update(self, environ, overhead):
        # Update
        with SQLAlchemySession(overhead.engine) as session:
            listing = {
                'status': 'ok',
                'updated_user': overhead.parameters['id'],
            }
        return reply(
            200,
            text=json.dumps(listing, sort_keys=True),
            content_type="application/json")

    @route("/delete/{id:digits}", methods=['DELETE', 'OPTIONS'])
    def delete(self, environ, overhead):
        # delete
        with SQLAlchemySession(overhead.engine) as session:
            listing = {
                'status': 'ok',
                'deleted_user': overhead.parameters['id'],
            }
        return reply(
            200,
            text=json.dumps(listing, sort_keys=True),
            content_type="application/json")

    @route("/list[/{department}]", methods=['GET', 'OPTIONS'])
    def list(self, environ, overhead):
        # list users by departement
        listing = []
        department = overhead.parameters.get('department')
        for username, details in USERS.items():
            payload = details['profile'] 
            if not department:
                listing.append({username: payload})
            elif department in payload['departments']:
                listing.append({username: payload})

        if department and not listing:
            return reply(404, text="No matching users found.")
        return reply(
            200,
            text=json.dumps(listing, sort_keys=True),
            content_type="application/json")

    @route("/personal", methods=['GET', 'OPTIONS'])
    @protected
    def personal_info(self, environ, overhead):
        user = USERS.get(overhead.identity['user'])
        if user is not None:
            info = json.dumps(user['profile'], indent=4, sort_keys=True)
            return reply(200, text=info, content_type="application/json")
        return reply(404)


modules = (ManageUser(),)
