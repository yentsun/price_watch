# -*- coding: utf-8 -*-

import os
import shutil
import unittest
import datetime
import transaction

from price_watch.models import (PriceReport, Merchant, Product, Category,
                                ProductCategory, Reporter,
                                PackageLookupError, StorageManager, HOUR_AGO,
                                MONTH_AGO, DAY_AGO, WEEK_AGO)

STORAGE_DIR = 'storage'
STORAGE_PATH = '{dir}/test.fs'.format(dir=STORAGE_DIR)


def open_storage():
        return StorageManager(path=STORAGE_PATH)


class TestBasicLogic(unittest.TestCase):

    def setUp(self):
        try:
            shutil.rmtree(STORAGE_DIR)
        except OSError:
            pass
        os.mkdir(STORAGE_DIR)
        self.keeper = open_storage()
        category = ProductCategory('milk')
        product = Product(u'Молоко Great Milk 1L')
        merchant = Merchant('test merchant')
        self.keeper.register(category, product, merchant)
        transaction.commit()
        self.keeper.close()
        self.keeper = open_storage()
        self.category = ProductCategory.fetch('milk', self.keeper)
        self.product = Product.fetch(u'Молоко Great Milk 1L', self.keeper)
        self.merchant = Merchant.fetch('test merchant', self.keeper)

    def test_product_add_report(self):
        product = self.product
        product.category = self.category
        report1 = PriceReport(
            price_value=42.6,
            product=product,
            reporter=Reporter('Jill'),
            merchant=Merchant("Scotty's grocery"),
        )
        product.add_report(report1)
        product.add_report(report1)
        transaction.commit()
        self.keeper.close()

        self.keeper = open_storage()
        product = Product.fetch(u'Молоко Great Milk 1L', self.keeper)
        self.assertIn(report1, product.reports)
        self.assertEqual(1, len(product.reports))

    def test_category_add_product(self):
        milk = self.category
        product1 = Product(u'Молоко Great Milk 1L')
        product2 = Product(u'Молоко Greatest Milk 1L')
        milk.add_product(product1, product2)
        self.keeper.register(product1, product2)
        transaction.commit()
        self.keeper.close()

        self.keeper = open_storage()
        milk = ProductCategory.fetch('milk', self.keeper)
        stored_product1 = Product.fetch(u'Молоко Great Milk 1L', self.keeper)
        stored_product2 = Product.fetch(u'Молоко Greatest Milk 1L',
                                        self.keeper)
        self.assertIn(stored_product1, milk.products)
        self.assertIn(stored_product2, milk.products)

    def test_category_remove_product(self):
        self.category.add_product(self.product)
        transaction.commit()
        self.keeper.close()

        keeper = open_storage()
        milk = ProductCategory.fetch('milk', keeper)
        stored_product = Product.fetch(self.product.key, keeper)
        milk.remove_product(stored_product)
        transaction.commit()
        keeper.close()

        keeper = open_storage()
        stored_product = Product.fetch(self.product.key, keeper)
        milk = ProductCategory.fetch('milk', keeper)
        self.assertNotIn(stored_product, milk.products)

    def test_product_add_merchant(self):
        product = self.product
        merchant = Merchant('test merchant')
        product.add_merchant(merchant)
        transaction.commit()
        self.keeper.close()

        self.keeper = open_storage()
        product = Product.fetch(u'Молоко Great Milk 1L', self.keeper)
        self.assertIn(merchant, product.merchants)

    def test_merchant_add_product(self):
        merchant = self.merchant
        product = self.product
        merchant.add_product(product)
        transaction.commit()
        self.keeper.close()

        self.keeper = open_storage()
        product = Product.fetch(u'Молоко Great Milk 1L', self.keeper)
        merchant = Merchant.fetch('test merchant', self.keeper)
        self.assertIn(product, merchant.products)

    def test_merchant_remove_product(self):
        self.merchant.add_product(self.product)
        transaction.commit()
        self.keeper.close()

        keeper = open_storage()
        product = Product.fetch(u'Молоко Great Milk 1L', keeper)
        merchant = Merchant.fetch('test merchant', keeper)
        merchant.remove_product(product)
        transaction.commit()
        keeper.close()

        keeper = open_storage()
        product = Product.fetch(u'Молоко Great Milk 1L', keeper)
        merchant = Merchant.fetch('test merchant', keeper)
        self.assertNotIn(product, merchant.products)

    def test_report_assembly_new_product(self):
        from uuid import uuid4
        product_title = u'Молоко Great Milk TWO 1L'
        reporter_name = 'Jill'
        merchant_title = "Scotty's grocery"
        raw_data1 = {
            'product_title': product_title,
            'price_value': 42.6,
            'url': 'http://scottys.com/products/milk/1',
            'merchant_title': merchant_title,
            'date_time': None,
            'reporter_name': reporter_name
        }
        uuid_ = uuid4()
        report, stats = PriceReport.assemble(storage_manager=self.keeper,
                                             uuid=uuid_,
                                             **raw_data1)
        transaction.commit()
        self.keeper.close()

        self.keeper = open_storage()
        stored_report = PriceReport.fetch(report.key, self.keeper)
        self.assertEqual(report.key, stored_report.key)
        self.assertEqual(report.key, str(uuid_))

        product = Product.fetch(product_title, self.keeper)
        self.assertEqual(product_title, product.title)
        self.assertIn(report, product.reports)

        category = ProductCategory.fetch('milk', self.keeper)
        self.assertIn(product, category.products)

        merchant = Merchant.fetch(merchant_title, self.keeper)
        self.assertEqual(merchant_title, merchant.title)
        self.assertIn(product, merchant)

    def test_report_assembly_stored_product(self):
        product_title = u'Молоко Great Milk three 1L'
        product = Product(product_title, self.category)
        self.keeper.register(product)
        transaction.commit()
        self.keeper.close()

        self.keeper = open_storage()
        reporter_name = 'Jill'
        merchant_title = "Scotty's grocery 2"
        raw_data1 = {
            'product_title': product_title,
            'price_value': 42.6,
            'url': 'http://scottys2.com/products/milk/1',
            'merchant_title': merchant_title,
            'date_time': None,
            'reporter_name': reporter_name
        }
        report, stats = PriceReport.assemble(self.keeper, **raw_data1)
        transaction.commit()
        self.keeper.close()

        self.keeper = open_storage()
        stored_report = PriceReport.fetch(report.key, self.keeper)
        self.assertEqual(report.key, stored_report.key)

        product = Product.fetch(product_title, self.keeper)
        self.assertEqual(product_title, product.title)
        self.assertIn(report, product)

        category = ProductCategory.fetch('milk', self.keeper)
        self.assertIn(product, category)

        merchant = Merchant.fetch(merchant_title, self.keeper)
        self.assertEqual(merchant_title, merchant.title)
        self.assertIn(product, merchant)
        self.assertIn(merchant, product.merchants)

    def test_traverse_yaml(self):

        milk = ProductCategory('milk')

        self.assertEqual(u'молоко', milk.get_data('keyword').split(', ')[0])

        self.assertEqual('diary', milk.get_category_key())

        tuna = ProductCategory('tuna')
        self.assertEqual('fish', tuna.get_category_key())

        chair = ProductCategory('chair')
        self.assertEqual('furniture', chair.get_category_key())

        food = ProductCategory('food')
        self.assertEqual('product_categories', food.get_category_key())

        root = ProductCategory('product_categories')
        self.assertIsNone(root.get_category_key())

    def tearDown(self):
        self.keeper.close()
        shutil.rmtree('storage')


class TestFixtures(unittest.TestCase):

    def setUp(self):
        self.keeper = StorageManager()
        result = self.keeper.load_fixtures('fixtures.json')
        transaction.commit()
        self.report1_key = result['reports'][0].key
        self.report2_key = result['reports'][1].key

    def test_presense_in_references(self):
        milk = ProductCategory.fetch('milk', self.keeper)
        diary = Category.fetch('diary', self.keeper)
        self.assertEqual('diary', diary.title)
        self.assertEqual(4, len(milk.products))
        self.assertIn(64.3, milk.get_prices())

        report1 = PriceReport.fetch(self.report1_key, self.keeper)
        self.assertEqual(55.6, report1.normalized_price_value)
        self.assertIs(milk, report1.product.category)
        self.assertEqual(u'Московский магазин', report1.merchant.title)
        self.assertEqual('Jack', report1.reporter.name)
        self.assertIs(diary, milk.category)
        self.assertIn(milk, diary.categories)

    def test_product_category_median(self):
        milk = ProductCategory.fetch('milk', self.keeper)
        self.assertEqual(50.75, milk.get_price())

    def test_product_category_median_location(self):
        milk = ProductCategory.fetch('milk', self.keeper)
        self.assertEqual(45.9, milk.get_price(location=u'Санкт-Петербург'))
        self.assertEqual(55.6, milk.get_price(location=u'Москва'))

    def test_product_category_median_ignore_irrelevant(self):
        raw_data1 = {
            'product_title': u'Молоко Great Milk 0,5л',
            'price_value': 32.6,
            'url': 'http://scottys.com/products/milk/10',
            'merchant_title': "Scotty's grocery",
            'date_time': None,
            'reporter_name': 'Jill'
        }
        PriceReport.assemble(storage_manager=self.keeper, **raw_data1)
        transaction.commit()
        milk = ProductCategory.fetch('milk', self.keeper)
        self.assertEqual(50.75, milk.get_price())

    def test_product_category_get_locations(self):
        milk = ProductCategory.fetch('milk', self.keeper)
        self.assertIn(u'Москва', milk.get_locations())
        self.assertIn(u'Санкт-Петербург', milk.get_locations())

    def test_report_assembly(self):
        raw_data1 = {
            'product_title': u'Молоко Great Milk 1L',
            'price_value': 42.6,
            'url': 'http://scottys.com/products/milk/1',
            'merchant_title': "Scotty's grocery",
            'date_time': None,
            'reporter_name': 'Jill'
        }
        raw_data2 = {
            'product_title': u'Молоко Great Milk 0.93 L',
            'price_value': 50,
            'url': 'http://scottys.com/products/milk/5',
            'merchant_title': "Scotty's grocery",
            'date_time': None,
            'reporter_name': 'Jill'
        }
        raw_data3 = {
            'product_title': u'Сметана Great Sour Cream 450g',
            'price_value': 60.4,
            'url': 'http://scottys.com/products/sc/6',
            'merchant_title': "Scotty's grocery",
            'date_time': datetime.datetime(2014, 10, 5),
            'reporter_name': 'Jill'
        }
        raw_data4 = {
            'product_title': u'Сметана Great Sour Cream 987987g',
            'price_value': 60.4,
            'url': 'http://scottys.com/products/sc/8978',
            'merchant_title': "Scotty's grocery",
            'date_time': datetime.datetime(2014, 10, 5),
            'reporter_name': 'Jill'
        }
        raw_data5 = {
            'product_title': u'Картофель Вегетория для варки 3кг',
            'price_value': 80.5,
            'url': 'http://scottys.com/products/pot/324',
            'merchant_title': "Scotty's grocery",
            'reporter_name': 'Jill'
        }
        report1, stats1 = PriceReport.assemble(storage_manager=self.keeper,
                                               **raw_data1)
        report2, stats2 = PriceReport.assemble(storage_manager=self.keeper,
                                               **raw_data2)
        report3, stats3 = PriceReport.assemble(storage_manager=self.keeper,
                                               **raw_data3)
        report5, stats5 = PriceReport.assemble(storage_manager=self.keeper,
                                               **raw_data5)
        try:
            PriceReport.assemble(storage_manager=self.keeper, **raw_data4)
        except PackageLookupError:
            pass
        transaction.commit()

        # check category and products
        milk = ProductCategory.fetch('milk', self.keeper)
        sc = ProductCategory.fetch('sour cream', self.keeper)
        self.assertEqual(6, len(milk.products))
        self.assertIn(42.6, milk.get_prices())
        product1 = Product.fetch(u'Молоко Great Milk 1L', self.keeper)
        product2 = Product.fetch(u'Молоко Great Milk 0.93 L', self.keeper)
        self.assertIs(milk, product1.category)
        self.assertEqual('1 l', product1.package.title)
        self.assertEqual('0.93 l', product2.package.title)
        self.assertEqual(1, product1.package_ratio)
        self.assertEqual(0.93, product2.package_ratio)
        self.assertIn(product1, milk.products)
        self.assertEqual('sour cream', report3.product.category.title)
        self.assertIn(u'Сметана Great Sour Cream 450g',
                      [p.title for p in sc.products])
        self.assertNotIn(u'Сметана Great Sour Cream 987987g',
                         [p.title for p in sc.products])

        # check references
        potato = ProductCategory.fetch('potato', self.keeper)
        self.assertIn(report5, PriceReport.fetch_all(self.keeper))
        self.assertIn(report5, potato.products[0].reports)
        self.assertIn(report5,
                      Product.fetch(u'Картофель Вегетория для варки 3кг',
                                    self.keeper).reports)

        # check reporter
        jill = Reporter.fetch('Jill', self.keeper)
        self.assertIs(jill, report1.reporter)
        self.assertIs(jill, report2.reporter)
        self.assertIs(jill, report3.reporter)

        # check price calculations
        self.assertEqual(42.60, round(report1.normalized_price_value, 2))
        self.assertEqual(53.76, round(report2.normalized_price_value, 2))
        self.assertEqual(53.69, round(report3.normalized_price_value, 2))

        # check merchant
        merchant = Merchant.fetch("Scotty's grocery", self.keeper)
        self.assertIs(merchant, report1.merchant)
        self.assertIn(merchant, product1.merchants)
        self.assertIn(product1, merchant)

        # check datetime that is not now
        date_in_past = datetime.datetime(2014, 10, 5)
        self.assertEqual(date_in_past, report3.date_time)

        # check if no false product is registered
        false_product = Product.fetch(u'Сметана Great Sour Cream 987987g',
                                      self.keeper)
        self.assertIsNone(false_product)

    def test_representation(self):
        milk = ProductCategory.fetch('milk', self.keeper)
        self.assertIn(u"55.6-Молоко Красная Цена у/паст. 3.2% 1л"
                      u"-Московский магазин-"
                      u"Москва-Jack",
                      [unicode(r) for r in milk.get_reports()])

    def test_strait_product_price(self):
        product = Product.fetch(u'Молоко Красная Цена у-паст. 3.2% 1л',
                                self.keeper)
        self.assertEqual(55.6, product.get_price())

    def test_merchant_added_to_product(self):
        raw_data = {
            "price_value": 50.4,
            "url": "http://eddies.com/products/milk/1",
            "product_title": u"Молоко Красная Цена у/паст. 3.2% 1л",
            "merchant_title": "Eddie's grocery",
            "reporter_name": "Jack",
            'date_time': DAY_AGO,
        }
        PriceReport.assemble(storage_manager=self.keeper, **raw_data)
        transaction.commit()
        product = Product.fetch(u'Молоко Красная Цена у-паст. 3.2% 1л',
                                self.keeper)
        merchants = list(product.merchants)
        self.assertEqual(2, len(merchants))

    def test_product_price_with_two_merchants(self):

        raw_data = {
            "price_value": 50.4,
            "url": "http://eddies.com/products/milk/1",
            "product_title": u"Молоко Красная Цена у/паст. 3.2% 1л",
            "merchant_title": "Eddie's grocery",
            "reporter_name": "Jack",
            'date_time': DAY_AGO,
        }
        PriceReport.assemble(storage_manager=self.keeper, **raw_data)
        transaction.commit()

        product = Product.fetch(u'Молоко Красная Цена у-паст. 3.2% 1л',
                                self.keeper)

        self.assertEqual(53, product.get_price())

    def test_fetch_all(self):
        products = Product.fetch_all(self.keeper)
        for product in products:
            self.assertIsInstance(product, Product)

    def test_price_from_past_date(self):
        milk = ProductCategory.fetch('milk', self.keeper)
        cheapest_milk_title = u'Молоко The Cheapest Milk!!! 1л'
        PriceReport.assemble(price_value=30.10,
                             product_title=cheapest_milk_title,
                             reporter_name='John',
                             merchant_title="Howie's grocery",
                             url='http://someshop.com/item/344',
                             date_time=HOUR_AGO,
                             storage_manager=self.keeper)
        PriceReport.assemble(price_value=29.10,
                             product_title=cheapest_milk_title,
                             reporter_name='John',
                             merchant_title="Howie's grocery",
                             url='http://someshop.com/item/344',
                             date_time=WEEK_AGO,
                             storage_manager=self.keeper)
        PriceReport.assemble(price_value=25.22,
                             product_title=cheapest_milk_title,
                             reporter_name='John',
                             merchant_title="Howie's grocery",
                             url='http://someshop.com/item/344',
                             date_time=MONTH_AGO,
                             storage_manager=self.keeper)

        transaction.commit()
        cheapest_milk = Product.fetch(cheapest_milk_title, self.keeper)

        self.assertEqual(30.10, cheapest_milk.get_price())
        self.assertEqual(1, cheapest_milk.get_price_delta(DAY_AGO,
                                                          relative=False))
        self.assertEqual(0.034364261168384876,
                         cheapest_milk.get_price_delta(DAY_AGO))
        self.assertEqual(30.10, min(milk.get_prices()))
        self.assertEqual(45.9, milk.get_price())
        self.assertEqual(0.5773195876288658, milk.get_price_delta(DAY_AGO))

    def test_price_report_lifetime(self):
        milk = ProductCategory.fetch('milk', self.keeper)

        # add an outdated report
        PriceReport.assemble(price_value=15.40,
                             product_title=u'Молоко Минувших дней 1л',
                             reporter_name='John',
                             merchant_title="Howie's grocery",
                             url='http://someshop.com/item/345',
                             date_time=MONTH_AGO,
                             storage_manager=self.keeper)
        transaction.commit()
        self.assertEqual(50.75, milk.get_price())

        # add a valid report
        PriceReport.assemble(price_value=10.22,
                             product_title=u'Молоко Минувших дней 1л',
                             reporter_name='John',
                             merchant_title="Howie's grocery",
                             url='http://someshop.com/item/349',
                             date_time=HOUR_AGO,
                             storage_manager=self.keeper)
        transaction.commit()
        self.assertEqual(45.9, milk.get_price())
        self.assertEqual(15.40, milk.get_price(datetime.datetime.now() -
                                               datetime.timedelta(days=25)))
        self.assertIsNone(milk.get_price(datetime.datetime.now() -
                                         datetime.timedelta(days=45)))

    def test_remove_from_category(self):
        product = Product.fetch(u'Молоко Farmers Milk 1L', self.keeper)
        product.category.remove_product(product)
        transaction.commit()

        product = Product.fetch(u'Молоко Farmers Milk 1L', self.keeper)
        milk = ProductCategory.fetch('milk', self.keeper)
        self.assertIsNone(product.category)
        self.assertEqual(55.6, milk.get_price())
        self.assertEqual(45.9, milk.get_price(cheap=True))

    def test_qualified_products(self):
        milk = ProductCategory.fetch('milk', self.keeper)
        fancy_milk_title = u'Молоко The Luxury Milk!!! 0,5л'
        PriceReport.assemble(price_value=40,
                             product_title=fancy_milk_title,
                             url='http"//blah',
                             merchant_title="Howie's grocery",
                             reporter_name='John',
                             storage_manager=self.keeper)
        transaction.commit()

        fancy_milk = Product.fetch(fancy_milk_title, self.keeper)
        qual_products = [p for p, pr in milk.get_qualified_products()]
        self.assertNotIn(fancy_milk, qual_products)
        self.assertEqual(4, len(qual_products))

    def test_key_sanitizing(self):
        title = u'Молоко Красная Цена у/паст. 3.2% 1000г'
        product = Product(title)
        self.assertEqual(u'Молоко Красная Цена у-паст. 3.2% 1000г',
                         product.key)

    def test_delete_report(self):
        victim = PriceReport.fetch(self.report1_key, self.keeper)
        product = victim.product
        victim.delete_from(self.keeper)
        transaction.commit()
        self.assertNotIn(victim, product)
        self.assertNotIn(victim, PriceReport.fetch_all(self.keeper))

    def test_multidict_to_list(self):
        from price_watch.utilities import multidict_to_list
        from webob.multidict import MultiDict
        multidict = MultiDict((
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
        ))
        dict_list = multidict_to_list(multidict)
        self.assertEqual(2, len(dict_list))

    def test_multidict_to_list_diff_valuecount(self):
        from price_watch.utilities import multidict_to_list
        from price_watch.exceptions import MultidictError
        from webob.multidict import MultiDict
        multidict = MultiDict((
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
            ('date_time', '2014.12.30 20:57'),
        ))
        self.assertRaises(MultidictError, multidict_to_list, multidict)

    def test_product_title_similarity(self):
        from difflib import get_close_matches
        titles = [
            u'Молоко Простоквашино пастеризованное 2,5% 930 мл',
            u'Молоко Простоквашино пастеризованное 3,2% 930 мл',
            u'Молоко Домик в деревне ультрапастеризованное 2,5%, 1450г',
            u'Молоко М Лианозовское ультрапастеризованное 1,5%, 950г',
            u'Молоко Новая деревня отборное пастеризованное 3,5%, 1л',
            u'Молоко Тевье молочник Luxury пастеризованное 3,4-4%, 1л',
            u'Молоко Рузское пастеризованное 2,5%, 1000г',
            u'Молоко Ясный луг ультрапастеризованное 3,2%, 1л',
            u'Молоко Parmalat ультрапастеризованное 3,5%, 1л'
        ]

        t1 = u'Молоко Простоквашино, пастеризованное, 2,5% 930 мл'
        t1_1 = u'Молоко ПРОСТОКВАШИНО пастеризованное, 3,2% 930 мл'.lower()
        t2 = u'МОЛОКО "ЯСНЫЙ ЛУГ" ПИТЬЕВОЕ УЛЬТРАПАСТЕРИЗОВАННОЕ 3,5% 1 Л'.lower()
        t3 = u'Молоко М Лианозовское ультрапастеризованное 3,5%, 950г',
        t4 = u'Каждыйдень пастеризованное 3,2% 1л'

        cut_off = 0.7
        cleared_titles = [t.replace(u'Молоко', '') for t in titles]
        self.assertEqual(get_close_matches(t1, cleared_titles, 1, cut_off)[0], cleared_titles[0])
        self.assertEqual(get_close_matches(t1_1, cleared_titles, 1, cut_off)[0], cleared_titles[1])

        self.assertEqual(get_close_matches(t2, cleared_titles, 1, cut_off)[0], cleared_titles[7])

        self.assertEqual(0, len(get_close_matches(t3, cleared_titles, 1, cut_off)))
        res = get_close_matches(t4, cleared_titles, 1, cut_off)
        self.assertEqual(0, len(res))

    def tearDown(self):
        self.keeper.close()