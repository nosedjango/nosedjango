from datetime import datetime

from django.test.testcases import TestCase

from nosedjangotests.polls.models import Choice, Poll


class _SubclassedTestCase(TestCase):
    pass


class AAAFixtureTestCase(_SubclassedTestCase):
    fixtures = [
        'choices',
    ]

    def test_to_load_fixtures(self):
        self.assertEqual(Choice.objects.count(), 1)


class BBBNoLeftoverFixturesTestCase(TestCase):
    def test_no_data_left_over_from_previous_fixture(self):
        self.assertEqual(Choice.objects.count(), 0)


class AAANonFixtureTestCase(_SubclassedTestCase):
    def test_to_load_fixtures(self):
        Poll.objects.create(
            pub_date=datetime.now()
        )
        self.assertEqual(Poll.objects.count(), 1)


class BBBNoLeftoverNonFixturesTestCase(TestCase):
    def test_no_data_left_over_from_previous_fixture(self):
        self.assertEqual(Poll.objects.count(), 0)
