from unittest import TestCase
from django.conf import settings


DEFAULT_ROOT_URLCONF = settings.ROOT_URLCONF


class ACustomURLConfTestCase(TestCase):
    def test_root_urlconf_is_default(self):
        from django.conf import settings
        self.assertEqual(settings.ROOT_URLCONF, DEFAULT_ROOT_URLCONF)


class BCustomURLConfTestCase(TestCase):
    urls = 'foo'

    def test_root_urlconf_is_set(self):
        from django.conf import settings
        self.assertEqual(settings.ROOT_URLCONF, 'foo')


class CCustomURLConfTestCase(TestCase):
    def test_root_urlconf_is_default(self):
        from django.conf import settings
        self.assertEqual(settings.ROOT_URLCONF, DEFAULT_ROOT_URLCONF)


class DCustomURLConfTestCase(TestCase):
    urls = 'bar'

    def test_root_urlconf_is_set(self):
        from django.conf import settings
        self.assertEqual(settings.ROOT_URLCONF, 'bar')
