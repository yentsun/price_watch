# -*- coding: utf-8 -*-

import datetime
import json

from babel.core import Locale
from babel.numbers import format_currency
from babel.dates import format_datetime
from mako.exceptions import TopLevelLookupException
from pyramid.view import view_config, view_defaults
from pyramid.renderers import render_to_response, render
from pyramid.httpexceptions import HTTPBadRequest, HTTPNotFound
from pyramid_dogpile_cache import get_region

from price_watch.models import (Page, PriceReport, PackageLookupError,
                                CategoryLookupError, ProductCategory, Product,
                                ProductPackage, Merchant)
from price_watch.utilities import multidict_to_list
from price_watch.exceptions import MultidictError

MULTIPLIER = 1
general_region = get_region('general')


def namespace_predicate(class_):
    """
    Custom predicate to check context for being a namespace
    """
    def check_namespace(context, request):
        try:
            return context == request.root[class_.namespace]
        except KeyError:
            return False
    return check_namespace


def get_datetimes(days):
    """Return list with days back range"""

    result = list()
    for count in range(0, int(days)):
        date = datetime.date.today() + datetime.timedelta(-1*MULTIPLIER*count)
        date_time = datetime.datetime.combine(date,
                                              datetime.datetime.now().time())
        result.append(date_time)
    return reversed(result)


class EntityView(object):
    """View class for Milk Price Report entities"""
    def __init__(self, request):
        self.request = request
        self.context = request.context
        self.root = request.root
        self.locale = Locale(request.locale_name)
        self.display_days = int(request.registry.settings['display_days'])
        self.delta_period = (datetime.datetime.now() -
                             datetime.timedelta(days=self.display_days))
        self.fd = format_datetime

    def menu(self):
        """Generate simple menu"""
        items = [
            (u'главная', '/'),
            (u'о проекте', '/pages/about')
        ]
        menu = list()
        for item in items:
            title, path = item
            menu.append((title, path, self.request.path == path))
        return menu

    def currency(self, value, symbol=''):
        """Format currency value with Babel"""
        return format_currency(value, symbol, locale=self.locale)


@view_defaults(custom_predicates=(namespace_predicate(Merchant),))
class MerchantsView(EntityView):
    """Merchant collection views"""

    @view_config(request_method='GET', renderer='json')
    def get(self):
        return list(self.context)


@view_defaults(context=Merchant)
class MerchantView(EntityView):
    """Merchant instance view"""

    @view_config(request_method='GET', renderer='json')
    def get(self):
        return {'key': self.context.key,
                'title': self.context.title,
                'location': self.context.location}

    @view_config(request_method='PATCH', renderer='json')
    def patch(self):
        data = self.request.params
        try:
            self.context.patch(data, self.root)
            return {'key': self.context.key,
                    'title': self.context.title,
                    'location': self.context.location}
        except TypeError as e:
            return HTTPBadRequest(e.message)


@view_defaults(context=Page)
class PageView(EntityView):
    """Page instance views"""

    @view_config(request_method='GET')
    def get(self):
        try:
            return render_to_response(
                'pages/{slug}.mako'.format(**self.context.__dict__),
                {'view': self},
                request=self.request
            )
        except TopLevelLookupException:  # Mako can't find the template
            raise HTTPNotFound


@view_defaults(custom_predicates=(namespace_predicate(Page),))
class PagesView(EntityView):
    """Pages collection views"""

    @view_config(request_method='POST', renderer='json')
    def post(self):
        post_data = self.request.POST
        try:
            new_page, stats = Page.assemble(storage_manager=self.root,
                                            **post_data)
            return {
                'new_page': new_page.slug
            }
        except TypeError as e:
            raise HTTPBadRequest(e.message)


@view_defaults(context=Product)
class ProductView(EntityView):

    @general_region.cache_on_arguments('product')
    def served_data(self, product):
        """Return prepared product data"""
        data = dict()
        data['current_price'] = self.currency(product.get_price())
        data['chart_data'] = list()
        datetimes = get_datetimes(self.display_days)
        for date in datetimes:
            data['chart_data'].append([date.strftime('%d.%m'),
                                      product.get_price(date)])
        data['chart_data'] = json.dumps(data['chart_data'])
        data['reports'] = list()
        for report in sorted(product.get_reports(
                from_date_time=self.delta_period),
                reverse=True, key=lambda rep: rep.date_time):
            url = self.request.resource_url(report)
            date = format_datetime(report.date_time, format='short',
                                   locale=self.request.locale_name)
            merchant = report.merchant.title
            location = report.merchant.location
            price = self.currency(report.normalized_price_value)
            data['reports'].append((url, date, merchant, location, price))
        return data

    @view_config(renderer='product.mako', request_method='GET')
    def get(self):
        return self.served_data(self.context)


@view_defaults(custom_predicates=(namespace_predicate(PriceReport),))
class PriceReportsView(EntityView):
    """PriceReports collection views"""

    @view_config(request_method='POST', renderer='json')
    def post(self):
        # TODO Implement validation
        try:
            dict_list = multidict_to_list(self.request.params)
        except MultidictError as e:
            raise HTTPBadRequest(e.message)
        counts = {'product': 0,
                  'category': 0,
                  'package': 0}
        new_report_keys = list()
        error_msgs = list()
        for dict_ in dict_list:
            try:
                report, new_items = PriceReport.assemble(
                    storage_manager=self.root, **dict_)
                new_report_keys.append(report.key)
                prod_is_new, cat_is_new, pack_is_new = new_items
                counts['product'] += int(prod_is_new)
                counts['category'] += int(cat_is_new)
                counts['package'] += int(pack_is_new)
            except (PackageLookupError, CategoryLookupError, ValueError,
                    TypeError) as e:
                error_msgs.append(e.message)
        counts['total'] = len(dict_list)
        counts['report'] = len(new_report_keys)
        counts['error'] = len(error_msgs)
        if len(new_report_keys):
            general_region.invalidate(hard=False)
            reporters = set(self.request.params.getall('reporter_name'))
            # send email
            from pyramid_mailer import get_mailer
            from pyramid_mailer.message import Message
            mailer = get_mailer(self.request)
            message = Message(subject=u'Price Watch: новые данные',
                              sender='no-reply@food-price.net',
                              recipients=["mkorinets@gmail.com"],
                              html=render('email/post_report_stats.mako',
                                          {'counts': counts,
                                           'reporters': reporters,
                                           'error_msgs': error_msgs}))
            mailer.send(message)

            return {
                'new_report_keys': new_report_keys,
                'counts': counts,
                'errors': error_msgs
            }
        else:
            raise HTTPBadRequest('No new reports\n' +
                                 '\n'.join(error_msgs))


@view_defaults(context=PriceReport)
class PriceReportView(EntityView):
    """PriceReport instance views"""

    @view_config(request_method='GET', renderer='report.mako')
    def get(self):
        return {}

    @view_config(request_method='DELETE', renderer='json')
    def delete(self):

        self.context.delete_from(self.root)
        general_region.invalidate(hard=False)
        return {'deleted_report_key': self.context.key}


@view_defaults(context=ProductCategory)
class CategoryView(EntityView):

    @general_region.cache_on_arguments('category')
    def served_data(self, category):
        """Return prepared category data"""

        cat_title = category.get_data('ru_accu_case')
        if not cat_title:
            cat_title = category.get_data('keyword').split(', ')[0]

        package_key = category.get_data('normal_package')
        package_title = ProductPackage(package_key).get_data('synonyms')[0]

        chart_data = list()
        datetimes = get_datetimes(self.display_days)
        for date in datetimes:
            chart_data.append([date.strftime('%d.%m'),
                               category.get_price(date)])

        products = list()
        sorted_products = sorted(category.get_qualified_products(),
                                 key=lambda pr: pr.get_price())
        for num, product in enumerate(sorted_products):
            try:
                price = product.get_price()
                middle_num = int(len(sorted_products) / 2)
                median = (num == middle_num)
                if len(sorted_products) % 2 == 0:
                    median = (num == middle_num or num == middle_num-1)

                # construct data row as tuple
                products.append((
                    num+1,
                    product,
                    self.request.resource_url(product),
                    self.currency(price),
                    int(product.get_price_delta(self.delta_period)*100),
                    median
                ))
            except TypeError:
                pass
        return {'price_data': json.dumps(chart_data),
                'products': products,
                'cat_title': cat_title,
                'package_title': package_title,
                'median_price': self.currency(category.get_price(), u'р.')}

    @view_config(request_method='GET',
                 renderer='product_category.mako')
    def get(self):
        category = self.request.context
        return self.served_data(category)


class RootView(EntityView):
    """General root views"""
    EXCLUDE_LIST = ['sour cream', 'salt', 'chicken egg', 'bread', 'rice']

    @general_region.cache_on_arguments('index')
    @view_config(request_method='GET', renderer='index.mako')
    def get(self):
        root = self.root
        categories = root['categories'].values()
        datetimes = get_datetimes(self.display_days)
        chart_rows = list()
        for date in datetimes:
            row = [date.strftime('%d.%m')]
            for category in categories:
                price = category.get_price(date)
                if category.title not in self.EXCLUDE_LIST and price:
                    row.append(price)
            chart_rows.append(row)
        category_tuples = list()
        chart_titles = list()
        # TODO optimize this
        for category in categories:
            price = category.get_price()
            if price:
                price = self.currency(price)
                url = self.request.resource_path(category)
                title = category.get_data('keyword').split(', ')[0]
                delta = int(category.get_price_delta(self.delta_period)*100)
                package_key = category.get_data('normal_package')
                package_title = ProductPackage(
                    package_key).get_data('synonyms')[0]
                locations = ', '.join(category.get_locations())
                category_tuples.append((url, title, price, delta,
                                        package_title, locations))
                if category.title not in self.EXCLUDE_LIST:
                    chart_titles.append(title)
        time = format_datetime(datetime.datetime.now(), format='long',
                               locale=self.request.locale_name)

        return {'categories': category_tuples,
                'time': time,
                'root': True,
                'chart_titles': json.dumps(chart_titles),
                'chart_rows': json.dumps(chart_rows)}