import unittest

from pyramid import testing


class ViewTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_my_view(self):
        from price_watch.views import product
        request = testing.DummyRequest()
        request.context = testing.DummyResource()
        info = product(request)
        self.assertEqual(info['product'], 'price_watch')
