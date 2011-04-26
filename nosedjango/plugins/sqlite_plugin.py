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
        settings.DATABASES['default']['ENGINE'] = 'django.db.backends.sqlite3'
        settings.DATABASES['default']['NAME'] = '' # in-memory database
        settings.DATABASES['default']['OPTIONS'] = {}
        settings.DATABASES['default']['USER'] = ''
        settings.DATABASES['default']['PASSWORD'] = ''
