from django.test import TestCase
from django.test.client import Client


class NoseClient(Client):
    is_nose = True

    def __init__(self):
        self.items = []


class CustomClientTestCase(TestCase):
    client_class = NoseClient

    def test_client_is_nose(self):
        assert self.client.is_nose

    def test_AAA_change_client_items(self):
        self.client.items.append(1)

    def test_BBB_client_items_empty(self):
        self.assertEqual(self.client.items, [])
