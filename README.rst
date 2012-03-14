Nose django helper plugin
=========================

Nosedjango brings the goodness of Nose and its plugin ecosystem to the world of
Django testing. Nose already has plugins for multiprocessing, coverage, tagging,
profiling, skipping, xunit plugin and most everything else you could need. 
Nosedjango means you don't have to re-invent those wheels.

Perhaps the most compelling case for using nosedjango is the performance gains 
seen when using the multiprocess module. (both runs on a core i7 laptop with a 
fixture-intensive test suite) 

Normal Django testrunner using sqlite ::

    $ ./manage.py test account
    ...
    Ran 65 tests in 507.930s

    OK

NoseDjango with 8 processes ::

    $ nosetests --with-doctest --with-django --django-settings pstat.settings --with-django-testfs --with-django-sqlite --processes 8 pstat.account
    ...
    Ran 65 tests in 35.731s

Nose is ~14x faster.
    
Easy Extensibility
------------------

In addition, Nosedjango provides its own plugin system to hook in to the low
level django-specific testing operations. Included with Nosedjango are plugins
to do things like:

* Create an isolated file storage location for testing.
* Use an in-memory sqlite database.
* Start a cherrpy server for integration-style tests.
* Make it easier to test Celery.
* Create and use a Sphinx search index for fulltext search tests.
* Open an SSH tunnel for things like Selenium that might need outside 
  resources.
* Run Selenium2 functional tests in a headless virtual frame buffer.
* Selectively switch out settings from the command line for different kinds
  of tests.

The plugin takes care of finding your applications settings.py file
and creating/tearing down test database. It also has support for
fixtures and it has experimental mechanism that wraps the tests in
transactions to speed up testing.

This plugin works with Django versions 1.2 and 1.3.

Basic Usage
-----------

Unit tests can be run with following command::

  nosetests --with-django [nose-options]

Command line options
~~~~~~~~~~~~~~~~~~~~

In addition to default nose command line options, nosedjango offers
the following options:

--django-settings=MODULE    Specify a custom Django settings `MODULE`.
                            The specified `MODULE` needs to be found
                            in ``sys.path``.

--django-sqlite             If set, use in-memory sqlite database for
                            tests.

--django-interactive        Run tests in interactive mode (see
                            `DjangoTestSuiteRunner documentation
                            <http://docs.djangoproject.com/en/dev/topics/testing/#django.test.simple.DjangoTestSuiteRunner>`_).
                            Default: false.

Parallel Test Running Via Multiprocess
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An easy win for Nosedjango out of the box is the ability to safely distribute
tests across multiple processes, dramatically speeding up test runs on
multicore machines. 

In the simplest case, the following will run your tests distributed across two
cores using in-memory sqlite databases and separate file storage locations
to minimize file collision conflicts::

    nosetests --with-django --with-django-sqlite --with-django-testfs --processes=2 <your_project_module>

.. Note:: 
    For very small test suites or test suites that don't use fixtures, the 
    overhead from starting multiple processes can result in the full test
    run actually being *slower* with multiple processes compared to a single
    process.

    Complex test suites might require some adaptation to support parallel test
    running. If tests rely on things like hardcoded file paths or shared
    external resources, these will need to be made generic. Usually this is as
    easy as using a NamedTemporaryFile instead of a hardcoded path.


Installation
------------

Installation via Pip is straightforward::

    $ pip install -e git+git://github.com/nosedjango/nosedjango.git#egg=nosedjango


Running the Nosedjango Test Suite
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An easy way to try out your nosedjango installation is to try the test suite
yourself::

    $ python setup.py nosetests


Deviations From the Django Testrunner
-------------------------------------

Nosedjango makes a few decisions differently than Django's normal testrunner
and depending on your project, you might need to make adjustments for all of
your tests to run properly.


Doctests Skipped by Default
~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default, Nose only runs doctests if the ``--with-doctest`` option is
included. Nosedjango respects this default rather than the Django default, so
if you'd like to run your doctests, add ``--with-doctest`` to your options.

Test Discovery
~~~~~~~~~~~~~~

Nosedjango relies on Nose's test discovery method, which means that Nose might
find some tests that weren't being run by Django. 

Database Schema Isn't Re-created Every Test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For performance reasons, the database schema is only created once. If you have
tests that alter the schema (migration tests for example), you'll need to add
a ``rebuild_schema`` attribute to those tests.

For example::

    class LargerUsernameTestCase(TestCase):
        rebuild_schema = True

        def setUp(self):
            if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.mysql':
                from django.db import connection # pylint: disable=W0404
                cursor = connection.cursor()
                cursor.execute("ALTER TABLE `auth_user` CHANGE COLUMN `username` "
                               "`username` VARCHAR(130) "
                               "COLLATE utf8_unicode_ci NOT NULL")
                                

        def test_long_username(self):
            # test some stuff

Fixture Loading
~~~~~~~~~~~~~~~

Nose supports module-level fixtures, and so does Nosedjango. This means that if
you have a ``fixtures`` variable floating around in a test module, Nosedjango
will load it.

For example:: 

    fixtures = ['cheese.json', 'cakes']

    def test_cheesecake():
        # do something...

Cache is Cleared Between Tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The cache is cleared between each test run, as is the case with newer versions
of Django. If you have tests that depend on other tests modifying the cache
(*tsk tsk tsk*), then you will need to modify those tests for them to work
under Nosedjango.


Plugin System
-------------

Nosedjango's plugin system is heavily inspired by Nose's own system and provides
loads of hooks in to the Django test-running process. Nosedjango plugins are
actually just Nose plugins themselves that have access to extra hooks. To see
available hooks, check out ``nosedjango.plugins.base_plugin.Plugin``. Plugins
should extend that class.

Better documentation is hopefully forthcoming, but reading the source for the
included ``file_storage_plugin`` and ``sqlite_plugin`` should provide clues
along with Nose's documentation on writing plugins. One example of solving
very project-specific testing needs is the NoseDjango plugin located at
https://github.com/jlward/nosedjango-pstat

Known Issues
------------

* Multiprocess testing only currently works with in-memory sqlite. This is very
  fixable though and pull requests are welcome.
* Nosedjango is broken with Nose 1.0 and higher due to changes in Nose's
  Multiprocessing module. This is currently being investigated.

Authors
-------

NoseDjango is currently maintained by Wes Winham <winhamwr@gmail.com>. 
It was previously maintained by Jyrki Pulliainen
<jyrki.pulliainen@inoi.fi>.

Original plugin courtesy of Victor Ng <crankycoder@gmail.com> who
rewrote Jason Pellerin's original nose-django plugin.

For all contributors, see *AUTHORS* file.

Contributing
------------

This project and it's issues are currently hosted in github_. If you
find a bug or have a feature request, use `github's issue tracker`_
for that.

.. _github: http://github.com/nosedjango/nosedjango/
.. _github's issue tracker: http://github.com/nosedjango/nosedjango/issues

Patches are welcome :)

Continuous Integration
----------------------

The `nosedjango Jenkins server`_ is graciously hosted by `Shining Panda`.
It allows us to test all supported versions of Django against all supported
databases.

.. _nosedjango Jenkins server: https://jenkins.shiningpanda.com/nosedjango/
.. _Shining Panda: http://www.shiningpanda.com

License
-------

This software is licensed with GNU LESSER GENERAL PUBLIC LICENSE
version 3 or (at your option) any later version. See *COPYING* for
more details.
