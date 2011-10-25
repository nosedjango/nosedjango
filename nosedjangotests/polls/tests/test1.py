import datetime
from unittest import TestCase as UnitTestCase

from nose.plugins.skip import SkipTest

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from nosedjangotests.polls.models import Poll, Choice

def _test_using_content_types(self):
    p1, _ = Poll.objects.get_or_create(
        question='Who you?', pub_date=datetime.datetime.now())

    choice1 = Choice(poll=p1, choice='me')
    choice1.save()

def _test_get_contenttypes(self):
    models = [Poll, Choice]

    for model in models:
        content_type = ContentType.objects.get_for_model(model)

        # Make sure this isn't just using the cache
        ct_db = ContentType.objects.get(pk=content_type.pk)
        for attr in ['name', 'app_label', 'model']:
            self.assertEqual(
                getattr(ct_db, attr), getattr(content_type, attr))

def _test_permissions(self):
    perm_types = ['add', 'change', 'delete']
    models = [(Poll, 'poll'), (Choice, 'choice')]

    for model, name in models:
        for perm_type in perm_types:
            codename = '%s_%s' % (perm_type, name)
            content_type = ContentType.objects.get_for_model(model)
            num_perms = Permission.objects.filter(
                codename=codename, content_type=content_type).count()
            self.assertEqual(num_perms, 1)

def _test_fixtures_1(self):
    num_polls = Poll.objects.all().count()
    self.assertEqual(num_polls, 1)

    bear_poll = Poll.objects.get(pk=1)
    self.assertEqual(bear_poll.question, 'What bear is best?')

    new_poll = Poll.objects.create(
        question="Did my shoes come off in the plane crash?",
        pub_date=datetime.datetime.now())
    new_poll.save()

def _test_fixtures_2(self):
    num_polls = Poll.objects.all().count()
    self.assertEqual(num_polls, 1)

    wood_poll = Poll.objects.get(pk=2)
    self.assertEqual(wood_poll.question, 'Is there fire wood on the island?')

    new_poll = Poll.objects.create(
        question="Did my shoes come off in the plane crash?",
        pub_date=datetime.datetime.now())
    new_poll.save()

def _test_multiple_fixtures(self):
    num_polls = Poll.objects.all().count()
    self.assertEqual(num_polls, 2)

    wood_poll = Poll.objects.get(pk=2)
    self.assertEqual(wood_poll.question, 'Is there fire wood on the island?')

    bear_poll = Poll.objects.get(pk=1)
    self.assertEqual(bear_poll.question, 'What bear is best?')

    new_poll = Poll.objects.create(
        question="Did my shoes come off in the plane crash?",
        pub_date=datetime.datetime.now())
    new_poll.save()


class DjangoTestCase(TestCase):
    fixtures = ['polls1.json']

    def test_a_skip(self):
        raise SkipTest('Skipping')

    def test_using_content_types_1(self):
        _test_using_content_types(self)

    def test_get_contenttypes_1(self):
        _test_get_contenttypes(self)

    def test_permissions_1(self):
        _test_permissions(self)

    def test_using_content_types_2(self):
        _test_using_content_types(self)

    def test_get_contenttypes_2(self):
        _test_get_contenttypes(self)

    def test_permissions_2(self):
        _test_permissions(self)

    def test_fixtures_1(self):
        _test_fixtures_1(self)

    def test_fixtures_2(self):
        _test_fixtures_1(self)


class DjangoTestCase2(DjangoTestCase):
    fixtures = ['polls2.json']

    def test_fixtures_1(self):
        _test_fixtures_2(self)

    def test_fixtures_2(self):
        _test_fixtures_2(self)


class DjangoTransactionTestCase(TestCase):
    fixtures = ['polls1.json']

    def test_a_skip(self):
        raise SkipTest('Skipping')

    def test_using_content_types_1(self):
        _test_using_content_types(self)

    def test_get_contenttypes_1(self):
        _test_get_contenttypes(self)

    def test_permissions_1(self):
        _test_permissions(self)

    def test_using_content_types_2(self):
        _test_using_content_types(self)

    def test_get_contenttypes_2(self):
        _test_get_contenttypes(self)

    def test_permissions_2(self):
        _test_permissions(self)

    def test_fixtures_1(self):
        _test_fixtures_1(self)

    def test_fixtures_2(self):
        _test_fixtures_1(self)


class DjangoTransactionTestCase2(DjangoTransactionTestCase):
    fixtures = ['polls2.json']

    def test_fixtures_1(self):
        _test_fixtures_2(self)

    def test_fixtures_2(self):
        _test_fixtures_2(self)


class WithTransactionUnitTestCase(UnitTestCase):
    fixtures = ['polls1.json']

    def test_a_skip(self):
        raise SkipTest('Skipping')

    def test_using_content_types_1(self):
        _test_using_content_types(self)

    def test_get_contenttypes_1(self):
        _test_get_contenttypes(self)

    def test_permissions_1(self):
        _test_permissions(self)

    def test_using_content_types_2(self):
        _test_using_content_types(self)

    def test_get_contenttypes_2(self):
        _test_get_contenttypes(self)

    def test_permissions_2(self):
        _test_permissions(self)

    def test_fixtures_1(self):
        _test_fixtures_1(self)

    def test_fixtures_2(self):
        _test_fixtures_1(self)


class WithTransactionUnitTestCase2(WithTransactionUnitTestCase):
    fixtures = ['polls2.json']

    def test_fixtures_1(self):
        _test_fixtures_2(self)

    def test_fixtures_2(self):
        _test_fixtures_2(self)


class NoTransactionUnitTestCase(UnitTestCase):
    fixtures = ['polls1.json']
    use_transaction_isolation = False

    def test_a_skip(self):
        raise SkipTest('Skipping')

    def test_using_content_types_1(self):
        _test_using_content_types(self)

    def test_get_contenttypes_1(self):
        _test_get_contenttypes(self)

    def test_permissions_1(self):
        _test_permissions(self)

    def test_using_content_types_2(self):
        _test_using_content_types(self)

    def test_get_contenttypes_2(self):
        _test_get_contenttypes(self)

    def test_permissions_2(self):
        _test_permissions(self)

    def test_fixtures_1(self):
        _test_fixtures_1(self)

    def test_fixtures_2(self):
        _test_fixtures_1(self)


class NoTransactionUnitTestCase2(NoTransactionUnitTestCase):
    fixtures = ['polls2.json']

    def test_fixtures_1(self):
        _test_fixtures_2(self)

    def test_fixtures_2(self):
        _test_fixtures_2(self)


class MultipleFixtureTestCase(UnitTestCase):
    fixtures = ['polls1.json', 'polls2.json']

    def test_a_skip(self):
        raise SkipTest('Skipping')

    def test_using_content_types_1(self):
        _test_using_content_types(self)

    def test_get_contenttypes_1(self):
        _test_get_contenttypes(self)

    def test_permissions_1(self):
        _test_permissions(self)

    def test_using_content_types_2(self):
        _test_using_content_types(self)

    def test_get_contenttypes_2(self):
        _test_get_contenttypes(self)

    def test_permissions_2(self):
        _test_permissions(self)

    def test_multiple_fixtures(self):
        _test_multiple_fixtures(self)
