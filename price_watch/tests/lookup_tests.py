# -*- coding: utf-8 -*-

import unittest

from price_watch.models import Product, ProductCategory, PackageLookupError


class TestPackageLookup(unittest.TestCase):

    def setUp(self):
        self.milk = ProductCategory('milk')

    def test_1l(self):
        product = Product(u'Молоко Веселый молочник 1л', category=self.milk)
        self.assertEqual('1 l', product.get_package_key())
        self.assertTrue(product.get_package().is_normal(self.milk))
        self.assertEqual(1, product.get_package().get_ratio(self.milk))

    def test_950g(self):
        product3 = Product(u'Молоко Веселый молочник 950г', category=self.milk)
        product4 = Product(u'Молоко Веселый молочник 950 г',
                           category=self.milk)
        self.assertEqual('0.95 kg', product3.get_package_key())
        self.assertEqual('0.95 kg', product4.get_package_key())
        self.assertFalse(product4.get_package().is_normal(self.milk))
        self.assertEqual(0.93,
                         round(product4.get_package().get_ratio(self.milk), 2))

    def test_unknown(self):
        product5 = Product(u'Молоко Веселый молочник 999,4599 г',
                           category=self.milk)
        self.assertRaises(PackageLookupError, product5.get_package_key)

    def test_05l(self):
        product6 = Product(u'Молоко Веселый молочник 0,5л', category=self.milk)
        self.assertEqual('0.5 l', product6.get_package().title)

    def test_250g_comma_preceding(self):
        sour_cream025 = Product(u'Сметана Углече Поле органическая 15%, 250г')
        key = sour_cream025.get_category_title()
        sour_cream = ProductCategory(key)
        self.assertEqual('0.25 kg', sour_cream025.get_package_key())
        self.assertEqual(0.625,
                         sour_cream025.get_package().get_ratio(sour_cream))

    def test_10pieces(self):
        product3_title = u'Яйцо Окское куриное С0 белое десяток'
        self.assertEqual('10 pcs',
                         Product(product3_title).get_package_key())

    def test_20pieces(self):
        egg = ProductCategory('chicken egg')
        product4_title = u'Яйцо динозавриное столовое, 20шт'
        self.assertEqual(2,
                         Product(product4_title).get_package().get_ratio(egg))

    def test_500g_model_preceding(self):
        product = Product(u'Спагетти PASTA ZARA №4,500г')
        self.assertEqual('0.5 kg', product.get_package_key())

    def test_1l_dot_preceding(self):
        product = Product(u'Молоко Пармалат 3.5% стерил.1л')
        self.assertEqual('1 l', product.get_package_key())

    def test_1l_plus_05l(self):
        product = Product(u'Молоко Углече Поле органическое пастеризованное '
                          u'отборное 3,6%-5,2%, 1л + 0,5л подарок')
        self.assertEqual('1.5 l', product.get_package_key())

    def test_175g_space_and_comma_preceding(self):
        product = Product(u'Сметана Рузская 20%, 175г')
        self.assertEqual('0.175 kg', product.get_package_key())

    def test_1_5kg(self):
        category = ProductCategory('rice')
        product = Product(u'Рис АГРОАЛЬЯНС краснодарский 1,5кг',
                          category=category)
        self.assertEqual('1.5 kg', product.get_package_key())

    def test_025kg_dot_and_text_preceding(self):
        product = Product(u'Хлеб Геркулес зерновой половин.нар.0.25кг ХД')
        self.assertEqual('0.25 kg', product.get_package_key())

    def test_085l(self):
        product = Product(u'МОЛОКО 3,2% п/п 0,85л КИРЗА',)
        self.assertEqual('0.85 l', product.get_package_key())

    def test_900g(self):
        product = Product(u'Гречка Maltagliati ядрица 900г')
        self.assertEqual('0.9 kg', product.get_package_key())

    def test_02kg_decimal_dot(self):
        product = Product(u'Сметана 15% 0.2кг стакан Пискаревский')
        self.assertEqual('0.2 kg', product.get_package_key())

    def test_4x0075g(self):
        product = Product(u'Булочка Щелковохлеб для хот-дога 0,3кг (4*0,075г)')
        self.assertEqual('0.3 kg', product.get_package_key())

    def test_12x1l(self):
        product = Product(u'Молоко Parmalat ультрапастеризованное 3,5%, 12*1л')
        self.assertEqual('12 l', product.get_package_key())

    def test_100g(self):
        product = Product(u'Глазурь Др.Откер сахарн.вкус марципана 100г')
        self.assertEqual('0.1 kg', product.get_package_key())

    def test_5x100g_asterisk(self):
        product = Product(u'Глазурь Др.Откер сахарн.вкус марципана 5*100г')
        self.assertEqual('0.5 kg', product.get_package_key())

    def test_5x100g(self):
        product = Product(u'Глазурь Др.Откер сахарн.вкус марципана 5х100г')
        self.assertEqual('0.5 kg', product.get_package_key())

    def test_05kg(self):
        product = Product(u'Сахар рафинад МОН КАФЕ фигурный 0,5 кг')
        self.assertEqual('0.5 kg', product.get_package_key())

    def test_04kg(self):
        product = Product(u'Хлеб Мультисид Английск.диетич.нар.0.4кг Каравай')
        self.assertEqual('0.4 kg', product.get_package_key())

    def test_045kg_model_preceding(self):
        product = Product(u'Макароны ШЕБЕКИНСКИЕ, ракушка №393,450г')
        self.assertEqual('0.45 kg', product.get_package_key())

    def test_1kg_12kg(self):
        product = Product(u'Томаты сливка, 1,0-1,2кг')
        self.assertEqual('1.1 kg', product.get_package_key())
