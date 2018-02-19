# -*- coding: utf-8 -*-

import json
from routes import Mapper
from cromlech.sqlalchemy import SQLAlchemySession
from dolmen.api_engine.validation import JSONSchema
from dolmen.api_engine.cors import allow_origins
from dolmen.api_engine.responder import reply
from zope.interface import Interface
from zope.schema import ASCIILine
from .api import BaseAction, filter_actions

import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.ext.declarative import declarative_base
from alchemyjsonschema import SchemaFactory
from alchemyjsonschema import ForeignKeyWalker


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


user_schema = JSONSchema(json.dumps(
    SchemaFactory(ForeignKeyWalker)(User, excludes='id')
))


class ManageUser(BaseAction):

    @allow_origins('*')
    @filter_actions('get_user', 'schema')
    def GET(self, environ, overhead):
        if overhead.routing['action'] == 'schema':
            # We want the schema
            return reply(
                200, text=user_schema.string,
                content_type="application/json")
        if overhead.routing['action'] == 'get_user':
            listing = {
                'status': 'ok',
                'fetched_user': overhead.routing['id'],
            }
            return reply(
                200, 
                text=json.dumps(listing, sort_keys=True), 
                content_type="application/json")

    @allow_origins('*')
    @filter_actions('create')
    @user_schema.json_validator
    def POST(self, environ, overhead):
        # Create
        with SQLAlchemySession(overhead.engine) as session:
            listing = {'status': 'ok'}
        return reply(
            200, 
            text=json.dumps(listing), 
            content_type="application/json") 
    
    @allow_origins('*')
    @filter_actions('update')
    @user_schema.json_validator
    def PUT(self, environ, overhead):
        # Update
        with SQLAlchemySession(overhead.engine) as session:
            listing = {
                'status': 'ok',
                'updated_user': overhead.routing['id'],
            }
        return reply(
            200, 
            text=json.dumps(listing, sort_keys=True), 
            content_type="application/json") 

    @allow_origins('*')
    @filter_actions('delete')
    def DELETE(self, environ, overhead):
        # delete
        with SQLAlchemySession(overhead.engine) as session:
            listing = {
                'status': 'ok',
                'deleted_user': overhead.routing['id'],
            }
        return reply(
            200, 
            text=json.dumps(listing, sort_keys=True), 
            content_type="application/json") 


mapper = Mapper()

with mapper.submapper(controller=ManageUser()) as m:
    m.connect(None, "/schema", action="schema")
    m.connect(None, "/create", action="create")
    m.connect(None, "/get/{id:\d+}", action="get_user")
    m.connect(None, "/update/{id:\d+}", action="update")
    m.connect(None, "/delete/{id:\d+}", action="delete")
