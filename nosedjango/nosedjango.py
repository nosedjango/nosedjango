"""
nose plugin for easy testing of django projects and apps. Sets up a test
database (or schema) and installs apps from test settings file before tests
are run, and tears the test database (or schema) down after all tests are run.
"""

import os, sys
import re

from nose.plugins import Plugin
import nose.case

# Force settings.py pointer
# search the current working directory and all parent directories to find
# the settings file
from nose.importer import add_path
if not 'DJANGO_SETTINGS_MODULE' in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from django.core.management import setup_environ

import re
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

    def disable_transaction_support(self, transaction):
        self.orig_commit = transaction.commit
        self.orig_rollback = transaction.rollback
        self.orig_savepoint_commit = transaction.savepoint_commit
        self.orig_savepoint_rollback = transaction.savepoint_rollback
        self.orig_enter = transaction.enter_transaction_management
        self.orig_leave = transaction.leave_transaction_management
        self.orig_managed = transaction.managed

        transaction.commit = _dummy
        transaction.rollback = _dummy
        transaction.savepoint_commit = _dummy
        transaction.savepoint_rollback = _dummy
        transaction.enter_transaction_management = _dummy
        transaction.leave_transaction_management = _dummy
        transaction.managed = _dummy

    def restore_transaction_support(self, transaction):
        transaction.commit = self.orig_commit
        transaction.rollback = self.orig_rollback
        transaction.savepoint_commit = self.orig_savepoint_commit
        transaction.savepoint_rollback = self.orig_savepoint_rollback
        transaction.enter_transaction_management = self.orig_enter
        transaction.managed = self.orig_managed
        transaction.leave_transaction_management = self.orig_leave

    def options(self, parser, env):
        parser.add_option('--django-settings',
                          help='Use custom Django settings module.',
                          metavar='SETTINGS',
                          )
        parser.add_option('--django-sqlite',
                          help='Use in-memory sqlite for the tests',
                          metavar='use_sqlite',
                          )
        parser.add_option('--django-interactive',
                          help='Run tests in interactive mode',
                          action='store_true',
                          default=False,
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

        self._use_sqlite = False
        if options.django_sqlite:
            self._use_sqlite = True

        self.interactive = options.django_interactive
        super(NoseDjango, self).configure(options, conf)

    def begin(self):
        """Create the test database and schema, if needed, and switch the
        connection over to that database. Then call install() to install
        all apps listed in the loaded settings module.
        """
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

        # If the user passed in --django-sqlite, use an in-memory sqlite db
        if self._use_sqlite:
            settings.DATABASE_ENGINE = 'sqlite3'
            settings.TEST_DATABASE_NAME = None # in-memory database

        # Some Django code paths evaluate differently
        # between DEBUG and not DEBUG.  Example of this include the url
        # dispatcher when 404's are hit.  Django's own test runner forces DEBUG
        # to be off.
        settings.DEBUG = False

        from django.core import management
        from django.test.utils import setup_test_environment

        self.old_db = settings.DATABASE_NAME
        from django.db import connection

        if 'south' in settings.INSTALLED_APPS:
            # South has its own test command that turns off migrations
            # during testings.  If we detected south, we need to fix syncdb.
            management.get_commands()
            management._commands['syncdb'] = 'django.core'

        setup_test_environment()

        if self.interactive:
            # For database creation only, bypass the capture plugin. This
            # allows the user to interact with the "test database already
            # exists" message.
            old_stdout = sys.stdout
            sys.stdout = sys.__stdout__
            try:
                connection.creation.create_test_db(verbosity=self.verbosity)
            finally:
                sys.stdout = old_stdout
        else:
            # If we're in the non-interactive mode (default) destroy
            # the existing test database without consulting the user
            connection.creation.create_test_db(
                verbosity=self.verbosity,
                autoclobber=True
                )

    def _has_transaction_support(self, test):
        from django.conf import settings
        transaction_support = True
        if hasattr(test.context, 'use_transaction'):
            transaction_support = test.context.use_transaction
        if hasattr(settings, 'DISABLE_TRANSACTION_MANAGEMENT'):
            # Do not use transactions if user has forbidden usage.
            # Assume that the database supports them anyway.
            transaction_support = not settings.DISABLE_TRANSACTION_MANAGEMENT
        if (hasattr(settings, 'DATABASE_SUPPORTS_TRANSACTIONS') and
            not settings.DATABASE_SUPPORTS_TRANSACTIONS):
            transaction_support = False
        return transaction_support

    def afterTest(self, test):
        # Restore transaction support on tests
        from django.db import connection, transaction
        from django.core.management import call_command

        transaction_support = self._has_transaction_support(test)
        try:
            # Django 1.0 doesn't have TransactionTestCase
            from django.test import TransactionTestCase
            if isinstance(test.test, TransactionTestCase):
                transaction_support = False
        except ImportError:
            pass

        if transaction_support:
            self.restore_transaction_support(transaction)
            transaction.rollback()
            transaction.leave_transaction_management()
            # If connection is not closed Postgres can go wild with
            # character encodings.
            connection.close()
        else:
            call_command('flush', verbosity=0, interactive=False)

    def beforeTest(self, test):

        if not self.settings_path:
            # short circuit if no settings file can be found
            return

        from django.core.management import call_command
        from django.core.urlresolvers import clear_url_caches
        from django.db import connection, transaction
        from django.core import mail
        from django.conf import settings

        mail.outbox = []

        transaction_support = self._has_transaction_support(test)
        try:
            # Django 1.0 doesn't have TransactionTestCase
            from django.test import TransactionTestCase
            if isinstance(test.test, TransactionTestCase):
                transaction_support = False
        except ImportError:
            pass

        if transaction_support:
            # If test is a django.TransactionTestCase, it already does
            # transactions, so let's not brother about it
            settings.TRANSACTIONS_MANAGED = True
            transaction.enter_transaction_management()
            transaction.managed(True)
            self.disable_transaction_support(transaction)

        if isinstance(test, nose.case.Test) and \
            isinstance(test.test, nose.case.MethodTestCase) and \
            hasattr(test.context, 'fixtures'):
                # We have to use this slightly awkward syntax due to the fact
                # that we're using *args and **kwargs together.
                call_command('loaddata', *test.context.fixtures, **{'verbosity': 0})

        if isinstance(test, nose.case.Test) and \
            isinstance(test.test, nose.case.MethodTestCase) and \
            hasattr(test.context, 'urls'):
            # We have to use this slightly awkward syntax due to the fact
            # that we're using *args and **kwargs together.
            self.old_urlconf = settings.ROOT_URLCONF
            settings.ROOT_URLCONF = self.urls
            clear_url_caches()


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
        connection.creation.destroy_test_db(self.old_db, verbosity=self.verbosity)
        teardown_test_environment()

        if hasattr(self, 'old_urlconf'):
            settings.ROOT_URLCONF = self.old_urlconf
            clear_url_caches()

