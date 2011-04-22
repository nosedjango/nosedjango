import os
from nose.config import ConfigError

from nosedjango.plugins.base_plugin import Plugin

class SqlitePlugin(Plugin):
    """
    Modify django database settings to use an in-memory sqlite instance for
    faster test runs and easy multiprocess testing.
    """
    name = 'django-sqlite'

    def beforeConnectionSetup(self, settings):
        settings.DATABASE_ENGINE = 'sqlite3'
        settings.DATABASE_NAME = '' # in-memory database
        settings.DATABASE_OPTIONS = {}
        settings.DATABASE_USER = ''
        settings.DATABASE_PASSWORD = ''