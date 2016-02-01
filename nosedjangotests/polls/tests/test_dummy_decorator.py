from importlib import import_module

from nose.plugins.skip import SkipTest

import django
from django.test import TestCase

from nosedjangotests.polls.models import Choice


class AtomicTestCase(TestCase):
    use_transaction_isolation = True

    fixtures = [
        'polls1.json',
        'choices.json',
    ]

    def test_decorator_atomic(self):
        if django.VERSION < (1, 7):
            raise SkipTest('This test is only an issue in django 1.8+')

        choice = Choice.objects.get()
        choice.votes = 42
        tester = import_module("polls.helpers")
        choice_pk = tester.decorator_reset_choice(choice=choice)
        self.assertEqual(choice_pk, choice.pk)
        choice = Choice.objects.get()
        self.assertEqual(choice.votes, 0)

    def test_callable_decorator_atomic(self):
        if django.VERSION < (1, 7):
            raise SkipTest('This test is only an issue in django 1.8+')

        choice = Choice.objects.get()
        choice.votes = 42
        tester = import_module("polls.helpers")
        choice_pk = tester.callable_reset_choice(choice=choice)
        self.assertEqual(choice_pk, choice.pk)
        choice = Choice.objects.get()
        self.assertEqual(choice.votes, 0)

    def test_context_manager_atomic(self):
        if django.VERSION < (1, 7):
            raise SkipTest('This test is only an issue in django 1.8+')

        choice = Choice.objects.get()
        choice.votes = 42
        tester = import_module("polls.helpers")
        choice_pk = tester.ctxt_man_reset_choice(choice=choice)
        self.assertEqual(choice_pk, choice.pk)
        choice = Choice.objects.get()
        self.assertEqual(choice.votes, 0)


class TransactionTestCase(TestCase):
    use_transaction_isolation = True

    fixtures = [
        'polls1.json',
        'choices.json',
    ]

    def test_decorator_atomic(self):
        if django.VERSION < (1, 7):
            raise SkipTest('This test is only an issue in django 1.8+')

        choice = Choice.objects.get()
        choice.votes = 42
        tester = import_module("polls.helpers")
        choice_pk = tester.transaction_decorator_reset_choice(choice=choice)
        self.assertEqual(choice_pk, choice.pk)
        choice = Choice.objects.get()
        self.assertEqual(choice.votes, 0)

    def test_callable_decorator_atomic(self):
        if django.VERSION < (1, 7):
            raise SkipTest('This test is only an issue in django 1.8+')

        choice = Choice.objects.get()
        choice.votes = 42
        tester = import_module("polls.helpers")
        choice_pk = tester.transaction_callable_reset_choice(choice=choice)
        self.assertEqual(choice_pk, choice.pk)
        choice = Choice.objects.get()
        self.assertEqual(choice.votes, 0)

    def test_context_manager_atomic(self):
        if django.VERSION < (1, 7):
            raise SkipTest('This test is only an issue in django 1.8+')

        choice = Choice.objects.get()
        choice.votes = 42
        tester = import_module("polls.helpers")
        choice_pk = tester.transaction_ctxt_man_reset_choice(choice=choice)
        self.assertEqual(choice_pk, choice.pk)
        choice = Choice.objects.get()
        self.assertEqual(choice.votes, 0)
