# -*- coding: utf-8 -*-

import unittest
import json
from webob.multidict import MultiDict
from pyramid import testing
from price_watch.models import PriceReport


class ViewTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_post_report(self):
        from price_watch.views import PriceReportView
        json_data = json.dumps({
            'price_value': '99.9',
            'product_title': u'Молоко Веселый молочник 1л',
            'url': 'http://howies.com/products/milk/1',
            'merchant': "Howie's grocery",
            'reporter': 'Jack'
        })
        post = MultiDict((('json_data', json_data),))
        post.getone('json_data')
        request = testing.DummyRequest(POST=post)
        request.context = PriceReport
        info = PriceReportView(request).post()
        self.assertEqual('ok', info['status'])
        self.assertEqual(u'Молоко Веселый молочник 1л', info['product_title'])
