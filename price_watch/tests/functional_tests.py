# -*- coding: utf-8 -*-

import unittest
import transaction
from webtest import TestApp
from pyramid.paster import bootstrap
from datetime import datetime, timedelta
from babel.dates import format_datetime

from price_watch.models import TWO_WEEKS_AGO


class FunctionalTests(unittest.TestCase):

    def setUp(self):
        boot = bootstrap('testing.ini')
        result = boot['root'].load_fixtures('fixtures.json')
        transaction.commit()
        self.testapp = TestApp(boot['app'])
        self.report = result['reports'][0]
        self.report_key = self.report.key

    def test_root(self):
        res = self.testapp.get('/', status=200)
        self.assertIn(u'<a href="/categories/milk">молоко</a>',
                      res.body.decode('utf-8'))
        self.assertIn(u'Москва', res.body.decode('utf-8'))
        self.assertIn(u'молочная продукция и яйцо', res.body.decode('utf-8'))

    def test_category(self):
        res = self.testapp.get('/categories/milk', status=200)
        self.assertIn(u'молоко', res.body.decode('utf-8'))
        self.assertIn(u'молочная продукция и яйцо', res.body.decode('utf-8'))

    def test_product(self):
        res = self.testapp.get(
            u'/products/Молоко Красная Цена у-паст. 3.2% 1л'.encode('utf-8'),
            status=200)
        self.assertIn(u'Молоко Красная Цена у/паст. 3.2% 1л',
                      res.body.decode('utf-8'))
        self.assertIn(u'молочная продукция и яйцо',
                      res.body.decode('utf-8'))

    def test_report_get(self):
        res = self.testapp.get('/reports/{}'.format(self.report_key),
                               status=200)
        self.assertIn(self.report_key, res.body)

    def test_404(self):
        res = self.testapp.get('/rubbishness', status=404)
        self.assertIn(u'Страница не найдена', res.body.decode('utf-8'))
        res = self.testapp.get('/products/rubbishness', status=404)
        self.assertIn(u'Страница не найдена', res.body.decode('utf-8'))

    def test_report_post_bad_request(self):
        bad_data = [('rubbish_field', 'say wha?')]
        res = self.testapp.post('/reports', bad_data, status=400)
        self.assertIn('400', res.body)

    def test_report_post_bad_category(self):
        data = [
            ('price_value', 55.6),
            ('url', 'http://howies.com/products/milk/4'),
            ('product_title', u'Элексир Веселый молочник 950г'.encode('utf-8')),
            ('merchant_title', "Howie's grocery"),
            ('reporter_name', 'Jack')
        ]
        res = self.testapp.post('/reports', data, status=400)
        self.assertIn(u'Category lookup failed for product '
                      u'"Элексир Веселый молочник 950г"',
                      res.body.decode('utf-8'))

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
        self.assertIn(u'Package lookup failed for product '
                      u'"Молоко Веселый молочник 3950г"',
                      res.body.decode('utf-8'))

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
            ('merchant_title', u"Московский магазин"),
            ('reporter_name', 'Jack'),

            ('price_value', 45.3),
            ('url', 'http://howies.com/products/milk/5'),
            ('product_title',
             u'Молоко Красная Цена у/паст. 1% 1л'.encode('utf-8')),
            ('merchant_title', u"Московский магазин"),
            ('reporter_name', 'Jack'),

            ('price_value', 67.1),
            ('url', 'http://howies.com/products/milk/6'),
            ('product_title',
             u'Волшебный Элексир Красная Цена у/паст. 1% 1л'.encode('utf-8')),
            ('merchant_title', u"Московский магазин"),
            ('reporter_name', 'Jill'),
        ]
        res = self.testapp.post('/reports', data, status=200)
        self.assertEqual(2, len(res.json_body['new_report_keys']))
        self.assertEqual(1, res.json_body['counts']['product'])
        self.assertEqual(0, res.json_body['counts']['category'])
        self.assertEqual(0, res.json_body['counts']['package'])

        new_report_keys = res.json_body['new_report_keys']
        for key in new_report_keys:
            self.testapp.get('/reports/{}'.format(key), status=200)

        errors = res.json_body['errors']
        self.assertIn(u'Category lookup failed for product '
                      u'"Волшебный Элексир Красная Цена у/паст. 1% 1л"',
                      errors)

        milk_page = self.testapp.get('/categories/milk', status=200)
        self.assertIn(u'45,90', milk_page.html.find('tr', 'info').text)
        self.assertIn(u'45,90', milk_page.html.find('div', 'cat_price').text)

        from pyramid_mailer import get_mailer
        registry = self.testapp.app.registry
        mailer = get_mailer(registry)

        self.assertEqual(len(mailer.outbox), 1)
        self.assertEqual(mailer.outbox[0].subject,
                         u'Price Watch: отчеты от Jill, Jack')
        self.assertIn(u'Category lookup failed for product '
                      u'&#34;Волшебный Элексир Красная Цена у/паст. 1% 1л&#34;',
                      mailer.outbox[0].html)
        self.assertIn(u'Jill, Jack', mailer.outbox[0].html)

    def test_post_incorrect_date_format(self):
        data = [
            ('price_value', 55.6),
            ('url', 'http://howies.com/products/milk/4'),
            ('product_title',
             u'Молоко Красная Цена у/паст. 3.2% 1л'.encode('utf-8')),
            ('merchant_title', "Howie's grocery"),
            ('reporter_name', 'Jack'),
            ('date_time', '2014.12.30 20:57')
        ]
        res = self.testapp.post('/reports', data, status=400)
        self.assertIn("time data '2014' does not match "
                      "format '%Y-%m-%d %H:%M:%S'", res.body)

    def test_post_multiple_reports_bad_multidict(self):
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
            ('date_time', '2014-12-1')
        ]
        res = self.testapp.post('/reports', data, status=400)
        self.assertIn('Bad multidict: value counts not equal', res.body)

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
        res = self.testapp.patch(
            u"/merchants/Московский магазин".encode('utf-8'),
            [('title', 'Fred & Co.')],
            status=200)
        self.assertEqual('Fred & Co.', res.json_body['title'])
        self.testapp.get(
            u"/merchants/Московский магазин".encode('utf-8'),
            status=404)
        res = self.testapp.get("/merchants/Fred & Co.", status=200)
        self.assertEqual('Fred & Co.', res.json_body['title'])

    def test_merchants_get(self):
        res = self.testapp.get('/merchants', status=200)
        self.assertIn(u"Московский магазин", res.json_body)

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
            ('date_time', ''),
        ]
        self.testapp.post('/reports', data, status=200)

        res = self.testapp.get(u'/products/Молоко Deli '
                               u'Milk 1L'.encode('utf-8'),
                               status=200)
        today_str = datetime.today().strftime('%d.%m')
        weeks_ago_str = TWO_WEEKS_AGO.strftime('%d.%m')
        self.assertIn('["{}", 64.299999999999997]'.format(today_str),
                      res.body)
        self.assertIn('["{}", 55.200000000000003]'.format(weeks_ago_str),
                      res.body)

    def test_display_days(self):
        data = [
            ('price_value', 59.3),
            ('url', 'http://howies.com/products/milk/4'),
            ('product_title',
             u'Молоко Deli Milk 1L'.encode('utf-8')),
            ('merchant_title', "Howie's grocery"),
            ('reporter_name', 'Jack'),
            ('date_time', datetime.now() - timedelta(weeks=7))
        ]
        self.testapp.post('/reports', data, status=200)
        res = self.testapp.get(u'/products/Молоко Deli '
                               u'Milk 1L'.encode('utf-8'),
                               status=200)
        self.assertNotIn('59,30', res.body)

    def test_location_at_root_view(self):
        res = self.testapp.get('/?location=Санкт-Петербург', status=200)
        self.assertIn(u'Санкт-Петербург', res.body.decode('utf-8'))
        self.assertIn('45,90', res.body.decode('utf-8'))

        res = self.testapp.get('/?location=Москва', status=200)
        self.assertIn(u'Москва', res.body.decode('utf-8'))
        self.assertIn('55,60', res.body.decode('utf-8'))

        res = self.testapp.get('/', status=200)
        self.assertIn('50,75', res.body.decode('utf-8'))

    def test_location_at_category_view(self):
        res = self.testapp.get('/categories/milk?location=Санкт-Петербург',
                               status=200)
        self.assertIn(u'Молоко Балтика ультрапас. 3.2% 1л',
                      res.body.decode('utf-8'))
        self.assertNotIn(u'Молоко Farmers Milk 1L', res.body.decode('utf-8'))
        self.assertIn(u'45,90', res.html.find('div', 'cat_price').text)

        res = self.testapp.get('/categories/milk?location=Москва',
                               status=200)
        self.assertNotIn(u'Молоко Балтика ультрапас. 3.2% 1л',
                         res.body.decode('utf-8'))
        self.assertIn(u'Молоко Farmers Milk 1L', res.body.decode('utf-8'))
        self.assertIn(u'55,60', res.html.find('div', 'cat_price').text)

        res = self.testapp.get('/categories/milk', status=200)
        self.assertIn(u'Молоко Балтика ультрапас. 3.2% 1л',
                         res.body.decode('utf-8'))
        self.assertIn(u'Молоко Farmers Milk 1L', res.body.decode('utf-8'))
        self.assertIn(u'50,75', res.html.find('div', 'cat_price').text)

    def test_noindex_tag(self):
        res = self.testapp.get('/')
        self.assertNotIn('<meta name="robots" content="noindex">', res.text)

        res = self.testapp.get(u'/products/Молоко Deli '
                               u'Milk 1L'.encode('utf-8'))
        self.assertNotIn('<meta name="robots" content="noindex">', res.text)

        res = self.testapp.get('/categories/milk')
        self.assertNotIn('<meta name="robots" content="noindex">', res.text)

        res = self.testapp.get('/reports/{}'.format(self.report_key))
        self.assertIn('<meta name="robots" content="noindex">', res.text)

    def test_description_tag(self):
        res = self.testapp.get(u'/products/Молоко Deli '
                               u'Milk 1L'.encode('utf-8'))
        self.assertIn(u'Текущая цена и история цен на '
                      u'Молоко Deli Milk 1L за последний месяц',
                      res.html.find(attrs={"name": "description"})['content'])

        res = self.testapp.get('/', status=200)
        self.assertIn(u'Динамика цен на '
                      u'продукты за последний месяц',
                      res.html.find(attrs={"name": "description"})['content'])

        res = self.testapp.get('/categories/milk')
        self.assertIn(u'Динамика цен на молоко за последний месяц',
                      res.html.find(attrs={"name": "description"})['content'])

        res = self.testapp.get('/reports/{}'.format(self.report_key))
        date_time = format_datetime(self.report.date_time, format='long',
                                    locale='ru')
        self.assertIn(u'\nОтчет о цене на '
                      u'{}\nу продавца {} за {}'.format(
                          self.report.product.title,
                          self.report.merchant.title,
                          date_time),
                      res.html.find(attrs={"name": "description"})['content'])

    def test_sitemap(self):
        res = self.testapp.get('/sitemap.xml'.encode('utf-8'))
        self.assertIn('urlset', res.xml.tag)
        self.assertIn('http://localhost/pages/about', res.text)
        self.assertIn('http://localhost/products/%D0%9C%D0%BE%D0%BB%D0%BE%D0%'
                      'BA%D0%BE%20Deli%20Milk%201L', res.text)
        self.assertIn('http://localhost/categories/milk', res.text)
        self.assertIn('http://localhost/categories/milk?location=%D0%A1%D0%'
                      'B0%D0%BD%D0%BA%D1%82-%D0%9F%D0%B5%D1%82%D0%B5%D1%'
                      '80%D0%B1%D1%83%D1%80%D0%B3', res.text)
        self.assertIn('http://localhost?location=%D0%A1%D0%'
                      'B0%D0%BD%D0%BA%D1%82-%D0%9F%D0%B5%D1%82%D0%B5%D1%'
                      '80%D0%B1%D1%83%D1%80%D0%B3', res.text)

    def test_empty_category(self):
        self.testapp.get('/categories/pumpkin', status=200)

    def test_empty_product(self):
        self.testapp.get(u'/products/Никому не нужный '
                         u'сахар 3 кг'.encode('utf-8'), status=200)