from nosedjango.plugins.base_plugin import Plugin


class SqlitePlugin(Plugin):
    """
    Modify django database settings to use an in-memory sqlite instance for
    faster test runs and easy multiprocess testing.
    """
    name = 'django-sqlite'

    def beforeConnectionSetup(self, settings):
        if hasattr(settings, 'DATABASES'):
            settings.DATABASES['default']['ENGINE'] = 'django.db.backends.sqlite3'  # noqa
            settings.DATABASES['default']['NAME'] = ':memory:'  # in-memory database
            settings.DATABASES['default']['OPTIONS'] = {}
            settings.DATABASES['default']['USER'] = ''
            settings.DATABASES['default']['PASSWORD'] = ''
            settings.DATABASES['default']['ATOMIC_REQUESTS'] = True
            settings.DATABASES['default']['AUTOCOMMIT'] = True
        else:
            settings.DATABASE_ENGINE = 'sqlite3'
            settings.DATABASE_NAME = ':memory:'
            settings.DATABASE_OPTIONS = {}
            settings.DATABASE_USER = ''
            settings.DATABASE_PASSWORD = ''
            settings.DATABASE_ATOMIC_REQUESTS = True
            settings.DATABASE_AUTOCOMMIT = True
