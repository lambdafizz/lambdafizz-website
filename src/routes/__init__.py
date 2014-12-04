"""
It seems flask-babel translations dont work outside request context,
so they cannot be used for translating urls (which is probably quite sane as
urls are rarely translatable and map directly between languages).

Hence this package. It's modules contain just a simple mapping of route names
to url strings.
"""
import importlib
import logging
from functools import partial

logger = logging.getLogger(__name__)


class Router(object):

    def __init__(self, application, locale):
        self.application = application
        self.locale = locale
        self.locale_module = importlib.import_module('routes.' + locale)  # no need to catch,
                                                                          # ImportError is meaningful here

    def route(self, name):
        return partial(self._route, name)

    def _route(self, name, fun):
        rule = self.locale_module.URLS.get(name, None)
        if rule is None:
            logger.warn('No rules found for route named `%s` with locale `%s`. Route not added.', name, self.locale)
        else:
            self.application.add_url_rule(rule, endpoint=name, view_func=fun)
        return fun
