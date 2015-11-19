from nosedjango.plugins.base_plugin import Plugin


class SqlitePlugin(Plugin):
    """
    Modify django database settings to use an in-memory sqlite instance for
    faster test runs and easy multiprocess testing.
    """
    name = 'django-sqlite'

    def beforeConnectionSetup(self, settings):
        settings.DATABASES['default']['ENGINE'] = 'django.db.backends.sqlite3'  # noqa
        settings.DATABASES['default']['NAME'] = ':memory:'
        settings.DATABASES['default']['OPTIONS'] = {}
        settings.DATABASES['default']['USER'] = ''
        settings.DATABASES['default']['PASSWORD'] = ''
