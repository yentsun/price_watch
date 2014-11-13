from datetime import datetime, timedelta
from babel.core import Locale
from babel.numbers import format_currency
from pyramid.view import view_config
from milkpricereport.models import ProductCategory, Product, PriceReport


class EntityView(object):
    """A view class for Milk Price Report entities"""
    def __init__(self, request):
        self.request = request
        self.locale = Locale(request.locale_name)
        self.week_ago = datetime.now() - timedelta(days=7)

    def currency(self, value, symbol=''):
        """Format currency value with Babel"""
        return format_currency(value, symbol, locale=self.locale)

    @view_config(context=ProductCategory,
                 renderer='templates/product_category.mako')
    def product_category(self):
        return {}

    @view_config(context=Product, renderer='templates/product.mako')
    def product(self):
        return {}

    @view_config(context=PriceReport, renderer='templates/report.mako')
    def report(self):
        return {}

    @view_config(renderer='templates/index.mako')
    def index(self):
        return {}