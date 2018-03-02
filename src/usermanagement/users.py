# -*- coding: utf-8 -*-

import json
from cromlech.sqlalchemy import SQLAlchemySession
from dolmen.api_engine.validation import JSONSchema
from dolmen.api_engine.responder import reply

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from alchemyjsonschema import SchemaFactory
from alchemyjsonschema import ForeignKeyWalker
from .api import route, protected
from .auth import USERS


Base = declarative_base()


class User(Base):
    __tablename__ = "z1ehr1aa_t"
    __table_args__ = {"schema": 'UKHINTERN'}

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


user_schema = JSONSchema.create_from_json(
    SchemaFactory(ForeignKeyWalker)(User, excludes='oid')
)


from zope import interface, schema
from dolmen.api_engine.validation import validate

class ISearch(interface.Interface):

    search = schema.TextLine(
        title=u"Search String", 
        )


from dolmen.api_engine.components import View
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
                        vname=user.vname.strip(),
                        nname=user.nname.strip()
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
            200, text=user_schema.string,
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
    @user_schema.json_validator
    def create(self, environ, overhead):
        # Create
        with SQLAlchemySession(overhead.engine) as session:
            listing = {'status': 'ok'}
        return reply(
            200,
            text=json.dumps(listing),
            content_type="application/json")

    @route("/update/{id:digits}", methods=['PUT', 'OPTIONS'])
    @user_schema.json_validator
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
        with SQLAlchemySession(overhead.engine) as session:
            for user in session.query(User).all():
                listing.append(
                    dict(
                        oid=str(user.oid),
                        vname=user.vname.strip(),
                        nname=user.nname.strip()
                    )
                )
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
