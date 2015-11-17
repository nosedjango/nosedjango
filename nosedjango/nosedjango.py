"""
nose plugin for easy testing of django projects and apps. Sets up a test
database (or schema) and installs apps from test settings file before tests
are run, and tears the test database (or schema) down after all tests are run.
"""

from __future__ import with_statement

import logging
import os
import re
import sys

from contextlib import contextmanager

import nose.case
from nose.plugins import Plugin

# Force settings.py pointer
# search the current working directory and all parent directories to find
# the settings file
from nose.importer import add_path
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

logger = logging.getLogger('nose.plugins.nosedjango')

NT_ROOT = re.compile(r"^[a-zA-Z]:\\$")


def get_settings_path(settings_module):
    '''
    Hunt down the settings.py module by going up the FS path
    '''
    cwd = os.getcwd()
    settings_filename = '%s.py' % (
        settings_module.split('.')[-1]
    )
    while cwd:
        if settings_filename in os.listdir(cwd):
            break
        cwd = os.path.split(cwd)[0]
        if os.name == 'nt' and NT_ROOT.match(cwd):
            return None
        elif cwd == '/':
            return None
    return cwd


def _dummy(*args, **kwargs):
    """Dummy function that replaces the transaction functions"""
    return


class NoseDjango(Plugin):
    """
    Enable to set up django test environment before running all tests, and
    tear it down after all tests.

    Note that your django project must be on PYTHONPATH for the settings file
    to be loaded. The plugin will help out by placing the nose working dir
    into sys.path if it isn't already there, unless the -P
    (--no-path-adjustment) argument is set.
    """
    name = 'django'

    def __init__(self):
        Plugin.__init__(self)
        self.nose_config = None
        self.django_plugins = []

        self._loaded_test_fixtures = []
        self._num_fixture_loads = 0
        self._num_flush_calls = 0
        self._num_syncdb_calls = 0

        self.orig_commit = self.transaction.commit
        self.orig_rollback = self.transaction.rollback
        self.orig_savepoint_commit = self.transaction.savepoint_commit
        self.orig_savepoint_rollback = self.transaction.savepoint_rollback
        self.orig_enter = self.transaction.enter_transaction_management
        self.orig_leave = self.transaction.leave_transaction_management

    @property
    def transaction(self):
        from django.db import transaction
        if self.django_version < 7:
            transaction.set_autocommit = lambda x: x
            transaction.get_autocommit = lambda: True
        else:
            transaction.enter_transaction_management = lambda: True
            transaction.leave_transaction_management = lambda: True
        return transaction

    @property
    def django_version(self):
        from django import VERSION
        return VERSION[1]

    @contextmanager
    def set_autocommit(self, value):
        old_value = self.transaction.get_autocommit()
        self.transaction.set_autocommit(value)
        yield
        self.transaction.set_autocommit(old_value)

    def disable_transaction_support(self):
        self.transaction.commit = _dummy
        self.transaction.rollback = _dummy
        self.transaction.savepoint_commit = _dummy
        self.transaction.savepoint_rollback = _dummy
        self.transaction.enter_transaction_management = _dummy
        self.transaction.leave_transaction_management = _dummy

    def restore_transaction_support(self):
        self.transaction.commit = self.orig_commit
        self.transaction.rollback = self.orig_rollback
        self.transaction.savepoint_commit = self.orig_savepoint_commit
        self.transaction.savepoint_rollback = self.orig_savepoint_rollback
        self.transaction.enter_transaction_management = self.orig_enter
        self.transaction.leave_transaction_management = self.orig_leave

    def options(self, parser, env):
        parser.add_option(
            '--django-settings',
            help='Use custom Django settings module.',
            metavar='SETTINGS',
        )
        super(NoseDjango, self).options(parser, env)

    def configure(self, options, conf):
        self.verbosity = conf.verbosity
        if options.django_settings:
            self.settings_module = options.django_settings
        elif 'DJANGO_SETTINGS_MODULE' in os.environ:
            self.settings_module = os.environ['DJANGO_SETTINGS_MODULE']
        else:
            self.settings_module = 'settings'

        super(NoseDjango, self).configure(options, conf)

        self.nose_config = conf

    def call_plugins_method(self, meth_name, *args, **kwargs):
        for plugin in self.django_plugins:
            if hasattr(plugin, meth_name):
                getattr(plugin, meth_name)(*args, **kwargs)

    def begin(self):
        """
        Create the test database and schema, if needed, and switch the
        connection over to that database. Then call install() to install
        all apps listed in the loaded settings module.
        """
        for plugin in self.nose_config.plugins.plugins:
            if getattr(plugin, 'django_plugin', False):
                self.django_plugins.append(plugin)

        os.environ['DJANGO_SETTINGS_MODULE'] = self.settings_module

        if self.conf.addPaths:
            map(add_path, self.conf.where)

        try:
            __import__(self.settings_module)
            self.settings_path = self.settings_module
        except ImportError:
            # Settings module is not found in PYTHONPATH. Try to do
            # some funky backwards crawling in directory tree, ie. add
            # the working directory (and any package parents) to
            # sys.path before trying to import django modules;
            # otherwise, they won't be able to find project.settings
            # if the working dir is project/ or project/..

            self.settings_path = get_settings_path(self.settings_module)

            if not self.settings_path:
                # short circuit if no settings file can be found
                raise RuntimeError("Can't find Django settings file!")

            add_path(self.settings_path)
            sys.path.append(self.settings_path)

        from django.conf import settings

        # Some Django code paths evaluate differently
        # between DEBUG and not DEBUG.  Example of this include the url
        # dispatcher when 404's are hit.  Django's own test runner forces DEBUG
        # to be off.
        settings.DEBUG = False

        self.call_plugins_method('beforeConnectionSetup', settings)

        from django.core import management
        from django.test.utils import setup_test_environment

        if hasattr(settings, 'DATABASES'):
            self.old_db = settings.DATABASES['default']['NAME']
        else:
            self.old_db = settings.DATABASE_NAME
        from django.db import connections

        self._monkeypatch_test_classes()

        for connection in connections.all():
            self.call_plugins_method(
                'beforeTestSetup', settings, setup_test_environment,
                connection)
        setup_test_environment()
        import django
        if hasattr(django, 'setup'):
            django.setup()

        self.call_plugins_method('afterTestSetup', settings)

        management.get_commands()
        # Ensure that nothing (eg. South) steals away our syncdb command
        if hasattr(management, '_commands'):
            management._commands['syncdb'] = 'django.core'
        else:
            pass
            # assert 0, dir(management)
            # management.commands['syncdb'] = 'django.core'

        for connection in connections.all():
            self.call_plugins_method(
                'beforeTestDb', settings, connection, management)
            connection.creation.create_test_db(verbosity=self.verbosity)
            logger.debug("Running syncdb")
            self._num_syncdb_calls += 1
            self.call_plugins_method('afterTestDb', settings, connection)

    def _should_use_transaction_isolation(self, test, settings):
        """
        Determine if the given test supports transaction management for
        database rollback test isolation and also whether or not the test has
        opted out of that support.

        Transactions make database rollback much quicker when supported, with
        the caveat that any tests that are explicitly testing transactions
        won't work properly and any tests that depend on external access to the
        test database won't be able to view data created/altered during the
        test.
        """
        if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':  # noqa
            return True
        if not getattr(test.context, 'use_transaction_isolation', True):
            # The test explicitly says not to use transaction isolation
            return False
        if getattr(settings, 'DISABLE_TRANSACTION_MANAGEMENT', False):
            # Do not use transactions if user has forbidden usage.
            return False
        if hasattr(settings, 'DATABASE_SUPPORTS_TRANSACTIONS'):
            if not settings.DATABASE_SUPPORTS_TRANSACTIONS:
                # The DB doesn't support transactions. Don't try it
                return False

        return True

    def should_use_transaction_isolation(self, test, settings):
        use_transaction_isolation = self._should_use_transaction_isolation(
            test=test,
            settings=settings,
        )
        if self.transaction_is_managed():
            return use_transaction_isolation
        if use_transaction_isolation:
            self.transaction.set_autocommit(True)
        else:
            self.transaction.set_autocommit(False)
        return use_transaction_isolation

    def _should_rebuild_schema(self, test):
        if getattr(test.context, 'rebuild_schema', False):
            return True
        return False

    def transaction_is_managed(self):
        if hasattr(self.transaction, 'is_managed'):
            return self.transaction.is_managed()
        return self.transaction.get_connection().in_atomic_block

    def afterTest(self, test):
        """
        Clean up any changes to the test database.
        """
        # Restore transaction support on tests
        from django.conf import settings
        from django.db import connections
        from django.test.utils import (
            setup_test_environment,
            teardown_test_environment,
        )

        use_transaction_isolation = self.should_use_transaction_isolation(
            test, settings)

        if self._should_rebuild_schema(test):
            for connection in connections.all():
                connection.creation.destroy_test_db(
                    self.old_db, verbosity=self.verbosity)

            teardown_test_environment()

            setup_test_environment()
            return
            import django
            if hasattr(django, 'setup'):
                django.setup()
            for connection in connections.all():
                connection.creation.create_test_db(verbosity=self.verbosity)

            self.restore_transaction_support()
            if use_transaction_isolation:
                self.transaction.commit()
            if self.transaction_is_managed():
                self.transaction.set_autocommit(False)
            # If connection is not closed Postgres can go wild with
            # character encodings.
            for connection in connections.all():
                connection.close()
            logger.debug("Running syncdb")
            self._num_syncdb_calls += 1
            self._loaded_test_fixtures = []
            return

        if use_transaction_isolation:
            self.restore_transaction_support()
            logger.debug("Rolling back")
            if self.django_version > 7:
                if not self.transaction_is_managed():
                    self.transaction.rollback()
            else:
                self.transaction.rollback()
            if self.transaction_is_managed():
                self.transaction.leave_transaction_management()
            # If connection is not closed Postgres can go wild with
            # character encodings.
            for connection in connections.all():
                connection.close()
        else:
            # Have to clear the db even if we're using django because django
            # doesn't properly flush the database after a test. It relies on
            # flushing before a test, so we want to avoid the case where a
            # django test doesn't flush and then a normal test runs, because it
            # will expect the db to already be flushed
            self._flush_db()
            self._loaded_test_fixtures = []

        self.call_plugins_method('afterRollback', settings)

    def _flush_db(self):
        from django.core.management import call_command
        if self.django_version < 7:
            with self.set_autocommit(True):
                call_command('flush', verbosity=0, interactive=False)
        else:
            call_command('flush', verbosity=0, interactive=False)

        logger.debug("Flushing database")
        self._num_flush_calls += 1

    def beforeTest(self, test):
        """
        Load any database fixtures, set up any test url configurations and
        prepare for using transactions for database rollback if possible.
        """
        if not self.settings_path:
            # short circuit if no settings file can be found
            return

        from django.contrib.sites.models import Site
        from django.contrib.contenttypes.models import ContentType
        from django.core.management import call_command
        from django.core.urlresolvers import clear_url_caches
        from django.conf import settings

        use_transaction_isolation = self.should_use_transaction_isolation(
            test, settings)

        if use_transaction_isolation:
            self.call_plugins_method(
                'beforeTransactionManagement',
                settings,
                test,
            )
            if self.django_version < 7:
                self.transaction.enter_transaction_management()
                self.transaction.managed(True)
                self.disable_transaction_support()

        Site.objects.clear_cache()
        # Otherwise django.contrib.auth.Permissions will depend on deleted
        # ContentTypes
        ContentType.objects.clear_cache()

        if use_transaction_isolation:
            self.call_plugins_method(
                'afterTransactionManagement',
                settings,
                test,
            )

        self.call_plugins_method('beforeFixtureLoad', settings, test)
        if isinstance(test, nose.case.Test):
            # Mirrors django.test.testcases:TestCase

            fixtures_to_load = getattr(test.context, 'fixtures', [])
            if fixtures_to_load is None:
                fixtures_to_load = []
            # We have to use this slightly awkward syntax due to the fact
            # that we're using *args and **kwargs together.
            ordered_fixtures = sorted(fixtures_to_load)
            if ordered_fixtures != self._loaded_test_fixtures:
                # Only clear + load the fixtures if they're not already
                # loaded

                # Flush previous fixtures
                if use_transaction_isolation:
                    self.restore_transaction_support()

                self._flush_db()

                if use_transaction_isolation:
                    if self.django_version < 7:
                        self.transaction.commit()
                    self.disable_transaction_support()

                # Load the new fixtures
                logger.debug("Loading fixtures: %s", fixtures_to_load)
                if fixtures_to_load:
                    commit = True
                    if use_transaction_isolation:
                        commit = False
                    call_command(
                        'loaddata',
                        *test.context.fixtures,
                        **{'verbosity': 0, 'commit': commit}
                    )
                if use_transaction_isolation:
                    self.restore_transaction_support()
                    if self.django_version < 7:
                        self.transaction.commit()
                    self.disable_transaction_support()
                self._num_fixture_loads += 1
                self._loaded_test_fixtures = ordered_fixtures
        self.call_plugins_method('afterFixtureLoad', settings, test)

        self.call_plugins_method('beforeUrlConfLoad', settings, test)
        if isinstance(test, nose.case.Test) and \
           hasattr(test.context, 'urls'):
            # We have to use this slightly awkward syntax due to the fact
            # that we're using *args and **kwargs together.
            self.old_urlconf = settings.ROOT_URLCONF
            settings.ROOT_URLCONF = test.context.urls
            clear_url_caches()
        self.call_plugins_method('afterUrlConfLoad', settings, test)

    def finalize(self, result=None):
        """
        Clean up any created database and schema.
        """
        if not self.settings_path:
            # short circuit if no settings file can be found
            return

        from django.test.utils import teardown_test_environment
        from django.db import connection
        from django.conf import settings
        from django.core.urlresolvers import clear_url_caches

        self.call_plugins_method('beforeDestroyTestDb', settings, connection)
        connection.creation.destroy_test_db(
            self.old_db,
            verbosity=self.verbosity,
        )
        self.call_plugins_method('afterDestroyTestDb', settings, connection)

        self.call_plugins_method(
            'beforeTeardownTestEnv', settings, teardown_test_environment)
        teardown_test_environment()
        self.call_plugins_method('afterTeardownTestEnv', settings)

        if hasattr(self, 'old_urlconf'):
            settings.ROOT_URLCONF = self.old_urlconf
            clear_url_caches()

    def report(self, stream):
        stream.writeln("Loaded fixtures %s times" % self._num_fixture_loads)
        stream.writeln("Flushed the db %s times" % self._num_flush_calls)
        stream.writeln("Sync'd the db %s times" % self._num_syncdb_calls)

    def _monkeypatch_test_classes(self):
        # Monkeypatching. Like a boss.
        # We're taking over all of the fixture management and such from the
        # django test classes. Dealing with switching back and forth between
        # them is a huge pita, and this just kind of works.
        import django.test.testcases

        overrides = [
            '_pre_setup',
            '_fixture_setup',
            '_urlconf_setup',
            '_post_teardown',
            '_fixture_teardown',
            '_urlconf_teardown',
        ]
        for override in overrides:
            setattr(
                django.test.testcases.TransactionTestCase,
                override,
                _dummy,
            )
            setattr(django.test.testcases.TestCase, override, _dummy)

        setattr(
            django.test.testcases.TransactionTestCase,
            'use_transaction_isolation',
            False,
        )
        setattr(
            django.test.testcases.TestCase,
            'use_transaction_isolation',
            True,
        )
