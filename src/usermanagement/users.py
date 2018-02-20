# -*- coding: utf-8 -*-

import json
from cromlech.sqlalchemy import SQLAlchemySession
from dolmen.api_engine.validation import JSONSchema
from dolmen.api_engine.responder import reply

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from alchemyjsonschema import SchemaFactory
from alchemyjsonschema import ForeignKeyWalker
from .api import route


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


class ManageUser:
    
    @route("/schema", methods=['GET', 'OPTIONS'])
    def schema(self, environ, overhead):
        return reply(
            200, text=user_schema.string,
            content_type="application/json")

    @route("/get/{id:\d+}", methods=['GET', 'OPTIONS'])
    def get(self, environ, overhead):
        listing = {
            'status': 'ok',
            'fetched_user': overhead.routing['id'],
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

    @route("/update/{id:\d+}", methods=['PUT', 'OPTIONS'])
    @user_schema.json_validator
    def update(self, environ, overhead):
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

    @route("/delete/{id:\d+}", methods=['DELETE', 'OPTIONS'])
    def delete(self, environ, overhead):
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


module = ManageUser()
