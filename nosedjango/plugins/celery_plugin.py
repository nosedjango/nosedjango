import os
from nose.config import ConfigError

from nosedjango.plugins.base_plugin import Plugin

try:
    djkombu_installed = True
    import djkombu  # noqa
except ImportError:
    djkombu_installed = False


class CeleryPlugin(Plugin):
    """
    Configure Celery to run locally for testing and optionally use a database
    backend so you don't have to install RabbitMQ to test.
    """
    name = 'django-celery'

    def __init__(self, *args, **kwargs):
        super(CeleryPlugin, self).__init__(*args, **kwargs)

        self.use_djkombu = False

    def options(self, parser, env=None):
        if env is None:
            env = os.environ
        parser.add_option(
            '--dbbacked-celery',
            dest='use_djkombu',
            action='store_true',
            default=False,
            help=(
                'Use django-kombu for database-backed Celery. Alleviates the '
                'need to install rabbitmq.'
            ),
        )

        super(CeleryPlugin, self).options(parser, env)

    def configure(self, options, config):
        self.use_djkombu = options.use_djkombu

        if self.use_djkombu and not djkombu_installed:
            # Trying to use django-kombu, but it's not actually installed
            raise ConfigError(
                "django-kombu must be installed in order to use --dbbacked-celery",  # noqa
            )

        super(CeleryPlugin, self).configure(options, config)

    def beforeTestSetup(self, settings, setup_test_environment, connection):
        settings.CELERY_ALWAYS_EAGER = True
        settings.CELERY_RESULTS_BACKEND = 'database'

        if self.use_djkombu:
            settings.INSTALLED_APPS += 'djkombu'
            settings.BROKER_BACKEND = "djkombu.transport.DatabaseTransport"
