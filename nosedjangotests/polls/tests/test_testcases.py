from datetime import datetime

from django.db import transaction
from django.test.testcases import TestCase, TransactionTestCase

from nosedjangotests.polls.models import Poll


class MakePollMixin():
    def make_poll(self):
        Poll.objects.create(
            question='Test',
            pub_date=datetime.now(),
        )

    def make_poll_and_error(self):
        Poll.objects.create(
            question='Test',
            pub_date=datetime.now(),
        )
        raise Exception("Oops, that is not a question")


class TestTestCase(TestCase, MakePollMixin):
    def test_make_poll(self):
        with transaction.atomic():
            self.make_poll()
        self.assertEqual(Poll.objects.count(), 1)

    def test_make_poll_and_error(self):
        with self.assertRaisesMessage(Exception, "Oops"):
            with transaction.atomic():
                self.make_poll_and_error()
        self.assertEqual(Poll.objects.count(), 1)


class TestTransactionTestCase(TransactionTestCase, MakePollMixin):
    def test_make_poll(self):
        with transaction.atomic():
            self.make_poll()
        self.assertEqual(Poll.objects.count(), 1)

    def test_make_poll_and_error(self):
        with self.assertRaisesMessage(Exception, "Oops"):
            with transaction.atomic():
                self.make_poll_and_error()
        self.assertEqual(Poll.objects.count(), 0)
