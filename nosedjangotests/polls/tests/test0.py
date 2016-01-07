from contextlib import contextmanager
from datetime import datetime

import django
try:
    from django.db.transaction import atomic
except ImportError:
    from django.db.transaction import commit_on_success as atomic
from django.db import transaction
from django.db.transaction import TransactionManagementError
from django.test import TestCase

from nose.plugins.skip import SkipTest

from nosedjangotests.polls.models import Choice, Poll


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


@contextmanager
def set_autocommit(value):
    old_value = transaction.get_autocommit()
    transaction.set_autocommit(value)
    yield
    transaction.set_autocommit(old_value)


class FixtureBleedThroughTestCase(TestCase):
    use_transaction_isolation = True

    fixtures = [
        'polls1.json',
        'choices.json',
    ]

    def test_AAA_change_poll_question(self):
        if django.VERSION < (1, 7):
            raise SkipTest('This test is only an issue in django 1.8+')
        poll = Poll.objects.get()
        poll.question = 'What does the fox say?'

        # If we are using transaction isolation, then using atomic/autocommit
        # is invalid.
        if self.use_transaction_isolation:
            with self.assertRaises(TransactionManagementError):
                with set_autocommit(True):
                    with atomic():
                        poll.save()
        else:
            with set_autocommit(True):
                with atomic():
                    poll.save()

    def test_BBB_poll_question_is_what_is_in_the_fixture(self):
        poll = Poll.objects.get()
        self.assertEqual(poll.question, 'What bear is best?')


class NonFixtureBleedThroughTestCase(TestCase):
    use_transaction_isolation = True

    def test_AAA_create_a_poll(self):
        if django.VERSION < (1, 7):
            raise SkipTest('This test is only an issue in django 1.8+')
        # If we are using transaction isolation, then using atomic/autocommit
        # is invalid.
        if self.use_transaction_isolation:
            with self.assertRaises(TransactionManagementError):
                with set_autocommit(True):
                    with atomic():
                        Poll.objects.create(
                            question='Test',
                            pub_date=datetime.now(),
                        )
        else:
            with set_autocommit(True):
                with atomic():
                    Poll.objects.create(
                        question='Test',
                        pub_date=datetime.now(),
                    )

    def test_BBB_no_polls_in_the_db(self):
        self.assertEqual(Poll.objects.count(), 0)


class FixtureBleedThroughWithoutTransactionManagementTestCase(FixtureBleedThroughTestCase):  # noqa
    use_transaction_isolation = False


class NonFixtureBleedThroughWithoutTransactionManagementTestCase(NonFixtureBleedThroughTestCase):  # noqa
    use_transaction_isolation = False
