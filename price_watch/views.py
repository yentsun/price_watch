# -*- coding: utf-8 -*-

import datetime
import json
from babel.core import Locale
from babel.numbers import format_currency
from pyramid.view import view_config
from dogpile.cache import make_region
from milkpricereport.models import ProductCategory, Product, PriceReport

MULTIPLIER = 1
region = make_region().configure(
    'dogpile.cache.memory'
)


def get_datetimes(days):
    """Return list with days back range"""

    result = list()
    for count in range(0, int(days)):
        date = datetime.date.today() + datetime.timedelta(-1*MULTIPLIER*count)
        date_time = datetime.datetime.combine(date,
                                              datetime.datetime.now().time())
        result.append(date_time)
    return reversed(result)


def get_category_price_data(category, days=7):
    """This function is to be cached"""
    price_data = list()
    datetimes = get_datetimes(7)
    for date in datetimes:
        price_data.append([date.strftime('%d.%m'),
                           category.get_price(date)])
    return json.dumps(price_data)


class EntityView(object):
    """A view class for Milk Price Report entities"""
    def __init__(self, request):
        self.request = request
        self.locale = Locale(request.locale_name)
        self.week_ago = datetime.datetime.now() - datetime.timedelta(days=7)

    def currency(self, value, symbol=''):
        """Format currency value with Babel"""
        return format_currency(value, symbol, locale=self.locale)

    @region.cache_on_arguments()
    def category_data(self, category):
        """Return cached category data"""
        products = list()
        for num, product in enumerate(sorted(category.get_qualified_products(),
                                             key=lambda pr: pr.get_price())):
            products.append((num+1,
                             product,
                             self.request.resource_url(product),
                             self.currency(product.get_price()),
                             product.get_price_delta(self.week_ago)))
        return {'price_data': get_category_price_data(category),
                'products': products,
                'cat_title': category.get_data('keyword'),
                'median_price': self.currency(category.get_price(), u'р.')}

    @view_config(context=ProductCategory,
                 renderer='templates/product_category.mako')
    def product_category(self):
        category = self.request.context
        return self.category_data(category)

    @view_config(context=Product, renderer='templates/product.mako')
    def product(self):
        return {}

    @view_config(context=PriceReport, renderer='templates/report.mako')
    def report(self):
        return {}

    @view_config(renderer='templates/index.mako')
    def index(self):
        return {}