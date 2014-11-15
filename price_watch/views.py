# -*- coding: utf-8 -*-

import datetime
import json
from babel.core import Locale
from babel.numbers import format_currency
from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import HTTPMethodNotAllowed
from dogpile.cache import make_region
from milkpricereport.models import (ProductCategory, Product, PriceReport)

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
    """View class for Milk Price Report entities"""
    def __init__(self, request):
        self.request = request
        self.context = request.context
        self.root = request.root
        self.locale = Locale(request.locale_name)
        self.week_ago = datetime.datetime.now() - datetime.timedelta(days=7)

    def currency(self, value, symbol=''):
        """Format currency value with Babel"""
        return format_currency(value, symbol, locale=self.locale)


@view_defaults(context=Product)
class ProductView(EntityView):
    @view_config(renderer='templates/product.mako', request_method='GET')
    def get(self):
        return {}


@view_defaults(context=PriceReport)
class PriceReportView(EntityView):

    @view_config(renderer='templates/report.mako',
                 request_method='GET')
    def get(self):
        return {}


@view_defaults(context=ProductCategory)
class CategoryView(EntityView):

    @region.cache_on_arguments()
    def cached_data(self, category):
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

    @view_config(request_method='GET',
                 renderer='templates/product_category.mako')
    def get(self):
        category = self.request.context
        return self.cached_data(category)


class RootView(EntityView):
    """General root views"""

    @view_config(request_method='GET', renderer='templates/index.mako')
    def get(self):
        if self.context is self.root['ProductCategory']:
            return {}
        else:
            return {}

    @view_config(request_method='POST', renderer='json')
    def post(self):
        if self.context is self.root['PriceReport']:
            return {'status': 'post PriceReport'}
        raise HTTPMethodNotAllowed