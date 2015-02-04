from django.conf import settings
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

    def test_db_alteration(self):
        if (
                hasattr(settings, 'DATABASES') and settings.DATABASES['default']['ENGINE'] == 'django.db.backends.mysql'  # noqa
        ) or (
                hasattr(settings, 'DATABASE_NAME') and settings.DATABASE_NAME == 'mysql'  # noqa
        ):
            from django.db import connection
            cursor = connection.cursor()
            cursor.execute('ALTER TABLE `polls_poll` CHANGE COLUMN `question` `question` varchar(201) COLLATE utf8_unicode_ci NOT NULL')  # noqa


class AltersBleed2TestCase(TestCase):
    fixtures = ['polls2.json']

    def test_bleeding_alteration(self):
        _test_fixtures_2(self)
