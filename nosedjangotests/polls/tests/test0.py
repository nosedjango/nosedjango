
from django.test import TestCase

from nosedjangotests.polls.models import Choice


def _test_using_content_types(self):
    self.assertEqual(Choice.objects.all().count(), 1)


class ContentTypeTestCase(TestCase):
    fixtures = [
        'polls1.json',
        'choices.json',
    ]

    def test_using_content_types_1(self):
        _test_using_content_types(self)

    def test_using_content_types_2(self):
        _test_using_content_types(self)


class CherryPyTestCase(ContentTypeTestCase):
    start_live_server = True
