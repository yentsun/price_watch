# -*- coding: utf-8 -*-

import unittest
import transaction
from webtest import TestApp
from pyramid.paster import bootstrap


class FunctionalTests(unittest.TestCase):

    def setUp(self):
        boot = bootstrap('testing.ini')
        report_keys = boot['root'].load_fixtures('fixtures.json')
        transaction.commit()
        self.testapp = TestApp(boot['app'])
        self.report_key = report_keys[0]

    def test_root(self):
        res = self.testapp.get('/', status=200)
        self.assertIn(u'Категории', res.body.decode('utf-8'))
        self.assertIn(u'молоко', res.body.decode('utf-8'))

    def test_category(self):
        res = self.testapp.get('/categories/milk', status=200)
        self.assertIn(u'молоко', res.body.decode('utf-8'))

    def test_product(self):
        res = self.testapp.get(
            u'/products/Молоко Deli Milk 1L'.encode('utf-8'), status=200)
        self.assertIn(u'Молоко Deli Milk 1L', res.body.decode('utf-8'))

    def test_report_get(self):
        res = self.testapp.get('/reports/{}'.format(self.report_key),
                               status=200)
        self.assertIn(self.report_key, res.body)

    def test_404(self):
        res = self.testapp.get('/rubbishness', status=404)
        self.assertIn('404', res.body)

    def test_report_post(self):

        # bad request
        bad_data = [('rubbish_field', 'say wha?')]
        res = self.testapp.post('/reports', bad_data, status=400)
        self.assertIn('400', res.body)

        # bad category
        data = [
            ('price_value', 55.6),
            ('url', 'http://howies.com/products/milk/4'),
            ('product_title', u'Кефир Веселый молочник 950г'.encode('utf-8')),
            ('merchant_title', "Howie's grocery"),
            ('reporter_name', 'Jack')
        ]
        res = self.testapp.post('/reports', data, status=400)
        self.assertIn('Category lookup failed', res.body)

        # bad package
        data = [
            ('price_value', 55.6),
            ('url', 'http://howies.com/products/milk/4'),
            ('product_title', u'Молоко Веселый молочник 3950г'.encode('utf-8')),
            ('merchant_title', "Howie's grocery"),
            ('reporter_name', 'Jack')
        ]
        res = self.testapp.post('/reports', data, status=400)
        self.assertIn('Package lookup failed', res.body)

        # good request
        data = [
            ('price_value', 55.6),
            ('url', 'http://howies.com/products/milk/4'),
            ('product_title', u'Молоко Веселый молочник 950г'.encode('utf-8')),
            ('merchant_title', "Howie's grocery"),
            ('reporter_name', 'Jack')
        ]
        res = self.testapp.post('/reports', data, status=200)
        self.assertIn('new_report', res.body)