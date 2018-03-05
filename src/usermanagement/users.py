# -*- coding: utf-8 -*-

import json
from cromlech.sqlalchemy import SQLAlchemySession
from dolmen.api_engine.responder import reply

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from dolmen.api_engine.components import View
from zope import interface, schema
from dolmen.api_engine.validation import validate
from dolmen.api_engine.components import View

from .api import route, protected, validate_vbg
from .auth import USERS


Base = declarative_base()


class User(Base):
    __tablename__ = "z1ehr1aa_t"
    #__table_args__ = {"schema": 'UKHINTERN'}

    oid = sa.Column('oid', sa.Integer, primary_key=True)

    vname = sa.Column(
        'vname',
        sa.String(255),
        nullable=False,
    )

    nname = sa.Column(
        'nname',
        sa.String(255),
        nullable=False,
    )

    passwort = sa.Column(
        'passwort',
        sa.String(255),
        nullable=False,
    )


SCHEMA = {
    'fields': [
        {
            'type': "input",
            'inputType': "text",
            'label': "ID (disabled text field)",
            'model': "oid",
            'readonly': True,
            'disabled': True,
        },
        {
            'type': "input",
            'inputType': "text",
            'label': "Name",
            'model': "vname",
            'placeholder': "Your name",
            'featured': True,
            'required': True,
        },
        {
            'type': "input",
            'inputType': "surname",
            'label': "Surname",
            'model': "nname",
            'placeholder': "User's surname",
            'required': True,
        },
        {
            'type': "input",
            'inputType': "password",
            'label': "Password",
            'model': "passwort",
            'min': 6,
            'required': True,
            'hint': "Minimum 6 characters",
            'required': True,
        },
    ],
}

SCHEMA_STRING = json.dumps(SCHEMA, sort_keys=True, indent=4)



class ISearch(interface.Interface):

    search = schema.TextLine(
        title=u"Search String", 
        )



class ManageUser(View):

    @route("/helper", methods=['GET', 'OPTIONS'])
    def helper(self, environ, overhead):
        # Create
        with SQLAlchemySession(overhead.engine) as session:
            print (session)
            session.query(User).all()
            import pdb; pdb.set_trace()
            print ("all good")
        return reply(200, text="ALL GOOD", content_type="application/json")

    @route("/search", methods=['POST', 'OPTIONS'])
    @validate(ISearch, as_dict=True)
    def search(self, environ, overhead):
        # Create
        query= overhead.data['search']
        listing = []
        with SQLAlchemySession(overhead.engine) as session:
            for user in session.query(User).filter(User.nname == query).all():
                listing.append(
                    dict(
                        oid=str(user.oid),
                        vname=user.vname,
                        nname=user.nname,
                    )
                )
        return reply(
            200,
            text=json.dumps(listing, sort_keys=True),
            content_type="application/json")
        return reply(200, text="ALL GOOD", content_type="application/json")

    @route("/schema", methods=['GET', 'OPTIONS'])
    def schema(self, environ, overhead):
        return reply(
            200, text=SCHEMA_STRING,
            content_type="application/json")

    @route("/get/{id:digit}", methods=['GET', 'OPTIONS'])
    def get(self, environ, overhead):
        data = None
        with SQLAlchemySession(overhead.engine) as session:
            user = session.query(User).get(overhead.parameters['id'])
            if user is not None:
                data = dict(
                    oid=str(user.oid),
                    vname=user.vname,
                    nname=user.nname,
                )
                
        if data is None:
            listing = {
                'status': 'error',
            }
        else:
            listing = {
                'status': 'ok',
                'model': data,
            }
        return reply(
            200,
            text=json.dumps(listing, sort_keys=True),
            content_type="application/json")

    @route("/create", methods=['POST', 'OPTIONS'])
    @validate_vbg(SCHEMA, as_dict=True)
    def create(self, environ, overhead):
        with SQLAlchemySession(overhead.engine) as session:
            user = User(**overhead.data)
            session.add(user)
        listing = {
            'status': 'ok',
        }
        return reply(
            200,
            text=json.dumps(listing),
            content_type="application/json")

    @route("/update/{id:digit}", methods=['PUT', 'OPTIONS'])
    @validate_vbg(SCHEMA, as_dict=True)
    def update(self, environ, overhead):
        updated = True
        with SQLAlchemySession(overhead.engine) as session:
            user = session.query(User).get(overhead.parameters['id'])
            if user is not None:
                for field, value in overhead.data.items():
                    setattr(user, field, value)
            else:
                updated = False
            
        listing = {
            'status': updated and 'ok' or 'error',
            'updated_user': overhead.parameters['id'],
        }
        return reply(
            200,
            text=json.dumps(listing, sort_keys=True),
            content_type="application/json")

    @route("/delete/{id:digit}", methods=['DELETE', 'OPTIONS'])
    def delete(self, environ, overhead):
        # delete
        
        with SQLAlchemySession(overhead.engine) as session:
            session.query(User).get(overhead.parameters['id']).delete()
        listing = {
            'status': 'ok',
            'deleted_user': overhead.parameters['id'],
        }
        return reply(
            200,
            text=json.dumps(listing, sort_keys=True),
            content_type="application/json")

    @route("/list", methods=['GET', 'OPTIONS'])
    def list(self, environ, overhead):
        with SQLAlchemySession(overhead.engine) as session:            
            listing = [dict(
                        oid=str(user.oid),
                        vname=user.vname.strip(),
                        nname=user.nname.strip()
                    ) for user in session.query(User).slice(0,5000).all()]
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
