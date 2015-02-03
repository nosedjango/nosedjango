from django.test import TestCase, TransactionTestCase

from nosedjangotests.polls.tests.test1 import (
    _test_fixtures_1,
    _test_fixtures_2,
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
