# Make Me A Package

from routes import Mapper
from .api import API
from . import users


def make_api(overhead=None):
    application = API(Mapper(), overhead)
    application['/users'] = users.module
    return application
