from pyramid.view import view_config
from milkpricereport.models import ProductCategory, Product, PriceReport


@view_config(context=ProductCategory,
             renderer='templates/product_category.mako')
def product_category(request):
    return {}


@view_config(context=Product, renderer='templates/product.mako')
def product(request):
    return {}


@view_config(context=PriceReport, renderer='templates/report.mako')
def report(request):
    return {}


@view_config(renderer='templates/index.mako')
def index(request):
    return {}