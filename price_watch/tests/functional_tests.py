# -*- coding: utf-8 -*-

import unittest
import transaction
from webtest import TestApp
from pyramid.paster import bootstrap
from datetime import datetime
from price_watch.models import TWO_WEEKS_AGO


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
        self.assertIn('No new reports', res.body)

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
        self.assertIn('No new reports', res.body)

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
        self.assertEqual(0, res.json_body['counts']['product'])
        new_report_key = res.json_body['new_report_keys'][0]
        self.testapp.get('/reports/{}'.format(new_report_key), status=200)

    def test_post_multiple_reports(self):

        data = [
            ('price_value', 55.6),
            ('url', 'http://howies.com/products/milk/4'),
            ('product_title',
             u'Молоко Красная Цена у/паст. 3.2% 1л'.encode('utf-8')),
            ('merchant_title', "Howie's grocery"),
            ('reporter_name', 'Jack'),

            ('price_value', 45.3),
            ('url', 'http://howies.com/products/milk/5'),
            ('product_title',
             u'Молоко Красная Цена у/паст. 1% 1л'.encode('utf-8')),
            ('merchant_title', "Howie's grocery"),
            ('reporter_name', 'Jack'),

            ('price_value', 67.1),
            ('url', 'http://howies.com/products/milk/6'),
            ('product_title',
             u'Волшебный Элексир Красная Цена у/паст. 1% 1л'.encode('utf-8')),
            ('merchant_title', "Howie's grocery"),
            ('reporter_name', 'Jack'),
        ]
        res = self.testapp.post('/reports', data, status=200)
        self.assertEqual(2, len(res.json_body['new_report_keys']))
        self.assertEqual(1, res.json_body['counts']['product'])
        self.assertEqual(0, res.json_body['counts']['category'])
        self.assertEqual(0, res.json_body['counts']['package'])
        new_report_keys = res.json_body['new_report_keys']
        for key in new_report_keys:
            self.testapp.get('/reports/{}'.format(key), status=200)

        milk_page = self.testapp.get('/categories/milk', status=200)
        self.assertIn(u'45,30', milk_page.html.find('tr', 'info').text)
        self.assertIn(u'50,45', milk_page.html.find('div', 'cat-price').text)

    def test_report_delete(self):
        res = self.testapp.delete('/reports/{}'.format(self.report_key),
                                  status=200)
        self.assertIn('deleted_report_key', res.body)
        self.testapp.get('/reports/{}'.format(self.report_key), status=404)

    def test_page_get(self):
        res = self.testapp.get('/pages/about', status=200)
        self.assertIn(u'О проекте', res.text)

    def test_page_post(self):
        res = self.testapp.post('/pages', [('slug', 'test')], status=200)
        self.assertIn('new_page', res.body)

        self.testapp.get('/pages/test', status=404)

    def test_merchant_patch(self):
        res = self.testapp.patch("/merchants/Howie's grocery",
                                 [('title', 'Fred & Co.')], status=200)
        self.assertEqual('Fred & Co.', res.json_body['title'])
        self.testapp.get("/merchants/Howie's grocery", status=404)
        res = self.testapp.get("/merchants/Fred & Co.", status=200)
        self.assertEqual('Fred & Co.', res.json_body['title'])

    def test_merchants_get(self):
        res = self.testapp.get('/merchants', status=200)
        self.assertIn("Howie's grocery", res.json_body)

    def test_product_chart_data(self):
        data = [
            ('price_value', 55.6),
            ('url', 'http://howies.com/products/milk/4'),
            ('product_title',
             u'Молоко Deli Milk 1L'.encode('utf-8')),
            ('merchant_title', "Howie's grocery"),
            ('reporter_name', 'Jack'),
            ('date_time', TWO_WEEKS_AGO),

            ('price_value', 54.8),
            ('url', 'http://eddies.com/products/milk/4'),
            ('product_title',
             u'Молоко Deli Milk 1L'.encode('utf-8')),
            ('merchant_title', "Eddie's grocery"),
            ('reporter_name', 'Jack'),
            ('date_time', TWO_WEEKS_AGO),

            ('price_value', 62.1),
            ('url', 'http://eddies.com/products/milk/4'),
            ('product_title',
             u'Молоко Deli Milk 1L'.encode('utf-8')),
            ('merchant_title', "Eddie's grocery"),
            ('reporter_name', 'Jack'),
        ]
        self.testapp.post('/reports', data, status=200)

        res = self.testapp.get(u'/products/Молоко Deli Milk 1L'.encode('utf-8'),
                               status=200)
        today_str = datetime.today().strftime('%d.%m')
        weeks_ago_str = TWO_WEEKS_AGO.strftime('%d.%m')
        self.assertIn('["{}", 64.299999999999997]'.format(today_str),
                      res.body)
        self.assertIn('["{}", 55.200000000000003]'.format(weeks_ago_str),
                      res.body)