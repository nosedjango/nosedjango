from django.test import TestCase, TransactionTestCase

from nosedjangotests.polls.models import Choice, Poll, PollPair
from nosedjangotests.polls.tests.test1 import (
    _test_fixtures_1,
    _test_fixtures_2,
)
from nosedjangotests.polls.test_helpers import (
    ClientTestCase,
    FactoryClientTestCase,
)


class AAATestCase(TransactionTestCase):
    fixtures = [
        'polls2',
    ]

    def test(self):
        _test_fixtures_2(self)


class BBBTestCase(TestCase):
    fixtures = [
        'polls1',
    ]

    def test(self):
        _test_fixtures_1(self)


class CCCFixtureTestCase(ClientTestCase):
    fixtures = [
        'choices',
        'polls1',
        'poll_pairs',
    ]

    def test_to_load_fixtures(self):
        self.assertEqual(PollPair.objects.filter(pk=1).count(), 1)
        self.assertEqual(Poll.objects.count(), 1)
        self.assertEqual(Choice.objects.count(), 1)


class _SharedBaseTestCase(FactoryClientTestCase):
    def setUp(self):
        super(_SharedBaseTestCase, self).setUp()


class DDDNoLeftoverFixturesTestCase(_SharedBaseTestCase):
    def test_no_data_left_over_from_previous_fixture(self):
        self.assertEqual(Poll.objects.count(), 0)
        self.assertEqual(PollPair.objects.count(), 0)
        self.assertEqual(Choice.objects.count(), 0)
