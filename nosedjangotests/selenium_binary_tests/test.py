from django.test import TransactionTestCase


class SeleniumTestCase(TransactionTestCase):
    def test_modified_binary_path_is_passed_into_driver(self):
        driver = self.driver

        self.assertIn('////', driver.binary._start_cmd)
