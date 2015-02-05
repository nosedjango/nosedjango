from django.test.testcases import TestCase

from nosedjangotests.polls.models import Choice


class AAAFixtureTestCase(TestCase):
    fixtures = [
        'choices',
    ]

    def test_to_load_fixtures(self):
        self.assertEqual(Choice.objects.count(), 1)


class BBBNoFixturesFollowingWithFixturesTestCase(TestCase):
    def test_no_data_left_over_from_previous_fixture(self):
        self.assertEqual(Choice.objects.count(), 0)
