from django.test import TestCase, TransactionTestCase

from nosedjangotests.polls.models import Poll, PollPair
from nosedjangotests.polls.tests.test1 import (
    _test_fixtures_1,
    _test_fixtures_2,
)


def _assert_no_data(self):
    self.assertEqual(Poll.objects.count(), 0)
    self.assertEqual(PollPair.objects.count(), 0)


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


class CCCBrokenFixtureTestCase(TestCase):
    fixtures = [
        'poll_pairs',
    ]

    def test(self):
        pp = PollPair.objects.get(pk=1)
        assert pp.first_poll
        _assert_no_data(self)


class DDDAfterBrokenFixtureNoLeftoversTestCase(TestCase):
    fixtures = []

    def test(self):
        _assert_no_data(self)
