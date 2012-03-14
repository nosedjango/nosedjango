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

import nose.case
from nose.plugins import Plugin

# Force settings.py pointer
# search the current working directory and all parent directories to find
# the settings file
from nose.importer import add_path
if not 'DJANGO_SETTINGS_MODULE' in os.environ:
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

    def disable_transaction_support(self, transaction):
        self.orig_commit = transaction.commit
        self.orig_rollback = transaction.rollback
        self.orig_savepoint_commit = transaction.savepoint_commit
        self.orig_savepoint_rollback = transaction.savepoint_rollback
        self.orig_enter = transaction.enter_transaction_management
        self.orig_leave = transaction.leave_transaction_management

        transaction.commit = _dummy
        transaction.rollback = _dummy
        transaction.savepoint_commit = _dummy
        transaction.savepoint_rollback = _dummy
        transaction.enter_transaction_management = _dummy
        transaction.leave_transaction_management = _dummy

    def restore_transaction_support(self, transaction):
        transaction.commit = self.orig_commit
        transaction.rollback = self.orig_rollback
        transaction.savepoint_commit = self.orig_savepoint_commit
        transaction.savepoint_rollback = self.orig_savepoint_rollback
        transaction.enter_transaction_management = self.orig_enter
        transaction.leave_transaction_management = self.orig_leave

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

        self.old_db = hasattr(settings, 'DATABASES') and settings.DATABASES['default']['NAME'] or settings.DATABASE_NAME
        from django.db import connection

        self._monkeypatch_test_classes()

        self.call_plugins_method(
            'beforeTestSetup', settings, setup_test_environment, connection)
        setup_test_environment()
        self.call_plugins_method('afterTestSetup', settings)

        management.get_commands()
        # Ensure that nothing (eg. South) steals away our syncdb command
        management._commands['syncdb'] = 'django.core'

        self.call_plugins_method(
            'beforeTestDb', settings, connection, management)
        connection.creation.create_test_db(verbosity=self.verbosity)
        logger.debug("Running syncdb")
        self._num_syncdb_calls += 1
        self.call_plugins_method('afterTestDb', settings, connection)

    def _should_use_transaction_isolation(self, test, settings):
        """
        Determine if the given test supports transaction management for database
        rollback test isolation and also whether or not the test has opted out
        of that support.

        Transactions make database rollback much quicker when supported, with
        the caveat that any tests that are explicitly testing transactions won't
        work properly and any tests that depend on external access to the test
        database won't be able to view data created/altered during the test.
        """
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

    def _should_rebuild_schema(self, test):
        if getattr(test.context, 'rebuild_schema', False):
            return True
        return False

    def afterTest(self, test):
        """
        Clean up any changes to the test database.
        """
        # Restore transaction support on tests
        from django.conf import settings
        from django.contrib.contenttypes.models import ContentType
        from django.db import connection, transaction
        from django.test.utils import setup_test_environment, teardown_test_environment
        from django import VERSION as DJANGO_VERSION

        if self._should_rebuild_schema(test):
            connection.creation.destroy_test_db(
                self.old_db, verbosity=self.verbosity)
            teardown_test_environment()

            setup_test_environment()
            connection.creation.create_test_db(verbosity=self.verbosity)
            logger.debug("Running syncdb")
            self._num_syncdb_calls += 1
            self._loaded_test_fixtures = []
            return

        use_transaction_isolation = self._should_use_transaction_isolation(
            test, settings)

        if use_transaction_isolation:
            self.restore_transaction_support(transaction)
            logger.debug("Rolling back")
            transaction.rollback()
            if transaction.is_managed():
                transaction.leave_transaction_management()
            # If connection is not closed Postgres can go wild with
            # character encodings.
            connection.close()
        else:
            # Have to clear the db even if we're using django because django
            # doesn't properly flush the database after a test. It relies on
            # flushing before a test, so we want to avoid the case where a django
            # test doesn't flush and then a normal test runs, because it will
            # expect the db to already be flushed
            self._flush_db()
            self._loaded_test_fixtures = []

            # In Django <1.2 Depending on the order of certain post-syncdb
            # signals, ContentTypes can be removed accidentally. Manually delete and re-add all
            # and recreate ContentTypes if we're using the contenttypes app
            # See: http://code.djangoproject.com/ticket/9207
            # See: http://code.djangoproject.com/ticket/7052
            if DJANGO_VERSION[0] <= 1 and DJANGO_VERSION[1] < 2 \
               and 'django.contrib.contenttypes' in settings.INSTALLED_APPS:
                from django.contrib.contenttypes.management import update_all_contenttypes
                from django.db import models
                from django.contrib.auth.management import create_permissions
                from django.contrib.auth.models import Permission

                ContentType.objects.all().delete()
                ContentType.objects.clear_cache()
                update_all_contenttypes(verbosity=0)

                # Because of various ways of handling auto-increment, we need to
                # make sure the new contenttypes start at 1
                next_pk = 1
                content_types = list(ContentType.objects.all().order_by('pk'))
                ContentType.objects.all().delete()
                for ct in content_types:
                    ct.pk = next_pk
                    ct.save()
                    next_pk += 1

                # Because of the same problems with ContentTypes, we can get
                # busted permissions
                Permission.objects.all().delete()
                for app in models.get_apps():
                    create_permissions(app=app, created_models=None, verbosity=0)

                # Because of various ways of handling auto-increment, we need to
                # make sure the new permissions start at 1
                next_pk = 1
                permissions = list(Permission.objects.all().order_by('pk'))
                Permission.objects.all().delete()
                for perm in permissions:
                    perm.pk = next_pk
                    perm.save()
                    next_pk += 1

        self.call_plugins_method('afterRollback', settings)

    def _flush_db(self):
        from django.contrib.contenttypes.models import ContentType
        from django.core.management import call_command
        ContentType.objects.clear_cache() # Otherwise django.contrib.auth.Permissions will depend on deleted ContentTypes
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
        from django.db import transaction

        use_transaction_isolation = self._should_use_transaction_isolation(
            test, settings)

        if use_transaction_isolation:
            self.call_plugins_method('beforeTransactionManagement', settings, test)
            transaction.enter_transaction_management()
            transaction.managed(True)
            self.disable_transaction_support(transaction)

        Site.objects.clear_cache()
        ContentType.objects.clear_cache() # Otherwise django.contrib.auth.Permissions will depend on deleted ContentTypes

        if use_transaction_isolation:
            self.call_plugins_method('afterTransactionManagement', settings, test)

        self.call_plugins_method('beforeFixtureLoad', settings, test)
        if isinstance(test, nose.case.Test):
            # Mirrors django.test.testcases:TestCase

            if hasattr(test.context, 'fixtures'):
                # We have to use this slightly awkward syntax due to the fact
                # that we're using *args and **kwargs together.
                ordered_fixtures = sorted(test.context.fixtures)
                if ordered_fixtures != self._loaded_test_fixtures:
                    # Only clear + load the fixtures if they're not already loaded

                    # Flush previous fixtures
                    self._flush_db()
                    if use_transaction_isolation:
                        self.restore_transaction_support(transaction)
                        transaction.commit()
                        self.disable_transaction_support(transaction)

                    # Load the new fixtures
                    logger.debug("Loading fixtures: %s", test.context.fixtures)
                    if use_transaction_isolation:
                        call_command(
                            'loaddata',
                            *test.context.fixtures,
                            **{'verbosity': 0, 'commit': False}
                        )
                        self.restore_transaction_support(transaction)
                        transaction.commit()
                        self.disable_transaction_support(transaction)
                    else:
                        call_command(
                            'loaddata',
                            *test.context.fixtures,
                            **{'verbosity': 0}
                        )
                    self._num_fixture_loads += 1
                    self._loaded_test_fixtures = ordered_fixtures
        self.call_plugins_method('afterFixtureLoad', settings, test)

        self.call_plugins_method('beforeUrlConfLoad', settings, test)
        if isinstance(test, nose.case.Test) and \
           hasattr(test.context, 'urls'):
            # We have to use this slightly awkward syntax due to the fact
            # that we're using *args and **kwargs together.
            self.old_urlconf = settings.ROOT_URLCONF
            settings.ROOT_URLCONF = self.urls
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
        connection.creation.destroy_test_db(self.old_db, verbosity=self.verbosity)
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
            setattr(django.test.testcases.TransactionTestCase, override, _dummy)
            setattr(django.test.testcases.TestCase, override, _dummy)

        setattr(django.test.testcases.TransactionTestCase, 'use_transaction_isolation', False)
        setattr(django.test.testcases.TestCase, 'use_transaction_isolation', True)
