import codecs
import os
import sys

from setuptools import setup, find_packages, Command

class RunTests(Command):
    description = "Run the test suite from the tests dir."
    user_options = []
    extra_env = {}

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
            print nosedjango.__version__
        except ImportError:
            print 'nose and nosedjango are required to run this test suite'
            sys.exit(1)

        print "Running tests with sqlite"
        args = [
            '-v',
            '--with-doctest',
            '--with-django',
            '--django-settings', 'nosedjangotests.settings',
            '--with-django-sqlite',
            'nosedjangotests.polls',
        ]
        TestProgram(argv=args, exit=False)

        print "Running tests multiprocess"
        args = [
            '-v',
            '--with-doctest',
            '--processes', '3',
            '--with-django',
            '--django-settings', 'nosedjangotests.settings',
            '--with-django-sqlite',
            'nosedjangotests.polls',
        ]
        TestProgram(argv=args, exit=False)

        print "Running tests with mysql. (will fail if mysql not configured)"
        args = [
            '-v',
            '--with-id',
            '--with-doctest',
            '--with-django',
            '--django-settings', 'nosedjangotests.settings',
            'nosedjangotests.polls',
        ]
        TestProgram(argv=args, exit=False)

        print "Running tests selenium. (will fail if mysql not configured)"
        args = [
            '-v',
            '--with-id',
            '--with-doctest',
            '--with-django',
            '--with-selenium',
            '--django-settings', 'nosedjangotests.settings',
            'nosedjangotests.selenium_tests',
        ]
        TestProgram(argv=args, exit=False)

        os.chdir(setup_dir)

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

import nosedjango

long_description = codecs.open("README.rst", "r", "utf-8").read()

setup(
    name='nosedjango',
    version=nosedjango.__version__,
    description=nosedjango.__doc__,
    author=nosedjango.__author__,
    author_email=nosedjango.__contact__,
    long_description=long_description,
    install_requires=['nose>=0.11', 'nose<1.0'],
    url = "http://github.com/nosedjango/nosedjango",
    license = 'GNU LGPL',
    packages = find_packages(exclude=['nosedjangotests', 'nosedjangotests.*']),
    zip_safe = False,
    cmdclass = {'test': RunTests},
    include_package_data = True,
    entry_points = {
        'nose.plugins': [
            'celery = nosedjango.plugins.celery_plugin:CeleryPlugin',
            'cherrypyliveserver = nosedjango.plugins.cherrypy_plugin:CherryPyLiveServerPlugin',
            'django = nosedjango.nosedjango:NoseDjango',
            'djangofilestorage = nosedjango.plugins.file_storage_plugin:FileStoragePlugin',
            'djangosphinxsearch = nosedjango.plugins.sphinxsearch_plugin:SphinxSearchPlugin',
            'djangosqlite = nosedjango.plugins.sqlite_plugin:SqlitePlugin',
            'selenium = nosedjango.plugins.selenium_plugin:SeleniumPlugin',
            'sshtunnel = nosedjango.plugins.ssh_tunnel_plugin:SshTunnelPlugin',
        ],
    },
)
