# Make Me A Package

from rutter import urlmap
from .users import mapper as users_actions
from dolmen.api_engine.components import Endpoint


def make_api(overhead=None):
    # Creating the applications
    application = urlmap.URLMap()
    application['/users'] = Endpoint(users_actions, overhead)
    return application
