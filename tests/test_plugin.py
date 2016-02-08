from unittest import TestCase

from nosedjango.nosedjango import NoseDjango


class PluginTestBase(TestCase):
    def setUp(self):
        super(PluginTestBase, self).setUp()
        self.plugin = NoseDjango()


class CustomURLConfTestCase(PluginTestBase):
    def test_original_url_conf_is_restored_after_test_run(self):
        pass
