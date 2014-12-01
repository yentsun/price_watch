# -*- coding: utf-8 -*-

import unittest
import transaction
from webtest import TestApp
from pyramid.paster import bootstrap


class FunctionalTests(unittest.TestCase):

    def setUp(self):
        boot = bootstrap('testing.ini')
        result = boot['root'].load_fixtures('fixtures.json')
        transaction.commit()
        self.testapp = TestApp(boot['app'])
        self.report_key = result['reports'][0].key

    def test_root(self):
        res = self.testapp.get('/', status=200)
        self.assertIn(u'Категории', res.body.decode('utf-8'))
        self.assertIn(u'молоко', res.body.decode('utf-8'))

    def test_category(self):
        res = self.testapp.get('/categories/milk', status=200)
        self.assertIn(u'молоко', res.body.decode('utf-8'))

    def test_product(self):
        res = self.testapp.get(
            u'/products/Молоко Красная Цена у-паст. 3.2% 1л'.encode('utf-8'),
            status=200)
        self.assertIn(u'Молоко Красная Цена у/паст. 3.2% 1л',
                      res.body.decode('utf-8'))

    def test_report_get(self):
        res = self.testapp.get('/reports/{}'.format(self.report_key),
                               status=200)
        self.assertIn(self.report_key, res.body)

    def test_404(self):
        res = self.testapp.get('/rubbishness', status=404)
        self.assertIn('404', res.body)

    def test_report_post_bad_request(self):
        bad_data = [('rubbish_field', 'say wha?')]
        res = self.testapp.post('/reports', bad_data, status=400)
        self.assertIn('400', res.body)

    def test_report_post_bad_category(self):
        data = [
            ('price_value', 55.6),
            ('url', 'http://howies.com/products/milk/4'),
            ('product_title', u'Кефир Веселый молочник 950г'.encode('utf-8')),
            ('merchant_title', "Howie's grocery"),
            ('reporter_name', 'Jack')
        ]
        res = self.testapp.post('/reports', data, status=400)
        self.assertIn('Category lookup failed', res.body)

    def test_report_post_bad_package(self):
        data = [
            ('price_value', 55.6),
            ('url', 'http://howies.com/products/milk/4'),
            ('product_title',
             u'Молоко Веселый молочник 3950г'.encode('utf-8')),
            ('merchant_title', "Howie's grocery"),
            ('reporter_name', 'Jack')
        ]
        res = self.testapp.post('/reports', data, status=400)
        self.assertIn('Package lookup failed', res.body)

    def test_report_post_existent_product(self):
        data = [
            ('price_value', 55.6),
            ('url', 'http://howies.com/products/milk/4'),
            ('product_title',
             u'Молоко Красная Цена у/паст. 3.2% 1л'.encode('utf-8')),
            ('merchant_title', "Howie's grocery"),
            ('reporter_name', 'Jack')
        ]
        res = self.testapp.post('/reports', data, status=200)
        self.assertFalse(res.json_body['stats']['new_product'])
        new_report_key = res.json_body['new_report']
        self.testapp.get('/reports/{}'.format(new_report_key), status=200)

    def test_report_delete(self):
        res = self.testapp.delete('/reports/{}'.format(self.report_key),
                                  status=200)
        self.assertIn('deleted_report_key', res.body)
        self.testapp.get('/reports/{}'.format(self.report_key), status=404)

    def test_page_get(self):
        res = self.testapp.get('/pages/about', status=200)
        self.assertIn(u'О проекте', res.body.decode('utf-8'))

    def test_page_post(self):
        res = self.testapp.post('/pages', [('slug', 'test')], status=200)
        self.assertIn('new_page', res.body)

        self.testapp.get('/pages/test', status=404)