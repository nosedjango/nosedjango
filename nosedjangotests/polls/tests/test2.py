from django.test import TestCase

from nosedjangotests.polls.models import Poll
from nosedjangotests.polls.tests.test1 import _test_fixtures_2


class BaseCase(TestCase):

    def __init__(self, *args, **kwargs):
        inits = ['polls1.json', 'polls2.json']
        self.fixtures = list(inits + getattr(self, 'fixtures', []))
        super(BaseCase, self).__init__(*args, **kwargs)

    def setUp(self):
        pass


class FixtureBleed1TestCase(BaseCase):
    fixtures = [
        'polls1.json',
    ]

    def test_fixtures_loaded(self):
        num_polls = Poll.objects.all().count()
        # Ignore the evil __init__ overriding of self.fixtures
        self.assertEqual(num_polls, 1)


class FixtureBleed2TestCase(TestCase):
    fixtures = ['polls1.json']

    def test_fixture_bleed(self):
        num_polls = Poll.objects.all().count()
        self.assertEqual(num_polls, 1)


class AltersBleed1TestCase(TestCase):
    fixtures = ['polls1.json']
    rebuild_schema = True

    # This test must run first
    def test_aaa_db_alteration(self):
        # Alter the table in a sufficient fashion that if the schema was not
        # rebuilt, it would cause problems for future tests.
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute('DROP TABLE `polls_poll`')

    # This test must run second.
    def test_zzz_db_was_rebuilt(self):
        # Ensure the schema was rebuilt by querying on the Poll Table
        self.assertNotEqual(Poll.objects.count(), 0)


class AltersBleed2TestCase(TestCase):
    fixtures = ['polls2.json']

    def test_bleeding_alteration(self):
        _test_fixtures_2(self)
