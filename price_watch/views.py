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
    for count in reversed(range(0, int(days))):
        date = datetime.date.today() + datetime.timedelta(-1*MULTIPLIER*count)
        date_time = datetime.datetime.combine(date,
                                              datetime.datetime.now().time())
        result.append(date_time)
    return result


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

    def __str__(self):
        return self.__class__.__name__

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
        current_price = product.get_price()
        if current_price:
            data['current_price'] = self.currency(current_price)
            data['product_delta'] = int(product.get_price_delta(
                self.delta_period)*100)
            data['last_report_url'] = None
        else:
            data['current_price'] = None
            data['last_report_url'] = self.request.resource_url(
                self.context.get_last_report())
        data['chart_data'] = list()
        datetimes = get_datetimes(self.display_days)
        for date in datetimes:
            data['chart_data'].append([date.strftime('%d.%m'),
                                      product.get_price(date)])
        data['chart_data'] = json.dumps(data['chart_data'])
        data['reports'] = list()

        package_key = product.category.get_data('normal_package')
        data['category_name'] = \
            product.category.get_data('keyword').split(', ')[0]
        data['category_url'] = self.request.resource_url(product.category)
        data['package_title'] = ProductPackage(
            package_key).get_data('synonyms')[0]

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
    def served_data(self, category, location):
        """Return prepared category data"""

        cat_title = category.get_data('ru_accu_case')
        median_price = category.get_price(location=location)
        category_delta = int(category.get_price_delta(self.delta_period,
                                                      location=location)*100)
        if not cat_title:
            cat_title = category.get_data('keyword').split(', ')[0]

        package_key = category.get_data('normal_package')
        package_title = ProductPackage(package_key).get_data('synonyms')[0]

        chart_data = list()
        datetimes = get_datetimes(self.display_days)
        for date in datetimes:
            chart_data.append([date.strftime('%d.%m'),
                               category.get_price(date, location=location)])

        products = list()
        locations = category.get_locations()
        current_path = self.request.resource_url(category)
        sorted_products = sorted(
            category.get_qualified_products(location=location),
            key=lambda pr: pr[1])
        for num, product_tuple in enumerate(sorted_products):
            try:
                product, price = product_tuple
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
                'current_location': location,
                'locations': locations,
                'current_path': current_path,
                'package_title': package_title,
                'median_price': self.currency(median_price),
                'category_delta': category_delta
                if median_price else None}

    @view_config(request_method='GET',
                 renderer='product_category.mako')
    def get(self):
        category = self.request.context
        location = None
        if 'location' in self.request.params:
            location = self.request.params.getone('location')
        return self.served_data(category, location)


class RootView(EntityView):
    """General root views"""
    CHART_EXCLUDE_LIST = ['sour cream', 'salt', 'chicken egg',
                          'bread', 'sugar', 'hard cheese', 'tomato', 'pumpkin',
                          'orange']

    @general_region.cache_on_arguments('index')
    def served_data(self, location):
        """Serve general index data optionally filter by region"""
        categories = self.root['categories'].values()

        # charts
        datetimes = get_datetimes(self.display_days)
        date_column = [date.strftime('%d.%m') for date in datetimes]
        category_columns = list()
        for category in categories:
            if category.title not in self.CHART_EXCLUDE_LIST:
                category_column = [category.get_data('keyword').split(', ')[0]]
                for date in datetimes:
                    category_column.append(
                        category.get_price(date, location=location))
                category_columns.append(category_column)

        # category list
        category_tuples = list()
        all_locations = set()
        for category in categories:
            price = category.get_price(location=location)
            if price:
                price = self.currency(price)
                query = {'location': location} if location else None
                url = self.request.resource_path(category, query=query)
                title = category.get_data('keyword').split(', ')[0]
                delta = int(category.get_price_delta(self.delta_period,
                                                     location=location)*100)
                package_key = category.get_data('normal_package')
                package_title = ProductPackage(
                    package_key).get_data('synonyms')[0]
                cat_locations = category.get_locations()
                all_locations.update(cat_locations)
                locations = ', '.join(cat_locations)
                category_tuples.append((url, title, price, delta,
                                        package_title, locations))
        time = format_datetime(datetime.datetime.now(), format='long',
                               locale=self.request.locale_name)
        return {'categories': category_tuples,
                'time': time,
                'current_location': location,
                'locations': list(all_locations),
                'root': True,
                'date_column': json.dumps(date_column),
                'category_columns': json.dumps(category_columns)}

    @view_config(request_method='GET', renderer='index.mako')
    def get(self):
        location = None
        if 'location' in self.request.params:
            location = self.request.params.getone('location')
        return self.served_data(location)
