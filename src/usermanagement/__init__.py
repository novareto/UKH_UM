# Make Me A Package

from selector import Selector
from dolmen.api_engine.responder import reply
from .api import API
from . import users


def make_api(overhead=None):
    selector = Selector()
    selector.status404 = reply(404)
    selector.status405 = reply(405)
    application = API(selector, overhead)
    application['/users'] = users.module
    return application
