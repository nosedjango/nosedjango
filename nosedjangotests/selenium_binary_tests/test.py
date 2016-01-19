from django.test import TransactionTestCase


class SeleniumTestCase(TransactionTestCase):
    def test_simple(self):
        driver = self.driver

        self.assertIn('////', driver.binary._start_cmd)
