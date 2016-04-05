import codecs
import os
import sys

from setuptools import setup, find_packages, Command

import tempfile


class RunTestBase(Command):
    description = "Run the test suite from the tests dir."
    user_options = []
    extra_env = {}

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass


class RunTests(RunTestBase):
    test_app = 'nosedjangotests.polls'
    check_selenium = False
    label = ''
    args = []

    def verify_selenium(self):
        if not self.check_selenium:
            return
        try:
            import selenium  # noqa
        except ImportError:
            print("Selenium not installed. Skipping tests.")
            sys.exit(0)

    def run(self):
        for env_name, env_value in self.extra_env.items():
            os.environ[env_name] = str(env_value)

        setup_dir = os.path.abspath(os.path.dirname(__file__))
        tests_dir = os.path.join(setup_dir, 'nosedjangotests')
        os.chdir(tests_dir)
        sys.path.append(tests_dir)

        try:
            from nose.core import TestProgram
            import nosedjango
            print(nosedjango.__version__)
        except ImportError:
            print('nose and nosedjango are required to run this test suite')
            sys.exit(1)

        print("Running tests with {label}".format(label=self.label))
        self.verify_selenium()

        test_args = [
            '-v',
            '--verbosity=2',
            '--with-doctest',
            '--with-django',
            '--django-settings', 'nosedjangotests.settings',
            self.test_app,
        ] + self.args
        TestProgram(argv=test_args, exit=True)


class SQLiteTestCase(RunTests):
    label = 'sqlite'
    args = [
        '--with-django-sqlite',
    ]


class MultiProcessTestCase(RunTests):
    label = 'sqlite and multiprocess'
    args = [
        '--with-django-sqlite',
        '--processes', '3',
    ]


class MySQLTestCase(RunTests):
    label = 'MySQL'


class CherryPyLiveServerTestCase(RunTests):
    label = 'Cherry Py Test Case'
    args = [
        '--with-django-sqlite',
        '--with-cherrypyliveserver',
    ]


class SeleniumTestCase(RunTests):
    label = 'Selenium'
    test_app = 'nosedjangotests.selenium_tests'
    check_selenium = True
    args = [
        '--with-selenium',
    ]

class SeleniumFirefoxProfileTestCase(RunTests):
    label = 'Selenium'
    test_app = 'nosedjangotests.selenium_firefox_profile_tests'
    check_selenium = True
    args = [
        '--with-selenium',
        '--with-django-sqlite',
        '--ff-profile', 'browser.helperApps.neverAsk.saveToDisk="application/ourfakemimetype"',
        '--ff-profile', 'browser.download.dir="{0}"'.format(tempfile.gettempdir()),
        '--ff-profile', 'browser.download.folderList=2',
        '--ff-profile', 'browser.download.manager.showWhenStarting=False'
    ]

class SeleniumBinaryTestCase(RunTests):
    label = 'Selenium Binary Option'
    test_app = 'nosedjangotests.selenium_binary_tests'
    check_selenium = True
    args = [
        '--with-django-sqlite',
        '--with-selenium',
    ]

    def run(self):
        self.verify_selenium()
        from selenium.webdriver.firefox.firefox_binary import FirefoxBinary

        # borrow selenium's magical binary finding logic
        dummy_binary = FirefoxBinary()
        ff_path = dummy_binary._start_cmd.strip()

        # mangle the path with a no-op of prefix slashes.
        # symlinks run into very nasty issues with newer versions of Firefox on OSX

        self.args.append('--firefox-binary=////%s' % ff_path)

        RunTests.run(self)

import nosedjango

long_description = codecs.open("README.rst", "r", "utf-8").read()

setup(
    name='nosedjango',
    version=nosedjango.__version__,
    description=nosedjango.__doc__,
    author=nosedjango.__author__,
    author_email=nosedjango.__contact__,
    long_description=long_description,
    install_requires=['nose<2.0', 'django'],
    extras_require={
        'selenium': ['selenium>=2.0'],
    },
    dependency_links=['http://bitbucket.org/jpellerin/nose/get/release_0.11.4.zip#egg=nose-0.11.4.dev'],  # noqa
    url="http://github.com/nosedjango/nosedjango",
    license='GNU LGPL',
    # We're using find_packages here to ensure that the plugin package as well
    # as the main package are included in the distribution
    packages=find_packages(exclude=['nosedjangotests', 'nosedjangotests.*']),
    zip_safe=False,
    cmdclass={
        'test_sqlite': SQLiteTestCase,
        'test_multiprocess': MultiProcessTestCase,
        'test_mysql': MySQLTestCase,
        'test_selenium': SeleniumTestCase,
        'test_selenium_firefox_profile': SeleniumFirefoxProfileTestCase,
        'test_selenium_binary': SeleniumBinaryTestCase,
        'test_cherrypy': CherryPyLiveServerTestCase,
    },
    include_package_data=True,
    entry_points={
        'nose.plugins': [
            'celery = nosedjango.plugins.celery_plugin:CeleryPlugin',
            'cherrypyliveserver = nosedjango.plugins.cherrypy_plugin:CherryPyLiveServerPlugin',  # noqa
            'django = nosedjango.nosedjango:NoseDjango',
            'djangofilestorage = nosedjango.plugins.file_storage_plugin:FileStoragePlugin',  # noqa
            'djangosphinxsearch = nosedjango.plugins.sphinxsearch_plugin:SphinxSearchPlugin',  # noqa
            'djangosqlite = nosedjango.plugins.sqlite_plugin:SqlitePlugin',
            'selenium = nosedjango.plugins.selenium_plugin:SeleniumPlugin',
            'sshtunnel = nosedjango.plugins.ssh_tunnel_plugin:SshTunnelPlugin',
        ],
    },
)
